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

from audit.core import AuditEngine, case_key, read_csv
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
    args = parser.parse_args()
    started = time.perf_counter()
    engine = AuditEngine(args.dataset)
    requests = read_csv(args.dataset/args.cases)
    if args.command == 'validate':
        engine.validate(read_csv(args.output), requests)
        print('Output contract validated.')
        return
    engine.load()
    failed = [f for f in engine.ingestion if not f['success']]
    runtime = root/'.runtime'
    runtime.mkdir(exist_ok=True)
    (runtime/'ingestion.json').write_text(json.dumps(engine.ingestion, indent=2), encoding='utf-8')
    persist_index(engine, runtime/'observations.sqlite')
    print(f'Inspected {len(engine.ingestion)} evidence files; {len(engine.observations)} observations; {len(failed)} failures', flush=True)
    if failed:
        raise RuntimeError('Evidence ingestion failed. See .runtime/ingestion.json; refusing silent omissions.')
    rows = [engine.audit(request) for request in sorted(requests, key=lambda r: case_key(r['case_id']))]
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
               'model_calls': 0, 'input_tokens': 0, 'output_tokens': 0,
               'ocr': 'Local operating-system OCR; content-hash cached',
               'ocr_usage': engine.ocr_stats,
               'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}
    (runtime/'run_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    write_case_report(rows, summary, runtime/'audit_report.html')
    usage = f'''# Final-run usage report

Output: `{args.output.name}`; {len(rows)} requests; SHA-256 `{summary['output_sha256']}`.
Elapsed time: {summary['seconds']} seconds on this machine with the existing OCR cache.

| Provider / model | Calls in final run | Input tokens | Output tokens | Total tokens | Estimated API cost |
|---|---:|---:|---:|---:|---:|
| Remote LLM: none | 0 | 0 | 0 | 0 | $0.00 |
| Local Windows.Media.Ocr (OS-managed model; internal model identifier not exposed) | {engine.ocr_stats['calls']} | N/A | N/A | N/A | $0.00 |

OCR cache hits: {engine.ocr_stats['cache_hits']}. Cold setup used two local OCR passes per screenshot (text and spatial layout) for 11 screenshots; those setup calls are not final-run calls.
No hosted generative model was called by inference. Token total and average per request: 0 and 0. Estimated total and per-request API cost: $0.00 and $0.00.
Local CPU/electricity and development-chat usage are not measured or included in API cost. OCR uses images and text, not a token-billed interface.
This report reflects the actual current implementation, not the proposed LLM-assisted architecture.
'''
    (Path(__file__).parent/'evaluation'/'usage_report.md').write_text(usage, encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'diagnostics'}, indent=2))
    print(f'Wrote {args.output}; diagnostic items: {len(engine.diagnostics)}')


if __name__ == '__main__':
    main()
