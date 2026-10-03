"""Persist actual source/fold support before the fixed draft-representation test."""
import json
from pathlib import Path
import numpy as np
import polars as pl
import prepare_practical_hitter_v31 as r
import evaluate_hitter_2020_extension as base
import prepare_practical_hitter_v33 as scale
from universal_baseball.draft_age_representation import ADDED,REMOVED,materialize
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-draft-age-v42'
SOURCE=r.ROOT/'reports/generated/hitter-2020-cohort/features.parquet'
FIXED=[(701762,2024),(677008,2023),(669394,2021),(683011,2022),(592450,2016),(592450,2024)]


def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str),encoding='utf8')


def profile(f):
    return f.with_columns(
        pl.when(pl.col('draft_age_known')==0).then(pl.lit('unknown'))
        .when(pl.col('draft_age_proxy')<20).then(pl.lit('under20'))
        .when(pl.col('draft_age_proxy')<25).then(pl.lit('20to24'))
        .otherwise(pl.lit('25plus')).alias('draft_age_band'),
        (pl.col('recent_all_pa')<150).alias('short_pro_sample'))


def main():
    assert r.read(r.ROOT/'reports/generated/practical-hitter-contact-v41/report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    prior=r.read(base.OUT/'preflight.json');f=materialize(pl.read_parquet(SOURCE))
    cols=[c for c in prior['features'] if c not in REMOVED]+ADDED
    assert len(cols)==198 and len(set(cols))==198
    known=f.filter(pl.col('draft_age_known')==1)
    assert known['draft_age_proxy'].min()>=15 and known['draft_age_proxy'].max()<=35
    assert (known['draft_year']<=known['origin_year']).all()
    assert np.isfinite(scale.safe_matrix(f,cols)).all()
    for c in prior['features']:assert f[c].equals(pl.read_parquet(SOURCE,columns=[c])[c])
    f.write_parquet(OUT/'features.parquet')
    coverage=f.filter(pl.col('draft_known')==1).group_by('draft_year').agg(
        pl.len().alias('rows'),pl.col('player_id').n_unique().alias('players'),
        (pl.col('draft_school_class')!='').sum().alias('class_rows'),
        pl.col('draft_age_known').sum().alias('known_age_rows')).sort('draft_year').to_dicts()
    drift=known.group_by('player_id','draft_year').agg(
        (pl.col('draft_age_proxy').max()-pl.col('draft_age_proxy').min()).alias('age_range'))
    drift.filter(pl.col('age_range')>0).write_parquet(OUT/'approximate-age-drift.parquet')
    small=f.filter((pl.col('prior_debut')==0)&(pl.col('recent_all_pa')<150)&
        (pl.col('draft_year')==pl.col('origin_year'))&(pl.col('pick_number')<=15)&
        (pl.col('draft_age_known')==1)&(pl.col('draft_age_proxy')>=20)).sort('origin_year','pick_number')
    small.write_parquet(OUT/'first-season-older-top-draftees.parquet')
    keys=['draft_known','draft_age_known','draft_age_band','short_pro_sample','prior_debut']
    supports=[];cells=[]
    for c in prior['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=cols,expected_keys=te.select('row_id','horizon').iter_rows())
        for head,sub in [('pa',tr),('rate',tr.filter(pl.col('next_pa')>0))]:
            cnt=profile(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            supports.append(profile(te).select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1')
                .with_columns(pl.col('profile_players').fill_null(0),pl.lit(head).alias('head')))
        cells.append(dict(**c,draft_age_preflight=note))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    raw=pl.read_parquet(r.OUT/'counts.parquet');walks=[]
    for pid,y in FIXED:
        row=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).to_dicts();assert len(row)==1
        o=row[0];peers=f.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=pid)&
            (pl.col('prior_debut')==o['prior_debut'])&(pl.col('draft_known')==o['draft_known']))
        distance=sum(((pl.col(c)-o[c])/s)**2 for c,s in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25)])
        peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
        history=raw.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','bucket')
        walks.append(dict(origin=o,history=history.to_dicts(),peers=peers.select('player_id','player_name','age',
            'draft_year','pick_number','draft_school_class','draft_age_proxy','recent_all_pa','next_pa','next_value','distance').to_dicts()))
    write('source-cases.json',walks)
    lines=['# V42 pre-fit source walkthrough','',
        'Age at draft is an approximate season-age proxy, not a reconstructed school class. Source metadata and actual training profiles are separate checks. Future outcomes shown here explain cohort reasonability; they do not define model inputs or eligibility.','']
    for c in walks:
        o=c['origin'];lines.extend([f"## {o['player_name']} — {o['origin_year']}",'',
            f"Known age {o['age']}, unknown flag {o['age_unknown']}; dated draft {o['draft_year']}, pick {o['pick_number']}; class {o['draft_school_class'] or 'missing'}. Approximate draft age {o['draft_age_proxy']}; known/centered/low-exposure interaction: "+str([o[x] for x in ADDED])+'.','',
            '| Season | Bucket | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|'])
        for h in c['history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Origin-selected peers: '+json.dumps(c['peers'],ensure_ascii=False)+'.',''])
    lines.extend(['## First-season, older top picks with <150 recent pro PA','',
        'Draft year equals origin; age proxy >=20; pick <=15; never debuted; full source cohort, not a selection of successful players. These actual results do not guarantee comparable exposure or playing-time support. 2020 is a canceled minor season, not an ordinary first pro season.','',
        '| Origin | Players | Next-year MLB players | Total next-year MLB PA |','|---|---:|---:|---:|'])
    groups=small.group_by('origin_year').agg(pl.len().alias('players'),(pl.col('next_pa')>0).sum().alias('mlb_players'),pl.col('next_pa').sum().alias('actual_pa')).sort('origin_year').to_dicts()
    for q in groups:lines.append(f"| {q['origin_year']} | {q['players']} | {q['mlb_players']} | {q['actual_pa']} |")
    (OUT/'source-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    write('source-audit.json',dict(class_coverage=coverage,age_proxy_min=float(known['draft_age_proxy'].min()),
        age_proxy_max=float(known['draft_age_proxy'].max()),age_drift_players=int((drift['age_range']>0).sum()),
        maximum_age_drift=float(drift['age_range'].max()),older_first_season_groups=groups,protected_outcomes_used=False))
    paths=[SOURCE,base.OUT/'predictions.parquet',base.OUT/'preflight.json',base.OUT/'report.json',OUT/'features.parquet',
        OUT/'support.parquet',OUT/'source-audit.json',OUT/'source-cases.json',OUT/'source-walkthrough.md',
        r.ROOT/'docs/practical-hitter-draft-age-v42-contract.md',Path(__file__),
        r.ROOT/'src/universal_baseball/draft_age_representation.py',Path(scale.__file__)]
    write('preflight.json',dict(before_fitting=True,features=cols,old_features=prior['features'],removed_features=REMOVED,
        added_features=ADDED,cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False,
        source_walkthrough_status='pending'))
    print('35 folds prepared; 198 inputs; manual source review must precede fitting.',flush=True)


if __name__=='__main__':main()
