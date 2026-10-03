"""Rebuild the observable canceled-season cohort without future eligibility."""
import json
from pathlib import Path
import numpy as np
import polars as pl
import prepare_practical_hitter_v31 as r
import prepare_practical_hitter_v33 as pooled
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file

OUT = r.ROOT / 'reports/generated/hitter-2020-cohort'
BASE = r.ROOT / 'reports/generated/practical-hitter-v33b'


def eligible_ids(previous, current, roster, old):
    """No outcome, current-person position or future draft field is accepted."""
    historical_hitters = roster.filter(~pl.col('position').is_in(['1', 'X', 'UNKNOWN']))
    observed_hitters = current.filter(~pl.col('position').is_in(['1', 'X', 'UNKNOWN']))
    return sorted(set(previous['player_id']) | set(observed_hitters['player_id']) |
                  set(historical_hitters['player_id']) | set(old['player_id']))


def make_rows(old, stints, counts, targets, roster, forty, births, debuts):
    year = 2020
    prior = old.filter(pl.col('origin_year') == 2019)
    previous = {o['player_id']:o for o in prior.iter_rows(named=True)}
    legacy = old.filter(pl.col('origin_year') == year)
    current = stints.filter(pl.col('season') == year)
    ids = eligible_ids(prior, current, roster, legacy)
    assert set(legacy['player_id']) <= set(ids)
    assert not set(ids) & {701762, 805811}, 'Later entrant unexpectedly in 2020 source'
    old_ids = dict(legacy.select('player_id','row_id').iter_rows())
    next_id = old['row_id'].max()+1
    historical = stints.filter((pl.col('season') <= year) & (pl.col('plate_appearances') > 0))
    ann = historical.group_by('season','player_id').agg(pl.col('reported_age').drop_nulls().median().alias('age'))
    primary = historical.sort(['season','player_id','plate_appearances','team_id'],
        descending=[False,False,True,False]).unique(['season','player_id'],keep='first')
    meta = primary.join(ann,on=['season','player_id'],validate='1:1').sort('season')
    histories = {}
    for o in meta.iter_rows(named=True): histories.setdefault(o['player_id'],[]).append(o)
    membership = dict(forty.select('player_id','team_id').iter_rows())
    raw_rosters = {}
    for o in roster.sort('team_id','position').iter_rows(named=True):
        raw_rosters.setdefault(o['player_id'],[]).append(o)
    bdates = dict(births.select('player_id','birth_date').iter_rows())
    # Debut dates are admitted only when already historical at the origin.
    debuted = {o['player_id']:o['mlb_debut_date'].year for o in debuts.iter_rows(named=True)
               if o['mlb_debut_date'].year <= year}
    values = {(o['season'],o['player_id']):o for o in targets.iter_rows(named=True)}
    env = {o['season']:(o['schedule_fraction'],570*o['schedule_fraction']/o['league_pa'])
           for o in targets.unique('season').iter_rows(named=True)}
    lut = {(o['season'],o['player_id'],o['bucket']):o for o in counts.iter_rows(named=True)}
    mlb = counts.filter((pl.col('bucket')=='MLB') & (pl.col('season')<=year))
    career = dict(mlb.group_by('player_id').agg(pl.col('plate_appearances').sum()).iter_rows())
    rows=[]; provenance=[]
    for pid in ids:
        past=histories.get(pid,[]);last=past[-1] if past else None;p=previous.get(pid)
        listing=raw_rosters.get(pid,[])
        age_source='unknown';age=None
        if last and last['age'] is not None:
            age=last['age']+year-last['season'];age_source='past reported season age'
        elif p and not p['age_unknown']:
            age=p['age']+1;age_source='2019 snapshot advanced one year'
        elif pid in bdates:
            age=year-int(bdates[pid][:4]);age_source='immutable birth year'
        unknown=age is None
        if unknown:age=27.
        d=debuted.get(pid);elapsed=year-d if d is not None else -1
        position=last['position'] if last else listing[0]['position'] if listing else 'UNKNOWN'
        if position not in r.POS:position='UNKNOWN'
        rid=old_ids.get(pid)
        if rid is None:rid=next_id;next_id+=1
        row=dict(row_id=rid,origin_year=year,target_year=year+1,horizon=1,player_id=pid,
            outer_fold=player_fold(pid),age=float(age),age_unknown=int(unknown),
            age_centered=(age-27)/5,age_squared=((age-27)/5)**2,
            elapsed=elapsed,elapsed_scaled=max(-1,elapsed)/10,prior_debut=int(elapsed>=0),
            window_complete=True,player_name=last['player_name'] if last else listing[0]['player_name'] if listing else p['player_name'] if p else None,
            team_id=membership.get(pid,last['team_id'] if last else listing[0]['team_id'] if listing else p['team_id'] if p else None),
            on_40man=int(pid in membership),reorganized=0,last_stat_gap=min(5,year-last['season']) if last else 5,
            source_position=position,snapshot_level='MLB' if lut.get((year,pid,'MLB')) else p['snapshot_level'] if p else 'INACTIVE')
        for pos in r.POS:row['position_'+pos]=int(position==pos)
        regular=0;absence=0
        for lag in range(3):
            y=year-lag;row[f'milb_canceled_{lag}']=int(y==2020);allpa=0;mpa=0
            for bucket in r.BUCKETS:
                c=lut.get((y,pid,bucket));pa=c['plate_appearances'] if c else 0;allpa+=pa
                prefix=f'{bucket}_{lag}_';row[prefix+'pa']=float(pa);row[prefix+'present']=int(pa>0)
                for ev,(num,den,prior_rate) in EVENTS.items():
                    row[prefix+ev]=((c[num] if c else 0)+100*prior_rate)/((c[den] if c else 0)+100)
                if bucket=='MLB':mpa=pa
            row[f'pa_{lag}']=mpa;row[f'work_{lag}']=mpa/env[y][0];row[f'minor_pa_{lag}']=allpa-mpa
            t=values.get((y,pid));v=t['component_war'] if t else 0
            row[f'quality_{lag}']=600*(v-env[y][1]*mpa)/(mpa+1200)
            row[f'quality_present_{lag}']=int(mpa>0);regular+=row[f'work_{lag}']>=400;absence+=mpa==0
        row.update(regular_window=int(regular),regular_window_scaled=regular/3,absence_window_scaled=absence/3,
            current_state=0 if row['pa_0']==0 else 1 if row['pa_0']<200 else 2 if row['pa_0']<400 else 3,
            origin_replacement_rate=env[year][1]/env[year][0],career_mlb_observed_pa=career.get(pid,0),
            career_mlb_left_truncated=int(d is not None and d<2008),hard_unavailable=False,needs_availability_scenario=False)
        # This stage is last observed competition, not invented 2020 MiLB games.
        row['stage']='Current MLB' if row['pa_0']>0 else 'Upper minors' if row['AAA_1_pa']+row['AA_1_pa']>0 else 'Lower minors' if row['minor_pa_1']>0 else 'Inactive / unknown'
        nxt=values.get((year+1,pid));pa=nxt['mlb_pa'] if nxt else 0;v=nxt['component_war'] if nxt else 0
        row.update(next_pa=pa,next_value=v,next_state=0 if pa==0 else 1 if pa<200 else 2 if pa<400 else 3,
            next_batting_rate=600*(v-env[year+1][1]*pa)/pa if pa else 0.)
        rows.append(row)
        provenance.append(dict(player_id=pid,row_id=rid,carried_2019=pid in previous,
            old_2020_subset=pid in old_ids,historical_2020_listing=bool(listing),roster_capture_missing=False,
            last_observed_minor_level_carried=row['pa_0']==0 and row['minor_pa_1']>0,
            age_source=age_source,roster_teams=sorted({o['team_id'] for o in listing}),
            historical_roster_positions=sorted({o['position'] for o in listing})))
    return pl.DataFrame(rows),pl.DataFrame(provenance)


def main():
    assert r.read(BASE/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'source-report.json').exists(), 'Preserve completed source'
    old=pl.read_parquet(BASE/'features.parquet');stints=pl.read_parquet(r.OUT/'dated-stints.parquet')
    counts=pl.read_parquet(r.OUT/'counts.parquet');targets=pl.read_parquet(r.ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    assert set(targets['season'])==set(range(2009,2026)) and stints['season'].max()==2025
    assert counts.filter((pl.col('season')==2020)&(pl.col('bucket')!='MLB')).is_empty()
    mlb=counts.filter(pl.col('bucket')=='MLB').select('season','player_id','plate_appearances')
    check=targets.join(mlb,on=['season','player_id'],validate='1:1')
    assert len(check)==len(targets) and check['mlb_pa'].equals(check['plate_appearances'])
    roster=pl.read_parquet(OUT/'full-roster.parquet');forty=pl.read_parquet(OUT/'40man.parquet')
    births=pl.read_parquet(OUT/'birthdates.parquet');debuts=pl.read_parquet(r.ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet')
    fresh,provenance=make_rows(old,stints,counts,targets,roster,forty,births,debuts)
    fresh=pooled.materialize(fresh,counts,pl.read_parquet(BASE/'draft-evidence.parquet'))
    fresh=fresh.select(old.columns).cast(old.schema,strict=True)
    combined=pl.concat([old.filter(pl.col('origin_year')!=2020),fresh]).sort('row_id')
    assert combined.unique(['origin_year','player_id']).height==len(combined)
    assert combined['row_id'].n_unique()==len(combined)
    unchanged=combined.filter(pl.col('origin_year')!=2020).sort('row_id')
    assert unchanged.equals(old.filter(pl.col('origin_year')!=2020).sort('row_id'))
    old20=old.filter(pl.col('origin_year')==2020)
    matched=old20.select('player_id','next_pa','next_value').join(fresh.select('player_id',
        pl.col('next_pa').alias('_pa'),pl.col('next_value').alias('_v')),on='player_id',validate='1:1')
    assert len(matched)==len(old20) and matched['next_pa'].equals(matched['_pa']) and matched['next_value'].equals(matched['_v'])
    features=r.read(BASE/'preflight.json')['features']['pedigree']
    assert np.isfinite(fresh.select(features).to_numpy()).all()
    fresh.write_parquet(OUT/'origin-2020.parquet');combined.write_parquet(OUT/'features.parquet');provenance.write_parquet(OUT/'provenance.parquet')
    outside=targets.filter(pl.col('season')==2021).join(fresh.select('player_id'),on='player_id',how='anti')
    outside.write_parquet(OUT/'outside-2021.parquet')
    paths=[BASE/'features.parquet',BASE/'draft-evidence.parquet',r.OUT/'counts.parquet',r.OUT/'dated-stints.parquet',
        r.ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet',r.ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet',
        OUT/'capture-report.json',OUT/'birthdate-report.json',OUT/'full-roster.parquet',OUT/'40man.parquet',OUT/'birthdates.parquet',
        OUT/'features.parquet',OUT/'origin-2020.parquet',OUT/'provenance.parquet',Path(__file__),r.ROOT/'docs/practical-hitter-2020-cohort-contract.md']
    report=dict(origin_year=2020,old_subset_rows=len(old20),reconstructed_rows=len(fresh),
        source_rows=len(combined),existing_non2020_bit_exact=True,all_evaluation_targets_unchanged=True,
        known_roster_members=int(fresh['on_40man'].sum()),unknown_age=int(fresh['age_unknown'].sum()),
        actual_future_pa=int(fresh['next_pa'].sum()),outside_future_pa=int(outside['mlb_pa'].sum()),
        stage_counts=fresh.group_by('stage').agg(pl.len().alias('rows'),pl.col('next_pa').sum().alias('next_pa')).sort('stage').to_dicts(),
        all_old_2020_people_retained=True,no_2020_milb_counts=True,no_future_eligibility=True,
        international_never_observed_entry_coverage='Unknown beyond historical fullRoster lists',
        protected_outcomes_used=False,frozen_forecast_changed=False,player_walkthrough_status='pending',
        input_hashes={str(p):sha256_file(p) for p in paths})
    (OUT/'source-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'},indent=2))


if __name__=='__main__':main()
