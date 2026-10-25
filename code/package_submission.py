"""Build the code-only submission archive; never includes corpus or runtime data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    source=Path(__file__).resolve().parent
    destination=source.parent/'code.zip'
    excluded={'.git','.runtime','__pycache__','.venv','venv','node_modules','dataset','data','build','dist'}
    required={'code/evaluation/evaluation_report.md','code/evaluation/usage_report.md'}
    names=[]
    with ZipFile(destination,'w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.is_symlink():continue
            relative=path.relative_to(source)
            if any(part in excluded or part.startswith('.env') for part in relative.parts):continue
            if path.suffix.lower() in {'.zip','.pyc','.pyo','.pem','.key'}:continue
            name='code/'+relative.as_posix()
            archive.write(path,name);names.append(name)
    with ZipFile(destination) as archive:
        assert required <= set(archive.namelist()), 'Required evaluation reports missing'
        assert archive.testzip() is None, 'Archive integrity check failed'
    print(f'Wrote {destination.name}: {len(names)} files; required evaluation reports included.')


if __name__=='__main__':main()
