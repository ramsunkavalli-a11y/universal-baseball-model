"""Verify endpoint calculations and complete the reviewed development disposition."""
from pathlib import Path
import subprocess
import sys
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import prepare_hitter_statcast_next_year as prep


def independent_loss(g,arm,kind):
    if kind=='rate': g=g.filter(pl.col('next_pa')>0)
    values=[]
    for (year,),part in g.group_by('origin_year'):
        if kind=='rate':
            actual=part['actual_future_relative_rate'].to_numpy();pred=part[arm+'_rate'].to_numpy();weight=part['next_pa'].to_numpy()
        else:actual=part['next_value'].to_numpy();pred=part[arm+'_value'].to_numpy();weight=np.ones(len(part))
        values.append([np.average((pred-actual)**2,weights=weight),np.average(np.abs(pred-actual),weights=weight),np.average(pred-actual,weights=weight)])
    return np.mean(values,axis=0)


def main():
    out=prep.OUT; assert not (out/'final-review.json').exists(),'Preserve final review'
    pre=prep.read(out/'preflight.json');scores=prep.read(out/'scores.json');cases=prep.read(out/'cases.json');fit=prep.read(out/'fit-report.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    for cell in fit['cells']:
        assert sha256_file(Path(cell['predictions_path']))==cell['predictions_sha256']
        for h in cell['heads']:assert sha256_file(Path(h['path']))==h['sha256']
    current=pl.read_parquet(pre['current_anchor']).sort('row_id');q=pl.read_parquet(out/'scored-predictions.parquet').sort('row_id')
    assert q.select(current.columns).equals(current) and len(q)==30506 and scores['replayed_heads']==140
    arms=['preseason',*pre['arms']]
    for arm in pre['arms']:
        inactive=q.filter(~pl.col('sc_tracked'))
        assert inactive[arm+'_rate'].equals(inactive['preseason_rate'])
        assert np.allclose(inactive[arm+'_value'],inactive['preseason_value'],atol=1e-12,rtol=0)
        expected=q['preseason_pa'].to_numpy()*(q[arm+'_rate'].to_numpy()/600+q['origin_replacement_rate'].to_numpy())
        assert np.allclose(expected,q[arm+'_value'],atol=1e-12,rtol=0)
    byscope={s['scope']:s for s in scores['scopes']}
    for scope,g in [('all',q),('tracked',q.filter(pl.col('sc_tracked'))),('untracked',q.filter(~pl.col('sc_tracked')))]:
        for arm in arms:
            mse,mae,bias=independent_loss(g,arm,'value');r=byscope[scope]['contribution'][arm]
            assert np.allclose([mse,mae,bias],[r['mse'],r['mae'],r['bias']],atol=1e-12,rtol=0)
            mse,mae,bias=independent_loss(g,arm,'rate');r=byscope[scope]['participant_rate'][arm]
            assert np.allclose([mse,mae,bias],[r['mse'],r['mae'],r['bias']],atol=1e-12,rtol=0)
    decisions={}
    for candidate in ['ridge_measurements','hist_measurements']:
        control=candidate.replace('measurements','coverage');rate=byscope['tracked']['participant_rate']
        ci=next(x for x in scores['intervals'] if x['candidate']==candidate and x['control']=='preseason' and x['kind']=='rate')
        year_failures=[s['scope'] for s in scores['scopes'] if s['scope'].startswith('tracked_origin_')
            and s['participant_rate'][candidate]['mse']>1.05*s['participant_rate']['preseason']['mse']]
        gates=dict(primary_beats_current=rate[candidate]['mse']<rate['preseason']['mse'],primary_beats_coverage=rate[candidate]['mse']<rate[control]['mse'],
            primary_nominal_interval_below_zero=ci['nominal_95_percent'][1]<0,
            mae_within_tolerance=rate[candidate]['mae']<=1.01*rate['preseason']['mae'],
            contribution_within_tolerance=byscope['all']['contribution'][candidate]['mse']<=1.005*byscope['all']['contribution']['preseason']['mse'],
            origin_tolerance_pass=not year_failures)
        decisions[candidate]=dict(gates=gates,numeric_gates_pass=all(gates.values()),origin_failures=year_failures,
            disposition='retain_qualified_research_candidate' if all(gates.values()) else 'do_not_replace_current_with_this_fixed_arm')
    assert len(cases['cases'])==16
    reasons=[r for c in cases['cases'] for r in c['selection']]
    for arm in ['ridge_measurements','hist_measurements']:
        assert all(arm+' '+reason in reasons for reason in ['largest gain','largest harm','false high','false low','ordinary active'])
    for c in cases['cases']:
        o=c['origin']; assert all(s['season']<=o['origin_year'] for s in c['source_history']+c['launch_history'])
        for arm,tr in c['saved_traces'].items():
            raw=tr['raw_rate'] if arm.startswith('ridge') else tr['raw_prediction']
            assert np.isclose(raw,o[arm+'_raw_rate'],atol=1e-10)
        # Correct presentation only: preserve the originally stored zero-placeholder artifacts.
        if o['next_pa']==0:o['actual_future_relative_rate']=None
        for peer in c['peers']:
            if peer['next_pa']==0:peer['actual_future_relative_rate']=None
    cases['player_walkthrough_status']='complete'
    cases['inactive_rate_display']='null; original zero placeholder never fitted or scored as observed talent'
    prep.write('reviewed-cases.json',cases)
    doc=prep.ROOT/'docs/hitter-statcast-next-year-result.md'
    freeze=subprocess.run([sys.executable,'-X','utf8',str(prep.ROOT/'scripts/verify_hitter_full_2026_freeze.py')],cwd=prep.ROOT,check=True,capture_output=True,text=True)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider','tests/test_hitter_statcast_next_year.py',
        'tests/test_hitter_statcast_measurement.py','tests/test_hitter_statcast_history.py','tests/test_mlb_contact_history.py','-q'],
        cwd=prep.ROOT,check=True,capture_output=True,text=True)
    prep.write('final-review.json',dict(execution_integrity=True,independent_primary_and_contribution_scores_verified=True,
        population_unchanged=True,playing_time_unchanged=True,untracked_rate_exact_fallback=True,replayed_heads=140,
        player_walkthrough_status='complete',walkthrough_path=str(doc),walkthrough_sha256=sha256_file(doc),
        decisions=decisions,reasonability='qualified_with_calibration_and_prospect_limits',full_profile_validation=False,
        original_provider_vintage_known=False,independent_confirmation=False,deployment_approved=False,
        protected_freeze=prep.read(prep.source.OUT/'final-source-review.json')['protected_freeze'],latest_protected_freeze=__import__('json').loads(freeze.stdout),
        focused_tests=tests.stdout,reviewer_sha256=sha256_file(Path(__file__)),
        artifact_hashes={str(p):sha256_file(p) for p in [out/'preflight.json',out/'fit-report.json',out/'scores.json',out/'cases.json',out/'reviewed-cases.json',out/'scored-predictions.parquet']}))
    print('Reviewed:',decisions,'No deployment or protected forecast change.')


if __name__=='__main__':main()
