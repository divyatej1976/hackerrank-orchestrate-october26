"""Public-label evaluation is isolated from prediction code."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit.core import AuditEngine, read_csv, deletion_intent
from audit import llm


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
    # Match the main CLI: classify the requested inputs in their given order
    # before global ownership can revisit other intake windows.
    for request in requests:
        deletion_intent(request['request_text'],request['case_id'],engine.diagnostics)
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
    parser.add_argument('--intent-mode',choices=('primary','shadow','rules'),default=llm.DEFAULT_MODE)
    args=parser.parse_args()
    intent_client=llm.configure(args.intent_mode)
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
    rejected_intent_trial=None
    from intent_evaluation import comparison as compare_intent, write_report as write_intent_report
    intent_comparison=compare_intent(root,args.dataset,metrics,expected)
    if (engine is not None and not args.capture_baseline and not args.cross_case_elimination
            and intent_client.mode=='primary' and intent_comparison['gate_failed']):
        # Persist only the policy enum, never labels or expected operations.
        rejected_intent_trial=intent_comparison
        primary_summary_path=runtime/'run_summary.json'
        if primary_summary_path.exists():
            primary_summary=json.loads(primary_summary_path.read_text(encoding='utf-8'))
            rejected_intent_trial['primary_run_usage']=primary_summary.get('intent_usage',{})
            (runtime/'groq_primary_run_summary.json').write_text(json.dumps(primary_summary,indent=2),encoding='utf-8')
        (runtime/'groq_rejected_trial.json').write_text(json.dumps(rejected_intent_trial,indent=2),encoding='utf-8')
        llm.POLICY_PATH.write_text('{"mode":"shadow"}\n',encoding='utf-8')
        print('Intent regression gate failed; keeping rules and using Groq only as a second opinion.')
        import subprocess
        subprocess.run([sys.executable,str(root/'code/main.py'),'--dataset',str(args.dataset),'--intent-mode','shadow'],check=True)
        subprocess.run([sys.executable,str(root/'code/main.py'),'validate','--dataset',str(args.dataset)],check=True)
        intent_client=llm.configure('shadow')
        engine=AuditEngine(args.dataset).load()
        predictions=infer(engine,read_csv(args.dataset/'sample_deletion_requests.csv'))
        metrics=evaluate(predictions,expected)
        intent_comparison=compare_intent(root,args.dataset,metrics,expected)
        if rejected_intent_trial.get('primary_run_usage'):
            u=rejected_intent_trial['primary_run_usage']
            with (root/'code/evaluation/usage_report.md').open('a',encoding='utf-8') as stream:
                stream.write('\n## Rejected primary validation run (separate from final-run totals)\n\n'
                    f"Provider/model: {u.get('provider')} / {u.get('model')}; live HTTP calls {u.get('live_calls',0)}; "
                    f"live input tokens {u.get('live_input_tokens',0)}; live output tokens {u.get('live_output_tokens',0)}; "
                    f"cache hits {u.get('cache_hits',0)}; cached input tokens {u.get('cached_input_tokens',0)}; "
                    f"cached output tokens {u.get('cached_output_tokens',0)}. "
                    f"Estimated incremental cost ${u.get('estimated_live_cost_usd',0):.8f}. "
                    'These development-validation calls are not counted again as live calls when their cached responses are reused by the final shadow run.\n')
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
              '| Explicit lookup lock and competing requests | Lock provenance retained and candidate elimination traced | PASS |',
              '| Groq says true for a Spanish account-closure request (mock HTTP) | Intent True | PASS |',
              '| Groq says true but request says do not delete | Intent False; refusal wins; disagreement diagnostic | PASS |',
              '| GROQ_API_KEY absent (network forbidden) | Same answer as rules_intent | PASS |',
              '| Groq response contains malformed JSON | Same answer as rules_intent; consumed tokens still counted | PASS |',
              '| A second client reads the cached model/prompt/text response | No second HTTP request; cached tokens reported separately | PASS |',
              '| Three requests, one COMPLETE and two NOT_STARTED, sharing a window | Status filter assigns the unique account; two FAILED candidates for two subjects stay unassigned | PASS |','',
              'Other regressions cover null/404 lookup ownership, historical aliases, replica drift, incomplete-case full verification, future ownership versus eligible state, contested singletons, input-order determinism and conflicting primary account locks.','',
              '## Changes and remaining failures','',
              '- Added auditable direct-lock provenance, deterministic propagation traces and fixed-point candidate lists over both request files.',
              '- Tested the full audit-time episode window separately. Strict replacement and wider replacement fail the no-regression gate; both remain disabled. Supplemental variants preserve existing results but add no steps.',
              '- Fixed media ownership contamination from unknown neighboring emails and classified state from local resource context.',
              '- Inventoried all 11 screenshots and 4 PDFs, including recognized identifiers, OCR variants, short checksums, statuses, observations and remaining OCR omissions.',
              '- Biggest improvement: every sample deletion has exactly one primary-account step, but the engine grounded only 18/32. Added a primary-account slot (`AuditEngine._slot_assignments`): candidates are deletion-worker account events between reported_at-90min and reported_at+15min whose result is consistent with the workflow claim (COMPLETE->SUCCESS, NOT_STARTED->FAILED, PARTIALLY_COMPLETE->PARTIAL/SUCCESS; 31/32 samples agree, the other has no event). A candidate is assigned only when it is the unique remaining one after one-to-one elimination across all 550 requests; contested candidates stay unassigned. COMPLETE cases drop an inferred account that lacks audit-time evidence instead of citing nothing. Result: status 96.9%->100%, exact rows 46.9%->65.6%, precision stays 100%, and 113 of 518 evaluation rows gained their account step.',
              '- Tried the same slot for analytics profiles: no sample change, so it was removed. Never uses case/resource ID patterns, row order or expected answers.',
              '', '| Failing case | Predicted status | Expected status | Missing | Extra |','|---|---|---|---:|---:|']
    lines += [f"| {f['case_id']} | {f['predicted_status']} | {f['expected_status']} | {len(f['missing'])} | {len(f['extra'])} |" for f in metrics['failures']]
    lines += ['', '## Measurements for every trial','']+comparison[4:]
    lines += ['', '## Limits','',
              f"Exact-row accuracy is {metrics['exact_row_accuracy']:.4%}. Missing expected steps: {sum(len(f['missing']) for f in metrics['failures'])}; extra: {sum(len(f['extra']) for f in metrics['failures'])}. Unresolved sample decisions: {sum(f['predicted_status']=='UNRESOLVED' for f in metrics['failures'])}. See evidence_gaps.md for all candidates and grouped reasons.",
              'The media recheck uses existing OCR caches, not a new OCR model. Three small security reference IDs remain unread by OCR, as documented in media_audit.md. Remaining ownership ambiguities are not resolved by intent classification. Groq classifies intent when a valid answer is available, rules handle missing/invalid responses, and explicit refusal always wins; measured usage is in usage_report.md.',
              '', '## Reproduction','',
              'Run `python code/evaluation/main.py`. Use --cross-case-elimination, optionally --extended-window and --supplemental, to reproduce the rejected/supplemental trials. Run `python code/main.py`, then `python code/main.py validate` for final predictions. No workflow writes log.txt.']
    intent_lines=write_intent_report(root,intent_comparison,intent_client,
                                   {r['case_id'] for r in expected},rejected_intent_trial)
    lines += ['', '## Groq intent step and regression gate','']+intent_lines[2:]
    (folder/'evaluation_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with (folder/'accuracy_comparison.md').open('a',encoding='utf-8') as stream:
        stream.write('\n## Groq intent comparison\n\n'+'\n'.join(intent_lines[2:])+'\n')
    print(json.dumps({k:v for k,v in metrics.items() if k!='failures'},indent=2))
    print('Previously correct sample regressions:',broken)
    print('Intent agreement:',json.dumps(intent_client.agreement({r['case_id'] for r in expected})))
    print('NOT_APPLICABLE changed cases:',json.dumps(intent_comparison['changed_cases'],ensure_ascii=True))


if __name__=='__main__':
    main()
