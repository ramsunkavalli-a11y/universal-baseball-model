"""Read hashes or restore missing archived artifacts; never overwrite existing data."""
from pathlib import Path
import argparse
import hashlib
from zipfile import ZipFile

from verify_minor_range_correction_v21 import ROOT,PUBLIC,OUT,read
from universal_baseball.storage import sha256_file


def digest(p):
    if p.exists():return sha256_file(p)
    rel=p.resolve().relative_to(OUT.resolve()).as_posix()
    with ZipFile(PUBLIC/'execution-artifacts.zip') as z:return hashlib.sha256(z.read(rel)).hexdigest()


def check(restore=False):
    receipt=read(PUBLIC/'archive-index.json.gz');archive=PUBLIC/'execution-artifacts.zip'
    assert sha256_file(archive)==receipt['archive_sha256']
    assert sha256_file(ROOT/'scripts/archive_minor_range_correction_v21.py')==receipt['runner_sha256']
    with ZipFile(archive) as z:
        assert sorted(z.namelist())==sorted(receipt['entries_sha256'])
        for name,h in receipt['entries_sha256'].items():
            target=(OUT/name).resolve();assert target.is_relative_to(OUT.resolve())
            data=z.read(name);assert hashlib.sha256(data).hexdigest()==h
            if target.exists():assert sha256_file(target)==h
            elif restore:
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as f:f.write(data)
    print(dict(archive_entries_verified=len(receipt['entries_sha256']),restore_requested=restore),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--restore',action='store_true')
    check(parser.parse_args().restore)
