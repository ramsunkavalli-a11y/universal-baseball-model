"""Reconcile current native components, preserving new ABS credit and gaps."""
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
import gzip
import json
import math

import polars as pl

from universal_baseball.arm_receiving_source import normalize_receiving
from universal_baseball.arm_receiving_coverage import arm_record
from universal_baseball.older_fielding_source import outs_from_baseball_innings
from universal_baseball.player_value_runs_per_win import calculate_v1_runs_per_win
from universal_baseball.player_value_replacement_level import build_replacement_reference
from universal_baseball.storage import sha256_file
from capture_hitter_2027_nonbatting_sources import OUT,PUBLIC
from capture_hitter_2027_origin_counts import ROOT,write_once

COMPONENTS=('range_runs','arm_runs','dp_runs','fielding_runs_prevented_on_rec1b',
            'framing_runs','throwing_runs','blocking_runs','abs_runs')


def read_rows(name):
    return json.loads(gzip.decompress((OUT/f'{name}-rows.json.gz').read_bytes()))


def close(a,b):
    if not math.isclose(a,b,abs_tol=1e-8,rel_tol=0):
        raise ValueError(f'Component mismatch: {a} vs {b}')


def catcher_record(kind,row,native):
    """Same reviewed opportunity arithmetic, explicit new 2026 source boundary."""
    assert int(row['start_year'])==2026 and (not row['end_year'] or int(row['end_year'])==2026)
    if kind=='throwing':
        n=float(row['sb_attempts']);actual=float(row['n_cs']);expected=n*float(row['est_cs_pct'])
        numerator=actual-expected;runs=.65*numerator
        close(numerator,float(row['caught_stealing_above_average']))
        close(numerator/n,float(row['cs_aa_per_throw']))
        close(runs,float(row['catcher_stealing_runs']))
    else:
        n=float(row['pitches']);actual=float(row['n_pbwp']);expected=float(row['x_pbwp'])
        numerator=expected-actual;runs=.25*numerator
        close(40*numerator/n,float(row['blocks_above_average_per_game']))
        close(numerator,sum(float(row['diff_pbwp_'+s]) for s in ['easy','medium','tough']))
        close(1.,sum(float(row['freq_pbwp_'+s]) for s in ['easy','medium','tough']))
        assert abs(float(row['blocks_above_average'])-numerator)<=.500001
        assert abs(float(row['catcher_blocking_runs'])-runs)<=.500001
    assert n>0 and n.is_integer() and 0<=actual<=n and 0<=expected<=n
    close(runs,native[kind+'_runs'])
    return dict(season=2026,player_id=native['player_id'],player_name=native['player_name'],
        component=kind,opportunities=int(n),numerator=numerator,runs=runs,rate_per_1000=1000*runs/n,
        observed_events=actual,expected_events=expected,native_outs=native['native_outs'],
        exposure_valid=native['exposure_valid'],measurement_valid=native['exposure_valid'],
        source_method='Unchanged V5 native attempt/chance arithmetic; 2026 inputs; blocking display rounding excluded')


def main():
    review_path=PUBLIC/'nonbatting-source-reconciliation.json'
    assert not review_path.exists(),'Preserve completed source review'
    capture=json.loads((PUBLIC/'nonbatting-source-capture.json').read_text(encoding='utf8'))
    for c in capture['captures']:
        assert sha256_file(Path(c['parsed_path']))==c['parsed_sha256']
        assert sha256_file(Path(c['source_path']))==c['source_sha256']
    official={}
    for r in read_rows('official-fielding'):
        key=int(r['player']['id']),int(r['position']['code'])
        assert key not in official,'Duplicate official position row'
        official[key]=outs_from_baseball_innings(r['stat']['innings'])
    rows=read_rows('fielding-position');aggregate={r['id']:r for r in read_rows('fielding-aggregate')}
    sums=defaultdict(lambda:defaultdict(float));ledger=[];seen=set()
    for r in rows:
        pid,pos=r['id'],r['pos_id'];assert (pid,pos) not in seen;seen.add((pid,pos))
        close(sum(r[c] or 0. for c in COMPONENTS),r['total_runs'])
        for c in [*COMPONENTS,'total_runs','outs_total']:sums[pid][c]+=r[c] or 0.
        n,independent=int(r['outs_total']),official.get((pid,pos))
        valid=independent is not None and n>0 and independent>0 and abs(n-independent)<=5 and abs(n-independent)<=.01*max(n,independent)
        ledger.append(dict(season=2026,player_id=pid,player_name=r['name'],position=pos,native_outs=n,
            official_outs=independent,exposure_valid=valid,range_valid=valid and r['range_runs'] is not None,
            **{c:r[c] for c in COMPONENTS},total_runs=r['total_runs']))
    assert set(sums)==set(aggregate)
    aggregate_outs_review=[]
    for pid,parts in sums.items():
        for c,value in parts.items():
            if c!='outs_total':close(value,aggregate[pid][c] or 0.)
        a=aggregate[pid]
        position_outs=sum(a.get(f'outs_{pos}') or 0 for pos in range(2,10))
        omitted_position_outs=position_outs-parts['outs_total']
        pitcher_outs=a['outs_total']-position_outs
        assert omitted_position_outs>=0 and pitcher_outs>=0
        if omitted_position_outs or pitcher_outs:
            aggregate_outs_review.append(dict(player_id=pid,player_name=a['name'],
                aggregate_outs=a['outs_total'],returned_position_outs=parts['outs_total'],
                aggregate_nonpitcher_outs=position_outs,
                omitted_position_outs=omitted_position_outs,pitcher_outs=pitcher_outs,
                official_pitcher_outs=official.get((pid,1),0),
                pitcher_outs_match=pitcher_outs==official.get((pid,1),0)))
    gaps=[dict(player_id=pid,position=pos,official_outs=n) for (pid,pos),n in official.items()
          if 2<=pos<=9 and n>0 and (pid,pos) not in seen]
    by_player=defaultdict(list)
    for r in ledger:by_player[r['player_id']].append(r)
    catchers={r['player_id']:r for r in ledger if r['position']==2}
    opportunity=[]
    for kind in ['throwing','blocking']:
        for r in read_rows(kind):opportunity.append(catcher_record(kind,r,catchers[int(r['player_id'])]))
    framing=[]
    for r in read_rows('framing'):
        n=catchers[r['id']];assert r['pitches']>0
        close(r['rv_tot'],n['framing_runs'])
        framing.append(dict(season=2026,player_id=r['id'],player_name=r['name'],pitches=r['pitches'],
            shadow_pitches=r['pitches_shadow'],framing_runs=r['rv_tot'],native_catcher_outs=n['native_outs'],
            exposure_valid=n['exposure_valid'],framing_measurement_valid=True,rate_per_1000=1000*r['rv_tot']/r['pitches']))
    arms=[arm_record(r,by_player[int(r['entity_id'])],2026) for r in read_rows('arm')]
    receiving=[normalize_receiving(r,by_player[int(r['player_id'])],2026) for r in read_rows('receiving')]
    pitching=read_rows('official-team-pitching');pitch_outs=sum(r['stat']['outs'] for r in pitching)
    assert all(outs_from_baseball_innings(r['stat']['inningsPitched'])==r['stat']['outs'] for r in pitching)
    batting=pl.read_parquet(ROOT/'reports/generated/hitter-2027-origin-counts/team-aggregates.parquet').filter(pl.col('sport_id')==1)
    assert batting['runs'].sum()==sum(r['stat']['runs'] for r in pitching)
    games=sum(r['stat']['gamesPlayed'] for r in pitching)/2
    rpw=calculate_v1_runs_per_win(batting['runs'].sum(),pitch_outs/3,reference_season=2026)
    replacement=build_replacement_reference(games,batting['plate_appearances'].sum(),rpw.runs_per_win,reference_season=2026)
    frames=dict(component_ledger=pl.DataFrame(ledger,infer_schema_length=None),
                catcher_opportunities=pl.DataFrame(opportunity,infer_schema_length=None),
                framing_annual=pl.DataFrame(framing,infer_schema_length=None),
                arm_receiving_annual=pl.DataFrame(arms+receiving,infer_schema_length=None))
    outputs={}
    for name,f in frames.items():
        path=OUT/f'{name.replace("_","-")}.parquet';assert not path.exists();f.write_parquet(path);outputs[str(path)]=sha256_file(path)
    abs_rows=[r for r in ledger if r['abs_runs'] is not None]
    result=dict(status='component_reconciliation_complete_player_interpretation_pending',
        native_position_rows=len(ledger),native_components_add_up=True,split_aggregate_runs_match=True,
        aggregate_outs_review=aggregate_outs_review,
        aggregate_outs_policy='Run additivity does not certify exposure. Aggregate outs include pitching and tiny positions omitted from native splits. Only independently reconciled position rows qualify for rates; missing quality stays unknown.',
        official_positive_position_gaps=gaps,exposure_mismatches=[r for r in ledger if not r['exposure_valid']],
        catcher_opportunity_rows=len(opportunity),framing_rows=len(framing),
        arm_rows=len(arms),receiving_rows=len(receiving),
        arm_native_gaps=[r for r in arms if not r['native_match']],receiving_native_gaps=[r for r in receiving if not r['native_match']],
        abs_challenge_rows=len(abs_rows),abs_runs_total=sum(r['abs_runs'] for r in abs_rows),
        max_abs_credit_magnitude=max(abs(r['abs_runs']) for r in abs_rows),
        abs_source_definition='https://baseballsavant.mlb.com/abs-metrics-documentation',
        abs_boundary='Initial-call framing and separate challenge value. One MLB season is not longitudinal talent validation.',
        runs_per_win=asdict(rpw),replacement_reference=asdict(replacement),
        output_hashes=outputs,runner_sha256=sha256_file(Path(__file__)),
        source_approved_for_estimation=False,player_walkthrough_status='pending',models_fitted=0)
    write_once(review_path,result)
    print(f'Native rows {len(ledger)}; {len(gaps)} missing positive-out position rows; {len(abs_rows)} separate ABS records',flush=True)
    print(f'2026 reference runs/win {rpw.runs_per_win:.6f}; replacement runs/600 {replacement.replacement_runs_per_600_pa:.6f}',flush=True)


if __name__=='__main__':main()
