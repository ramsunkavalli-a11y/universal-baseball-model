"""Historical extension with separate immutable pilot and early-quality quarantine."""
from collections import defaultdict
import csv
import json
from pathlib import Path

import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import FIXED,PUBLIC
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.catcher_throw_block_coverage import qualified
from universal_baseball.storage import sha256_file


def main():
    protected=protections()
    capture=json.loads((OUT/'extension-capture.json').read_text(encoding='utf8'))
    assert capture['protections']==protected
    pilot=json.loads((OUT/'pilot-review.json').read_text(encoding='utf8'))
    for path,h in pilot['hashes'].items():assert sha256_file(Path(path))==h
    source=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    native={(r['season'],r['player_id']):r for r in pl.read_parquet(source).filter(pl.col('position')==2).to_dicts()}
    framing={(r['season'],r['player_id']):r['pitches'] for r in pl.read_parquet(ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet').to_dicts()}
    rows=[];summary=[];walks=[];gaps=[];hashes={str(source):sha256_file(source)};fingerprints=defaultdict(set)
    for c in capture['captures']:
        k,y=c['kind'],c['year'];p=Path(c['path']);assert sha256_file(p)==c['sha256'];hashes[str(p)]=c['sha256'];fingerprints[k].add(c['sha256'])
        raw=list(csv.DictReader(p.open(encoding='utf-8-sig')))
        annual=[]
        for r in raw:
            key=y,int(r['player_id']);assert key in native
            a=qualified(k,y,r,native[key]);a['framing_pitches']=framing.get(key);rows.append(a);annual.append(a)
        seen={r['player_id'] for r in annual}
        missing=[n for (year,pid),n in native.items() if year==y and pid not in seen and n[k+'_runs'] is not None]
        gaps.extend(dict(component=k,season=y,player_id=n['player_id'],native_outs=n['native_outs'],runs=n[k+'_runs'],quality='unknown') for n in missing)
        summary.append(dict(component=k,year=y,rows=len(annual),valid=sum(a['measurement_valid'] for a in annual),
                context_identity_failures=sum(not a['context_identity_valid'] for a in annual),opportunities=sum(a['opportunities'] for a in annual),
                runs=sum(a['runs'] for a in annual),missing_native_rows=len(missing),minimum=min(a['opportunities'] for a in annual)))
        selected={a['player_id'] for a in annual if a['player_id'] in FIXED or not a['context_identity_valid']}|{a['player_id'] for a in sorted(annual,key=lambda a:(a['opportunities'],a['player_id']))[:2]}
        for pid in sorted(selected):
            a=next(r for r in annual if r['player_id']==pid)
            peers=sorted([p for p in annual if p['player_id']!=pid],key=lambda p:(abs(p['opportunities']-a['opportunities']),p['player_id']))[:3]
            walks.append(dict(selection='fixed identity, context discrepancy or two smallest samples; three exposure/ID-selected peers',primary=a,peers=peers))
    assert all(len(fingerprints[k])==sum(c['kind']==k for c in capture['captures']) for k in fingerprints)
    table=OUT/'extension-annual.parquet';assert not table.exists();pl.DataFrame(rows,infer_schema_length=None).write_parquet(table)
    walk=OUT/'extension-player-walkthrough.json';assert not walk.exists();save(walk,dict(player_walkthrough_status='complete',cases=walks,model_fit=False))
    for p in (table,walk,Path(__file__),ROOT/'src/universal_baseball/catcher_throw_block_coverage.py',OUT/'extension-capture.json',ROOT/'docs/catcher-throw-block-v5-source-amendment.md'):
        hashes[str(p)]=sha256_file(p)
    review=OUT/'extension-review.json';assert not review.exists()
    save(review,dict(source_integrity='pass',source_coverage='qualified',player_walkthrough_status='complete',summary=summary,
         source_cases=len(walks),missing_native_rows=gaps,context_quarantined=[r for r in rows if not r['context_identity_valid']],
         protections=protected,hashes=hashes,no_2026_outcomes=True,model_fit=False,deployment_approved=False))
    for p in (review,walk):
        dest=PUBLIC/p.name;assert not dest.exists();dest.write_bytes(p.read_bytes())
    print(json.dumps(dict(summary=summary,source_cases=len(walks),gaps=len(gaps)),indent=2))


if __name__=='__main__':main()
