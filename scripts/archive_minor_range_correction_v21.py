"""Archive exact private experiment bytes before removing any duplicate priors."""
from pathlib import Path
import hashlib
from zipfile import ZipFile,ZIP_STORED

from verify_minor_range_correction_v21 import ROOT,PUBLIC,OUT,read,write
from universal_baseball.storage import sha256_file


def main():
    reviewed=read(PUBLIC/'independent-review.json.gz')
    assert reviewed['forecasts_replayed']==13133
    paths=sorted(p for p in OUT.rglob('*') if p.is_file())
    assert sum(p.parent.name=='priors' for p in paths)==7519
    hashes={p.relative_to(OUT).as_posix():sha256_file(p) for p in paths}
    archive=PUBLIC/'execution-artifacts.zip';assert not archive.exists()
    with ZipFile(archive,'w',compression=ZIP_STORED) as z:
        for p in paths:z.write(p,arcname=p.relative_to(OUT).as_posix())
    with ZipFile(archive) as z:
        assert sorted(z.namelist())==sorted(hashes)
        for name,h in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==h
    write(PUBLIC/'archive-index.json.gz',dict(archive_sha256=sha256_file(archive),entries_sha256=hashes,
        private_root=str(OUT),original_files=len(paths),exact_compressed_bytes=True,originals_retained_at_archive_check=True,
        runner_sha256=sha256_file(Path(__file__))))
    print(dict(files=len(paths),archive_bytes=archive.stat().st_size,exact_archive_check=True),flush=True)


if __name__=='__main__':main()
