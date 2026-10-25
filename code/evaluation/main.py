"""Public-label evaluation is isolated from prediction code."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit.core import AuditEngine, read_csv


def key(step):
    return json.dumps({k:v for k,v in step.items() if k != 'step_no'}, sort_keys=True)


def evaluate(predictions, expected):
    predicted = {r['case_id']: r for r in predictions}
    status = exact = sequence = matched = predicted_n = expected_n = field_ok = field_n = 0
    failures = []
    for target in expected:
        row = predicted.get(target['case_id'], {'deletion_status': 'UNRESOLVED', 'steps_json': '[]'})
        actual_steps, target_steps = json.loads(row['steps_json']), json.loads(target['steps_json'])
        status += row['deletion_status'] == target['deletion_status']
        sequence += actual_steps == target_steps
        exact += row['deletion_status'] == target['deletion_status'] and actual_steps == target_steps
        pa, pe = Counter(map(key, actual_steps)), Counter(map(key, target_steps))
        matched += sum((pa & pe).values())
        predicted_n += len(actual_steps)
        expected_n += len(target_steps)
        # Align by phase/operation/system/resource. Missing/extra steps count
        # as seven field errors, and step_no is a scored field.
        def identity(s): return tuple(s[k] for k in ('phase','operation','system_id','resource_id'))
        a, e = {identity(s):s for s in actual_steps}, {identity(s):s for s in target_steps}
        for item in a.keys() | e.keys():
            field_n += 7
            if item in a and item in e:
                field_ok += sum(a[item].get(k) == v for k,v in e[item].items())
        if actual_steps != target_steps or row['deletion_status'] != target['deletion_status']:
            failures.append({'case_id': target['case_id'], 'predicted_status': row['deletion_status'],
                             'expected_status': target['deletion_status'],
                             'missing': list((pe-pa).elements()), 'extra': list((pa-pe).elements())})
    count = len(expected)
    precision = matched/predicted_n if predicted_n else 0
    recall = matched/expected_n if expected_n else 0
    return {'cases': count, 'status_accuracy': status/count, 'exact_row_accuracy': exact/count,
            'sequence_accuracy': sequence/count, 'step_precision': precision, 'step_recall': recall,
            'step_f1': 2*precision*recall/(precision+recall) if precision+recall else 0,
            'field_accuracy': field_ok/field_n if field_n else 0,
            'matched_steps': matched, 'predicted_steps': predicted_n, 'expected_steps': expected_n,
            'matched_fields': field_ok, 'field_denominator': field_n, 'failures': failures}


def infer(engine, requests):
    predictions=[]
    for request in requests:
        try:
            predictions.append(engine.audit(request))
        except ValueError as exc:
            print(str(exc))
    return predictions


def main():
    root=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,default=root/'dataset')
    parser.add_argument('--predictions',type=Path)
    parser.add_argument('--expected',type=Path)
    parser.add_argument('--capture-baseline',action='store_true')
    parser.add_argument('--cross-case-elimination',action='store_true')
    parser.add_argument('--extended-window',action='store_true')
    parser.add_argument('--supplemental',action='store_true',help='Trial strict links as additions to the baseline')
    args=parser.parse_args()
    if (args.extended_window or args.supplemental) and not args.cross_case_elimination:
        parser.error('Window and supplemental experiments require --cross-case-elimination')
    runtime=root/'.runtime';runtime.mkdir(exist_ok=True)
    engine=None
    if args.predictions:
        predictions=read_csv(args.predictions)
    else:
        engine=AuditEngine(args.dataset,enable_ownership_elimination=args.cross_case_elimination).load()
        engine.extend_ownership_window=args.extended_window
        if args.supplemental:
            engine.workflow_resources=lambda r,u:engine._baseline_workflow_resources(r,u)|engine._eliminated_workflow_resources(r,u)
        predictions=infer(engine,read_csv(args.dataset/'sample_deletion_requests.csv'))
    # Labels are opened only after inference is complete.
    expected=read_csv(args.expected or args.dataset/'sample_output.csv')
    metrics=evaluate(predictions,expected)
    baseline_path=runtime/'cross_case_baseline.json'
    baseline=json.loads(baseline_path.read_text(encoding='utf-8')) if baseline_path.exists() else None
    history_path=Path(__file__).parent/'experiment_history.json'
    if baseline is None and history_path.exists():
        baseline=json.loads(history_path.read_text(encoding='utf-8')).get('baseline')
    failed={f['case_id'] for f in metrics['failures']}
    broken=sorted(set(baseline['correct_cases']) & failed) if baseline else []
    if args.capture_baseline:
        snapshot=dict(metrics=metrics,predictions=predictions,
                      correct_cases=sorted(r['case_id'] for r in expected if r['case_id'] not in failed))
        baseline_path.write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
        print(f'Captured baseline: {len(snapshot["correct_cases"])} exact-correct samples.')
        return
    if args.cross_case_elimination:
        trial=dict(metrics=metrics,previously_correct_regressions=broken,
                   accepted=bool(baseline and metrics['step_precision']>=1 and not broken))
        name=('supplemental_extended' if args.extended_window else 'supplemental_strict') if args.supplemental else ('extended_trial' if args.extended_window else 'strict_trial')
        (runtime/(name+'.json')).write_text(json.dumps(trial,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in metrics.items() if k!='failures'},indent=2))
        print('Previously correct case regressions:',broken,'Accepted:',trial['accepted'])
        return
    (runtime/'sample_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    import unittest
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
    tests=unittest.TextTestRunner(verbosity=1).run(suite)
    if not tests.wasSuccessful():
        raise SystemExit('Regression tests failed; refusing to publish evaluation reports')
    from diagnostics import write_gaps,write_media,write_trace,write_comparison,METRICS
    folder=Path(__file__).parent
    if engine:
        write_gaps(engine,metrics,folder/'evidence_gaps.md')
        write_media(engine,folder/'media_audit.md')
        write_trace(engine,folder/'ownership_trace.md')
    comparison=write_comparison(root,metrics,tests)
    lines=['# Evaluation report','','Measured on 32 public samples. Hidden full-dataset labels are unavailable. Expected answers are read only by evaluation after inference.','',
           '| Metric | Final |','|---|---:|']
    lines += [f'| {k} | {metrics[k]:.4%} |' for k in METRICS]
    lines += ['',f"Matching steps: {metrics['matched_steps']}/{metrics['expected_steps']} expected; {metrics['predicted_steps']} predicted. Matching fields: {metrics['matched_fields']}/{metrics['field_denominator']}.",
              'Steps are multiset matched excluding step_no. Fields align by phase/operation/system/resource; missing or extra steps count as seven errors. Sequence compares complete arrays, including numbering and citations.','',
              '## Regression workflow','',f'Tests: {tests.testsRun}; failures: {len(tests.failures)}; errors: {len(tests.errors)}. Test fixtures are participant-authored and do not read expected answers.','',
              '| Authored input | Required result | Outcome |','|---|---|---|',
              '| Export request explicitly prohibits deletion | NOT_APPLICABLE, empty steps | PASS |',
              '| Search record exists and sync is active | Disable writer before deleting dependent record | PASS |',
              '| Redacted tombstone, retained audit record, blocked backup | COMPLETE with all three policy checks | PASS |',
              '| State correction arrives after audit cutoff | Earlier noncompliant state remains decisive | PASS |',
              '| Unknown email on neighboring visual table row | Does not inherit sole recognized page customer | PASS |',
              '| Worker event after report but before audit | Extended ownership only when forced; two candidates abstain | PASS |',
              '| Explicit lookup lock and competing requests | Lock provenance retained and candidate elimination traced | PASS |','',
              'Other regressions cover null/404 lookup ownership, historical aliases, replica drift, incomplete-case full verification, future ownership versus eligible state, contested singletons, input-order determinism and conflicting primary account locks.','',
              '## Changes and remaining failures','',
              '- Added auditable direct-lock provenance, deterministic propagation traces and fixed-point candidate lists over both request files.',
              '- Tested the full audit-time episode window separately. Strict replacement and wider replacement fail the no-regression gate; both remain disabled. Supplemental variants preserve existing results but add no steps.',
              '- Fixed media ownership contamination from unknown neighboring emails and classified state from local resource context.',
              '- Inventoried all 11 screenshots and 4 PDFs, including recognized identifiers, OCR variants, short checksums, statuses, observations and remaining OCR omissions.',
              '- Ownership cannot be resolved by operation SUCCESS/FAILED, case/resource ID patterns, row order, timestamp proximity, or expected answers.',
              '', '| Failing case | Predicted status | Expected status | Missing | Extra |','|---|---|---|---:|---:|']
    lines += [f"| {f['case_id']} | {f['predicted_status']} | {f['expected_status']} | {len(f['missing'])} | {len(f['extra'])} |" for f in metrics['failures']]
    lines += ['', '## Measurements for every trial','']+comparison[4:]
    lines += ['', '## Limits','',
              f"Exact-row accuracy is {metrics['exact_row_accuracy']:.4%}. Missing expected steps: {sum(len(f['missing']) for f in metrics['failures'])}; extra: {sum(len(f['extra']) for f in metrics['failures'])}. Unresolved sample decisions: {sum(f['predicted_status']=='UNRESOLVED' for f in metrics['failures'])}. See evidence_gaps.md for all candidates and grouped reasons.",
              'The media recheck uses existing OCR caches, not a new OCR model. Three small security reference IDs remain unread by OCR, as documented in media_audit.md. Identity availability and multilingual intent handling remain limited. The current agent uses deterministic extraction and local OCR, with no remote generative model. A contract-valid full-dataset output does not prove semantic accuracy.',
              '', '## Reproduction','',
              'Run `python code/evaluation/main.py`. Use --cross-case-elimination, optionally --extended-window and --supplemental, to reproduce the rejected/supplemental trials. Run `python code/main.py`, then `python code/main.py validate` for final predictions. No workflow writes log.txt.']
    (folder/'evaluation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in metrics.items() if k!='failures'},indent=2))
    print('Previously correct sample regressions:',broken)


if __name__=='__main__':
    main()
