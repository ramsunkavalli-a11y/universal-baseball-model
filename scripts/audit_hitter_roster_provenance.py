"""Review all saved 40Man captures and dated roster-event conflicts; no fits."""
import gzip
import json
import argparse
import shutil
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

import audit_hitter_candidate_integration as base
from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
from score_hitter_compatible_value_v63 import linear_trace

ROOT=base.ROOT
OUT=ROOT/'reports/generated/hitter-roster-provenance-audit'
SOURCE=ROOT/'reports/generated/hitter-arrival-source-repair-v1'
FIXED=[(680574,2024,'Matt McLain',113),(687952,2024,'Christian Encarnacion-Strand',113),
       (666158,2023,'Gavin Lux',119),(645277,2021,'Ozzie Albies',144),
       (665161,2021,'Jeremy Peña',117),(474832,2023,'Brandon Belt',141),
       (519346,2016,'Eric Thames',158),(808975,2024,'Hyeseong Kim',119),
       (136860,2016,'Carlos Beltrán',117)]


def write(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def classify(raw,mlb_teams):
    """Explicit dated events are evidence at their event, not cutoff rights proof."""
    text=raw.get('description','').lower()
    kind=raw.get('typeDesc','').lower()
    team=raw.get('toTeam',{}).get('id')
    from_team=raw.get('fromTeam',{}).get('id')
    if team not in mlb_teams and from_team not in mlb_teams:return None
    if kind=='declared free agency' or any(t in text for t in [' elected free agency',' became a free agent']):
        return 'negative'
    if any(t in text for t in [' designated ',' outrighted ',' released ']):
        return 'negative'
    if team not in mlb_teams:return None
    if 'selected the contract' in text or 'selected contract' in text or 'contract selected' in text:
        return 'positive'
    if ' activated ' in text and 'from the 60-day injured list' in text:
        return 'positive'
    return None


def event_at_cutoff(records,year,mlb_teams):
    cutoff=f'{year}-12-31';eligible=[];date_conflicts=[]
    for raw in records:
        day=str(raw.get('date',''))[:10]
        if not day or day>cutoff:continue
        later=[str(raw[key])[:10] for key in ['effectiveDate','resolutionDate'] if raw.get(key)]
        if any(d>cutoff for d in later):
            date_conflicts.append(raw);continue
        sign=classify(raw,mlb_teams)
        if sign:eligible.append(dict(sign=sign,recorded_date=day,raw=raw))
    if not eligible:return dict(sign='unknown',latest_date=None,latest_events=[],date_conflicts=date_conflicts)
    latest=max(z['recorded_date'] for z in eligible);events=[z for z in eligible if z['recorded_date']==latest]
    signs={z['sign'] for z in events}
    return dict(sign=next(iter(signs)) if len(signs)==1 else 'conflicting',latest_date=latest,
                latest_events=events,date_conflicts=date_conflicts)


def main():
    complete=base.e.read(base.OUT/'final-report.json')
    assert complete['player_walkthrough_status']=='complete'
    base.e.verify(complete['input_hashes']);base.e.verify(complete['review_hashes'])
    pre=base.e.read(base.CURRENT/'preflight.json');base.e.verify(pre['input_hashes'])
    f=pl.read_parquet(base.CURRENT/'features.parquet');q=pl.read_parquet(base.CURRENT/'scored-predictions.parquet')
    assert len(f)==63282 and len(q)==30506
    extra=ROOT/'reports/generated/hitter-2020-cohort'
    listing=pl.concat([pl.read_parquet(SOURCE/'year-end-rosters.parquet'),pl.read_parquet(extra/'40man.parquet')])
    teams=set(listing['team_id']);paths=[];raw_rows=[];capture_lookup={};duplicates=[]
    rosterpaths=sorted((SOURCE/'captures/roster').glob('*/*.json.gz'))+sorted((extra/'captures/40Man').glob('*.json.gz'))
    for path in rosterpaths:
        if path.name=='teams.json.gz':continue
        year=2020 if path.parent.name=='40Man' else int(path.parent.name);team=int(path.name.split('.')[0])
        assert year<=2024
        obj=json.load(gzip.open(path,'rt',encoding='utf8'))
        assert obj['endpoint']==f'/teams/{team}/roster'
        assert obj['params']=={'rosterType':'40Man','season':year,'date':f'{year}-12-31'}
        people=[z['person']['id'] for z in obj['payload']['roster']]
        for pid in set(people):
            same=[z for z in obj['payload']['roster'] if z['person']['id']==pid]
            assert len({(z['person'].get('fullName'),z['person'].get('link')) for z in same})==1
            if len(same)>1:duplicates.append(dict(year=year,team_id=team,player_id=pid,raw_rows=len(same)))
        raw_rows.extend(dict(season=year,team_id=team,player_id=pid) for pid in sorted(set(people)))
        capture_lookup[year,team]=obj;paths.append(path)
    reconstructed=pl.DataFrame(raw_rows).sort('season','team_id','player_id')
    assert len(paths)==480 and len(reconstructed)==18708
    assert reconstructed.equals(listing.select('season','team_id','player_id').sort('season','team_id','player_id'))
    present={(z['season'],z['player_id']) for z in raw_rows}
    flags=np.array([int((z['origin_year'],z['player_id']) in present) for z in f.iter_rows(named=True)])
    assert np.array_equal(flags,f['on_40man'].to_numpy())
    lookup={};capture_counts=[]
    for year in range(2015,2025):
        folder='source-2015' if year==2015 else 'source'
        path=ROOT/f'reports/generated/hitter-injury-history-v2/{folder}/captures/transactions-{year}.json'
        raw=base.e.read(path)['transactions'];paths.append(path)
        capture_counts.append(dict(year=year,records=len(raw)))
        for z in raw:
            pid=z.get('person',{}).get('id')
            if pid:lookup.setdefault(pid,{})[z['id']]=z
    lookup={pid:sorted(rs.values(),key=lambda z:(z.get('date',''),z['id'])) for pid,rs in lookup.items()}
    rows=[];details={}
    for r in f.select('row_id','player_id','origin_year','on_40man').iter_rows(named=True):
        state=event_at_cutoff(lookup.get(r['player_id'],[]),r['origin_year'],teams) if r['origin_year']>=2015 else dict(sign='unknown',latest_date=None,latest_events=[],date_conflicts=[])
        conflict=(state['sign']=='positive' and r['on_40man']==0) or (state['sign']=='negative' and r['on_40man']==1)
        rows.append(dict(row_id=r['row_id'],roster_event_capture_scope=r['origin_year']>=2015,
            roster_event_sign=state['sign'],roster_event_date=state['latest_date'],
            date_conflict_count=len(state['date_conflicts']),event_listing_conflict=conflict))
        if (r['player_id'],r['origin_year']) in {(pid,y) for pid,y,_,_ in FIXED}:details[r['row_id']]=state
    states=pl.DataFrame(rows,schema_overrides={'roster_event_date':pl.String})
    joined=q.join(states,on='row_id',validate='1:1');assert len(joined)==len(q)
    source=f.join(states,on='row_id',validate='1:1');assert source.select(f.columns).equals(f)
    states.write_parquet(OUT/'states.parquet')
    conflicts=source.filter(pl.col('event_listing_conflict')).select('row_id','player_id','player_name','origin_year','stage','prior_debut','on_40man','roster_event_sign','roster_event_date')
    write('conflicts.json',conflicts.to_dicts())
    counts=pl.read_parquet(base.e.COUNTS);support=pl.read_parquet(base.CURRENT/'support.parquet')
    refined=pl.read_parquet(base.CURRENT/'profile-support.parquet')
    ratefeatures=base.e.read(base.RATE/'preflight.json')['rate_features'];cases=[]
    with threadpool_limits(limits=2):
        for pid,y,name,team in FIXED:
            g=joined.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(g)==1,(pid,y)
            r=g.row(0,named=True);s=f.filter(pl.col('row_id')==r['row_id']);x=s.select(pre['pa_features']).to_numpy();k=r['outer_fold']
            index=pre['pa_features'].index('on_40man');probe=x.copy();probe[0,index]=1-probe[0,index]
            traces={};probes={}
            for h in base.e.read(base.CURRENT/f'fit-{y}-{k}.json')['heads']:
                base.e.verify({h['path']:h['sha256']});m=joblib.load(h['path']);paths.append(Path(h['path']))
                if h['head']=='participation':
                    assert np.isclose(m.predict_proba(x)[0,1],r['preseason_raw_p'],atol=1e-10)
                    traces[h['head']]=logit_trace(m,x[0],pre['pa_features']);probes['raw_p']=float(m.predict_proba(probe)[0,1])
                else:
                    assert np.isclose(m.predict(x)[0],r['preseason_raw_conditional_pa'],atol=1e-10)
                    traces[h['head']]=trace(m,x[0],pre['pa_features']);probes['raw_active_pa']=float(m.predict(probe)[0])
            hard=r['hard_unavailable'] or r['reported_retired']
            assert np.isclose((0. if hard else r['preseason_p'])*np.clip(r['preseason_conditional_pa'],1,800),r['preseason_pa'],atol=1e-10)
            probes['bounded_active_pa']=float(np.clip(probes['raw_active_pa'],1,800))
            probes['expected_pa']=0. if hard else probes['raw_p']*probes['bounded_active_pa']
            h=next(h for h in base.e.read(base.RATE/f'fit-{y}-{k}.json')['heads'] if h['head']=='rate')
            base.e.verify({h['path']:h['sha256']});m=joblib.load(h['path']);paths.append(Path(h['path']))
            rx=safe_matrix(s,ratefeatures);assert np.isclose(m.predict(rx)[0],r['preseason_rate'],atol=1e-10)
            traces['rate']=linear_trace(m,rx[0],ratefeatures)
            peers=joined.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&
                (pl.col('stage')==r['stage'])&(pl.col('player_id')!=pid)).with_columns(
                    (((pl.col('age')-r['age'])/3)**2+sum(((pl.col('pa_'+str(l))-r['pa_'+str(l)])/250)**2 for l in range(3))).alias('distance')).sort('distance','player_id').head(4)
            capture=capture_lookup[y,team]
            case_events=[z for z in lookup.get(pid,[]) if str(z.get('date',''))[:10]<=f'{y}-12-31']
            returned=[z for z in capture['payload']['roster'] if z['person']['id']==pid]
            assert bool(returned)==bool(r['on_40man'])
            fields=['row_id','player_id','player_name','origin_year','outer_fold','age','stage','prior_debut','on_40man','pa_0','pa_1','pa_2',
                'preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value','next_pa','next_value',
                'hard_unavailable','reported_retired','roster_event_sign','roster_event_date','event_listing_conflict','date_conflict_count']
            cases.append(dict(display_name=name,origin={n:r[n] for n in fields},roster_request=capture['params'],returned_case_rows=returned,
                cutoff_raw_transactions=case_events,explicit_event_diagnostic=details[r['row_id']],
                source_history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs=s.select(pre['pa_features']).row(0,named=True),saved_paths=traces,
                listing_toggle=dict(probes,old_listing=r['on_40man'],new_listing=1-r['on_40man'],
                    claim='Synthetic saved-fit mechanics only; not causal, scored, validated or a replacement forecast. Batting estimate not toggled.'),
                broad_support=support.filter(pl.col('row_id')==r['row_id']).to_dicts(),
                refined_support=refined.filter(pl.col('row_id')==r['row_id']).to_dicts(),
                peers=peers.select('player_id','player_name','age','stage','pa_0','pa_1','pa_2','on_40man','roster_event_sign','preseason_pa','next_pa','distance').to_dicts(),
                peer_limit='Generic age/stage/workload controls; not independently verified rights, matching surgery, foreign talent or job competition'))
    write('cases.json',cases)
    groups=joined.group_by('origin_year','roster_event_sign','on_40man').agg(pl.len().alias('rows'),pl.col('player_id').n_unique().alias('people'),
        pl.col('preseason_pa').sum().alias('expected_pa'),pl.col('next_pa').sum().alias('actual_pa')).sort('origin_year','roster_event_sign','on_40man')
    risk=joined.filter(pl.col('event_listing_conflict')).with_columns(
        (pl.col('roster_event_date').str.slice(0,4).cast(pl.Int64)==pl.col('origin_year')).alias('current_year_event'))
    paths += [Path(__file__),ROOT/'docs/hitter-roster-provenance-audit-contract.md',base.OUT/'final-report.json',
        SOURCE/'year-end-rosters.parquet',extra/'40man.parquet',extra/'capture-report.json',base.CURRENT/'features.parquet',base.CURRENT/'scored-predictions.parquet',
        base.CURRENT/'support.parquet',base.CURRENT/'profile-support.parquet',base.CURRENT/'preflight.json',base.RATE/'preflight.json',base.e.COUNTS]
    write('report.json',dict(roster_captures=480,returned_memberships=18708,source_rows=63282,evaluation_rows=30506,
        source_conflicts=len(conflicts),evaluation_conflicts=int(joined['event_listing_conflict'].sum()),
        explicit_event_groups=groups.to_dicts(),source_conflict_counts=conflicts.group_by('origin_year','roster_event_sign').len().sort('origin_year','roster_event_sign').to_dicts(),
        conflict_age_groups=risk.group_by('roster_event_sign','current_year_event').agg(pl.len().alias('rows'),pl.col('player_id').n_unique().alias('people')).to_dicts(),
        transaction_capture_counts=capture_counts,duplicate_source_entries=duplicates,saved_heads_replayed=27,
        source_state_certifies_continuous_membership=False,player_walkthrough_status='pending',
        new_fits=False,predictions_changed=False,protected_outcomes_used=False,
        incidental_public_search_exposure='A historical-source search unexpectedly returned a current McLain profile with a 2026 summary. Those data were not retained, used in source states, fitting, scoring or forecast changes. Later protected-test claims must acknowledge this exposure.',
        input_hashes={str(p):sha256_file(p) for p in paths},case_sha256=sha256_file(OUT/'cases.json')))
    print('All 480 captures reconciled;',len(conflicts),'source conflicts;',int(joined['event_listing_conflict'].sum()),'evaluation conflicts',flush=True)
    for c in cases:
        r=c['origin'];print(c['display_name'],r['origin_year'],'listing',r['on_40man'],'explicit',r['roster_event_sign'],
            'PA',round(r['preseason_pa'],2),'toggle',round(c['listing_toggle']['expected_pa'],2),'actual',r['next_pa'],flush=True)


def finalize():
    report=base.e.read(OUT/'report.json');base.e.verify(report['input_hashes'])
    assert sha256_file(OUT/'cases.json')==report['case_sha256']
    cases=base.e.read(OUT/'cases.json')
    reviews=ROOT/'config/hitter_roster_provenance_review.json'
    document=ROOT/'docs/hitter-roster-provenance-audit-result.md'
    manual=base.e.read(reviews)
    base.validate_manual_review(cases,manual)
    body=document.read_text(encoding='utf8')
    assert all(c['display_name'] in body for c in cases)
    final=dict(report,player_walkthrough_status='complete',reviewed_cases=len(cases),
        review_hashes={str(p):sha256_file(p) for p in [reviews,document]},
        disposition=manual['disposition'],next_action=manual['next_action'],deployment_approved=False)
    write('reviewed-cases.json',manual);write('final-report.json',final)
    dest=ROOT/'reports/model-evidence/hitter-roster-provenance-audit';dest.mkdir(parents=True,exist_ok=True)
    for name in ['cases.json','conflicts.json','report.json','reviewed-cases.json','final-report.json']:
        shutil.copy2(OUT/name,dest/name)
        assert sha256_file(OUT/name)==sha256_file(dest/name)
    print('Nine source/player reviews completed; original forecasts unchanged',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--finalize',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    finalize() if args.finalize else main()
