"""Participant-source ownership trace; labels are not needed for this diagnostic."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit.core import AuditEngine, read_csv
from audit.ownership import build, request_key, resource_type


def trace(engine, requests, selected=('case_01', 'case_07'), extended=False):
    result = build(engine, requests, **({'extended': True} if extended else {}))
    rows = []
    for request in requests:
        if request['case_id'] not in selected:
            continue
        episode = result['membership'].get(request_key(request, engine.identities))
        resources = set().union(*(v for name in ('candidates', 'grounded')
                                for slot, v in result[name].items() if slot[0] == episode))
        resources.update((a['target_system'],a['resource_id']) for a in engine.activities
                         if a['source_system']=='deletion_worker'
                         and request['requested_at'] <= a['event_time'] <=
                         min(request['audit_at'], request['audit_at'] if extended else request['reported_at'])
                         and resource_type((a['target_system'],a['resource_id'])))
        rows.append({'case_id': request['case_id'], 'request': request, 'episode': episode,
                     'resources': []})
        for resource in sorted(resources):
            events = [a for a in engine.activities if a['source_system'] == 'deletion_worker'
                      and (a['target_system'], a['resource_id']) == resource]
            contenders = [dict(case_id=r['case_id'], email=r['email'], requested_at=r['requested_at'],
                               reported_at=r['reported_at'], audit_at=r['audit_at'])
                          for r in requests if any(r['requested_at'] <= a['event_time'] <=
                              min(r['audit_at'], r['audit_at'] if extended else r['reported_at']) for a in events)]
            rows[-1]['resources'].append(dict(resource=resource, type=resource_type(resource),
                events=events, containing_requests=contenders,
                locks=[dict(subject=u, available=t, evidence_id=e)
                       for u,t,e in engine.resource_links.get(resource, ())],
                assigned_to=[slot for slot, rs in result['assigned'].items() if resource in rs]))
    return {'cases': rows, 'elimination_steps': result.get('trace', [])}


if __name__ == '__main__':
    root=Path(__file__).resolve().parents[2]
    engine=AuditEngine(root/'dataset').load()
    report=trace(engine, engine.request_windows, extended='--extended' in sys.argv)
    text=json.dumps(report, indent=2)
    (root/'.runtime'/('ownership_trace_extended.json' if '--extended' in sys.argv else 'ownership_trace.json')).write_text(text, encoding='utf-8')
    print(text)
