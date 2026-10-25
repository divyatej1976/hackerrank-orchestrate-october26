"""Run a reproducible audit; expected sample labels are never imported here."""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from audit.core import AuditEngine, read_csv, deletion_intent
from audit.llm import configure, DEFAULT_MODE, write_usage_report
from audit.reporting import persist_index, write_case_report


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', default='audit', choices=['audit', 'validate'])
    root = Path(__file__).resolve().parent.parent
    parser.add_argument('--dataset', type=Path, default=root/'dataset')
    parser.add_argument('--output', type=Path, default=root/'output.csv')
    parser.add_argument('--cases', default='deletion_requests.csv')
    parser.add_argument('--intent-mode', choices=('primary','shadow','rules'), default=DEFAULT_MODE)
    args = parser.parse_args()
    intent_client = configure(args.intent_mode)
    started = time.perf_counter()
    engine = AuditEngine(args.dataset)
    requests = read_csv(args.dataset/args.cases)
    if args.command == 'validate':
        engine.validate(read_csv(args.output), requests)
        print('Output contract validated.')
        return
    # Prime requests in their supplied input order before ownership searches.
    for r in requests:
        deletion_intent(r['request_text'],r['case_id'],engine.diagnostics)
    engine.load()
    failed = [f for f in engine.ingestion if not f['success']]
    runtime = root/'.runtime'
    runtime.mkdir(exist_ok=True)
    (runtime/'ingestion.json').write_text(json.dumps(engine.ingestion, indent=2), encoding='utf-8')
    persist_index(engine, runtime/'observations.sqlite')
    print(f'Inspected {len(engine.ingestion)} evidence files; {len(engine.observations)} observations; {len(failed)} failures', flush=True)
    if failed:
        raise RuntimeError('Evidence ingestion failed. See .runtime/ingestion.json; refusing silent omissions.')
    rows = [engine.audit(request) for request in sorted(requests, key=lambda r: r['case_id'])]
    engine.validate(rows, requests)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.csv.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['case_id', 'deletion_status', 'steps_json'])
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, args.output)
    summary = {'requests': len(rows), 'status_counts': dict(Counter(r['deletion_status'] for r in rows)),
               'seconds': round(time.perf_counter()-started, 3), 'diagnostics': engine.diagnostics,
               'model_calls': intent_client.usage()['live_calls'],
               'input_tokens': intent_client.usage()['input_tokens'],
               'output_tokens': intent_client.usage()['output_tokens'],
               'intent_usage': intent_client.usage(),
               'intent_agreement': intent_client.agreement({r['case_id'] for r in requests}),
               'output_name': args.output.name,
               'ocr': 'Local operating-system OCR; content-hash cached',
               'ocr_usage': engine.ocr_stats,
               'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    (runtime/'run_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    write_case_report(rows, summary, runtime/'audit_report.html')
    (runtime/'intent_decisions.json').write_text(json.dumps(intent_client.records, indent=2), encoding='utf-8')
    write_usage_report(Path(__file__).parent/'evaluation'/'usage_report.md', summary)
    print(json.dumps({k:v for k,v in summary.items() if k != 'diagnostics'}, indent=2))
    print(f'Wrote {args.output}; diagnostic items: {len(engine.diagnostics)}')


if __name__ == '__main__':
    main()
