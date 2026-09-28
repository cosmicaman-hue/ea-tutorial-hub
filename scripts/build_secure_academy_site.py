"""Build the unified Pages shell with general Scoreboard and protected party views.

This never reads the live ledger. Only already-published resource catalog files
and referenced public images enter the output; the legacy SPA is excluded.
"""
from pathlib import Path
import argparse
import json
import shutil
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'public_site'
OUTPUT = ROOT / 'rebuild/out/secure_academy_site'
GENERAL_KEYS = {'updated_at','top_full_count','months','scoreboard','chess_champion','public_information'}
ROW_KEYS = {'rank','roll','name','class','total','photo_path','masked'}
FILES = ['index.html','_headers','academy-auth.js','student-portraits.js','profile/app.js','profile/styles.css',
         'excel_results/app.js','excel_results/styles.css','excel_results/catalog.json',
         'excel_study_notes/app.js','excel_study_notes/styles.css','excel_study_notes/catalog.json']

def general_snapshot(data):
    result={key:value for key,value in data.items() if key in GENERAL_KEYS}
    result['scoreboard']={month:[{key:value for key,value in row.items() if key in ROW_KEYS}
        for row in rows] for month,rows in (data.get('scoreboard') or {}).items()}
    return result

def referenced_files(value):
    if isinstance(value,dict):
        for child in value.values():yield from referenced_files(child)
    elif isinstance(value,list):
        for child in value:yield from referenced_files(child)
    elif isinstance(value,str):
        parsed=urlsplit(value)
        if not parsed.scheme and not parsed.netloc:
            path=unquote(parsed.path).lstrip('./')
            if path.startswith(('static/uploads/','excel_results/files/','excel_study_notes/files/')):
                target=(SOURCE/path).resolve()
                if not target.is_relative_to(SOURCE.resolve()) or '..' in Path(path).parts:raise ValueError('Unsafe published asset path')
                yield target.relative_to(SOURCE.resolve()).as_posix()

def catalog_files(value,folder):
    if isinstance(value,dict):
        if 'storage_key' in value and value['storage_key']:
            key=str(value['storage_key'])
            if Path(key).name!=key or any(char in key for char in ('/','\\',':','%')) or key in ('.','..'):raise ValueError('Unsafe published storage key')
            yield folder+'/files/'+key
        for child in value.values():yield from catalog_files(child,folder)
    elif isinstance(value,list):
        for child in value:yield from catalog_files(child,folder)

def expected_files():
    data=general_snapshot(json.loads((SOURCE/'scores.json').read_text(encoding='utf-8-sig')))
    credentials=json.loads((SOURCE/'credentials.json').read_text(encoding='utf-8-sig'))
    # Explicitly retain the existing general-login contract, with no extra fields.
    credentials={'credentials':[{k:v for k,v in row.items() if k in {'roll','salt','hash'}} for row in credentials.get('credentials',[])]}
    generated={'scores.json':json.dumps(data,ensure_ascii=False,separators=(',',':')).encode(),
               'credentials.json':json.dumps(credentials,separators=(',',':')).encode()}
    allowed=set(FILES)
    allowed.update(referenced_files(data))
    for folder in ('excel_results','excel_study_notes'):
        catalog=json.loads((SOURCE/folder/'catalog.json').read_text(encoding='utf-8-sig'))
        allowed.update(referenced_files(catalog));allowed.update(catalog_files(catalog,folder))
    for name in allowed:
        source=SOURCE/name
        if source.is_symlink() or not source.is_file():raise ValueError('Published asset missing or symlink: '+name)
        generated[name]=source.read_bytes()
    return generated

def build(check=False):
    expected=expected_files()
    actual={p.relative_to(OUTPUT).as_posix() for p in OUTPUT.rglob('*') if p.is_file()}
    extra=actual-set(expected)
    if extra:raise ValueError('Unexpected output files; review before removal: '+', '.join(sorted(extra)))
    for name,body in expected.items():
        target=OUTPUT/name
        if not check:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
        if not target.is_file() or target.read_bytes()!=body:raise ValueError('Build differs from source: '+name)
    print(f'Verified {len(expected)} allowlisted files in {OUTPUT}')
    return expected

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    build(parser.parse_args().check)
