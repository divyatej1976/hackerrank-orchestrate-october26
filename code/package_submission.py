"""Build the code-only submission archive; never includes corpus or runtime data."""
from pathlib import Path
import os
from zipfile import ZipFile, ZIP_DEFLATED

EXCLUDED_DESIGN_DOCS = {
    'AGENT_DESIGN.md', 'API_DESIGN.md', 'BACKEND_DESIGN.md',
    'DATABASE_DESIGN.md', 'FRONTEND_DESIGN.md', 'MARKET_AND_PROBLEM_RESEARCH.md',
    'MEMORY_DESIGN.md', 'PRD.md', 'PRODUCT_VISION.md', 'USER_EXPERIENCE.md',
    'AI_ARCHITECTURE.md',
}


def main():
    source=Path(__file__).resolve().parent
    destination=source.parent/'code.zip'
    excluded={'.git','.runtime','__pycache__','.venv','venv','node_modules','dataset','data','build','dist'}
    required={'README.md','code/evaluation/evaluation_report.md','code/evaluation/usage_report.md',
              'code/prompts/intent_classification.md', 'code/README.md',
              'code/SYSTEM_ARCHITECTURE.md', 'code/PROMPT_ENGINEERING.md'}
    names=[]
    with ZipFile(destination,'w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.is_symlink():continue
            relative=path.relative_to(source)
            if any(part in excluded or part.startswith('.env') for part in relative.parts):continue
            if path.suffix.lower() in {'.zip','.pyc','.pyo','.pem','.key'}:continue
            if path.name in EXCLUDED_DESIGN_DOCS:continue
            if path.name=='ownership_trace.md':continue  # 5 MB generated trace; reproducible via evaluation/main.py
            name='code/'+relative.as_posix()
            archive.write(path,name);names.append(name)
        archive.write(source/'README.md','README.md')  # judges see the README first
    with ZipFile(destination) as archive:
        assert required <= set(archive.namelist()), 'Required evaluation reports missing'
        assert archive.testzip() is None, 'Archive integrity check failed'
        assert not any(Path(n).name in EXCLUDED_DESIGN_DOCS for n in archive.namelist()), 'Excluded design document in archive'
        assert not any(any(part.startswith('.env') for part in Path(n).parts) for n in archive.namelist()), 'Environment file in archive'
        key=os.environ.get('GROQ_API_KEY')
        if key:
            assert not any(key.encode('utf-8') in archive.read(n) for n in archive.namelist()), 'Credential detected; do not distribute archive'
        contents=sorted(archive.namelist())
    print(f'Wrote {destination.name}: {len(contents)} files; required evaluation reports included.')
    print('Archive contents:\n'+'\n'.join(contents))


if __name__=='__main__':main()
