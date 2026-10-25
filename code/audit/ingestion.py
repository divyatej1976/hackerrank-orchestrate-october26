"""Participant evidence readers. No expected outputs are read by this module."""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path

from .core import Observation, COLLECTIONS, RESOURCE, category_for, norm, scalars, truth


def record_state(category, record):
    if record.get('status_code') == 404 or record.get('http_status') in (404, '404'):
        return 'ABSENT'
    if record.get('profile', ...) is None:
        return 'ABSENT'
    if 'hits' in record and record['hits'].get('total') == 0:
        return 'ABSENT'
    if category == 'DATA_FLOW':
        return 'ACTIVE' if truth(record.get('enabled', False)) else 'DISABLED'
    if category == 'BACKUP_ARCHIVE':
        return 'ACTIVE' if truth(record.get('restore_allowed', True)) else 'BLOCKED'
    if category in ('ANALYTICS_PROFILE', 'PRODUCT_TELEMETRY', 'SUPPORT_MESSAGE', 'EMAIL_DELIVERY_LOG', 'ACCOUNT_TOMBSTONE'):
        fields = ('email', 'phone', 'email_hash', 'name', 'full_name', 'display_name',
                  'requester_email', 'requester_phone', 'requester_name', 'owner_email')
        personal = any(record.get(k) not in (None, '', '[REDACTED]') for k in fields)
        if category in ('ANALYTICS_PROFILE', 'PRODUCT_TELEMETRY'):
            personal |= any(record.get(k) for k in ('user_id', 'customer_reference', 'subject_reference'))
            return 'IDENTIFIABLE' if personal else 'ANONYMIZED'
        for key in ('message_text', 'message_excerpt', 'body'):
            text = str(record.get(key, ''))
            personal |= bool(re.search(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]+', text))
            personal |= bool(re.search(r'\+\d[\d\s().-]{6,}\d', text))
        return 'IDENTIFIABLE' if personal else 'REDACTED'
    return 'PRESENT'


def add_record(engine, source, record, system, category, time, scope='service', locator='', priority=2):
    if 'record_type' in record and 'result' in record:
        category = record['record_type']
        system = record.get('system', system)
        state = {'FOUND': 'PRESENT', 'NOT_FOUND': 'ABSENT'}.get(record['result'], record['result'])
    else:
        state = record_state(category, record)
    engine.add(Observation(system, record.get('resource_id', ''), category, state, time,
                           source['captured_at'], source['file_id'], scope,
                           record, locator=locator, priority=priority))


def snapshot(engine, source, system, category, records, time, scope):
    present = {r['resource_id'] for r in records if 'resource_id' in r}
    engine.snapshots.append((system, scope, time, source['captured_at'], source['file_id'], present, category))
    for i, record in enumerate(records):
        add_record(engine, source, record, system, category, record.get('recorded_at', time),
                   scope, f'{scope}/record/{i}')


def ingest_json(engine, source, path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if 'snapshots' in data:
        for i, snap in enumerate(data['snapshots']):
            collection = snap['collection']
            if collection == 'operational_record_history':
                for r in snap['records']:
                    add_record(engine, source, r, r['system'], r['record_type'], r['recorded_at'], 'service')
                continue
            system, category = COLLECTIONS.get(collection, (snap['data_store'], ''))
            snapshot(engine, source, system, category, snap['records'], snap['captured_at'], 'service')
    elif 'service_exports' in data:
        kinds = {'profile_lookups': 'USER_PROFILE', 'profiles': 'ANALYTICS_PROFILE',
                 'restore_entries': 'BACKUP_ARCHIVE', 'exports': 'USER_EXPORT',
                 'connectors': 'DATA_FLOW', 'index_queries': 'SEARCH_INDEX_ENTRY',
                 'audit_records': 'SECURITY_AUDIT_LOG', 'tickets': 'SUPPORT_MESSAGE'}
        for system, collections in data['service_exports'].items():
            for name, records in collections.items():
                for record in records:
                    add_record(engine, source, record, system, kinds[name], record['observed_at'])
    elif data.get('records') is not None:
        collection = data.get('collection')
        if collection:
            system, category = COLLECTIONS[collection]
            snapshot(engine, source, system, category, data['records'], data.get('captured_at', source['captured_at']), 'service')
        else:
            for record in data['records']:
                add_record(engine, source, record, record['system'], record['record_type'], record['recorded_at'])


def ingest_sql(engine, source, path):
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    connection.enable_load_extension(False)
    denied = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}

    def authorize(action, arg1, arg2, db, trigger):
        if action in denied or action == sqlite3.SQLITE_PRAGMA:
            if action == sqlite3.SQLITE_PRAGMA and arg1 == 'foreign_keys':
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and arg2 not in ('json_valid',):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(authorize)
    ticks = [0]

    def progress():
        ticks[0] += 1
        return int(ticks[0] > 100000)

    connection.set_progress_handler(progress, 1000)
    try:
        connection.executescript(path.read_text(encoding='utf-8-sig'))
        tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            if not re.fullmatch(r'[A-Za-z_0-9]+', table):
                raise ValueError('Unsafe snapshot table identifier')
            if table == 'snapshot_scope':
                continue
            rows = [dict(r) for r in connection.execute(f'SELECT * FROM "{table}"')]
            if 'customer_data_' in table and ('record_json' in (rows[0] if rows else {})):
                groups = {}
                for row in rows:
                    groups.setdefault((row['origin_system'], row['collection_name']), []).append(json.loads(row['record_json']))
                # Every topology table is a full capture of its known collections.
                for (system, collection), records in groups.items():
                    _, category = COLLECTIONS.get(collection, (system, ''))
                    snapshot(engine, source, system, category, records, source['captured_at'], table)
            else:
                base = table
                for known in sorted(COLLECTIONS, key=len, reverse=True):
                    if table == known or table.startswith(known+'_'):
                        base = known
                        break
                if table.startswith('search_documents_'):
                    base = 'customer_search_documents'
                if base not in COLLECTIONS:
                    continue
                system, category = COLLECTIONS[base]
                snapshot(engine, source, system, category, rows, source['captured_at'], table)
    finally:
        connection.close()


KV = re.compile(r'([A-Za-z_][\w]*)=("(?:[^"\\]|\\.)*"|\S+)')


def typed_fields(data):
    """Log encodings often stringify SQL/JSON null; it is not retained PII."""
    return {k: None if isinstance(v, str) and v.casefold() in ('null', 'none') else v
            for k, v in data.items()}


def log_fields(line):
    if '{' in line:
        try:
            return typed_fields(json.loads(line[line.index('{'):]))
        except json.JSONDecodeError:
            pass
    data = {k: (json.loads(v) if v.startswith('"') else v) for k, v in KV.findall(line)}
    if 'message' in data and 'function' in data:
        data.update(log_fields(data['message']))
        data['service'] = data['function']
        data['trace_id'] = data.get('requestId')
    bracket = re.match(r'^\S+ \[\w+\] \[([^]]+)\] \[([^]]+)\] (\w+):', line)
    if bracket:
        data.update(service=bracket[1], trace_id=bracket[2], event=bracket[3])
    if ' | ' in line:
        parts = line.split(' | ', 5)
        if len(parts) == 6:
            data.update(service=parts[2], trace_id=parts[3], event=parts[4])
    syslog = re.match(r'^\S+ <\d+>\d+ \S+ (\S+) (\S+)', line)
    if syslog:
        data.update(service=syslog[1], trace_id=syslog[2])
    return typed_fields(data)


def ingest_log(engine, source, path):
    traces = {}
    for line_no, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        data = log_fields(line)
        time_match = re.search(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', line)
        if not time_match:
            continue
        time = time_match[0]
        trace = data.get('trace_id')
        if trace:
            traces.setdefault(trace, {}).update(data)
            combined = dict(traces[trace])
        else:
            combined = data
        resource = data.get('resource_id')
        event = data.get('event', '')
        if not resource:
            continue
        system = data.get('system', data.get('service', ''))
        if system == 'support_replica':
            system = 'support_platform'
        category = data.get('record_type', category_for(resource, system))
        state = None
        if event == 'record_lookup':
            state = {'FOUND': 'PRESENT', 'NOT_FOUND': 'ABSENT'}.get(data['result'], data['result'])
        elif event in ('profile_lookup_completed', 'contact_query_completed', 'audit_record_read_completed', 'contact_lookup_completed'):
            state = 'ABSENT' if str(data.get('rows')) == '0' else 'PRESENT'
            if category == 'ANALYTICS_PROFILE' and event == 'contact_lookup_completed':
                category = 'SECONDARY_IDENTIFIER'
            if system == 'support_platform' and event == 'contact_query_completed':
                category = 'SECONDARY_IDENTIFIER'
        elif event == 'index_query_completed':
            state = 'ABSENT' if data.get('result') == 'miss' or str(data.get('total_hits')) == '0' else 'PRESENT'
        elif event in ('message_pii_scan', 'message_read', 'support_ticket_read_completed'):
            category = 'SUPPORT_MESSAGE'
            state = 'IDENTIFIABLE' if event == 'message_pii_scan' else record_state(category, data)
        elif event == 'attachment_pii_scan':
            category, state = 'SUPPORT_ATTACHMENT', 'PRESENT'
        elif event in ('analytics_identity_scan', 'analytics_profile_read', 'analytics_profile_read_completed'):
            category = 'ANALYTICS_PROFILE'
            state = 'IDENTIFIABLE' if event == 'analytics_identity_scan' else record_state(category, data)
        elif event in ('connector_heartbeat', 'connector_config_loaded', 'connector_config_read_completed'):
            category, state = 'DATA_FLOW', 'ACTIVE' if truth(data.get('enabled')) else 'DISABLED'
        elif event in ('restore_candidate_evaluated', 'restore_authorization_completed', 'restore_policy_read_completed'):
            category = 'BACKUP_ARCHIVE'
            active = truth(data.get('eligible')) or truth(data.get('restore_allowed'))
            state = 'ACTIVE' if active else 'BLOCKED'
        elif event in ('export_download_check_completed', 'export_metadata_read_completed'):
            category, state = 'USER_EXPORT', 'PRESENT' if truth(data.get('available')) else 'ABSENT'
        if state:
            engine.add(Observation(system, resource, category, state, time, source['captured_at'],
                                   source['file_id'], 'service', combined,
                                   locator=f'line:{line_no}', priority=3))


def ingest_text(engine, source, path):
    text = path.read_text(encoding='utf-8-sig')
    for i, line in enumerate(text.splitlines(), 1):
        if ' | ' in line:
            values = [s.strip() for s in line.lstrip('- ').split('|')]
            if len(values) == 6:
                time, system, resource, category, state, subject = values
                add_record(engine, source, dict(resource_id=resource, record_type=category,
                           result=state, subject_reference=subject), system, category, time, locator=f'line:{i}')


def ocr_text(path, cache):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    target = cache / (digest+'.txt')
    if target.exists():
        return target.read_text(encoding='utf-8-sig')
    cache.mkdir(parents=True, exist_ok=True)
    if os.name == 'nt':
        script = Path(__file__).resolve().parents[1] / 'extract_windows_ocr.ps1'
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                 '-File', str(script), '-ImagePath', str(path)],
                                capture_output=True, timeout=45)
        text = result.stdout.decode('utf-8-sig', errors='replace')
        if result.returncode or result.stderr or not text.strip():
            raise RuntimeError('Windows OCR failed; run with local media access or install tesseract')
    elif shutil.which('tesseract'):
        result = subprocess.run(['tesseract', str(path), 'stdout'], capture_output=True, text=True, timeout=45, check=True)
        text = result.stdout
    else:
        raise RuntimeError('Screenshot OCR requires Windows OCR or tesseract')
    target.write_text(text, encoding='utf-8')
    return text


EMAIL = re.compile(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]+')


def media_context(text, contexts, identities):
    """A row's explicit, even unknown, email vetoes page-level ownership."""
    matching = [(region, loc, identities.match(region)) for region, loc in contexts]
    matching = [item for item in matching if item[2]]
    if matching:
        return ('\n'.join(item[0] for item in matching),
                set().union(*(item[2] for item in matching)),
                ';'.join(item[1] for item in matching))
    links = identities.match(text)
    row_has_email = any(EMAIL.search(region) for region, _ in contexts)
    if len(links) == 1 and len(set(EMAIL.findall(text))) <= 1 and not row_has_email:
        return text, links, 'single-subject document'
    return '\n'.join(region for region, _ in contexts), set(), 'unattributed visual resource'


def ingest_media(engine, source, path):
    layout = None
    if path.suffix.lower() == '.pdf':
        from pypdf import PdfReader
        text = '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)
        if not text.strip():
            raise ValueError('Scanned PDF requires OCR; no extractable text')
    else:
        cache = engine.dataset.parent / '.runtime' / 'ocr'
        cached = (cache / (hashlib.sha256(path.read_bytes()).hexdigest()+'.txt')).exists()
        engine.ocr_stats['cache_hits' if cached else 'calls'] += 1
        text = ocr_text(path, cache)
        from .layout import read_layout
        layout_path = cache / (hashlib.sha256(path.read_bytes()).hexdigest()+'.layout-v2.json')
        layout_cached = layout_path.exists()
        layout = read_layout(path, cache)
        if layout:
            engine.ocr_stats['cache_hits' if layout_cached else 'calls'] += 1
    text = re.sub(r'\buser\s*_?\s+(\d+)\b', r'user_\1', text)
    # OCR resource spellings are matched literally. Uncertain/malformed IDs are
    # not repaired using case numbers or expected answers.
    resources = set(RESOURCE.findall(text))
    links = engine.identities.match(text)
    local_regions = {}
    if layout:
        from .layout import resource_regions
        for resource, region, locator in resource_regions(layout):
            region = re.sub(r'\buser\s*_?\s+(\d+)\b', r'user_\1', region)
            local_regions.setdefault(resource, []).append((region, locator))
            resources.add(resource)
    origin = source['origin']
    # Catalog rows explicitly connect otherwise opaque object/document names to
    # modeled resources. Match the supplied alias literally, not by ID arithmetic.
    for activity in engine.activities:
        if activity['event_type'] != 'LINK_RESOURCE_IDENTITY':
            continue
        alias = re.search(r'\(([^)]+)\)', activity['details'])
        if alias and alias[1] in text and activity['resource_id'] not in resources:
            resource = activity['resource_id']
            category = category_for(resource)
            if not category and 'belongs only' in activity['details']:
                category = 'SUPPORT_ATTACHMENT'
            if category:
                alias_state = 'PRESENT'
                if category == 'ACCOUNT_TOMBSTONE':
                    alias_state = 'IDENTIFIABLE' if re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]+', text) else 'REDACTED'
                engine.add(Observation(activity['target_system'], resource, category,
                                       alias_state, source['captured_at'], max(source['captured_at'], activity['event_time']),
                                       source['file_id'], 'service', {'alias': alias[1]},
                                       links=engine.identities.match(activity['details']), locator='catalog-linked media'))
    for resource in resources:
        contexts = local_regions.get(resource, [])
        context, resource_links, locator = media_context(text, contexts, engine.identities)
        category = category_for(resource)
        system = next((s for s, c in COLLECTIONS.values() if c == category), origin)
        if category == 'MARKETING_PROFILE':
            system = 'marketing_platform'
        if category == 'SUPPORT_MESSAGE':
            # A document with attachment/upload properties is not a shared message.
            if re.search(r'attachment|uploaded|uploader|file name', text, re.I):
                category = 'SUPPORT_ATTACHMENT'
        # Ordinary statements contain order references, not necessarily a modeled
        # legal_hold resource. Do not manufacture one from an order number.
        record = {'resource_id': resource, 'extracted_text': context}
        state = 'PRESENT'
        if category == 'ANALYTICS_PROFILE':
            state = 'IDENTIFIABLE' if EMAIL.search(context) else 'ANONYMIZED'
        elif category == 'DATA_FLOW':
            state = 'DISABLED' if re.search(r'\bdisabled\b', context, re.I) else 'ACTIVE'
        elif category == 'BACKUP_ARCHIVE':
            state = 'BLOCKED' if re.search(r'\bblocked\b|restore.*denied', context, re.I) else 'ACTIVE'
        elif category == 'SUPPORT_MESSAGE':
            state = 'IDENTIFIABLE' if EMAIL.search(context) else 'REDACTED'
        engine.add(Observation(system, resource, category, state, source['captured_at'],
                               source['captured_at'], source['file_id'], 'service', record,
                               links=set(resource_links), locator=locator, priority=0))


def ingest_file(engine, source, path):
    readers = {'.json': ingest_json, '.sql': ingest_sql, '.log': ingest_log,
               '.txt': ingest_text, '.png': ingest_media, '.pdf': ingest_media}
    if path.suffix.lower() not in readers:
        raise ValueError('Unsupported evidence format')
    readers[path.suffix.lower()](engine, source, path)
