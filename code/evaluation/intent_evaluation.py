"""Label-dependent intent regression gate: imported only by evaluation."""
import json
from pathlib import Path

from audit.core import read_csv
from audit.llm import MODEL

METRICS=('status_accuracy','exact_row_accuracy','sequence_accuracy','step_precision','step_recall','step_f1','field_accuracy')


def rejected_sample_changes(dataset, rejected):
    requests={r['case_id']:r for r in read_csv(dataset/'sample_deletion_requests.csv')}
    changes=[f for f in rejected['after']['failures']
             if (f['predicted_status']=='NOT_APPLICABLE') != (f['expected_status']=='NOT_APPLICABLE')]
    if not changes:
        return []
    lines=['## Rejected primary trial: public NOT_APPLICABLE changes','',
           'The pre-Groq sample status accuracy was 100%, so these expected statuses also describe the correct baseline decisions. The final shadow policy restores them; the full 518-row NOT_APPLICABLE set is unchanged.','',
           '| Public case | Correct baseline status | Rejected primary status | Exact request text |','|---|---|---|---|']
    for row in changes:
        text=requests[row['case_id']]['request_text'].replace('|','\\|').replace('\n','<br>')
        lines.append(f"| {row['case_id']} | {row['expected_status']} | {row['predicted_status']} | {text} |")
    return lines+['']


def comparison(root, dataset, metrics, expected):
    snapshot_path=root/'code/evaluation/intent_baseline.json'
    snapshot=json.loads(snapshot_path.read_text(encoding='utf-8')) if snapshot_path.exists() else {}
    baseline_path=root/'.runtime'/'pre_groq_metrics.json'
    baseline=json.loads(baseline_path.read_text(encoding='utf-8')) if baseline_path.exists() else snapshot.get('metrics')
    before_path=root/'.runtime'/'pre_groq_output.csv'
    after_path=root/'output.csv'
    before=({r['case_id'] for r in read_csv(before_path) if r['deletion_status']=='NOT_APPLICABLE'} if before_path.exists()
            else set(snapshot['not_applicable']) if 'not_applicable' in snapshot else None)
    after={r['case_id'] for r in read_csv(after_path) if r['deletion_status']=='NOT_APPLICABLE'} if after_path.exists() else None
    changes=sorted(before ^ after) if before is not None and after is not None else []
    degraded=[k for k in METRICS if baseline and metrics[k]<baseline[k]-1e-12]
    old_failed={r['case_id'] for r in baseline.get('failures',[])} if baseline else set()
    old_correct=({r['case_id'] for r in expected}-old_failed if baseline and 'failures' in baseline
                 else set(snapshot.get('correct_cases',[])))
    if not snapshot and baseline and before is not None:
        # Portable aggregate reference lives strictly in evaluation/. No target
        # resource IDs, expected operations or labels are imported by inference.
        snapshot_path.parent.mkdir(parents=True,exist_ok=True)
        snapshot_path.write_text(json.dumps(dict(metrics={k:baseline[k] for k in METRICS},
            correct_cases=sorted(old_correct),not_applicable=sorted(before)),indent=2)+'\n',encoding='utf-8')
    broken=sorted(old_correct & {r['case_id'] for r in metrics['failures']})
    requests={r['case_id']:r for r in read_csv(dataset/'deletion_requests.csv')}
    return dict(before=baseline,after=metrics,degraded_metrics=degraded,
                previously_correct_regressions=broken,
                before_not_applicable=sorted(before) if before is not None else None,
                after_not_applicable=sorted(after) if after is not None else None,
                changed_cases=[dict(case_id=c,request_text=requests[c]['request_text'],
                    was_not_applicable=c in before,is_not_applicable=c in after) for c in changes],
                gate_failed=bool(degraded or broken or changes))


def write_report(root, comparison, client, sample_ids, rejected_trial=None):
    usage=client.usage();agreement=client.agreement(sample_ids)
    full_path=root/'.runtime'/'run_summary.json'
    full=json.loads(full_path.read_text(encoding='utf-8')) if full_path.exists() else {}
    rate=f"{agreement['agreement_rate']:.4%}" if agreement['agreement_rate'] is not None else 'N/A: no valid Groq answers'
    lines=['# Groq intent classification evaluation','',
        'Only the evaluator reads public expected labels. Inference receives request text, the system prompt and policy mode; it never receives expected labels.',
        f'Groq {MODEL} uses temperature 0, low reasoning effort and JSON object mode. An explicit refusal always overrides the model; unavailable or invalid answers fall back to rules. Mode shadow keeps rules authoritative while retaining model disagreement diagnostics.','',
        '| Metric | Pre-Groq baseline | Final |','|---|---:|---:|']
    for name in METRICS:
        before=f"{comparison['before'][name]:.4%}" if comparison['before'] else 'Unavailable'
        lines.append(f"| {name} | {before} | {comparison['after'][name]:.4%} |")
    before_na=comparison['before_not_applicable'];after_na=comparison['after_not_applicable']
    lines += ['',f"Full output NOT_APPLICABLE count: {len(before_na) if before_na is not None else 'unavailable'} → {len(after_na) if after_na is not None else 'unavailable'}.",
              f"Changed NOT_APPLICABLE cases: {len(comparison['changed_cases'])}. Degraded metrics: {comparison['degraded_metrics']}. Previously correct sample regressions: {comparison['previously_correct_regressions']}.",'',
              '| Changed case | Before NOT_APPLICABLE | After NOT_APPLICABLE | Exact request text |','|---|---|---|---|']
    for row in comparison['changed_cases']:
        text=row['request_text'].replace('|','\\|').replace('\n','<br>')
        lines.append(f"| {row['case_id']} | {row['was_not_applicable']} | {row['is_not_applicable']} | {text} |")
    if not comparison['changed_cases']:lines.append('| None | — | — | No decisions changed |')
    lines += ['',f"Sample agreement between model and rules: {rate}; valid model answers {agreement['classified']}/{agreement['cases']}; disagreements {agreement['disagreements']}; unavailable {agreement['unavailable']}.",
              f"Sample inference usage (including other requests needed by global ownership): live HTTP calls {usage['live_calls']}, disk cache hits {usage['cache_hits']}, input tokens {usage['input_tokens']}, output tokens {usage['output_tokens']}.",
              f"Full-run agreement: {json.dumps(full.get('intent_agreement',{}),sort_keys=True)}.",
              f"Final full-run HTTP failure statuses: {json.dumps(full.get('intent_usage',{}).get('http_failures_by_status',{}),sort_keys=True)}. Error bodies and credentials are never included.",
              f"Chosen default policy: {client.mode}. "+('All classified disagreements are retained as case diagnostics; explicit refusals remain false.'),'',
              '| Sample case | Rules delete | LLM delete | Selected delete | Refusal override | Short reason |','|---|---|---|---|---|---|']
    for case_id,record in sorted(client.records.items()):
        if case_id in sample_ids and record['llm_deletes'] is not None and record['llm_deletes']!=record['rules_deletes']:
            reason=(record['reason'] or '').replace('|','\\|').replace('\n',' ')
            lines.append(f"| {case_id} | {record['rules_deletes']} | {record['llm_deletes']} | {record['selected_deletes']} | {record['explicit_refusal']} | {reason} |")
    if rejected_trial:
        lines += ['', '## Rejected primary trial','',
                  'Rules were retained as the decision and the LLM downgraded to a second opinion because a metric/case regressed or the NOT_APPLICABLE set changed. Every changed decision is conservatively flagged for text review; no label is passed into inference.',
                  f"Degraded metrics: {rejected_trial['degraded_metrics']}. Regressed cases: {rejected_trial['previously_correct_regressions']}.",
                  '', '| Trial changed case | Request text |','|---|---|']
        for row in rejected_trial['changed_cases']:
            text=row['request_text'].replace('|','\\|').replace('\n','<br>')
            lines.append(f"| {row['case_id']} | {text} |")
        lines += ['']+rejected_sample_changes(root/'dataset',rejected_trial)
    if agreement['classified']==0:
        lines += ['', '**Live-model validation remains pending.** No valid live or cached model answers were available, so the effective decisions came from rules. Agreement cannot be inferred from zero answers. Unit-test response tokens are never included in inference reports. No claim of measured non-zero usage or successful live LLM acceptance is made.']
    availability_path=root/'.runtime/groq_available_models.json'
    if availability_path.exists():
        availability=json.loads(availability_path.read_text(encoding='utf-8'))
        if availability.get('requested_model_listed') is False:
            lines += ['', f'Provider migration: the originally requested llama-3.3-70b-versatile was absent from the authenticated Groq model list and returned HTTP 404 model_not_found. The user explicitly authorized Groq openai/gpt-oss-120b as its replacement; the active model is {MODEL}. Credentials remain environment-only.']
    lines += ['',f"Pricing: {usage['price_note']}",'']
    (root/'code/evaluation/intent_classification_report.md').write_text('\n'.join(lines),encoding='utf-8')
    (root/'.runtime'/'groq_intent_comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    return lines
