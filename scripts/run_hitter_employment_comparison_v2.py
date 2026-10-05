"""Complete timing dependencies; explicitly reuse the unchanged fitting recipe."""
import argparse
from pathlib import Path
import subprocess
import sys
import numpy as np
import polars as pl
import run_hitter_employment_comparison as base
from universal_baseball.employment_timing import timing,complete_frame
from universal_baseball.employment_comparison import FLAGS,support
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

ROOT,GEN,OLD,FIX=base.ROOT,base.GEN,base.OLD,base.FIX
FIRST=base.OUT
OUT=GEN/'hitter-employment-comparison-v2'
read,verify=base.read,base.verify


def prepare():
    if OUT.exists():raise ValueError('Inspect existing preparation; no restart')
    final=read(FIRST/'final-review.json')
    assert final['player_walkthrough_status']=='complete' and not final['complete_employment_correction_tested']
    verify(final['hashes']);prior=read(FIRST/'preflight.json');verify(prior['hashes'])
    receipt=read(FIX/'final-review.json');verify(receipt['hashes'])
    check=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',
        'tests/test_employment_comparison.py','tests/test_employment_timing.py'],cwd=ROOT,capture_output=True,text=True)
    if check.returncode:raise ValueError(check.stdout+check.stderr)
    ledger=read(GEN/'hitter-status-evidence-v2/status-ledger.json')['rows']
    deltas={r['candidate_key']:r for r in read(FIX/'employment-deltas.json')['rows']}
    records=[]
    for r in ledger:
        assert r['target_year']<=2025 and r['target_year']==r['origin_year']+1
        old=r['employment'];new=deltas[r['candidate_key']]['employment'] if r['candidate_key'] in deltas else old
        a=timing(r['information_date'],old['latest_date']);b=timing(r['information_date'],new['latest_date'])
        records.append(dict(candidate_key=r['candidate_key'],origin_year=r['origin_year'],player_id=r['player_id'],
            information_date=r['information_date'],old_latest_date=old['latest_date'],new_latest_date=new['latest_date'],
            **{'old_'+n:v for n,v in a.items()},**{'new_'+n:v for n,v in b.items()}))
    dates=pl.DataFrame(records);assert dates.height==83300 and dates['candidate_key'].n_unique()==83300
    del ledger,deltas,records
    source=pl.read_parquet(FIX/'employment-indicators.parquet')
    paths=[Path(__file__),ROOT/'docs/hitter-employment-comparison-timing-amendment.md',
        ROOT/'src/universal_baseball/employment_timing.py',ROOT/'tests/test_employment_timing.py',
        ROOT/'scripts/run_hitter_employment_comparison.py',ROOT/'scripts/review_hitter_employment_comparison.py',
        ROOT/'scripts/review_hitter_employment_comparison_v2.py',FIRST/'final-review.json',FIRST/'preflight.json',
        FIRST/'player-walks.json',FIRST/'predictions.parquet',FIX/'final-review.json',
        FIX/'employment-deltas.json',FIX/'employment-indicators.parquet',
        GEN/'hitter-status-evidence-v2/status-ledger.json',OLD/'predictions.parquet']
    paths+=[OLD/f'features-{k}.parquet' for k in range(5)]
    OUT.mkdir();base.OUT=OUT
    base.save('source-seal.json',dict(before_fitting=True,hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths},
        old_result_preserved=True,settings_unchanged=True))
    dates.write_parquet(OUT/'employment-timing.parquet')
    joincols=['origin_year','player_id','information_date',*['old_'+n for n in ['employment_evidence_unknown','employment_evidence_age_years']],
        *['new_'+n for n in ['employment_evidence_unknown','employment_evidence_age_years']]]
    columns=FLAGS+['signed_first_team_work','employment_evidence_unknown','employment_evidence_age_years']
    newframes={}; changes=None; source_date_changes=0
    for k in range(5):
        f=pl.read_parquet(OLD/f'features-{k}.parquet').sort('row_id')
        n=complete_frame(f,source,dates.select(joincols));n.write_parquet(OUT/f'features-{k}.parquet')
        newframes[k]=n;paths.append(OUT/f'features-{k}.parquet')
        if k==0:
            changed=np.any(f.select(columns).to_numpy()!=n.select(columns).to_numpy(),axis=1)
            changes=f.select('row_id').with_columns(pl.Series('employment_input_changed',changed))
            joined=f.select('origin_year','player_id').join(dates,on=['origin_year','player_id'],validate='1:1')
            source_date_changes=int((joined['old_latest_date'].fill_null('unknown')!=joined['new_latest_date'].fill_null('unknown')).sum())
            assert source_date_changes==10267
        print(__import__('json').dumps(dict(prepared_fold=k,all_employment_dependencies_consistent=True)),flush=True)
    # Old-arm subsets already verified and sealed. Recheck every new full/active subset.
    checks=[c for c in prior['checks'] if c['arm']=='old_job'];assert len(checks)==70
    oldsupports=pl.read_parquet(FIRST/'profile-support.parquet').filter(pl.col('arm')=='old_job')
    parts=[oldsupports];ranges=[r for r in read(FIRST/'feature-ranges.json')['rows'] if r['arm']=='old_job']
    q=pl.read_parquet(OLD/'predictions.parquet')
    for c in prior['cells']:
        y,k=c['year'],c['fold'];f=newframes[k]
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        assert tr['ctx_information_date'].max()<te['ctx_information_date'].min()
        assert te['row_id'].equals(q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')['row_id'])
        for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
            s,note=preflight(sub,te,cutoff=y,fold=k,features=prior['job_features'],expected_keys=te.select('row_id','horizon').iter_rows())
            d=support(sub,te).join(s.select('row_id','extrapolation','sparse_profile'),on='row_id',validate='1:1').with_columns(
                pl.lit('corrected_job').alias('arm'),pl.lit(head).alias('head'),pl.lit(y).alias('origin'),pl.lit(k).alias('fold'))
            parts.append(d);checks.append(dict(arm='corrected_job',head=head,origin=y,fold=k,**note,
                exact_profile_zero=int((d['profile_people']==0).sum()),exact_profile_under20=int((d['profile_people']<20).sum())))
            low=sub.select(prior['job_features']).to_numpy().min(axis=0);high=sub.select(prior['job_features']).to_numpy().max(axis=0)
            outside=((te.select(prior['job_features']).to_numpy()<low)|(te.select(prior['job_features']).to_numpy()>high)).sum(axis=0)
            ranges.extend(dict(arm='corrected_job',head=head,origin=y,fold=k,feature=name,minimum=float(a),maximum=float(b),test_outside=int(v))
                for name,a,b,v in zip(prior['job_features'],low,high,outside,strict=True))
    assert len(checks)==140
    pl.concat(parts).write_parquet(OUT/'profile-support.parquet');changes.write_parquet(OUT/'source-changes.parquet')
    base.save('feature-ranges.json',dict(rows=ranges))
    base.save('preflight.json',dict(before_fitting=True,new_fits=0,checks=checks,cells=prior['cells'],
        job_features=prior['job_features'],settings=prior['settings'],baseline_heads_replayed=70,
        baseline_replay_provenance=str((FIRST/'preflight.json').relative_to(ROOT)),
        source_rows=63314,source_date_changed_rows=source_date_changes,
        changed_job_input_rows=int(changes['employment_input_changed'].sum()),original_rows=30506,addition_rows=13,
        allowed_changes=columns,target_year_maximum=2025,player_walkthrough_status='pending',deployment_approved=False,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths+[OUT/'employment-timing.parquet',OUT/'profile-support.parquet',
            OUT/'source-changes.parquet',OUT/'feature-ranges.json',OUT/'source-seal.json']}))
    verify(read(OUT/'source-seal.json')['hashes'])
    print(__import__('json').dumps(dict(preflight='complete',source_date_changed_rows=source_date_changes,
        changed_job_input_rows=int(changes['employment_input_changed'].sum()),new_fits=0)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','fit']);phase=parser.parse_args().phase
    base.OUT=OUT
    if phase=='prepare':prepare()
    else:base.fit()
