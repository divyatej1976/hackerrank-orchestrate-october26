"""Evaluation-only evidence gap, media coverage and experiment reports."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from audit.core import RESOURCE, read_csv
from audit.ingestion import EMAIL, ocr_text
from audit.layout import grouped_rows, read_layout
from audit.ownership import build, request_key, resource_type
from diagnose_ownership import trace

METRICS=('status_accuracy','exact_row_accuracy','sequence_accuracy','step_precision','step_recall','step_f1','field_accuracy')


def values(items):
    return ', '.join(sorted(set(items))) or 'None'


def write_gaps(engine, metrics, destination):
    maps={False:build(engine,engine.request_windows), True:build(engine,engine.request_windows,extended=True)}
    requests={r['case_id']:r for r in read_csv(engine.dataset/'sample_deletion_requests.csv')}
    known={o.resource for o in engine.observations}|{a['resource_id'] for a in engine.activities}
    rows=[];counts=Counter()
    for failure in metrics['failures']:
        q=requests[failure['case_id']]
        ep=maps[False]['membership'][request_key(q,engine.identities)]
        for encoded in failure['missing']:
            step=json.loads(encoded);resource=step['system_id'],step['resource_id'];slot=ep,resource_type(resource)
            normal=maps[False]['candidates'].get(slot,set()) | maps[False]['grounded'].get(slot,set())
            extended=maps[True]['candidates'].get(slot,set()) | maps[True]['grounded'].get(slot,set())
            remaining=maps[True]['unresolved'].get(slot,set())
            if step['resource_id'] not in known:
                reason='Identifier absent from parsed participant records/activity'
                detail='No target ID, worker event, or grounded alias; cannot manufacture a resource identifier.'
            elif resource not in normal and resource in extended:
                reason='Post-report event; wider window remains ambiguous'
                detail=f'Excluded by original window; extended elimination leaves {len(remaining)} candidates.'
            elif len(remaining)>1:
                reason='Overlapping requests without direct ownership'
                detail=f'{len(remaining)} candidates survive extended elimination; no distinguishing identity/lookup/reference link.'
            else:
                reason='Contested or unsupported workflow ownership'
                detail='Candidate is not forced by direct grounding and one-to-one constraints; keep unassigned.'
            counts[reason]+=1
            owner_links=engine.resource_links.get(resource,())
            rows.append((reason, f"| {q['case_id']} | {step['operation']} {step['resource_id']} | {values(r[1] for r in normal)} | {values(r[1] for r in extended)} | {values(r[1] for r in remaining)} | {detail} Grounded target links: {owner_links or 'none'}. |"))
    lines=['# Remaining public-sample evidence gaps','','Labels are read only by code/evaluation/. Candidate maps use both request files and participant evidence only. Every missing step has a row; no inferred target is injected into the engine.','',
           '| Reason group | Missing steps |','|---|---:|']
    lines += [f'| {reason} | {n} |' for reason,n in sorted(counts.items())]
    for reason in sorted(counts):
        lines += ['',f'## {reason}','','| Case | Missing step | All original-window candidates/locks | All extended-window candidates/locks | Remaining extended candidates | Why unassigned |','|---|---|---|---|---|---|']
        lines += [row for group,row in rows if group==reason]
    lines += ['','All candidates are listed without truncation. The original and extended maps retain direct locks separately from unowned candidates; direct resources belonging to someone else are excluded. The complete competing-request and grounding provenance for case_01 and case_07 is in ownership_trace.md.','',
              'No remaining group supplies a new evidence-grounded ownership rule. Choosing by resource ID, case ID, row order, timestamp proximity, or an expected target would be a guess. The media row-isolation rule is general and tested, but it does not resolve these 22 missing ownership links.']
    destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def inventory(text):
    return dict(ids=sorted(set(RESOURCE.findall(text)) | set(re.findall(r'\buser[_ ]\d+\b|\b(?:ORD|CS|FIN|NST|CJX|SWF)-[\w-]+',text))),
                emails=sorted(set(EMAIL.findall(text))),
                phones=sorted(set(re.findall(r'\+\d[\d ().-]{7,}\d',text))),
                hashes=sorted(set(re.findall(r'\b[0-9a-fA-F]{32,64}\b',text))),
                statuses=sorted(set(re.findall(r'\b(?:active|disabled|blocked|valid|live|ready|collecting|packaging|processing|expired|retained|paid|delivered|returned|completed|healthy|continuous|in transit|archive)\b',text,re.I))))


def write_media(engine,destination):
    lines=['# Media extraction audit','','Rechecked all 11 screenshots using both cached full-page OCR and versioned spatial OCR, and all 4 PDFs using plain and layout text extraction. These are extracted strings, not corrections inferred from expected answers. No new OCR invocation was needed to inspect the existing text/layout artifacts.','',
           'Resource observations, subject links and state are compared below. Other IDs (orders, tickets and statements), short checksum prefixes, and business statuses are context; they are not automatically modeled as deletion resources. None of these media exposes a complete email hash. OCR spelling variants are preserved for review rather than guessed.','']
    count=Counter()
    for source in engine.manifest:
        path=engine.dataset/source['file_path']
        if path.suffix not in ('.pdf','.png'):continue
        count[path.suffix]+=1
        if path.suffix=='.pdf':
            from pypdf import PdfReader
            pages=PdfReader(path).pages
            raw='\n'.join(page.extract_text() or '' for page in pages)
            spatial='\n'.join(page.extract_text(extraction_mode='layout') or '' for page in pages)
        else:
            cache=engine.dataset.parent/'.runtime'/'ocr'
            raw=ocr_text(path,cache)
            spatial='\n'.join(' '.join(w['text'] for w in sorted(row['words'],key=lambda w:w['x']))
                              for row in grouped_rows(read_layout(path,cache)))
        union=raw+'\n'+spatial;data=inventory(union)
        observations=[o for o in engine.observations if o.evidence==source['file_id']]
        modeled={o.resource for o in observations};visible=set(RESOURCE.findall(union))
        lines += [f"## {source['file_id']} — {path.name}",'',f"SHA-256: `{hashlib.sha256(path.read_bytes()).hexdigest()}`. Captured: {source['captured_at']}.",'']
        for key,items in data.items():lines.append(f'- {key.title()}: {values(items)}')
        checksum=[]
        raw_lines=union.splitlines()
        for i,line in enumerate(raw_lines):
            if re.search(r'checksum|fingerprint|SHA-256',line,re.I):checksum.append(' / '.join(raw_lines[i:i+3]).replace('|','/'))
        lines += [f'- Short checksum/fingerprint context: {values(checksum)}',f'- Recognized resource IDs dropped by ingestion: {values(visible-modeled)}',
                  '', '| Extracted resource | Engine state | Subject links | Locator |','|---|---|---|---|']
        lines += [f"| {o.resource} | {o.state} | {values(o.links)} | {o.locator} |" for o in sorted(observations,key=lambda o:o.resource)]
        contexts='\n'.join(str(o.data.get('extracted_text','')) for o in observations)
        missing_emails=set(data['emails'])-set(EMAIL.findall(contexts))
        lines += ['',f'Emails outside modeled record contexts: {values(missing_emails)}. Unknown neighboring customers must remain unlinked; catalog-only observations store the literal alias instead of the full document.','']
    lines += ['## Findings and fixes','',
              '- Fixed the page-to-row fallback: a row exposing an unknown email no longer inherits the sole recognized customer elsewhere on the page. This removed false media ownership of search_1874 and export_1258/1259/1261. Known customer headers still link single-customer documents.',
              '- Status classification now reads the selected resource context. A disabled/blocked label or email elsewhere on a multi-customer page cannot determine another resource’s state.',
              '- Plain OCR misreads user_11 as user_ll (evidence_04), gmail as gmaiI (evidence_09/32), and numeric backup IDs (evidence_32). Spatial OCR recovers the useful email/resource rows; the correct account link is independently grounded by the visible email. No fuzzy identifier substitution is used.',
              '- Visual inspection of evidence_37 confirms audit_record_001, audit_record_004 and audit_record_005 as well as the three IDs OCR recognizes. Both OCR passes drop those three small reference strings. They are not synthesized into inference. The image is captured after the affected sample cutoff, so it cannot prove earlier state. This remains an OCR coverage limitation.',
              '- Evidence_60 exposes sj.park@naver.com and +8210-5837-9451 but the supplied identity catalog links marketing_001 to a different subject. The literal content is preserved; no new subject is fabricated from this conflict.',
              '- PDFs preserve the visible user references, emails, phone and retention details in extracted text. Opaque statement/tombstone/object names require explicit catalog aliases, not ID arithmetic.',
              '',f"Coverage: {count['.png']} screenshots; {count['.pdf']} PDFs. Sample metrics after the extraction fix are unchanged; no missing sample ownership link is supplied by these media."]
    destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def write_trace(engine,destination):
    root=engine.dataset.parent
    lines=['# Cross-case ownership trace','','All requests are included. No expected labels are used in this trace. Reported workflow outcomes are printed as claims only and never decide record state.','']
    for extended in (False,True):
        result=trace(engine,engine.request_windows,extended=extended)
        suffix='extended' if extended else 'original'
        (root/'.runtime'/f'ownership_trace_{suffix}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        lines += [f'## {suffix.title()} window','']
        for case in result['cases']:
            lines += [f"### {case['case_id']}",'',f"Request window: {case['request']['requested_at']} → {case['request']['audit_at'] if extended else case['request']['reported_at']}. Audit cutoff: {case['request']['audit_at']}.",'',
                      '| Candidate | Worker event time / ID | Every containing request: start → report / audit | Every direct lock: subject / evidence ID | Assigned episode |','|---|---|---|---|---|']
            for item in case['resources']:
                contenders='; '.join(f"{q['case_id']}: {q['requested_at']} → {q['reported_at']} / {q['audit_at']}" for q in item['containing_requests'])
                locks='; '.join(f"{q['subject']} / {q['evidence_id']} (available {q['available']})" for q in item['locks']) or 'none'
                events='; '.join(f"{a['event_time']} / {a['activity_id']}" for a in item['events'])
                lines.append(f"| {item['resource'][1]} ({item['type']}) | {events} | {contenders} | {locks} | {item['assigned_to'] or 'unassigned'} |")
        lines += ['', '### Every propagation step (global, in stable execution order)','',
                  'One complete JSON object per line; fixed-point rows list every remaining slot. Full indented JSON is also written under .runtime/.','','```jsonl']
        lines += [json.dumps(step,separators=(',',':')) for step in result['elimination_steps']]
        lines += ['```','']
    lines += ['## Root cause and decision','',
              'Original-window case_01 has ungrounded account_001 and account_4070 candidates. Case_07 has ungrounded account_007, account_008, account_4990 and account_6829 candidates. Their expected account IDs were neither wrongly locked nor removed by propagation; no forced assignment exists. Evaluation-set requests compete for the same events. Direct-owner filtering and resource types are correct for these candidates.',
              'The previous baseline assigned the account near the earliest completion boundary. Replacing that heuristic with strict elimination removes those links. Seeding elimination with those guesses would violate the direct-grounding requirement. Widening to audit_at adds further unrelated events and causes another regression, rather than providing identifying evidence.',
              'Strict and extended replacements remain disabled. Supplemental strict/extended trials preserve the baseline but recover zero additional sample steps. Final inference retains the prior window behavior plus the independent media extraction correction.']
    destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def write_comparison(root,metrics,tests):
    runtime=root/'.runtime'
    history_path=root/'code/evaluation/experiment_history.json'
    history=json.loads(history_path.read_text(encoding='utf-8')) if history_path.exists() else {}
    baseline_path=runtime/'cross_case_baseline.json'
    baseline=json.loads(baseline_path.read_text(encoding='utf-8')) if baseline_path.exists() else history.get('baseline',dict(metrics=metrics,correct_cases=[]))
    history['baseline']=dict(metrics={k:v for k,v in baseline['metrics'].items() if k!='failures'},correct_cases=baseline['correct_cases'])
    trials=[('Before',baseline['metrics'])]
    for label,filename in [('Strict replacement','strict_trial.json'),('Extended replacement','extended_trial.json'),
                           ('Supplemental strict','supplemental_strict.json'),('Supplemental extended','supplemental_extended.json')]:
        path=runtime/filename
        if path.exists():
            data=json.loads(path.read_text(encoding='utf-8'));trials.append((label,data.get('metrics',data)))
        elif label in history:
            trials.append((label,history[label]))
    trials.append(('Final: media fix; elimination disabled',metrics))
    for name,m in trials:
        history[name]={k:v for k,v in m.items() if k!='failures'}
    history_path.write_text(json.dumps(history,indent=2)+'\n',encoding='utf-8')
    lines=['# Accuracy comparison','','Public samples only. Expected answers are read exclusively in code/evaluation/. No sample labels or target resource IDs are used by inference.','',
           '| Variant | '+' | '.join(METRICS)+' |','|---|'+'---:|'*len(METRICS)]
    lines += ['| '+name+' | '+' | '.join(f'{m[k]:.4%}' for k in METRICS)+' |' for name,m in trials]
    failed={f['case_id'] for f in metrics['failures']};broken=sorted(set(baseline['correct_cases']) & failed)
    lines += ['',f"Final previously-correct sample regressions: {broken}. All {len(baseline['correct_cases'])} original exact-correct cases checked. Final matching steps: {metrics['matched_steps']}/{metrics['expected_steps']}; missing: {sum(len(f['missing']) for f in metrics['failures'])}; extra: {sum(len(f['extra']) for f in metrics['failures'])}.",
              f'Tests: {tests.testsRun}; failures: {len(tests.failures)}; errors: {len(tests.errors)}.','',
              'Strict replacement breaks case_01 and case_07; extended replacement also breaks case_30. Both replacements fail the acceptance gate and remain disabled. Neither supplemental trial recovers a step. The media correction is retained because it fixes cross-row ownership contamination without sample regressions. Exact-row accuracy did not increase; preserving precision and abstaining on unresolved ownership takes precedence over guessing.',
              '', 'See ownership_trace.md for the complete candidate/lock/elimination trace, evidence_gaps.md for every remaining missing step, and media_audit.md for all 15 media inventories.', '',
              'Reproduce: `python code/evaluation/main.py`; `python code/evaluation/main.py --cross-case-elimination`; `python code/evaluation/main.py --cross-case-elimination --extended-window`. No command writes log.txt.']
    (root/'code/evaluation/accuracy_comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return lines
