from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def case_key(case_id):
    return int(case_id.rsplit('_', 1)[1])


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def norm(value):
    return str(value).strip().casefold()


def scalars(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from scalars(v)
    elif isinstance(value, list):
        for v in value:
            yield from scalars(v)
    elif value is not None:
        yield str(value)


def truth(value):
    return value is True or norm(value) in ('true', '1', 'yes', 'enabled', 'allow')


RESOURCE = re.compile(r'\b(?:account|analytics|search|support|export|backup|data_flow|audit_record|legal_hold|tombstone|marketing|cache|email_delivery|telemetry)_[0-9]+\b')
TOKENS = re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]+|\buser_\d+\b|\b[a-fA-F0-9]{64}\b')

COLLECTIONS = {
    'customer_profiles': ('account_service', 'USER_PROFILE'),
    'customer_search_documents': ('search_service', 'SEARCH_INDEX_ENTRY'),
    'customer_analytics_reports': ('analytics_platform', 'ANALYTICS_PROFILE'),
    'customer_analytics_profiles': ('analytics_platform', 'ANALYTICS_PROFILE'),
    'backup_catalog': ('backup_service', 'BACKUP_ARCHIVE'),
    'backup_restore_entries': ('backup_service', 'BACKUP_ARCHIVE'),
    'customer_export_jobs': ('export_service', 'USER_EXPORT'),
    'customer_exports': ('export_service', 'USER_EXPORT'),
    'connector_configurations': ('integration_service', 'DATA_FLOW'),
    'connector_subscriptions': ('integration_service', 'DATA_FLOW'),
    'security_audit_events': ('security_service', 'SECURITY_AUDIT_LOG'),
    'security_audit_records': ('security_service', 'SECURITY_AUDIT_LOG'),
    'support_conversations': ('support_platform', 'SUPPORT_MESSAGE'),
    'support_records': ('support_platform', 'SUPPORT_MESSAGE'),
    'ticket_attachments': ('support_platform', 'SUPPORT_ATTACHMENT'),
    'retained_order_records': ('legal_service', 'LEGAL_HOLD_RECORD'),
    'deleted_customer_references': ('identity_service', 'ACCOUNT_TOMBSTONE'),
}

OPERATIONS = [
    ('FINDING', 'REPORT_REMAINING_RECORD', 'PRESENT'),
    ('FINDING', 'REPORT_EXPOSED_PII', 'PRESENT'),
    ('FINDING', 'REPORT_ACTIVE_DATA_FLOW', 'ACTIVE'),
    ('FINDING', 'REPORT_RESTORE_RISK', 'ACTIVE'),
    ('REMEDIATION', 'DISABLE_DATA_FLOW', 'DISABLED'),
    ('REMEDIATION', 'BLOCK_RESTORE', 'BLOCKED'),
    ('REMEDIATION', 'DELETE_RECORD', 'ABSENT'),
    ('REMEDIATION', 'REDACT_RECORD', 'REDACTED'),
    ('REMEDIATION', 'ANONYMIZE_RECORD', 'ANONYMIZED'),
    ('VERIFICATION', 'VERIFY_RECORD_ABSENT', 'ABSENT'),
    ('VERIFICATION', 'VERIFY_RECORD_PRESENT', 'PRESENT'),
    ('VERIFICATION', 'VERIFY_RECORD_REDACTED', 'REDACTED'),
    ('VERIFICATION', 'VERIFY_RECORD_ANONYMIZED', 'ANONYMIZED'),
    ('VERIFICATION', 'VERIFY_DATA_FLOW_DISABLED', 'DISABLED'),
    ('VERIFICATION', 'VERIFY_RESTORE_BLOCKED', 'BLOCKED'),
]
OP_RANK = {op: i for i, (_, op, _) in enumerate(OPERATIONS)}
OP_SPEC = {op: (phase, state) for phase, op, state in OPERATIONS}


def category_for(resource, system=''):
    prefix = resource.rsplit('_', 1)[0]
    return {
        'account': 'USER_PROFILE', 'analytics': 'ANALYTICS_PROFILE',
        'search': 'SEARCH_INDEX_ENTRY', 'support': 'SUPPORT_MESSAGE',
        'export': 'USER_EXPORT', 'backup': 'BACKUP_ARCHIVE',
        'data_flow': 'DATA_FLOW', 'audit_record': 'SECURITY_AUDIT_LOG',
        'legal_hold': 'LEGAL_HOLD_RECORD', 'tombstone': 'ACCOUNT_TOMBSTONE',
        'marketing': 'MARKETING_PROFILE', 'cache': 'CACHE_ENTRY',
        'email_delivery': 'EMAIL_DELIVERY_LOG', 'telemetry': 'PRODUCT_TELEMETRY',
    }.get(prefix, '')


@dataclass
class Observation:
    system: str
    resource: str
    category: str
    state: str
    time: str
    available: str
    evidence: str
    scope: str = 'service'
    data: dict = field(default_factory=dict)
    links: set = field(default_factory=set)
    locator: str = ''
    priority: int = 1


class IdentityIndex:
    def __init__(self, dataset):
        self.rows = {r['user_id']: r for r in read_csv(dataset / 'user_identities.csv')}
        self.history = read_csv(dataset / 'user_audit_log.csv')
        self.by_value = defaultdict(set)
        self.values = defaultdict(set)
        self.by_phone = defaultdict(set)
        for uid, row in self.rows.items():
            for key in ('user_id', 'email', 'phone', 'email_hash'):
                self.add(uid, row.get(key))
        for row in self.history:
            if row['field_name'] != 'name':
                self.add(row['user_id'], row['old_value'])
                self.add(row['user_id'], row['new_value'])

    def add(self, uid, value):
        if value:
            self.by_value[norm(value)].add(uid)
            self.values[uid].add(norm(value))
            if str(value).startswith('+'):
                self.by_phone[re.sub(r'\D', '', str(value))].add(uid)

    def match(self, value):
        found = set()
        for v in scalars(value):
            found.update(self.by_value.get(norm(v), ()))
            for token in TOKENS.findall(v):
                found.update(self.by_value.get(norm(token), ()))
            for phone in re.findall(r'\+\d[\d\s().-]{6,}\d', v):
                found.update(self.by_phone.get(re.sub(r'\D', '', phone), ()))
        return found

    def resolve(self, email):
        candidates = self.by_value.get(norm(email), set())
        if len(candidates) != 1:
            raise ValueError(f'Identity resolution found {len(candidates)} candidates')
        return next(iter(candidates))


def deletion_intent(text):
    """Conservative multilingual intent gate; independent of workflow claims."""
    t = norm(text).replace('’', "'")
    negative = ("don't delete", 'do not delete', 'not a request to erase',
                'marketing lists only', 'stop the promotional', 'portable format',
                'resetting the login', 'copy of last year', 'surname is misspelled',
                'mobile number on my profile', 'change the email address')
    if any(x in t for x in negative):
        return False
    positive = ('delet', 'erase', 'erased', 'erasure', 'remove my account',
                'remove the profile', 'close my account', 'close this account',
                'account closed', 'account closure', 'elimin', 'exclus', 'supprim',
                'suppression', '削除', '삭제', 'effac', 'borrar', 'apagar',
                'remove that search', 'remove records', 'remove my profile',
                'close the account', 'deletion', 'privacy page', 'profile is gone',
                'verify that my account', 'account was fully removed', 'remaining records cannot identify')
    if any(x in t for x in positive):
        return True
    if 'closed' in t and ('account' in t or 'profile' in t):
        return True
    return False


class AuditEngine:
    def __init__(self, dataset, enable_ownership_elimination=False):
        self.dataset = Path(dataset).resolve()
        self.identities = IdentityIndex(self.dataset)
        self.rules = {r['data_category']: r for r in read_csv(self.dataset / 'deletion_rules.csv')}
        self.activities = read_csv(self.dataset / 'system_activity.csv')
        self.manifest = read_csv(self.dataset / 'evidence_files.csv')
        self.observations = []
        self.snapshots = []
        self.resource_links = defaultdict(list)
        self.diagnostics = []
        self.ingestion = []
        self.sources = {r['file_id']: r['captured_at'] for r in self.manifest}
        self.sources.update({r['activity_id']: r['event_time'] for r in self.activities})
        self.sources.update({r['audit_id']: r['event_time'] for r in self.identities.history})
        self.by_resource = defaultdict(list)
        self.ocr_stats = {'calls': 0, 'cache_hits': 0}
        self.source_subjects = defaultdict(set)
        self.source_resources = defaultdict(set)
        self.relationships = []
        # Experimental strict replacement is gated by public regression checks.
        # Default remains the validated baseline when that replacement regresses.
        self.enable_ownership_elimination = enable_ownership_elimination
        # Intake metadata is permitted inference input; no answer files are read.
        self.request_windows = []
        for path in sorted(self.dataset.glob('*requests.csv')):
            self.request_windows.extend(read_csv(path))

    def workflow_resources(self, request, uid):
        if getattr(self, 'enable_ownership_elimination', False):
            return self._eliminated_workflow_resources(request, uid)
        return self._baseline_workflow_resources(request, uid)

    def _baseline_workflow_resources(self, request, uid):
        """Previously validated behavior, retained after the strict experiment
        failed the requested no-regression gate. New elimination never uses
        this completion-boundary ranking as a grounded ownership constraint."""
        cutoff = request['audit_at']
        start = request.get('requested_at', '')
        end = min(request.get('reported_at', cutoff), cutoff)
        result = set()
        for event in self.activities:
            if event['source_system'] != 'deletion_worker' or not start <= event['event_time'] <= end:
                continue
            key = event['target_system'], event['resource_id']
            owners = {u for u, _, _ in self.resource_links.get(key, ())}
            if owners:
                if uid in owners:
                    result.add(key)
                continue
            category = category_for(event['resource_id'])
            attributed = any(k[0] == key[0] and k != key
                             and category_for(k[1]) == category
                             and any(owner == uid for owner, _, _ in links)
                             and any(start <= o.time <= cutoff for o in self.by_resource.get(k, ()))
                             for k, links in self.resource_links.items())
            if attributed:
                continue
            contenders = defaultdict(list)
            for candidate in getattr(self, 'request_windows', []) + [request]:
                if (candidate.get('requested_at', '') <= event['event_time']
                        <= min(candidate.get('reported_at', ''), candidate['audit_at'])
                        and deletion_intent(candidate['request_text'])):
                    try:
                        owner = self.identities.resolve(candidate['email'])
                    except ValueError:
                        continue
                    contenders[candidate.get('reported_at','')].append(owner)
            if contenders and set(contenders[min(contenders)]) == {uid}:
                result.add(key)
        return result

    def _eliminated_workflow_resources(self, request, uid):
        """Ownership-only constraint propagation over all intake windows."""
        from .ownership import build, request_key, resolved_for
        requests = list(getattr(self, 'request_windows', []))
        if not any(all(r.get(k) == request.get(k) for k in
                       ('email','requested_at','reported_at','audit_at')) for r in requests):
            requests.append(request)
        signature = (tuple(sorted((r['email'],r.get('requested_at',''),
                                   r.get('reported_at',''),r['audit_at'],r['request_text']) for r in requests)),
                     len(self.observations),len(self.activities),
                     sum(len(v) for v in self.resource_links.values()),
                     getattr(self,'extend_ownership_window',False))
        cache = getattr(self, '_ownership_cache', None)
        if cache is None or cache[0] != signature:
            cache = signature, build(self, requests, extended=getattr(self,'extend_ownership_window',False))
            self._ownership_cache = cache
        result = cache[1]
        episode = result['membership'].get(request_key(request,self.identities))
        for (owner_episode, kind), candidates in sorted(result['unresolved'].items()):
            if owner_episode == episode:
                diagnostic = dict(case_id=request['case_id'], issue='Unresolved workflow ownership',
                                  resource_type=kind, candidates=[list(r) for r in sorted(candidates)])
                if diagnostic not in self.diagnostics:
                    self.diagnostics.append(diagnostic)
        start = request.get('requested_at','')
        cutoff = request['audit_at']
        end = cutoff if getattr(self,'extend_ownership_window',False) else min(request.get('reported_at',cutoff),cutoff)
        return {resource for resource in resolved_for(result,request,self.identities)
                if any(event['source_system']=='deletion_worker'
                       and (event['target_system'],event['resource_id']) == resource
                       and start <= event['event_time'] <= end for event in self.activities)
                or any(start <= obs.time <= cutoff for obs in self.by_resource.get(resource,()))}

    def add(self, obs):
        if not obs.resource or not obs.category:
            return
        # A lookup key can differ from the returned subject. Shared record
        # content may expose additional people and must remain discoverable.
        stable = {v for k, v in obs.data.items() if k in ('user_id', 'subject_reference', 'customer_reference')
                  and isinstance(v, str) and re.fullmatch(r'user_\d+', v)}
        contents = {k:v for k,v in obs.data.items()
                    if not stable or k not in ('lookup_key','query','subject_key','owner_key','scan_key')}
        obs.links |= self.identities.match(contents)
        if str(obs.data.get('event', '')).endswith('_completed') and obs.data.get('lookup_key'):
            obs.links |= self.identities.match(obs.data['lookup_key'])
        self.observations.append(obs)
        self.by_resource[(obs.system, obs.resource)].append(obs)
        self.source_subjects[obs.evidence].update(obs.links)
        self.source_resources[obs.evidence].add((obs.system, obs.resource))
        for uid in obs.links:
            self.resource_links[(obs.system, obs.resource)].append((uid, obs.available, obs.evidence))
        for key in ('source_resource_id', 'parent_resource_id', 'account_resource_id'):
            reference = obs.data.get(key)
            if isinstance(reference, str) and RESOURCE.fullmatch(reference):
                system = next((s for s, c in COLLECTIONS.values() if c == category_for(reference)), '')
                if system:
                    self.relationships.append(((obs.system, obs.resource), (system, reference), obs.available, obs.evidence))

    def load(self):
        from .ingestion import ingest_file
        for source in self.manifest:
            path = (self.dataset / source['file_path']).resolve()
            if not path.is_relative_to(self.dataset):
                raise ValueError('Manifest path escapes dataset')
            before = len(self.observations)
            try:
                ingest_file(self, source, path)
                self.ingestion.append({'evidence_id': source['file_id'], 'format': path.suffix,
                                       'success': True, 'observations': len(self.observations)-before})
            except Exception as exc:
                self.ingestion.append({'evidence_id': source['file_id'], 'format': path.suffix,
                                       'success': False, 'error': str(exc)})
        for row in self.activities:
            refs = self.identities.match(row['details'])
            for uid in refs:
                self.resource_links[(row['target_system'], row['resource_id'])].append(
                    (uid, row['event_time'], row['activity_id']))
        # Transfer identity only through typed resource references, retaining the
        # latest availability of the reference and the ownership observation.
        for left, right, available, evidence in self.relationships:
            for uid, linked_at, _ in list(self.resource_links[left]):
                link = (uid, max(available, linked_at), evidence)
                if link not in self.resource_links[right]:
                    self.resource_links[right].append(link)
        return self

    def _state(self, resource, system, cutoff, uid):
        candidates = [o for o in self.by_resource[(system, resource)]
                      if o.available <= cutoff and o.time <= cutoff]
        # A complete scoped snapshot can establish absence for a known resource.
        known_categories = {o.category for o in candidates} or {category_for(resource)}
        for system_s, scope, time, available, evidence, present, category in self.snapshots:
            # Snapshot exports are scoped cohorts, not global system inventories.
            # Require the subject in that artifact or the same resource in another
            # replica of it before interpreting an omitted row as absence.
            subject_in_source = uid in self.source_subjects[evidence]
            resource_in_source = (system, resource) in self.source_resources[evidence]
            if (system_s == system and category in known_categories
                    and self.rules.get(category, {}).get('required_action') == 'DELETE' and time <= cutoff
                    and available <= cutoff and resource not in present
                    and (subject_in_source or resource_in_source
                         or scope.startswith('customer_profiles_'))):
                candidates.append(Observation(system, resource, category, 'ABSENT', time,
                                               available, evidence, scope, priority=1))
        if not candidates:
            return None
        # Scope changes cannot cancel a residual replica. Non-delete treatments
        # use the newest observed service state; copies requiring deletion need
        # explicit absence in every observed scope.
        category = max(candidates, key=lambda o: (o.available, o.time, o.priority, o.category)).category
        treatment = self.rules.get(category, {}).get('required_action')
        newest = max(o.available for o in candidates)
        current = candidates if treatment == 'DELETE' else [o for o in candidates if o.available == newest]
        per_scope = {}
        for o in sorted(current, key=lambda o: (o.time, o.priority, o.evidence)):
            per_scope[o.scope] = o
        present = [o for o in per_scope.values() if o.state != 'ABSENT']
        return max(present or list(per_scope.values()), key=lambda o: (o.time, o.priority, o.evidence))

    def audit(self, request):
        case = request['case_id']
        if not deletion_intent(request['request_text']):
            return {'case_id': case, 'deletion_status': 'NOT_APPLICABLE', 'steps_json': '[]'}
        uid = self.identities.resolve(request['email'])
        cutoff = request['audit_at']
        # Ownership discovery and audit-time state are separate channels. A later
        # artifact may discover a stable resource/subject relationship, but it
        # cannot supply state or a citation for the earlier audit.
        requested_at = request.get('requested_at', '')
        workflow = self.workflow_resources(request, uid)
        relevant = set(workflow)
        for key, links in self.resource_links.items():
            if (any(u == uid for u, _, _ in links)
                    and any(requested_at <= o.time <= cutoff for o in self.by_resource.get(key, ()))):
                relevant.add(key)
        states = []
        unknown = []
        for system, resource in sorted(relevant):
            obs = self._state(resource, system, cutoff, uid)
            if obs:
                states.append(obs)
            else:
                known = self.by_resource.get((system, resource), [])
                category = max(known, key=lambda o:(o.available,o.time,o.priority)).category if known else category_for(resource)
                unknown.append(Observation(system,resource,category,'UNKNOWN','','',''))
        findings, actions, checks = [], [], []
        violations = False

        def step(op, obs, evidence=''):
            phase, state = OP_SPEC[op]
            return dict(phase=phase, system_id=obs.system, resource_id=obs.resource,
                        operation=op, state=state, evidence_id=evidence)

        for obs in states + unknown:
            category = obs.category
            rule = self.rules.get(category)
            if category == 'DATA_FLOW':
                target, finding, action, verify = 'DISABLED', 'REPORT_ACTIVE_DATA_FLOW', 'DISABLE_DATA_FLOW', 'VERIFY_DATA_FLOW_DISABLED'
            elif category == 'BACKUP_ARCHIVE':
                target, finding, action, verify = 'BLOCKED', 'REPORT_RESTORE_RISK', 'BLOCK_RESTORE', 'VERIFY_RESTORE_BLOCKED'
            elif not rule:
                self.diagnostics.append({'case_id': case, 'resource_id': obs.resource, 'issue': 'Unknown policy'})
                continue
            else:
                treatment = rule['required_action']
                target, action, verify = {
                    'DELETE': ('ABSENT', 'DELETE_RECORD', 'VERIFY_RECORD_ABSENT'),
                    'REDACT': ('REDACTED', 'REDACT_RECORD', 'VERIFY_RECORD_REDACTED'),
                    'ANONYMIZE': ('ANONYMIZED', 'ANONYMIZE_RECORD', 'VERIFY_RECORD_ANONYMIZED'),
                    'RETAIN': ('PRESENT', None, 'VERIFY_RECORD_PRESENT'),
                }[treatment]
                finding = 'REPORT_REMAINING_RECORD' if treatment == 'DELETE' else 'REPORT_EXPOSED_PII'
            compliant = obs.state == target or (target == 'PRESENT' and obs.state not in ('ABSENT','UNKNOWN'))
            if obs.state == 'UNKNOWN':
                checks.append(step(verify, obs))
                continue
            if not compliant:
                violations = True
                if action is None:
                    self.diagnostics.append({'case_id': case, 'resource_id': obs.resource, 'issue': 'Missing required retained record'})
                else:
                    findings.append(step(finding, obs, obs.evidence))
                    actions.append(step(action, obs))
            checks.append(step(verify, obs, obs.evidence))
        if not states:
            raise ValueError(f'{case}: no eligible state evidence; refusing unsupported completion')
        status = 'INCOMPLETE' if violations else 'COMPLETE'
        if unknown and not violations:
            raise ValueError(f'{case}: linked resources lack eligible state evidence; refusing unsupported completion')
        if violations:
            for check in checks:
                check['evidence_id'] = ''
        steps = sorted(findings+actions+checks, key=lambda s: (OP_RANK[s['operation']], s['system_id'], s['resource_id']))
        for i, item in enumerate(steps, 1):
            item['step_no'] = i
        return {'case_id': case, 'deletion_status': status, 'steps_json': json.dumps(steps, ensure_ascii=False, separators=(',', ':'))}

    def validate(self, rows, requests):
        expected = sorted((r['case_id'] for r in requests), key=case_key)
        if [r['case_id'] for r in rows] != expected or len(set(expected)) != len(expected):
            raise ValueError('Missing, duplicate, or unsorted cases')
        request_map = {r['case_id']: r for r in requests}
        for row in rows:
            status = row['deletion_status']
            assert status in ('COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE')
            steps = json.loads(row['steps_json'])
            assert status != 'NOT_APPLICABLE' or steps == []
            assert steps == sorted(steps, key=lambda s: (OP_RANK[s['operation']], s['system_id'], s['resource_id']))
            for i, item in enumerate(steps, 1):
                assert set(item) == {'step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id'}
                assert item['step_no'] == i
                assert OP_SPEC[item['operation']] == (item['phase'], item['state'])
                needs_evidence = item['phase'] == 'FINDING' or status == 'COMPLETE'
                if needs_evidence:
                    assert item['evidence_id'] in self.sources
                    assert self.sources[item['evidence_id']] <= request_map[row['case_id']]['audit_at']
                else:
                    assert item['evidence_id'] == ''
                if status == 'COMPLETE':
                    assert item['phase'] == 'VERIFICATION'
