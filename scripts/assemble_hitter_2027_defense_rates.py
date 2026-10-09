"""Refresh reviewed skill recipes; role/opportunity and total WAR stay separate."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import polars as pl
from universal_baseball.hitter_defense_rates_v1 import DefenseRates
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-defense-rates'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'
NEW=ROOT/'reports/generated/hitter-2027-nonbatting-source'


def main():
    assert not (PUBLIC/'defense-rates-assembly.json').exists()
    sources=dict(native=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet',
        framing=ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet',
        catcher=ROOT/'reports/generated/catcher-throw-block-v5/extension-annual.parquet',
        other=ROOT/'reports/generated/arm-receiving-v6/official-scope/annual.parquet')
    additions=dict(native=[NEW/'component-ledger.parquet'],framing=[NEW/'framing-annual.parquet'],
        catcher=[NEW/'catcher-opportunities.parquet'],other=[NEW/'arm-official-scope-annual.parquet',NEW/'receiving-native-annual.parquet'])
    for name in ['nonbatting-source-player-review.json','arm-official-scope-review.json']:
        note=json.loads((PUBLIC/name).read_text())
        assert note['source_approved_for_estimation']
        for p,h in note['hashes'].items():assert sha256_file(Path(p))==h
    records={};paths=[*sources.values(),*[p for pp in additions.values() for p in pp]]
    for kind,path in sources.items():
        old=pl.read_parquet(path);assert old['season'].max()<=2025
        # Lists retain each reviewed source's optional metadata without coercing
        # incompatible nested audit structs. The estimator needs the common fields.
        records[kind]=old.to_dicts()
        for p in additions[kind]:
            fresh=pl.read_parquet(p);assert set(fresh['season'])=={2026}
            records[kind].extend(fresh.to_dicts())
    model=DefenseRates(origin=2026,native=records['native'],framing=records['framing'],
        catcher=records['catcher'],arm_receiving=records['other'])
    stints_path=ROOT/'reports/generated/hitter-2027-origin-counts/team-season-inputs.parquet'
    stints=pl.read_parquet(stints_path)
    frozen_path=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/forecast.parquet'
    frozen=pl.read_parquet(frozen_path,columns=['player_id'])
    ids=sorted(set(stints.filter(pl.col('position')!='1')['player_id'])|set(frozen['player_id']))
    names={r['player_id']:r['player_name'] for r in stints.to_dicts()}
    rows=[dict(**r,player_name=names.get(pid)) for pid in ids for r in model.player(pid)]
    OUT.mkdir(parents=True,exist_ok=True);p=OUT/'rates.parquet';assert not p.exists()
    frame=pl.DataFrame(rows,infer_schema_length=None);frame.write_parquet(p)
    by=defaultdict(list)
    for r in rows:by[r['player_id']].append(r)
    fixed=[672275,596019,621566,624431,592450,805811,660271,804944]
    walks=[]
    for pid in fixed:
        source={k:[r for r in rr if r['player_id']==pid and 2024<=r['season']<=2026] for k,rr in records.items()}
        peers=[]
        primary=max(by[pid],key=lambda r:r['weighted_history_opportunities'])
        pool=[r for r in rows if r['player_id']!=pid and r['component']==primary['component'] and r['context']==primary['context']]
        for r in sorted(pool,key=lambda r:(abs(r['weighted_history_opportunities']-primary['weighted_history_opportunities']),r['player_id']))[:3]:
            peers.append(dict(rates=by[r['player_id']],source={k:[s for s in rr if s['player_id']==r['player_id'] and 2024<=s['season']<=2026] for k,rr in records.items()}))
        walks.append(dict(player_id=pid,player_name=names.get(pid),rates=by[pid],source=source,peers=peers,
            peer_selection='Same largest-exposure component/context; closest history exposure then player ID; no future outcomes'))
    walk=PUBLIC/'defense-rates-player-walkthrough.json.gz';assert not walk.exists()
    walk.write_bytes(gzip.compress(json.dumps(walks,allow_nan=False,default=str).encode(),mtime=0))
    paths.extend([stints_path,frozen_path,Path(__file__),ROOT/'src/universal_baseball/hitter_defense_rates_v1.py'])
    write_once(PUBLIC/'defense-rates-assembly.json',dict(origin=2026,first_projection_year=2027,
        people=len(ids),rows=len(rows),source_reuse='Previously reviewed V3/V4/V5/V6/V26/V28 histories; same recency and shrinkage, current evidence',
        recipe_changes=False,source_walkthrough_cases=len(walks),player_interpretation_status='pending_written_review',
        observed_by_component=frame.group_by('component','context').agg(pl.col('individual_evidence_observed').sum()).sort('component','context').to_dicts(),
        forecasts_of_delivered_value=False,release_population_final=False,model_release_approved=False,
        remaining=['Position and native opportunity forecast','DP, non-OF arms and ABS estimator decisions','Running assembly','Lower-minor profile support','Full additive value and financial paths'],
        input_hashes={str(p):sha256_file(p) for p in paths},output_hashes={str(p):sha256_file(p) for p in [p,walk]}))
    print(f'Refreshed 12 defensive skill channels for {len(ids)} provisional hitter identities; no WAR awarded without projected exposure.')
    for pid in fixed:
        print(names.get(pid,pid),[(r['component'],r['context'],round(r['runs_per_unit'],3)) for r in by[pid] if r['individual_evidence_observed']])


if __name__=='__main__':main()
