"""Local provenance index and readable, static run report."""
import html
import json
import sqlite3
from pathlib import Path


def persist_index(engine, destination):
    connection = sqlite3.connect(destination)
    with connection:
        connection.executescript('''
        DROP TABLE IF EXISTS sources;
        DROP TABLE IF EXISTS observations;
        CREATE TABLE sources(evidence_id TEXT PRIMARY KEY, available_at TEXT NOT NULL);
        CREATE TABLE observations(observation_id INTEGER PRIMARY KEY, system_id TEXT,
          resource_id TEXT, category TEXT, state TEXT, observed_at TEXT, available_at TEXT,
          evidence_id TEXT REFERENCES sources(evidence_id), scope TEXT, locator TEXT,
          subject_links TEXT, facts TEXT);
        CREATE INDEX resource_time ON observations(system_id,resource_id,scope,observed_at);
        ''')
        connection.executemany('INSERT INTO sources VALUES (?,?)', engine.sources.items())
        connection.executemany('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            [(i,o.system,o.resource,o.category,o.state,o.time,o.available,o.evidence,o.scope,
              o.locator,json.dumps(sorted(o.links)),json.dumps(o.data,ensure_ascii=False))
             for i,o in enumerate(engine.observations,1)])
    connection.close()


def write_case_report(rows, summary, destination):
    esc = html.escape
    blocks = []
    for row in rows:
        steps = json.loads(row['steps_json'])
        body = ''.join('<tr>'+''.join('<td>'+esc(str(s[k]))+'</td>' for k in
                      ('step_no','phase','system_id','resource_id','operation','state','evidence_id'))+'</tr>' for s in steps)
        blocks.append(f'<details><summary>{esc(row["case_id"])} — {esc(row["deletion_status"])} · {len(steps)} steps</summary>'
                      '<table><thead><tr><th>#</th><th>Phase</th><th>System</th><th>Resource</th><th>Operation</th><th>State</th><th>Evidence</th></tr></thead>'
                      f'<tbody>{body}</tbody></table></details>')
    content = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Deletion audit report</title>
    <style>body{font:15px system-ui;max-width:1400px;margin:32px auto;padding:16px;color:#172334}
    details{border:1px solid #ccd6e0;border-radius:6px;margin:10px 0;padding:12px}summary{cursor:pointer;font-weight:600}
    table{border-collapse:collapse;width:100%;margin-top:12px}td,th{text-align:left;padding:8px;border-bottom:1px solid #ddd}
    .notice{padding:16px;background:#fff4d9}pre{white-space:pre-wrap}</style>
    <h1>Deletion audit report</h1><p class="notice">Proposed remediation has not been executed. Incomplete-case verification steps are future checks.
    This prototype has known coverage limitations; consult the evaluation report before relying on completion decisions.</p>'''
    content += '<h2>Run summary</h2><pre>'+esc(json.dumps(summary,indent=2))+'</pre>'
    content += '<h2>Cases</h2>'+''.join(blocks)+'</html>'
    Path(destination).write_text(content,encoding='utf-8')
