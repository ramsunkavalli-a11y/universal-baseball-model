"""Player-level source review, retaining native runs and explicit small discrepancies."""
from pathlib import Path
import gzip
import json
import polars as pl
from universal_baseball.storage import sha256_file
from capture_hitter_2027_nonbatting_sources import OUT,PUBLIC
from capture_hitter_2027_origin_counts import write_once


def main():
    review=PUBLIC/'nonbatting-source-player-review.json'
    assert not review.exists()
    reconciliation=PUBLIC/'nonbatting-source-reconciliation.json'
    r=json.loads(reconciliation.read_text(encoding='utf8'))
    for p,h in r['output_hashes'].items():assert sha256_file(Path(p))==h
    frames={n:pl.read_parquet(OUT/f'{n}.parquet') for n in
        ['component-ledger','catcher-opportunities','framing-annual','arm-receiving-annual']}
    receiving=frames['arm-receiving-annual'].filter(pl.col('kind')=='receiving')
    # Two independently retrieved Savant tables differ by <.01 run per player.
    # Use the published component ledger's numerator, NOT a fabricated exact match.
    # The threshold is source materiality (<.001 WAR), not an empirical skill test.
    assert receiving['native_runs'].null_count()==0
    assert receiving['numerator_gap'].abs().max()<.01
    assert receiving['opportunities'].min()>0
    native=frames['component-ledger'].filter(pl.col('position')==3).select(
        'player_id','exposure_valid')
    certified=receiving.join(native,on='player_id',validate='1:1').with_columns(
        pl.col('runs').alias('oaa_conversion_runs'),
        pl.col('native_runs').alias('runs'),
        (100*pl.col('native_runs')/pl.col('opportunities')).alias('runs_per_100'),
        pl.col('exposure_valid').alias('quality_valid'),
        pl.lit('Native FRV receiving runs; independently checked receiving chances; <.01 run cross-table discrepancy retained').alias('source_method'))
    path=OUT/'receiving-native-annual.parquet';assert not path.exists();certified.write_parquet(path)
    cases=[]
    reasons={672275:'Catcher: distinct framing, throwing, blocking and ABS credit',
        596019:'Shortstop: arm credit is not automatically outfield credit',
        621566:'First base: exact innings plus omitted tiny other-position exposure',
        624431:'Catcher who also pitched: pitcher innings must not enter catcher rate',
        592450:'Outfielder: range and throwing are separate skills',
        805811:'New MLB first baseman: measured evidence, not a blanket minors prior',
        660271:'DH/two-way: no position-fielding record is not missing everyday defense',
        804944:'Minor leaguer: no MLB tracking record is unknown MLB defensive skill'}
    for pid,reason in reasons.items():
        player={n:f.filter(pl.col('player_id')==pid).to_dicts() for n,f in frames.items()}
        player['receiving-native-annual']=certified.filter(pl.col('player_id')==pid).to_dicts()
        player['aggregate_outs_review']=[a for a in r['aggregate_outs_review'] if a['player_id']==pid]
        player['missing_position_rows']=[a for a in r['official_positive_position_gaps'] if a['player_id']==pid]
        positions=player['component-ledger']
        peers=[]
        if positions:
            primary=max(positions,key=lambda a:a['native_outs'])
            pool=frames['component-ledger'].filter((pl.col('position')==primary['position'])&(pl.col('player_id')!=pid))
            peers=pool.with_columns((pl.col('native_outs')-primary['native_outs']).abs().alias('distance')).sort('distance','player_id').head(3).to_dicts()
        cases.append(dict(player_id=pid,reason=reason,sources=player,peers=peers,
            peer_selection='Same source position, closest current outs, then ID; no future outcome selection',
            measured_2027_result=False))
    walk=PUBLIC/'nonbatting-source-player-walkthrough.json.gz'
    assert not walk.exists();walk.write_bytes(gzip.compress(json.dumps(cases,allow_nan=False).encode(),mtime=0))
    write_once(review,dict(player_walkthrough_status='complete',source_approved_for_estimation=True,
        performance_validation=False,forecasts_created=False,source_cases=len(cases),
        receiving_source_discrepancy_max_runs=receiving['numerator_gap'].abs().max(),
        receiving_policy='Use native published runs with independently checked counts. Do not claim exact cross-table equality. Materiality limit .01 run; all raw values and differences retained.',
        excluded_position_rate_rows=r['exposure_mismatches'],
        missing_position_rows=len(r['official_positive_position_gaps']),
        current_abs_only=True,abs_no_longitudinal_skill_validation=True,
        no_data_rule='Unknown skill for absent MLB records; no automatic zero-talent label',
        hashes={str(p):sha256_file(p) for p in [reconciliation,path,walk,Path(__file__)]}))
    print(f'Source review complete: {len(cases)} cases; native receiving runs retained for {len(certified)} players')


if __name__=='__main__':main()
