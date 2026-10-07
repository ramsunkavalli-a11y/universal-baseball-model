"""Close player review with independently replayed scores, not deployment."""

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_defense_transition_v10 import ROOT,OUT,PUBLIC,read,check
from run_hitter_finite_return_baseline import save,protections


def main():
    check();assert not (OUT/'final-review.json').exists()
    report=read(OUT/'fit-report.json');verified=read(OUT/'independent-verification.json')
    walk=read(OUT/'player-walkthrough.json');returns=read(OUT/'return-history-review.json')
    assert verified['integrity_pass'] and verified['forecasts_replayed']==12432
    for r in (report,verified,walk,returns):
        for p,h in r['hashes'].items():assert sha256_file(__import__('pathlib').Path(p))==h,p
    assert len(walk['cases'])==20 and sum(len(c['records'])-1 for c in walk['cases'])==60
    assert len(returns['records'])==4
    q=pl.read_parquet(OUT/'predictions.parquet');people=q['player_id'].unique().sort().to_list();idx={p:i for i,p in enumerate(people)}
    loss=np.zeros((len(people),3,3));present=np.zeros((len(people),3))
    for r in q.to_dicts():
        i,j=idx[r['player_id']],r['origin_year']-2022;present[i,j]=1
        for a,arm in enumerate(('transition','ratio','repair')):
            loss[i,j,a]=np.mean([(r[f'{arm}_{p}']-r[f'actual_{p}'])**2 for p in range(2,10)])
    rng=np.random.default_rng(708008);differences=[]
    for _ in range(40):
        counts=rng.multinomial(len(people),np.full(len(people),1/len(people)),size=50)
        errors=np.sqrt(np.einsum('bi,ija->bja',counts,loss)/(counts@present)[:,:,None])
        differences.extend(np.stack([(errors[:,:,0]-errors[:,:,a]).mean(axis=1) for a in (1,2)],axis=1))
    intervals=np.quantile(differences,[.025,.975],axis=0)
    for a,s in enumerate(report['intervals']):assert np.allclose(intervals[:,a],s['interval_95'],atol=1e-8,rtol=0)
    means={a:float(np.mean([s['cell_rmse'] for s in report['overall'] if s['arm']==a])) for a in ('ratio','repair','transition')}
    checks=[]
    for g in report['groups']:
        if g['arm']!='transition' or g['origin'] not in (2022,2023) or g['rows']<100 or g['field'] not in ('stage','age_band'):continue
        ref=next(s for s in report['groups'] if (s['origin'],s['field'],s['value'],s['arm'])==(g['origin'],g['field'],g['value'],'ratio'))
        checks.append(dict(origin=g['origin'],field=g['field'],value=g['value'],rows=g['rows'],transition_rmse=g['cell_rmse'],
            reference_rmse=ref['cell_rmse'],tolerance_pass=g['cell_rmse']<=1.1*ref['cell_rmse']))
    placement={a:float(np.mean([s['score']['mean_cell_squared_share_error'] for s in report['placement']
        if s['arm']==a and s['subset']=='zero_current_MLB_PA'])) for a in ('ratio','repair','transition')}
    totals=[s for s in report['overall'] if s['arm']=='transition' and s['origin'] in (2022,2023)]
    result=dict(date='2026-10-07',integrity_pass=True,player_walkthrough_status='complete',focal_walks=20,peer_walks=60,
        additional_return_focal=1,additional_return_peers=3,independent_intervals_replayed=True,intervals=report['intervals'],
        equal_origin_rmse=means,relative_error_improvement=1-means['transition']/means['ratio'],
        primary_tolerance_pass=bool(means['transition']<=1.02*means['ratio']),groups_pass=all(c['tolerance_pass'] for c in checks),group_checks=checks,
        development_totals_pass=all(abs(s['predicted_total_outs']/s['actual_total_outs']-1)<=.2 for s in totals),
        zero_current_MLB_PA_placement=placement,placement_tolerance_pass=placement['transition']<=placement['repair'],
        rare_young_participant_counts=[4,3,2],later_young_stress_failure=True,
        full_population_reasonability_pass=False,conditional_position_transport_validated=False,
        disposition='retain_qualified_research_bridge_not_universal_allocator_proceed_matched_skill_and_value_integration',
        gains=['Partly captures CF-to-corner and SS-to-2B arrival uncertainty.',
               'Maintains unchanged scalar potential outs, DH and upstream PA with no unqualified C assignments.',
               'Established missed-year roles prefer real older MLB history to minor rehab position.'],
        limitations=['Dominant-role averages erase differences between SS keepers and movers and specific personal secondary positions.',
                     'Volpe/Winn/Neto and Basallo/Ballesteros retain substantive misses; some loss improvements are dilution of excessive PA.',
                     'New or returning defenders remain below actual exposure totals; known dated assignments and finite-return PA are absent.',
                     'Sparse detailed support and selected future fielders do not establish eventual lower-minor defensive quality.'],
        next='No further position algorithm or constant sweep; contract a matched native-quality-times-opportunity and expanded-value comparison, retaining the reviewed skill baselines and all opportunity anchors.',
        forecast_or_explorer_changed=False,protected_outcomes_used=False,deployment_approved=False,value_integration_complete=False,
        historical_receipt_corrections=['Prefit scoring-array correction and post-fit potential-total check recovery are preserved separately; 15 fitted means replayed unchanged.',
            'Initial source-recovery-review contains the focal only; return-history-review completes all three announced comparisons.'],
        hashes={str(p):sha256_file(p) for p in [__import__('pathlib').Path(__file__),OUT/'preflight.json',OUT/'fit-report.json',OUT/'player-walkthrough.json',
            OUT/'independent-verification.json',OUT/'execution-amendment.json',OUT/'execution-recovery.json',OUT/'return-history-review.json',
            ROOT/'docs/defense-transition-v10-player-review.md',ROOT/'docs/defense-transition-v10-result.md']})
    assert result['groups_pass'] and result['primary_tolerance_pass'] and result['placement_tolerance_pass'] and result['development_totals_pass']
    save(OUT/'final-review.json',result);save(PUBLIC/'final-review.json',result)
    protections();print({k:result[k] for k in ['player_walkthrough_status','relative_error_improvement','groups_pass','disposition']})


if __name__=='__main__':main()
