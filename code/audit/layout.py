"""Spatial OCR grouping: associate subjects with rows, not whole screenshots."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from .core import RESOURCE


def read_layout(path, cache):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    target = cache / (digest+'.layout-v2.json')
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8-sig'))
    cache.mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':
        return None
    from PIL import Image
    with Image.open(path) as image:
        scale = min(2, 2500/max(image.size))
        size = tuple(round(v*scale) for v in image.size)
        resized = cache/(digest+'.scaled.png')
        image.resize(size,Image.Resampling.LANCZOS).save(resized)
    script = Path(__file__).resolve().parents[1]/'extract_windows_ocr.ps1'
    result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',
                             '-File',str(script),'-ImagePath',str(resized.resolve()),'-Layout'],
                            capture_output=True,timeout=45)
    if result.returncode or result.stderr:
        raise RuntimeError('Spatial OCR requires local media access')
    data = json.loads(result.stdout.decode('utf-8-sig'))
    target.write_text(json.dumps(data),encoding='utf-8')
    resized.unlink(missing_ok=True)
    return data


def grouped_rows(layout):
    """Merge OCR words on the same visual row, preserving left/right order."""
    rows=[]
    for word in sorted(layout['words'],key=lambda w:(w['y']+w['height']/2,w['x'])):
        center=word['y']+word['height']/2
        row=next((r for r in reversed(rows[-4:]) if abs(r['center']-center)<=max(4,word['height']*.45)),None)
        if row is None:
            row={'center':center,'words':[]};rows.append(row)
        row['words'].append(word)
    return rows


def resource_regions(layout):
    """Prefer literal resource+identifier rows. Single-subject pages may use
    their header, but multi-subject pages cannot share all identity links."""
    width=layout['width'];height=layout['height']
    regions=[]
    for row in grouped_rows(layout):
        # Exclude navigation and separate the detail card from the main table.
        for lo,hi in ((.13,.78),(.78,1.01)):
            words=sorted((w for w in row['words'] if lo*width<=w['x']<hi*width),key=lambda w:w['x'])
            text=' '.join(w['text'] for w in words)
            for resource in RESOURCE.findall(text):
                regions.append((resource,text,f'row:y={round(row["center"])},x={lo}-{hi}'))
    return regions
