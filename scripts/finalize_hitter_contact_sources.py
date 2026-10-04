"""Seal additive source/player review, without changing original receipts."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_contact_history import CELLS, KEY, annual_cells
from universal_baseball.hitter_statcast_history import annual_launch_features

ROOT=Path(__file__).resolve().parents[1]
OWN=ROOT/'reports/generated/hitter-own-mlb-contact-source'
LAUNCH=ROOT/'reports/generated/hitter-statcast-history'


def read(path): return json.loads(path.read_text(encoding='utf8'))


def check(group):
    for path, digest in group.items():
        assert sha256_file(Path(path))==digest, path


def write(path, value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def main():
    assert not (OWN/'final-report.json').exists() and not (LAUNCH/'final-report.json').exists()
    raw=read(OWN/'source-report.json'); review=read(OWN/'review-receipt.json'); cases=read(OWN/'cases.json')
    launch=read(LAUNCH/'source-report.json'); launch_cases=read(LAUNCH/'cases.json')
    for hashes in [raw['input_hashes'],raw['output_hashes'],review['source_hashes'],
                   cases['saved_head_hashes'],launch['source_hashes'],launch['output_hashes']]:
        check(hashes)
    assert cases['saved_heads_replayed']==30 and cases['current_forecasts_unchanged']
    current=ROOT/'reports/generated/hitter-preseason-readiness-v68'
    q=pl.read_parquet(current/'scored-predictions.parquet')
    f=pl.read_parquet(current/'features.parquet')
    cols=['plate_appearances','strike_outs','unintentional_walks','hit_by_pitch','singles','doubles','triples','home_runs']
    official=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('bucket')=='MLB').with_columns(
        (pl.col('babip_hits')-pl.col('doubles')-pl.col('triples')).alias('singles'))
    absent_geometry_homers=0; launch_absent_geometry_homers=0
    annual=[]
    for year in [2023,2024]:
        events=pl.read_parquet(OWN/f'events-{year}.parquet'); cells=pl.read_parquet(OWN/f'cells-{year}.parquet')
        assert events.unique(KEY).height==len(events) and set(events['season'])=={year}
        assert events['venue_id'].null_count()==0
        assert events['game_date'].cast(pl.String).equals(events['official_date'])
        assert annual_cells(events).equals(cells)
        counts=pl.read_parquet(OWN/f'outcomes-{year}.parquet').select('season','player_id',*cols).sort('player_id')
        expected=official.filter((pl.col('season')==year)&(pl.col('plate_appearances')>0)).select(counts.columns).sort('player_id')
        assert counts.equals(expected)
        absent_geometry_homers+=events.filter((pl.col('canonical_outcome')=='HR')&~pl.col('cell_eligible')).height
        measured=pl.read_parquet(LAUNCH/f'launch-events-{year}.parquet')
        assert measured.unique(['game_pk','player_id','at_bat_number','pitch_number']).height==len(measured)
        assert measured['venue_id'].null_count()==0 and set(measured['season'])=={year}
        assert measured['invalid_ev'].sum()==0 and measured['invalid_la'].sum()==0
        assert annual_launch_features(measured).equals(pl.read_parquet(LAUNCH/f'annual-{year}.parquet'))
        launch_absent_geometry_homers+=measured.filter((pl.col('events')=='home_run')&pl.col('core_bin').is_null()&pl.col('complete_pair')).height
        annual.append(measured)
    assert absent_geometry_homers==69 and launch_absent_geometry_homers==69
    launch_all=pl.concat(annual)
    own_doc=ROOT/'docs/hitter-own-mlb-contact-source-result.md'
    launch_doc=ROOT/'docs/hitter-statcast-history-result.md'
    text=own_doc.read_text(encoding='utf8'); launch_text=launch_doc.read_text(encoding='utf8')
    assert len(cases['cases'])==len(launch_cases['cases'])==10
    for a,b in zip(cases['cases'],launch_cases['cases'],strict=True):
        r=a['origin']; assert r==b['origin']
        name=r['player_name']; assert name in text and name in launch_text
        saved=q.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
        for field in ['preseason_raw_p','preseason_p','preseason_raw_conditional_pa',
                      'preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value','next_pa','next_value']:
            assert saved[field]==r[field]
        assert np.isclose(r['preseason_pa'],r['preseason_p']*r['preseason_conditional_pa'],atol=1e-10,rtol=0)
        assert np.isclose(r['preseason_value'],r['preseason_pa']*(r['preseason_rate']/600+r['origin_replacement_rate']),atol=1e-10,rtol=0)
        assert b['tracking_candidate_forecast'] is None and not b['forecasts_changed']
        source=f.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
        assert source['next_batting_rate']==a['actual_target_relative_rate'] if r['next_pa']>0 else a['actual_target_relative_rate'] is None
        for k,v in a['actual_rate_inputs'].items(): assert source[k]==v
        trace=a['unchanged_saved_rate_trace']; assert np.isclose(trace['rate'],r['preseason_rate'],atol=1e-10,rtol=0)
        for peer in a['peers']:
            assert peer['origin_year']==r['origin_year'] and peer['stage']==r['stage'] and peer['prior_debut']==r['prior_debut']
        for row in b['annual_launch_history']:
            assert row['season']<=r['origin_year']
            m=launch_all.filter((pl.col('season')==row['season'])&(pl.col('player_id')==r['player_id']))
            ev=m.filter(pl.col('valid_ev'))['launch_speed'].to_numpy()
            assert len(ev)==row['measured_ev_contacts']
            if len(ev):
                assert np.isclose(np.mean(ev),row['mean_ev'])
                assert np.isclose(np.quantile(ev,.95,method='linear'),row['ev95'])
                assert np.isclose(np.mean(ev>=95),row['hard_hit_fraction'])
    support=pl.read_parquet(LAUNCH/'forecast-source-coverage.parquet')
    lookup={(y,pid):n for y,pid,n in pl.read_parquet(LAUNCH/'annual-launch-features.parquet').select('season','player_id','measured_pair_contacts').iter_rows()}
    expected=[sum(lookup.get((r['origin_year']-lag,r['player_id']),0) for lag in range(3)) for r in f.iter_rows(named=True)]
    assert support['own_mlb_launch_pairs'].to_list()==expected
    preflight=read(current/'preflight.json')
    for row,c in zip(launch['actual_fold_support'],preflight['cells'],strict=True):
        train=support.filter(pl.col('row_id').is_in(c['training_row_ids']))
        assert train['target_year'].max()<=c['year'] and not train['outer_fold'].eq(c['fold']).any()
        count=train.filter((pl.col('next_pa')>0)&(pl.col('own_mlb_launch_pairs')>0))['player_id'].n_unique()
        assert count==row['active_training_people_with_launch']
        if c['year']<2024: assert count==0
    tested=subprocess.run([sys.executable,'-X','utf8','-m','pytest','tests/test_mlb_contact_history.py',
        'tests/test_hitter_statcast_history.py','-q','-p','no:cacheprovider'],cwd=ROOT,text=True,capture_output=True)
    assert tested.returncode==0,tested.stdout+tested.stderr
    freeze=subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,text=True,capture_output=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    verified=json.loads(freeze.stdout)
    assert verified['verified_files']==31 and not verified['protected_2026_opened']
    common=dict(source_only=True,new_model_fits=0,player_walkthrough_status='complete',reviewed_forecast_cases=10,
        forecasts_changed=False,protected_outcomes_used=False,deployment_approved=False,full_model_goal_complete=False,
        focused_tests=tested.stdout.strip(),frozen_forecast_verification=verified,
        finalizer_sha256=sha256_file(Path(__file__)),predictive_improvement_claimed=False)
    for directory,doc in [(OWN,own_doc),(LAUNCH,launch_doc)]:
        result=common|dict(accepted_as_raw_research_source=True,source_seasons=[2023,2024],
            raw_not_adjusted_talent=True,broad_forecast_support_complete=False,
            source_report_sha256=sha256_file(directory/'source-report.json'),cases_sha256=sha256_file(directory/'cases.json'),
            readable_walkthrough=str(doc),readable_walkthrough_sha256=sha256_file(doc),
            verified_missing_geometry_homers=69)
        write(directory/'final-report.json',result)
        destination=ROOT/'reports/model-evidence'/directory.name
        destination.mkdir(parents=True,exist_ok=True)
        names=['source-report.json','cases.json','final-report.json']
        names+=['review-receipt.json','annual-cells.parquet'] if directory==OWN else ['annual-launch-features.parquet']
        for name in names:
            target=destination/name; assert not target.exists(),target
            shutil.copyfile(directory/name,target)
            assert sha256_file(target)==sha256_file(directory/name)
    print(json.dumps(common,indent=2))


if __name__=='__main__': main()
