"""Freeze reviewed means, audit appearance probabilities, and export research UI."""
from pathlib import Path
import gzip
import json
import numpy as np
import polars as pl
from build_practical_hitter_explorer_v31 import team_map
from universal_baseball.storage import sha256_file
import evaluate_hitter_compatible_value_v63 as prior

ROOT=prior.ROOT
OUT=ROOT/'reports/generated/practical-hitter-handoff-v64'
EDGES=np.array([0,.01,.05,.10,.25,.50,.75,.90,1.])


def affiliation_context():
    """Dated roster takes precedence; otherwise label the last observed club."""
    mapping,hashes=team_map()
    for path in sorted((ROOT/'reports/generated/hitter-arrival-source-repair-v1/captures/roster').glob('*/teams.json.gz')):
        year=int(path.parent.name)
        if year>2024:continue
        with gzip.open(path,'rt',encoding='utf8') as stream:obj=json.load(stream)
        assert obj['params']=={'sportId':1,'season':year}
        hashes[str(path)]=sha256_file(path)
        assert len(obj['payload']['teams'])==30
        for t in obj['payload']['teams']:
            assert int(t['season'])==year and t['sport']['id']==1
            val=dict(club=t['name'],org=t['name'])
            key=(year,t['id'])
            assert key not in mapping or mapping[key]==val,key
            mapping[key]=val
    rp=ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet'
    sp=ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    roster=pl.read_parquet(rp);stints=pl.read_parquet(sp)
    hashes.update({str(p):sha256_file(p) for p in [rp,sp]})
    listings={(r['season'],r['player_id']):r['team_id'] for r in roster.iter_rows(named=True)}
    primary=stints.filter(pl.col('plate_appearances')>0).sort(['season','player_id','plate_appearances','team_id'],descending=[False,False,True,False]).unique(['season','player_id'],keep='first').sort('season')
    histories={}
    for r in primary.iter_rows(named=True):histories.setdefault(r['player_id'],[]).append(r)
    def lookup(r):
        key=(r['origin_year'],r['player_id'])
        if key in listings:
            year,team,basis=r['origin_year'],listings[key],'Requested December 31 historical 40-man roster'
        else:
            past=[v for v in histories.get(r['player_id'],[]) if v['season']<=r['origin_year']]
            last=past[-1] if past else None
            year,team,basis=(last['season'],last['team_id'],'Last observed primary batting club') if last else (None,None,'No usable dated club evidence')
        assert team==r['team_id'],(r['player_id'],r['origin_year'],team,r['team_id'])
        return dict(**mapping.get((year,team),dict(club='Unknown club',org='Unknown affiliation')),team_context_year=year,team_context_basis=basis)
    return lookup,hashes


def write(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')


def probability(g):
    p=g['repaired_p'].to_numpy();y=(g['next_pa'].to_numpy()>0).astype(float)
    assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    values=[]
    for year in sorted(g['target_year'].unique()):
        z=g['target_year'].to_numpy()==year;pp=p[z];yy=y[z];pc=np.clip(pp,1e-12,1-1e-12)
        values.append([np.mean((pp-yy)**2),-np.mean(yy*np.log(pc)+(1-yy)*np.log(1-pc)),np.mean(pp),np.mean(yy)])
    b=np.mean(values,axis=0)
    bins=np.minimum(np.searchsorted(EDGES,p,side='right')-1,len(EDGES)-2);bands=[]
    for j in range(len(EDGES)-1):
        sub=g.filter(pl.Series(bins==j));pp=p[bins==j];yy=y[bins==j]
        if len(sub):
            rates=[]
            for year in sorted(sub['target_year'].unique()):
                z=sub['target_year'].to_numpy()==year;rates.append([float(pp[z].mean()),float(yy[z].mean())])
            a=np.mean(rates,axis=0)
            bands.append(dict(lower=float(EDGES[j]),upper=float(EDGES[j+1]),upper_inclusive=j==len(EDGES)-2,
                rows=len(sub),people=sub['player_id'].n_unique(),years=sub['target_year'].n_unique(),
                expected_appearances=float(pp.sum()),actual_appearances=int(yy.sum()),
                pooled_predicted=float(pp.mean()),pooled_observed=float(yy.mean()),equal_year_predicted=float(a[0]),equal_year_observed=float(a[1])))
    return dict(rows=len(g),people=g['player_id'].n_unique(),brier=float(b[0]),log_loss=float(b[1]),
        equal_year_predicted=float(b[2]),equal_year_observed=float(b[3]),expected_appearances=float(p.sum()),actual_appearances=int(y.sum()),bands=bands)


def main():
    report=prior.read(prior.OUT/'report.json');assert report['player_walkthrough_status']=='complete'
    for key in ['input_hashes','output_hashes','review_code_hashes']:
        for path,h in report[key].items():assert sha256_file(Path(path))==h,path
    q=pl.read_parquet(prior.OUT/'scored-predictions.parquet').sort('row_id')
    source=pl.read_parquet(prior.OUT/'features.parquet').filter(pl.col('row_id').is_in(q['row_id'].to_list())).sort('row_id')
    assert len(q)==30506 and q['row_id'].equals(source['row_id'])
    # The freeze records actual input metadata, not legacy display fields.
    base=source.select('row_id','player_id','player_name','origin_year','target_year','age','team_id','stage','source_position',
        'pa_0','pa_1','pa_2','draft_known','draft_year','pick_number','draft_school_class','draft_elapsed','draft_college',
        'scout_list_available_0','scout_list_capacity_0','scout_listed_0','scout_rank_score_0','career_mlb_observed_pa',
        'career_mlb_left_truncated','age_unknown','last_stat_gap','minor_pa_0','prior_debut')
    cols=['repaired_p','repaired_raw_p','repaired_conditional_pa','baseline_pa','baseline_rate','baseline_value',
        'hard_unavailable','reported_retired','needs_availability_scenario','origin_evidence_bridge','next_pa','next_batting_rate','next_value',
        'origin_index','origin_replacement_rate','physical_low','physical_high','steamer_index','zips_index','steamer_pa','steamer_rate','zips_rate','steamer_value']
    frozen=base.join(q.select('row_id',*cols),on='row_id',validate='1:1').sort('row_id')
    assert frozen['baseline_pa'].equals(q['baseline_pa']) and frozen['baseline_rate'].equals(q['baseline_rate']) and frozen['baseline_value'].equals(q['baseline_value'])
    assert np.allclose(frozen['repaired_p']*frozen['repaired_conditional_pa'],frozen['baseline_pa'],atol=1e-10,rtol=0)
    assert np.allclose(frozen['baseline_pa']*(frozen['baseline_rate']/600+frozen['origin_replacement_rate']),frozen['baseline_value'],atol=1e-10,rtol=0)
    assert frozen['target_year'].max()==2025 and frozen['origin_year'].max()==2024
    OUT.mkdir(parents=True,exist_ok=True);frozen.write_parquet(OUT/'candidate.parquet')
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(pub)==2627
    scopes=[('all',q),('public_matched',pub),('never_debut',q.filter(pl.col('prior_debut')==0)),('prior_debut',q.filter(pl.col('prior_debut')==1)),
        ('current_brief',q.filter(pl.col('pa_0').is_between(1,199))),('current_partial',q.filter(pl.col('pa_0').is_between(200,399))),('current_regular',q.filter(pl.col('pa_0')>=400))]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    write('probability-audit.json',dict(definition='Probability of any next-calendar-year MLB PA, not success, health, full-season use or career arrival.',
        weighting='equal target years within scope; raw totals also shown; fixed bands descriptive, not a fitted calibrator',
        scopes=[dict(scope=s,**probability(g)) for s,g in scopes if len(g)],no_models_fitted=True,no_prediction_ranges_certified=True))
    support=pl.read_parquet(prior.BASE/'profile-support.parquet')
    supports={}
    for r in support.iter_rows(named=True):supports.setdefault(r['row_id'],{})[r['head']]=r['profile_players']
    affiliation,team_hashes=affiliation_context();rows=[]
    reviews=prior.read(prior.OUT/'reviewed-case-summary.json');byreview={f"{r['player_id']}|{r['origin_year']}":r for r in reviews}
    for r in frozen.iter_rows(named=True):
        r.update(affiliation(r))
        # Keep unknown identity text distinct from missing talent/PA evidence.
        missing_name=not r['player_name']
        if missing_name:r['player_name']=f"Name unavailable (MLBAM {r['player_id']})"
        r['support']=supports[r['row_id']]
        if r['next_pa']==0:r['next_batting_rate']=None
        flags=[]
        if missing_name:flags.append('Historical player name unavailable; MLBAM identity retained')
        if r['support'].get('rate',0)<20:flags.append('Sparse prior MLB outcomes for this profile')
        if not r['origin_evidence_bridge']:flags.append('Historical eligibility evidence incomplete')
        if r['age_unknown']:flags.append('Age unknown')
        if r['career_mlb_left_truncated']:flags.append('Earlier MLB career history truncated')
        if r['needs_availability_scenario']:flags.append('Availability needs a scenario, not a certain job')
        if r['hard_unavailable']or r['reported_retired']:flags.append('Dated opportunity policy sets expected PA to zero')
        if r['scout_listed_0']<0:flags.append('Current historical ranking absence unknown or partial')
        if not r['draft_known']and r['prior_debut']==0:flags.append('Draft or signing pedigree incomplete')
        if r['prior_debut']==0:flags.append('Conditional MLB hitting estimate; not a career grade')
        if r['draft_known']and r['draft_year']==r['origin_year']:flags.append('New draftee: immediate readiness is a known weakness')
        r['flags']=flags;r['reviewed']=f"{r['player_id']}|{r['origin_year']}" in byreview;rows.append(r)
    hist=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('season')<=2025)
    history={}
    for r in hist.iter_rows(named=True):
        pid=r.pop('player_id');history.setdefault(str(pid),[]).append(r)
    dest=OUT/'explorer';dest.mkdir(parents=True,exist_ok=True)
    template=ROOT/'src/universal_baseball/templates/practical_hitter_handoff.html'
    (dest/'index.html').write_text(template.read_text(encoding='utf8'),encoding='utf8')
    scores=prior.read(prior.OUT/'scores.json')
    for name,obj in [('data.json',rows),('history.json',history),('reviews.json',byreview),('scores.json',scores),('probability.json',prior.read(OUT/'probability-audit.json'))]:
        (dest/name).write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf8')
    # Eight explicit readiness/workload checks supplement the completed reviews.
    wanted={(592450,2016),(592450,2024),(701762,2024),(694671,2023),(665742,2017),(665487,2022),(806956,2024),(680574,2024)}
    selected=[r for r in reviews if (r['player_id'],r['origin_year']) in wanted]
    assert len(selected)==8
    paths=[prior.BASE/'preflight.json',prior.OUT/'report.json',prior.OUT/'scored-predictions.parquet',prior.OUT/'features.parquet',
        prior.OUT/'reviewed-case-summary.json',prior.BASE/'profile-support.parquet',ROOT/'reports/generated/practical-hitter-v31/counts.parquet',
        ROOT/'docs/practical-hitter-handoff-v64-contract.md',Path(__file__),template,OUT/'candidate.parquet',OUT/'probability-audit.json']
    hashes={str(p):sha256_file(p) for p in paths};hashes.update(team_hashes)
    write('handoff-manifest.json',dict(candidate='V53 appearance/conditional PA/relative conditional hitting, V63 corrected research value units',
        rows=len(rows),people=frozen['player_id'].n_unique(),origins=sorted(frozen['origin_year'].unique()),targets=sorted(frozen['target_year'].unique()),
        appearance_and_PA_and_rate_unchanged=True,source_inputs_not_legacy_display=True,historical_team_filter=True,unknown_affiliation=sum(r['org']=='Unknown affiliation' for r in rows),
        source_hashes=hashes,settings=prior.read(prior.BASE/'preflight.json')['settings'],ridge_alpha=100,
        no_models_fitted=True,calibrated_continuous_ranges=False,player_walkthrough_status='pending',browser_verification='pending',
        protected_outcomes_used=False,frozen_forecast_changed=False,old_explorer_changed=False,deployment_approved=False,
        probability_case_ids=[dict(player_id=r['player_id'],origin_year=r['origin_year']) for r in selected]))
    print('Frozen research rows',len(rows),'unknown historical affiliations',sum(r['org']=='Unknown affiliation' for r in rows),flush=True)


if __name__=='__main__':main()
