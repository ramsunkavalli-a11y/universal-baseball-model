"""Lossless archive for thousands of count priors; original local files retained."""
from pathlib import Path
import gzip
import hashlib
import json
from zipfile import ZipFile,ZIP_STORED

from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-count-reliability-v20'


def main():
    with gzip.open(PUBLIC/'summary.json.gz','rt',encoding='utf8') as f:summary=json.load(f)
    fits=sorted((PUBLIC/'fits').glob('*.json.gz'));assert len(fits)==summary['fitted_reference_groups']
    path=PUBLIC/'reference-fits.zip';receipt=PUBLIC/'archive-index.json.gz'
    assert not path.exists() and not receipt.exists()
    hashes={p.name:sha256_file(p) for p in fits}
    with ZipFile(path,'w',compression=ZIP_STORED) as archive:
        for p in fits:archive.write(p,arcname=p.name)
    with ZipFile(path) as archive:
        assert sorted(archive.namelist())==sorted(hashes)
        for name,h in hashes.items():assert hashlib.sha256(archive.read(name)).hexdigest()==h
    with gzip.open(receipt,'wt',encoding='utf8') as f:
        json.dump(dict(original_gzip_bytes_preserved=True,source_files=len(fits),original_local_files_retained=True,
            archive_sha256=sha256_file(path),archive_entries_sha256=hashes,runner_sha256=sha256_file(Path(__file__))),f,separators=(',',':'))
    print(dict(fits=len(fits),archive_bytes=path.stat().st_size,lossless_replay=True))


if __name__=='__main__':main()
