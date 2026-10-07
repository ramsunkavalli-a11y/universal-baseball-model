"""Replay native opportunities and source cases before talent testing."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.catcher_throw_block import normalize
from universal_baseball.storage import sha256_file

FIXED=(592663,596142,595978,663728,672386,672275)
PUBLIC=ROOT/'reports/model-evidence/catcher-throw-block-v5'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--extend',action='store_true');args=parser.parse_args()
    prefix='extension' if args.extend else 'pilot'
    capture=json.loads((OUT/(prefix+'-capture.json')).read_text(encoding='utf8'))
    protected=protections();assert capture['protections']==protected
    source=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    native={(r['season'],r['player_id']):r for r in pl.read_parquet(source).filter(pl.col('position')==2).to_dicts()}
    framing={(r['season'],r['player_id']):r['pitches'] for r in pl.read_parquet(ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet').to_dicts()}
    rows=[];summary=[];walks=[];gaps=[];hashes={str(source):sha256_file(source)};fingerprints=defaultdict(set)
    for c in capture['captures']:
        kind,year=c['kind'],c['year'];path=Path(c['path']);assert sha256_file(path)==c['sha256']
        fingerprints[kind].add(c['sha256']);hashes[str(path)]=c['sha256']
        raw=list(csv.DictReader(path.open(encoding='utf-8-sig')))
        annual=[]
        for r in raw:
            key=year,int(r['player_id']);assert key in native
            a=normalize(kind,year,r,native[key]);a['framing_pitches']=framing.get(key)
            rows.append(a);annual.append(a)
        seen={r['player_id'] for r in annual}
        missing=[n for (y,p),n in native.items() if y==year and p not in seen and n[kind+'_runs'] is not None]
        # Reconciliation certifies covered rows, not completeness. Preserve all
        # missing native records, including nonzero tiny cameos, as unknown.
        # Future labels must later reject a window with any such positive outs.
        gaps.extend(dict(component=kind,season=year,player_id=n['player_id'],native_outs=n['native_outs'],runs=n[kind+'_runs'],quality='unknown') for n in missing)
        summary.append(dict(component=kind,year=year,rows=len(annual),people=len(seen),valid=sum(a['measurement_valid'] for a in annual),
                            opportunities=sum(a['opportunities'] for a in annual),runs=sum(a['runs'] for a in annual),
                            missing_native_rows=len(missing),minimum=min(a['opportunities'] for a in annual),
                            blocking_equals_framing_count=sum(a['opportunities']==a['framing_pitches'] for a in annual) if kind=='blocking' else None))
        selected={a['player_id'] for a in annual if a['player_id'] in FIXED}|{a['player_id'] for a in sorted(annual,key=lambda a:(a['opportunities'],a['player_id']))[:2]}
        for pid in sorted(selected):
            a=next(r for r in annual if r['player_id']==pid)
            peers=sorted([p for p in annual if p['player_id']!=pid],key=lambda p:(abs(p['opportunities']-a['opportunities']),p['player_id']))[:3]
            walks.append(dict(selection='fixed identity or two smallest positive samples; three exposure/ID-selected peers',primary=a,peers=peers))
    assert all(len(fingerprints[k])==sum(c['kind']==k for c in capture['captures']) for k in fingerprints)
    table=OUT/(prefix+'-annual.parquet');assert not table.exists()
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(table)
    walk=OUT/(prefix+'-player-walkthrough.json');assert not walk.exists()
    save(walk,dict(player_walkthrough_status='complete',cases=walks,model_fit=False))
    paths=[table,walk,ROOT/'docs/catcher-throw-block-v5-source-contract.md',Path(__file__),ROOT/'src/universal_baseball/catcher_throw_block.py',OUT/(prefix+'-capture.json')]
    hashes.update({str(p):sha256_file(p) for p in paths})
    report=dict(source_integrity='pass',source_coverage='qualified_missing_rows' if gaps else 'complete_native_match',
                player_walkthrough_status='complete',year_specific_payloads=True,summary=summary,
                source_cases=len(walks),missing_native_rows=gaps,rounded_blocking_display_not_used_as_numerator=True,
                opportunity_scopes_separate=True,no_2026_outcomes=True,model_fit=False,deployment_approved=False,protections=protected,hashes=hashes)
    review=OUT/(prefix+'-review.json');assert not review.exists();save(review,report)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    for p in (review,walk):
        dest=PUBLIC/p.name;assert not dest.exists();dest.write_bytes(p.read_bytes())
    print(json.dumps(dict(summary=summary,cases=len(walks),missing_rows=len(gaps)),indent=2))


if __name__=='__main__':main()
