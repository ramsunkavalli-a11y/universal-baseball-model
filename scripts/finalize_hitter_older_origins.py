"""Review older source cases and measure additional actual-fold support; no fits."""
from __future__ import annotations

from pathlib import Path
import json

import polars as pl

from audit_hitter_older_origins import ROOT, OLD, OUT, read, write
from review_hitter_older_origins import check_audit
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v31 import bucket
from audit_hitter_rate_support import tagged, BUCKETS


def prepare():
    check_audit()
    sealed=read(OUT/'review-preparation.json')
    for path,digest in sealed['hashes'].items(): assert sha256_file(Path(path))==digest,path
    assert not (OUT/'review-detail.json').exists(),'Preserve completed review preparation'
    f=pl.read_parquet(OUT/'population-with-ages.parquet')
    h=pl.read_parquet(OUT/'history.parquet')
    h=h.with_columns(pl.Series('bucket',[bucket(s) for s in h.iter_rows(named=True)]))
    inventory=OLD/'career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet'
    outcomes=pl.read_parquet(inventory).filter(pl.col('season')<=2013)
    oldcases=read(OUT/'cases.json')
    selected=[dict(player_id=c['origin']['player_id'],origin_year=c['origin']['origin_year'],selection=c['selection']['selection']) for c in oldcases]
    selected.extend(dict(player_id=pid,origin_year=2010,selection='Additional fast-track source diagnostic; not an outcome-independent validation case')
                    for pid in [545361,543333,519058])
    source_by={}
    count_by={}
    for row in f.iter_rows(named=True):
        q=h.filter((pl.col('player_id')==row['player_id'])&(pl.col('season')==row['origin_year']))
        exposure={b:int(q.filter(pl.col('bucket')==b)['plate_appearances'].sum()) for b in BUCKETS}
        dominant=max(BUCKETS,key=lambda b:exposure[b]) if max(exposure.values())>0 else 'absent'
        top=q.sort('sport_id').head(1)
        highest=row['snapshot_level']
        name=(q.sort('plate_appearances',descending=True)['player_name'][0] if len(q) else next((c['origin']['display_name'] for c in oldcases if c['origin']['player_id']==row['player_id']),None))
        source_by[(row['origin_year'],row['player_id'])]=dict(**row,dominant_level=dominant,highest_level=highest,
            source_name=name,origin_pa=sum(exposure.values()),exposure=exposure,outer_fold=player_fold(row['player_id']),
            prior_debut=int(row['mlb_debut_date'] is not None and row['mlb_debut_date'].year<=row['origin_year']))
        count_by[(row['origin_year'],row['player_id'])]=exposure
    # Actual active training support only: every positive label has a recorded
    # debut, so no unknown prior-history status is silently called pre-MLB here.
    support_rows=[]
    for row in f.iter_rows(named=True):
        info=source_by[(row['origin_year'],row['player_id'])]
        if row['next_pa']>0: assert row['mlb_debut_date'] is not None
        support_rows.append(dict(row_id=-(row['origin_year']*10000000+row['player_id']),player_id=row['player_id'],origin_year=row['origin_year'],
            target_year=row['origin_year']+1,outer_fold=info['outer_fold'],age=row['resolved_age'] if row['resolved_age'] is not None else 27.,
            age_unknown=int(row['resolved_age'] is None),prior_debut=info['prior_debut'],next_pa=row['next_pa'],
            **{b+'_0_pa':count_by[(row['origin_year'],row['player_id'])][b] for b in BUCKETS}))
    earlier=tagged(pl.DataFrame(support_rows))
    current_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet'
    current=tagged(pl.read_parquet(current_path))
    pre_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/preflight.json'
    pre=read(pre_path);keys=['dominant_level','audit_age_band','prior_debut'];parts=[];cells=[]
    for cell in pre['cells']:
        y,k=cell['year'],cell['fold']
        test=current.filter(pl.col('row_id').is_in(cell['test_row_ids']))
        baseline=current.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0))
        added=earlier.filter((pl.col('outer_fold')!=k)&(pl.col('target_year')<=y)&(pl.col('next_pa')>0))
        assert not set(added['player_id'])&set(test['player_id'])
        assert added.is_empty() or added['target_year'].max()<=y
        assert baseline['target_year'].max()<=y and not set(baseline['player_id'])&set(test['player_id'])
        merged=pl.concat([baseline.select('player_id',*keys),added.select('player_id',*keys)])
        g=test.select('row_id','player_id','origin_year','outer_fold',*keys)
        for name,tr in [('baseline',baseline),('earlier',added),('union',merged)]:
            counts=tr.group_by(keys).agg(pl.col('player_id').n_unique().alias(name+'_active_people'))
            g=g.join(counts,on=keys,how='left',validate='m:1').with_columns(pl.col(name+'_active_people').fill_null(0))
        parts.append(g)
        cells.append(dict(origin=y,fold=k,added_active_rows=len(added),added_active_people=added['player_id'].n_unique(),
                          no_test_player_overlap=True,last_added_target=int(added['target_year'].max())))
    support=pl.concat(parts).sort('row_id');assert len(support)==30506
    support.write_parquet(OUT/'potential-support.parquet')
    cases=[]
    all_info=list(source_by.values())
    for selection in selected:
        row=source_by[(selection['origin_year'],selection['player_id'])]
        # Stronger source controls than the original broad sport-only peers.
        # Exact dominant bucket AND highest observed level, same prior-debut
        # state, age within two years, with no outcome used in ranking.
        peers=[s for s in all_info if s['origin_year']==row['origin_year'] and s['player_id']!=row['player_id'] and
            s['dominant_level']==row['dominant_level'] and s['highest_level']==row['highest_level'] and
            s['prior_debut']==row['prior_debut'] and s['resolved_age'] is not None and row['resolved_age'] is not None and
            abs(s['resolved_age']-row['resolved_age'])<=2]
        peers=sorted(peers,key=lambda s:(abs(s['resolved_age']-row['resolved_age'])+abs(s['origin_pa']-row['origin_pa'])/300,s['player_id']))[:4]
        q=h.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).sort('season','bucket','team_id')
        paths=[]
        for s in [row,*peers]:
            path=[]
            for step in [1,2,3]:
                target=outcomes.filter((pl.col('player_id')==s['player_id'])&(pl.col('season')==s['origin_year']+step))
                pa=int(target['batting_plate_appearances'].sum())
                path.append(dict(horizon=step,season=s['origin_year']+step,mlb_pa=pa,hitting_rate_observed=pa>0))
            paths.append(dict(player_id=s['player_id'],player_name=s['source_name'],age=s['resolved_age'],dominant_level=s['dominant_level'],
                highest_level=s['highest_level'],origin_pa=s['origin_pa'],exposure=s['exposure'],annual_mlb_pa=path))
        assert paths[0]['annual_mlb_pa'][0]['mlb_pa']==row['next_pa']
        cases.append(dict(selection=selection,origin=row,dated_stats=q.to_dicts(),paths=paths,
            peer_rule='Same origin, dominant bucket, highest observed level, prior-debut state; age within two years; nearest age/current PA, ID tie break; no future outcomes',
            peer_limit='Age and exposure controls, not equal performance or pedigree. An absent debut record does not certify never-debut. No causal player substitution is claimed.'))
    scopes=[]
    for name,filter in [('all',pl.lit(True)),('never_debut',(pl.col('prior_debut')==0)),
        ('teenage_DSL',(pl.col('dominant_level')=='DSL')&(pl.col('audit_age_band')=='<=17')&(pl.col('prior_debut')==0)),
        ('teenage_AAA',(pl.col('dominant_level')=='AAA')&(pl.col('audit_age_band')=='18-20')&(pl.col('prior_debut')==0))]:
        g=support.filter(filter)
        scopes.append(dict(scope=name,rows=len(g),before_absent=g.filter(pl.col('baseline_active_people')==0).height,
            after_absent=g.filter(pl.col('union_active_people')==0).height,
            before_median=float(g['baseline_active_people'].median()) if len(g) else None,
            after_median=float(g['union_active_people'].median()) if len(g) else None))
    earlier_summary=earlier.filter((pl.col('next_pa')>0)&(pl.col('prior_debut')==0)).group_by('dominant_level','audit_age_band').agg(
        pl.len().alias('active_origin_rows'),pl.col('player_id').n_unique().alias('active_people'),pl.col('next_pa').sum()).sort('dominant_level','audit_age_band').to_dicts()
    write(OUT/'review-detail.json',dict(cases=cases,actual_fold_potential_support=scopes,added_predebut_active_groups=earlier_summary,cells=cells,
        claim='Potential additional coarse support only; no model fitted and no certification of missing input families',player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'cases.json',OUT/'report.json',OUT/'population-with-ages.parquet',OUT/'potential-support.parquet',inventory,current_path,pre_path]}))
    print(json.dumps(dict(support=scopes,groups=earlier_summary,cases=[dict(name=c['origin']['source_name'],origin=c['origin']['origin_year'],age=c['origin']['resolved_age'],dominant=c['origin']['dominant_level'],highest=c['origin']['highest_level'],pa=c['origin']['origin_pa'],paths=c['paths']) for c in cases]),indent=2,ensure_ascii=False,default=str))


def finalize():
    assert not (OUT/'final-report.json').exists(),'Preserve completed review'
    report=check_audit();detail=read(OUT/'review-detail.json')
    for path,digest in detail['hashes'].items(): assert sha256_file(Path(path))==digest,path
    notes_path=ROOT/'config/hitter_older_origin_source_review.json'
    notes=read(notes_path)
    case_ids={(c['origin']['player_id'],c['origin']['origin_year']) for c in detail['cases']}
    assert set((c['player_id'],c['origin_year']) for c in notes['cases'])==case_ids
    assert all(len(c['assessment'])>100 for c in notes['cases'])
    result_path=ROOT/'docs/hitter-older-origin-source-result.md'
    assert result_path.exists()
    write(OUT/'reviewed-cases.json',dict(source_detail=detail,assessments=notes,player_walkthrough_status='complete'))
    write(OUT/'final-report.json',dict(source_review_complete=True,player_walkthrough_status='complete',reviewed_cases=len(case_ids),
        potential_added_origin_rows=report['potential_added_origin_rows'],positive_next_year_labels=report['active_next_year_labels'],
        zero_next_year_labels=report['zero_next_year_labels'],additional_shortseason_pa=sum(s['pa'] for s in report['restored_shortseason']),
        ages=read(OUT/'age-receipt.json')['age_bases'],potential_support=detail['actual_fold_potential_support'],
        no_model_fitted=True,current_candidate_changed=False,frozen_forecast_changed=False,protected_outcomes_used=False,deployment_approved=False,full_goal_complete=False,
        disposition='Use the repaired 2008-2010 sources for a matched augmentation comparison after compatible input and whole-player preflights; do not infer predictive improvement or immediate teenage AAA support',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'report.json',OUT/'age-receipt.json',OUT/'review-preparation.json',OUT/'review-detail.json',OUT/'reviewed-cases.json',notes_path,result_path]}))
    print('Older source review completed; no forecasts changed.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','finalize']);args=parser.parse_args()
    prepare() if args.action=='prepare' else finalize()
