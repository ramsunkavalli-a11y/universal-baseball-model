"""Build complete original/addition inputs and every actual preflight before fits."""
from collections import Counter
from datetime import date
from pathlib import Path
import json
import sys

import numpy as np
import polars as pl

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.hitter_dated_context import materialize as dated_context
from universal_baseball.hitter_numeric_history import repair
from universal_baseball.hitter_overseas_inputs import STATUS_FEATURES, FOREIGN_FEATURES, status_features, foreign_features
from universal_baseball.historical_prospect_rank import features as scout_features
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.practical_hitter_v30 import EVENTS as RAW_EVENTS
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v31 import BUCKETS, POS
from prepare_practical_hitter_v33 import materialize as pooled_features
from prepare_hitter_games_v38 import features as game_features

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-overseas-integration'
OLD=ROOT/'reports/generated/hitter-preseason-readiness-v68'
ANCHOR=ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
ADDITIONS=ROOT/'reports/generated/foreign-hitter-additions'
STATUS=ROOT/'reports/generated/hitter-status-evidence-v2'
FOREIGN=ROOT/'reports/generated/foreign-origin-inputs'
BORROWED=ROOT/'reports/generated/foreign-borrowed-stability'
CONTRACT=ROOT/'docs/hitter-overseas-integration-contract.md'


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def write(name,obj):
    path=OUT/name
    assert not path.exists(),f'Preserve {path}'
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def verify(mapping):
    for p,h in mapping.items():
        path=Path(p);path=path if path.is_absolute() else ROOT/path
        assert sha256_file(path)==h,str(path)


def annual_labels(stints):
    fields=['plate_appearances','strike_outs','unintentional_walks','hit_by_pitch','singles','doubles','triples','home_runs']
    ann=stints.filter(pl.col('sport_id')==1).group_by('season','player_id').agg(pl.col(fields).sum())
    ann=ann.with_columns((pl.col('plate_appearances')-pl.sum_horizontal(fields[1:])).alias('other'))
    assert ann['other'].min()>=0 and stints['season'].max()==2025
    names=['other',*fields[1:]]
    counts={(r['season'],r['player_id']):np.array([r[n] for n in names],float) for r in ann.to_dicts()}
    totals=ann.group_by('season').agg(pl.col(names).sum())
    env={r['season']:np.array([r[n] for n in names],float)/sum(r[n] for n in names) for r in totals.to_dicts()}
    assert set(env)==set(range(2008,2026))
    return counts,env


def addition_frame(old, admitted, overseas, counts, targets, env, debut):
    # Reconstruct every input family from its actual source; no borrowed player's
    # stats, guessed scouting absence or invented zero US history.
    cols=old.columns[:old.columns.index('pooled_MLB_pa')]
    lut={(r['season'],r['player_id'],r['bucket']):r for r in counts.to_dicts()}
    val={(r['season'],r['player_id']):r for r in targets.to_dicts()}
    meta={r['season']:r for r in targets.unique('season').to_dicts()}
    rows=[]
    for i,a in enumerate(sorted(admitted,key=lambda r:(r['origin_year'],r['player_id']))):
        y,pid=a['origin_year'],a['player_id'];foreign=overseas[a['candidate_key']]
        o={c:None if old.schema[c]==pl.String else False if old.schema[c]==pl.Boolean else 0 for c in cols}
        history=a['actual_prior_domestic_stints'];last=sorted(history,key=lambda r:(r['season'],r['plate_appearances'],r['team_id']))[-1] if history else None
        birth=foreign['birth_date'];age=(date(y,12,31)-date.fromisoformat(birth)).days/365.2425 if birth else None
        if age is None and last and last['reported_age'] is not None:age=last['reported_age']+y-last['season']
        unknown=age is None;age=27. if unknown else float(age)
        d=debut.get(pid);elapsed=y-d if d is not None and d<=y else -1
        mixed=a['mixed_role_uncertain'];position='Y' if mixed else last['position'] if last else 'UNKNOWN'
        o.update(row_id=int(old['row_id'].max())+1+i,origin_year=y,target_year=y+1,horizon=1,player_id=pid,
            outer_fold=player_fold(pid),age=age,age_unknown=int(unknown),age_centered=(age-27)/5,age_squared=((age-27)/5)**2,
            elapsed=elapsed,elapsed_scaled=max(-1,elapsed)/10,prior_debut=int(elapsed>=0),window_complete=True,
            player_name=a['player_name'],team_id=last['team_id'] if last else None,on_40man=0,reorganized=int(y>=2021),
            last_stat_gap=min(5,y-last['season']) if last else 5,source_position=position,snapshot_level='FOREIGN',
            career_mlb_observed_pa=a['career_observed_mlb_pa'],career_mlb_left_truncated=int(d is not None and d<2008),
            origin_replacement_rate=570/meta[y]['league_pa'],needs_availability_scenario=False,hard_unavailable=False)
        for pos in POS:o['position_'+pos]=int(position==pos)
        regular=absent=0
        for lag in range(3):
            year=y-lag;allpa=0;mlbpa=0;o[f'milb_canceled_{lag}']=int(year==2020)
            for b in BUCKETS:
                c=lut.get((year,pid,b));pa=c['plate_appearances'] if c else 0;allpa+=pa
                o[f'{b}_{lag}_pa']=float(pa);o[f'{b}_{lag}_present']=int(pa>0)
                for ev,(num,den,prior) in RAW_EVENTS.items():o[f'{b}_{lag}_{ev}']=((c[num] if c else 0)+100*prior)/((c[den] if c else 0)+100)
                if b=='MLB':mlbpa=pa
            v=val.get((year,pid),{}).get('component_war',0.)
            rep=570*meta[year]['schedule_fraction']/meta[year]['league_pa']
            o[f'pa_{lag}']=mlbpa;o[f'work_{lag}']=mlbpa/meta[year]['schedule_fraction'];o[f'minor_pa_{lag}']=allpa-mlbpa
            o[f'quality_{lag}']=600*(v-rep*mlbpa)/(mlbpa+1200);o[f'quality_present_{lag}']=int(mlbpa>0)
            regular+=o[f'work_{lag}']>=400;absent+=mlbpa==0
        o.update(regular_window=int(regular),regular_window_scaled=regular/3,absence_window_scaled=absent/3,
            current_state=0 if o['pa_0']==0 else 1 if o['pa_0']<200 else 2 if o['pa_0']<400 else 3,
            stage='Current MLB' if o['pa_0']>0 else 'Upper minors' if o['AAA_0_pa']+o['AA_0_pa']>0 else 'Lower minors' if o['minor_pa_0']>0 else 'Inactive / unknown')
        nxt=val.get((y+1,pid),{});pa=nxt.get('mlb_pa',0)
        o.update(next_pa=pa,next_value=nxt.get('component_war',0.),next_state=0 if pa==0 else 1 if pa<200 else 2 if pa<400 else 3,
            next_batting_rate=nxt.get('conditional_component_war_per_600',0.) if pa else 0.)
        assert sum(o[f'{b}_{lag}_pa'] for b in BUCKETS for lag in range(3))==a['recent_observed_domestic_pa']
        assert sum(o[f'pa_{lag}'] for lag in range(3))==a['recent_observed_mlb_pa']
        rows.append(o)
    f=pl.DataFrame(rows,schema_overrides={c:old.schema[c] for c in cols})
    f=pooled_features(f,counts,pl.read_parquet(ROOT/'reports/generated/practical-hitter-v33/draft-evidence.parquet'))
    f,_=repair(f,counts)
    f,_=game_features(f,pl.read_parquet(ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet'))
    ranks=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet').to_dicts()
    lookup={(r['season'],r['player_id']):r['rank'] for r in ranks};capacity={r['season']:r['list_capacity'] for r in ranks}
    scout=[]
    for o in f.to_dicts():scout.append(dict(row_id=o['row_id'],**{k:-1. if v is None else v for k,v in scout_features(o['player_id'],o['target_year'],lookup,capacity).items()}))
    f=f.join(pl.DataFrame(scout),on='row_id',validate='1:1').with_columns((pl.col('next_pa')>0).cast(pl.Int64).alias('next_active'))
    assert set(f.columns)==set(old.columns)
    return f.select(old.columns)


def tagged(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_group'),
        pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1).otherwise(2).alias('mlb_exposure'),
        (pl.col('foreign_recent_pa')>0).alias('foreign_exposure'),
        pl.when(pl.col('status_hard_unavailable')>0).then(3).when(pl.col('status_unresolved_nonmedical')>0).then(2)
          .when(pl.col('status_finite_nonmedical')>0).then(1).otherwise(0).alias('restriction_profile'))


def prepare():
    assert not OUT.exists(),'Inspect existing execution, never restart blindly'
    paths=[CONTRACT,Path(__file__),ROOT/'src/universal_baseball/hitter_overseas_inputs.py',ROOT/'tests/test_hitter_overseas_inputs.py',
        ROOT/'src/universal_baseball/forecast_validation.py',ROOT/'scripts/fit_hitter_overseas_integration.py',
        OLD/'features.parquet',OLD/'preflight.json',ANCHOR,ADDITIONS/'origin-inputs.json',ADDITIONS/'membership-seal.json',
        FOREIGN/'origin-inputs.json',BORROWED/'profiles.json',STATUS/'status-ledger.json',
        ROOT/'reports/generated/hitter-preseason-population-source/population.parquet',
        ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet',ROOT/'reports/generated/practical-hitter-v31/counts.parquet',
        ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet',ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet',
        ROOT/'reports/generated/practical-hitter-v33/draft-evidence.parquet',ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet',
        ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet']
    for directory in [ADDITIONS,STATUS,BORROWED]:
        report=read(directory/'final-review.json');assert report['player_walkthrough_status'].startswith('complete')
        verify(report['source_hashes']);verify(report['artifact_hashes']);paths.append(directory/'final-review.json')
    foreign_review=read(FOREIGN/'independent-review.json');verify(foreign_review['hashes']);paths.append(FOREIGN/'independent-review.json')
    old=pl.read_parquet(OLD/'features.parquet').sort('row_id');anchor=pl.read_parquet(ANCHOR).sort('row_id');pre=read(OLD/'preflight.json')
    overseas={r['candidate_key']:r for r in read(FOREIGN/'origin-inputs.json')['rows']}
    admitted=[r for r in read(ADDITIONS/'origin-inputs.json')['rows'] if r['qualified_for_batting_input']]
    assert len(admitted)==32 and sorted(r['candidate_key'] for r in admitted)==sorted(read(ADDITIONS/'membership-seal.json')['qualified_keys'])
    stints=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    targets=pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet');actual,env=annual_labels(stints)
    debut={r['player_id']:r['mlb_debut_date'].year for r in pl.read_parquet(ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet').to_dicts()}
    added=addition_frame(old,admitted,overseas,counts,targets,env,debut)
    assert added.join(old.select('player_id','origin_year'),on=['player_id','origin_year'],how='inner').is_empty()
    combined=pl.concat([old,added],how='vertical_relaxed')
    population=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-population-source/population.parquet').to_dicts()
    combined,changes=dated_context(combined,population,list(overseas.values()))
    status={r['candidate_key']:r for r in read(STATUS/'status-ledger.json')['rows']}
    mixed={r['candidate_key']:r['mixed_role_uncertain'] for r in admitted}
    flags=[]
    for o in combined.to_dicts():
        key=f'{o["origin_year"]}:{o["player_id"]}';s=status[key]
        assert o['ctx_information_date']==s['information_date']
        flags.append(dict(row_id=o['row_id'],source_addition=o['row_id']>old['row_id'].max(),**status_features(s,mixed.get(key,overseas.get(key,{}).get('dated_role_hint') in {'two_way_hint','two_way_or_conflicting_hints'}))))
    f=combined.join(pl.DataFrame(flags),on='row_id',validate='1:1').sort('row_id')
    # Reconstruct complete MLB labels independently, including preserved exits.
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in f.to_dicts()])
    origins=np.array([env[y] for y in f['origin_year']]);future=np.array([env[y] for y in f['target_year']])
    league_pa={y:sum(c.sum() for (s,_),c in actual.items() if s==y) for y in env}
    meta={r['season']:r for r in targets.unique('season').to_dicts()}
    assert all(league_pa[y]==meta[y]['league_pa'] for y in meta)
    rep=np.array([570*meta[y]['schedule_fraction']/league_pa[y] for y in f['origin_year']])
    lab=labels(raw,origins,future,rep)
    assert np.array_equal(lab['pa'],f['next_pa'].to_numpy())
    original=f.filter(~pl.col('source_addition'));assert original.select(old.columns).drop(['age','age_centered','age_squared','age_unknown','on_40man','source_position',*[n for n in old.columns if n.startswith('position_')]]).equals(old.drop(['age','age_centered','age_squared','age_unknown','on_40man','source_position',*[n for n in old.columns if n.startswith('position_')]]))
    matched=f.select('row_id').join(anchor.select('row_id','next_value','relative_value_label','actual_future_relative_rate'),on='row_id',how='inner').sort('row_id')
    mask=np.isin(f['row_id'].to_numpy(),matched['row_id'].to_numpy())
    assert np.allclose(lab['common_value'][mask],matched['next_value'],atol=1e-10,rtol=0)
    assert np.allclose(lab['relative_value'][mask],matched['relative_value_label'],atol=1e-10,rtol=0)
    assert np.allclose(lab['relative_rate'][mask],matched['actual_future_relative_rate'],atol=1e-10,rtol=0)
    f=f.with_columns(pl.Series('actual_relative_rate',lab['relative_rate']),pl.Series('actual_relative_value',lab['relative_value']),
        pl.Series('integration_replacement_rate',rep),pl.Series('origin_event_index',origins@VALUES))
    # Addition legacy labels use a different reference; replace only those labels
    # with independently reconstructed common-reference values for this contract.
    f=f.with_columns(pl.when(pl.col('source_addition')).then(pl.Series(lab['common_value'])).otherwise(pl.col('next_value')).alias('next_value'))
    profiles={(r['candidate_key'],r['outer_fold']):r for r in read(BORROWED/'profiles.json')['profiles']}
    assert len(profiles)==3205
    OUT.mkdir(parents=True);f.write_parquet(OUT/'features.parquet')
    write('source-review.json',dict(original_rows=old.height,addition_rows=added.height,source_changes=changes,
        addition_keys=[r['candidate_key'] for r in admitted],original_membership_labels_preserved=True,
        labels_reconstructed_from_complete_MLB_counts=True,replacement_reference='570 * completed origin schedule fraction / complete origin MLB PA, same as current benchmark',
        legacy_source_replacement_preserved=True,initial_preparation_failure='Legacy source omits completed schedule fraction; initial reconstruction and then an incorrect totals-only diagnosis failed before output or fitting. Source totals actually match exactly.',
        maximum_legacy_replacement_rate_difference=float(np.max(abs(rep-f['origin_replacement_rate'].to_numpy()))),
        new_fits=0,player_walkthrough_status='pending'))
    supports=[];profiles_support=[];ranges=[];cells=[]
    names=pre['pa_features']+STATUS_FEATURES
    for c in pre['cells']:
        y,k=c['year'],c['fold']
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']) | (pl.col('source_addition')&(pl.col('target_year')<=y)&(pl.col('target_year')!=2020)&(pl.col('outer_fold')!=k))).sort('row_id')
        te=f.filter(pl.col('row_id').is_in(c['test_row_ids']) | (pl.col('source_addition')&(pl.col('origin_year')==y)&(pl.col('outer_fold')==k))).sort('row_id')
        assert tr['ctx_information_date'].max()<te['ctx_information_date'].min()
        rows=[]
        for o in pl.concat([tr,te]).to_dicts():
            key=f'{o["origin_year"]}:{o["player_id"]}';s=overseas.get(key)
            rows.append(dict(row_id=o['row_id'],**foreign_features(s,profiles.get((key,k)),origin=o['origin_year'],outer_fold=k,own_fold=o['outer_fold'])))
        overlay=pl.DataFrame(rows);full=pl.concat([tr,te]).join(overlay,on='row_id',validate='1:1')
        full.write_parquet(OUT/f'features-{y}-{k}.parquet')
        paths.append(OUT/f'features-{y}-{k}.parquet')
        a=full.filter(pl.col('row_id').is_in(tr['row_id']));b=full.filter(pl.col('row_id').is_in(te['row_id']));checks={}
        for arm,features in [('domestic',names),('overseas',names+FOREIGN_FEATURES)]:
            for head,sub in [('participation',a),('conditional_pa',a.filter(pl.col('next_pa')>0)),('rate',a.filter(pl.col('next_pa')>0))]:
                sup,note=preflight(sub,b,cutoff=y,fold=k,features=features,expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm+'_'+head]=note
                supports.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(k).alias('test_fold')))
                keys=['prior_debut','stage','age_group','mlb_exposure','foreign_exposure','status_major_link','restriction_profile']
                cnt=tagged(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                profiles_support.append(tagged(b).select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(y).alias('origin_year'),pl.lit(k).alias('test_fold')))
                for n in features:
                    lo,hi=float(sub[n].min()),float(sub[n].max());outside=((b[n]<lo)|(b[n]>hi))
                    if outside.any():ranges.append(dict(origin_year=y,fold=k,arm=arm,head=head,feature=n,min=lo,max=hi,row_ids=b.filter(pl.Series(outside))['row_id'].to_list()))
        cells.append(dict(year=y,fold=k,information_date=c['information_date'],training_row_ids=tr['row_id'].to_list(),test_row_ids=te['row_id'].to_list(),checks=checks))
        print(f'All six actual head checks saved before fits: {y}/{k}, {te.height} forecasts.',flush=True)
    eval_ids={r for c in cells for r in c['test_row_ids']}
    assert set(anchor['row_id']) <= eval_ids
    add_eval=f.filter(pl.col('row_id').is_in(list(eval_ids))&pl.col('source_addition'))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles_support).write_parquet(OUT/'profile-support.parquet')
    write('feature-ranges.json',dict(warnings=ranges))
    paths.extend([OUT/'features.parquet',OUT/'source-review.json',OUT/'support.parquet',OUT/'profile-support.parquet',OUT/'feature-ranges.json'])
    write('preflight.json',dict(before_fitting=True,new_fits=0,cells=cells,arms={'domestic':names,'overseas':names+FOREIGN_FEATURES},
        settings=pre['settings'],ridge_alpha=100,source_rows=f.height,original_evaluation_rows=anchor.height,addition_evaluation_rows=add_eval.height,
        addition_evaluation_keys=[f'{r["origin_year"]}:{r["player_id"]}' for r in add_eval.to_dicts()],
        checks_before_fits=210,source_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths},
        player_walkthrough_status='pending',protected_outcomes_used=False,deployment_approved=False))
    print(f'Prepared {f.height} source origins, {anchor.height} original and {add_eval.height} additional evaluation forecasts.',flush=True)


if __name__=='__main__':prepare()
