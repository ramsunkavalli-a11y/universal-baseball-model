"""Check or restore exact compressed fit bytes; never overwrite existing fits."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re
from zipfile import ZipFile

from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-count-reliability-v20'


def digest(p):
    if not p.exists() and p.parent.name=='fits':
        with ZipFile(PUBLIC/'reference-fits.zip') as archive:return hashlib.sha256(archive.read(p.name)).hexdigest()
    return sha256_file(p)


def main(restore):
    with gzip.open(PUBLIC/'archive-index.json.gz','rt',encoding='utf8') as f:receipt=json.load(f)
    assert sha256_file(PUBLIC/'reference-fits.zip')==receipt['archive_sha256']
    assert sha256_file(ROOT/'scripts/archive_minor_count_fits_v20.py')==receipt['runner_sha256']
    hashes=receipt['archive_entries_sha256'];folder=PUBLIC/'fits'
    if restore:folder.mkdir(exist_ok=True)
    with ZipFile(PUBLIC/'reference-fits.zip') as archive:
        assert sorted(archive.namelist())==sorted(hashes)
        for name,h in hashes.items():
            assert re.fullmatch(r'g\d{5}\.json\.gz',name)
            data=archive.read(name);assert hashlib.sha256(data).hexdigest()==h
            note=json.loads(gzip.decompress(data).decode('utf8'));assert note['group_id']==name.split('.')[0]
            path=folder/name
            if path.exists():assert sha256_file(path)==h
            elif restore:
                # Lossless binary artifact restoration, not a new model or text edit.
                with path.open('xb') as f:f.write(data)
    print(dict(archive_entries_checked=len(hashes),exact_bytes=True,restoration_requested=restore))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--restore',action='store_true')
    main(parser.parse_args().restore)
