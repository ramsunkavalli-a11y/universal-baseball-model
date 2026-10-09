"""Read-only archive extraction; run with the bundled spreadsheet Python runtime."""
import csv,gzip,hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-2027-base/historical-full-value'


def main():
    manifest=ROOT/'model_artifacts/public-benchmark-intake-v2/verified-archive-manifest.json'
    records=json.loads(manifest.read_text())['records'];rows=[];sources=[]
    for r in records:
        if r['year'] not in (2023,2024,2025):continue
        assert r['label_verified'] and r['vintage_class']=='historical_preseason'
        p=ROOT/r['private_file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
        with p.open(encoding='utf-8-sig',newline='') as stream:
            raw=list(csv.DictReader(stream))
        valid=[];invalid=[]
        for q in raw:
            if not q['MLBAMID'].isdigit() or int(q['MLBAMID'])<=0:
                invalid.append(q['PlayerId']);continue
            row=dict(system=r['system'].lower(),season=r['year'],player_id=int(q['MLBAMID']),
                name=q['Name'],PA=float(q['PA']),WAR=float(q['WAR']),source=str(p))
            assert row['PA']>=0 and math.isfinite(row['WAR'])
            valid.append(row)
        assert len(valid)==len({q['player_id'] for q in valid})
        rows.extend(valid);sources.append(dict(system=r['system'],season=r['year'],sha256=r['sha256'],
            rows=len(raw),valid=len(valid),invalid_FG_ids=invalid,source=str(p)))
    assert len(sources)==6
    output=OUT/'public-preseason-WAR.json.gz';assert not output.exists()
    output.write_bytes(gzip.compress(json.dumps(rows,allow_nan=False).encode(),mtime=0))
    receipt=ROOT/'reports/model-evidence/hitter-2027-v1/public-WAR-extraction.json';assert not receipt.exists()
    receipt.write_text(json.dumps(dict(sources=sources,rows=len(rows),output=str(output),
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),source_csv_modified=False,
        limits='Existing historical preseason label verified; exact original snapshot timestamps remain qualified.'),indent=2)+'\n',encoding='utf8')
    print('Read-only public WAR extraction:',len(rows),'rows, six existing verified archives.')


if __name__=='__main__':main()
