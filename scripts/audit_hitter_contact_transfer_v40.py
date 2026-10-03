"""Audit estimand/coverage of old contact wins versus the broad MLB goal."""
from pathlib import Path
import json
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-contact-v40'
OLD=r.ROOT/'reports/generated/hitter-gradient-dataset-v1'
EARLY=Path('C:/Users/ramav/Documents/Codex/2026-08-23/do/work/universal-baseball-model')
SHAPE=EARLY/'reports/generated/hitter-v2-stage2b-contact-shape-source'
FIXED=[(592450,2016),(592450,2024),(691026,2023),(668715,2022),(701762,2024),(666158,2023),(805367,2024),(641355,2016)]


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False,default=str),encoding='utf8')


def shape_totals(shape):
    assert set(shape['level_group'])<= {'MLB','a','a+','aa','aaa','rk'}
    return shape.group_by('season','player_id').agg(pl.col('occurrence_count').sum().alias('shape_all'),
        pl.col('occurrence_count').filter(pl.col('level_group')=='MLB').sum().alias('shape_mlb'),
        pl.col('occurrence_count').filter(pl.col('level_group')!='MLB').sum().alias('shape_minor'))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'audit.json').exists():
        import sys
        assert '--repair-mlb-label' in sys.argv
        assert (OUT/'audit-before-level-case-repair.json').exists()
        assert (OUT/'source-availability-before-level-case-repair.parquet').exists()
    old_report=r.read(OLD/'report.json');shape_report=r.read(SHAPE/'report.json')
    p=OLD/'tables/player-season-features.parquet';m=OLD/'tables/modeling-rows.parquet';q=SHAPE/'tables/contact_shape_player_season.parquet'
    assert sha256_file(p)==old_report['artifacts']['player_features']['file_sha256']
    assert sha256_file(m)==old_report['artifacts']['modeling_rows']['file_sha256']
    assert sha256_file(q)==shape_report['artifacts']['player_season']['file_sha256']
    old=pl.read_parquet(p);meta=pl.read_parquet(m,columns=['origin_year','player_id','source_level','target_source_level','target_contacts'])
    shape=pl.read_parquet(q);assert old.unique(['season','player_id']).height==len(old)
    assert set(old['season'])==set(shape['season'])=={2021,2022,2023,2024}
    assert shape.unique(['season','league_id','player_id','core_bin']).height==len(shape)
    assert (shape['occurrence_count']>=0).all()
    wide=shape_totals(shape)
    base_path=r.ROOT/'reports/generated/hitter-2020-cohort/features.parquet';base=pl.read_parquet(base_path)
    f=base.join(old.select(pl.col('season').alias('origin_year'),'player_id',pl.col('source_level').alias('legacy_contact_level'),
        'materialized_contacts','opponent_context_known_rate','park_factor_known_rate'),on=['origin_year','player_id'],how='left',validate='1:1')
    f=f.join(wide.rename({'season':'origin_year'}),on=['origin_year','player_id'],how='left',validate='1:1')
    assert f.select(base.columns).equals(base)
    def summary(g):return dict(rows=len(g),people=g['player_id'].n_unique(),old_contact_rows=g['materialized_contacts'].drop_nulls().len(),
        old_contact_sum=int(g['materialized_contacts'].sum() or 0),universal_shape_rows=g['shape_all'].drop_nulls().len(),
        universal_mlb_shape_rows=int((g['shape_mlb'].fill_null(0)>0).sum()),universal_minor_shape_rows=int((g['shape_minor'].fill_null(0)>0).sum()),
        future_mlb_active_rows=int((g['next_pa']>0).sum()),future_mlb_active_with_old=int(g.filter((pl.col('next_pa')>0)&pl.col('materialized_contacts').is_not_null()).height),
        future_mlb_active_with_shape=int(g.filter((pl.col('next_pa')>0)&pl.col('shape_all').is_not_null()).height))
    coverage=[]
    for y in r.YEARS:
        for stage,g in [('all',f.filter(pl.col('origin_year')==y)),*[(stage,f.filter((pl.col('origin_year')==y)&(pl.col('stage')==stage))) for stage in sorted(f['stage'].unique())]]:
            coverage.append(dict(origin_year=y,stage=stage,**summary(g)))
    pre_path=r.ROOT/'reports/generated/practical-hitter-v34/preflight.json';cells=[]
    for c in r.read(pre_path)['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        assert not set(tr['player_id'])&set(te['player_id']) and tr['target_year'].max()<=c['year']
        cells.append(dict(year=c['year'],fold=c['fold'],training=summary(tr),test=summary(te)))
    counts=pl.read_parquet(r.OUT/'counts.parquet');cases=[]
    for pid,y in FIXED:
        a=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(a)==1,(pid,y);o=a.to_dicts()[0]
        peers=f.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=pid)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
        distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1)])
        peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
        cases.append(dict(player_id=pid,player_name=o['player_name'],origin_year=y,row_id=o['row_id'],
            inputs={c:o[c] for c in ['age','stage','source_position','pa_0','AAA_0_pa','AA_0_pa','draft_known','pick_number',
                'legacy_contact_level','materialized_contacts','opponent_context_known_rate','park_factor_known_rate','shape_all','shape_mlb','shape_minor']},
            batting_history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
            shape_history=shape.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','league_id','core_bin').to_dicts(),
            old_feature_history=old.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).select('season','source_level','contacts','materialized_contacts',
                'opponent_context_known_rate','park_factor_known_rate','park_effect__hr','share__PULL_OFFB','contact_result__PULL_OFFB__HR').to_dicts(),
            peers=peers.select('player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','materialized_contacts','shape_mlb','shape_minor','distance').to_dicts()))
    f.select('row_id','origin_year','player_id','stage','legacy_contact_level','materialized_contacts','shape_all','shape_mlb','shape_minor').write_parquet(OUT/'source-availability.parquet')
    fold_path=OLD/'tables/fold-manifest.parquet';legacy_folds=pl.read_parquet(fold_path)
    assert sha256_file(fold_path)==old_report['artifacts']['fold_manifest']['file_sha256']
    overlaps=[]
    for y in sorted(legacy_folds['evaluation_origin'].unique()):
        tr=legacy_folds.filter((pl.col('evaluation_origin')==y)&(pl.col('role')=='training'))
        te=legacy_folds.filter((pl.col('evaluation_origin')==y)&(pl.col('role')=='evaluation'))
        overlaps.append(dict(origin_year=y,train_players=tr['player_id'].n_unique(),test_players=te['player_id'].n_unique(),
            overlapping_people=len(set(tr['player_id'])&set(te['player_id']))))
    paths=[p,m,q,fold_path,OLD/'report.json',SHAPE/'report.json',base_path,pre_path,r.OUT/'counts.parquet',Path(__file__),r.ROOT/'docs/practical-hitter-contact-transfer-v40-contract.md']
    write('cases.json',cases)
    write('audit.json',dict(input_hashes={str(p):sha256_file(p) for p in paths},old_features_rows=len(old),old_modeling_rows=len(meta),
        old_source_levels=sorted(old['source_level'].unique()),old_target_levels=sorted(meta['target_source_level'].unique()),
        old_target_all_have_positive_contacts=bool((meta['target_contacts']>0).all()),old_fold_overlap=overlaps,
        old_estimand='Next-year minor-league contact outcomes among players with observed future contact; not future MLB batting or arrival.',
        universal_shape_seasons=sorted(shape['season'].unique()),universal_shape_levels=sorted(shape['level_group'].unique()),
        universal_shape_rows=len(shape),universal_shape_events=int(shape['occurrence_count'].sum()),
        coverage=coverage,cells=cells,source_walkthrough_status='pending',no_new_fit_or_score=True,protected_outcomes_used=False))
    print(json.dumps(dict(old_source_levels=sorted(old['source_level'].unique()),old_target_levels=sorted(meta['target_source_level'].unique()),
        coverage=[c for c in coverage if c['stage'] in ['all','Current MLB']],fixed_cases=len(cases)),indent=2),flush=True)


if __name__=='__main__':main()
