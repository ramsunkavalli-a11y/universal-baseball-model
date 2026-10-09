"""Current tracking source reconciliation and identical feature arithmetic."""
from pathlib import Path
import json
import math
import polars as pl
from polars.testing import assert_frame_equal
from universal_baseball.hitter_origin_tracking_v1 import project_measurements
from universal_baseball.hitter_statcast_measurement import interference_award
from universal_baseball.hitter_statcast_history import annual_launch_features
from universal_baseball.storage import sha256_file
from finalize_hitter_tracking_2025 import independent_annual
from capture_hitter_2027_origin_counts import ROOT,write_once
from capture_hitter_tracking_2026 import OUT as SOURCE

OUT=SOURCE/'review'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    assert not (PUBLIC/'tracking-2026-initial-review.json').exists()
    receipts=[json.loads((SOURCE/f'2026-{m:02}.json').read_text()) for m in range(3,11)]
    for note in receipts:
        for p,h in note['outputs'].items():assert sha256_file(Path(p))==h
    raw=pl.concat([pl.read_parquet(SOURCE/f'2026-{m:02}.parquet') for m in range(3,11)])
    q,excluded=project_measurements(raw,2026,source_cutoff=2026)
    annual=annual_launch_features(q)
    # Independent NumPy summaries, including EV95 and ddof=1 LA variability.
    source_rows={int(k[0]):g.to_dicts() for k,g in raw.filter((pl.col('type')=='X')&
        pl.col('events').fill_null('').str.strip_chars().ne('')&~interference_award()&
        ~pl.col('des').fill_null('').str.to_lowercase().str.contains(r'\bbunt\b')).partition_by('batter',as_dict=True).items()}
    checks=0
    for row in annual.to_dicts():
        expected=independent_annual(source_rows[row['player_id']])
        for k,v in expected.items():
            actual=row[k]
            if k.endswith('_date'):assert str(actual)==v
            elif v is None:assert actual is None
            else:assert math.isclose(actual,v,rel_tol=0,abs_tol=1e-10),(row['player_id'],k)
            checks+=1
    official=pl.read_parquet(ROOT/'reports/generated/hitter-2027-origin-counts/team-season-inputs.parquet').filter(pl.col('sport_id')==1)
    official=official.group_by('player_id').agg(pl.col('player_name').first(),
        (pl.col('at_bats')-pl.col('strike_outs')+pl.col('sac_flies')+pl.col('sac_bunts')).sum().alias('official_contacts'),
        *[pl.col(c).sum() for c in ['singles','doubles','triples','home_runs','plate_appearances']])
    contacts=raw.filter((pl.col('type')=='X')&pl.col('events').fill_null('').str.strip_chars().ne('')&~interference_award())
    actual=contacts.group_by(pl.col('batter').cast(pl.Int64).alias('player_id')).agg(pl.len().alias('source_contacts'),
        *[(pl.col('events')==e).sum().alias(c+'_source') for e,c in [('single','singles'),('double','doubles'),('triple','triples'),('home_run','home_runs')]])
    paired=official.join(actual,on='player_id',how='full',coalesce=True,validate='1:1').with_columns(pl.exclude('player_id','player_name').fill_null(0))
    paired=paired.with_columns((pl.col('source_contacts')-pl.col('official_contacts')).alias('contact_residual'))
    residuals=paired.filter((pl.col('contact_residual')!=0)|pl.any_horizontal([pl.col(c)!=pl.col(c+'_source') for c in ['singles','doubles','triples','home_runs']]))
    OUT.mkdir(exist_ok=True)
    outputs={}
    for name,f in [('launch-events',q),('annual-features',annual),('player-reconciliation',paired)]:
        p=OUT/f'{name}.parquet'
        if p.exists():
            keys=['game_pk','player_id','at_bat_number','pitch_number'] if name=='launch-events' else ['player_id']
            # Parallel group reduction can change final floating-point bits and
            # group output order. Preserve the first file; prove value equality
            # at the same tolerance used by the independent metric calculation.
            assert_frame_equal(pl.read_parquet(p).sort(keys),f.sort(keys),check_exact=False,rel_tol=0,abs_tol=1e-10)
        else:f.write_parquet(p)
        outputs[str(p)]=sha256_file(p)
    fixed=[592450,665487,660271,805811,672275,596019,804944,808393]
    walks=[]
    for pid in fixed:
        rows=annual.filter(pl.col('player_id')==pid).to_dicts()
        peers=[]
        if rows:
            n=rows[0]['measured_pair_contacts']
            peers=annual.filter(pl.col('player_id')!=pid).with_columns((pl.col('measured_pair_contacts')-n).abs().alias('distance')).sort('distance','player_id').head(3).to_dicts()
        walks.append(dict(player_id=pid,features=rows,counts=paired.filter(pl.col('player_id')==pid).to_dicts(),peers=peers,
            meaning='Missing MLB tracking is unknown, not poor contact quality; exact metric definitions retained.'))
    report=dict(raw_contacts=len(raw),selected_nonbunt_contacts=len(q),
        excluded_rows=len(excluded),people=len(annual),arithmetic_checks=checks,duplicate_terminal_pa=False,
        source_date_min=raw['game_date'].min(),source_date_max=raw['game_date'].max(),
        residuals=residuals.to_dicts(),source_player_cases=walks,
        source_approved_for_estimation=False,remaining='Review official-contact residuals and source game coverage before promotion',
        output_hashes=outputs,runner_sha256=sha256_file(Path(__file__)))
    write_once(PUBLIC/'tracking-2026-initial-review.json',json.loads(json.dumps(report,default=str,allow_nan=False)))
    print(f'{len(annual)} hitter measurement summaries; {len(raw)} raw contacts; {checks} independent arithmetic checks.')
    print('Contact/hit discrepancies:',residuals.to_dicts())


if __name__=='__main__':main()
