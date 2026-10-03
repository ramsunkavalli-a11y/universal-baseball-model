"""Reconstruct raw contact source, preserve league identity, audit actual folds."""
from pathlib import Path
import json
import polars as pl
import prepare_practical_hitter_v31 as r
import evaluate_hitter_2020_extension as base
from audit_hitter_contact_transfer_v40 import SHAPE,FIXED
from universal_baseball.hitter_contact_transfer import bucket,classify,materialize
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-contact-v41'
YEARS={2016,2017,2018,2019,2021,2022,2023,2024}
COLS=['season','level','league_id','game_pk','at_bat_index','batter','is_batted_ball','bb_type','hc_x','hc_y','stand']


def write(n,o):(OUT/n).write_text(json.dumps(o,indent=2,allow_nan=False,default=str),encoding='utf8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'preflight.json').exists():
        import sys
        assert '--source-repair' in sys.argv and (OUT/'preflight-before-source-bridge-repair.json').exists()
        assert not (OUT/'fit-report.json').exists()
    assert r.read(r.ROOT/'reports/generated/practical-hitter-contact-v40/report.json')['source_walkthrough_status']=='complete'
    assert r.read(base.OUT/'report.json')['player_walkthrough_status']=='complete'
    paths=[p for p in sorted((r.ROOT/'data/working/pbp-opportunity-foundation-v1').glob('season=*/level=*/terminal/*.parquet')) if int(p.parts[-4].split('=')[1]) in YEARS]
    assert paths
    hashes={str(p):sha256_file(p) for p in paths};frames=[];summaries=[]
    for y in sorted(YEARS):
        selected=[p for p in paths if f'season={y}' in p.parts]
        t=pl.concat([pl.read_parquet(p,columns=COLS) for p in selected],how='vertical_relaxed')
        assert set(t['season'])=={y}
        raw=len(t);t=t.unique();deduplicated=len(t)
        conflicts=t.group_by('season','game_pk','at_bat_index').len().filter(pl.col('len')>1)
        if len(conflicts):
            assert len(conflicts)<=100,'Review a material source conflict before continuing'
            t.join(conflicts.drop('len'),on=['season','game_pk','at_bat_index']).write_parquet(OUT/f'ambiguous-terminals-{y}.parquet')
            t=t.join(conflicts.drop('len'),on=['season','game_pk','at_bat_index'],how='anti')
        assert t.unique(['season','game_pk','at_bat_index']).height==len(t)
        q=classify(t.filter(pl.col('is_batted_ball').fill_null(False))).filter(pl.col('core_bin').is_not_null()&pl.col('batter').is_not_null())
        q=q.with_columns(pl.Series('bucket',[bucket(s['level'],s['league_id']) for s in q.select('level','league_id').iter_rows(named=True)]))
        a=q.group_by('season',pl.col('batter').alias('player_id'),'league_id','level','bucket','core_bin').len().rename({'len':'contacts'})
        frames.append(a);summaries.append(dict(season=y,raw_terminal_rows=raw,unique_terminal_rows=len(t),exact_duplicate_rows=raw-deduplicated,ambiguous_terminal_keys=len(conflicts),
            eligible_contacts=len(q),people=q['batter'].n_unique(),levels=sorted(q['level'].unique()),by_bucket=a.group_by('bucket').agg(pl.col('contacts').sum()).sort('bucket').to_dicts()))
        print(y,len(q),'contacts',flush=True)
    shape_path=SHAPE/'tables/contact_shape_player_season.parquet';hashes[str(shape_path)]=sha256_file(shape_path)
    assert hashes[str(shape_path)]==r.read(SHAPE/'report.json')['artifacts']['player_season']['file_sha256']
    m=pl.read_parquet(shape_path).filter(pl.col('level_group')=='MLB').rename({'level_group':'level','occurrence_count':'contacts'}).with_columns(pl.lit('MLB').alias('bucket'))
    assert set(m['season'])=={2021,2022,2023,2024} and m['contacts'].sum()==475972
    annual=pl.concat([*frames,m.select(frames[0].columns)],how='vertical_relaxed').sort('season','player_id','league_id','core_bin')
    assert annual.unique(['season','player_id','league_id','core_bin']).height==len(annual)
    annual.write_parquet(OUT/'league-contact-counts.parquet')
    fpath=base.SOURCE/'features.parquet';opath=r.OUT/'counts.parquet';features=pl.read_parquet(fpath);official=pl.read_parquet(opath)
    totals=annual.group_by('season','player_id','bucket').agg(pl.col('contacts').sum()).join(
        official.select('season','player_id','bucket','plate_appearances'),on=['season','player_id','bucket'],how='left',validate='1:1')
    unknown=totals.filter(pl.col('plate_appearances').is_null()|(pl.col('plate_appearances')<=0)|(pl.col('contacts')>pl.col('plate_appearances')))
    unknown.write_parquet(OUT/'unreconciled-player-leagues.parquet')
    valid=totals.join(unknown.select('season','player_id','bucket'),on=['season','player_id','bucket'],how='anti')
    counts=annual.join(valid.select('season','player_id','bucket'),on=['season','player_id','bucket'],how='semi').group_by('season','player_id','bucket','core_bin').agg(pl.col('contacts').sum())
    f,added=materialize(features,counts,official,r.BUCKETS);assert f.select(features.columns).equals(features)
    f.write_parquet(OUT/'features.parquet');prior=r.read(base.OUT/'preflight.json');cells=[]
    for c in prior['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=prior['features']+added,expected_keys=te.select('row_id','horizon').iter_rows())
        active=tr.filter(pl.col('next_pa')>0)
        people={b:active.filter(pl.col(f'shape_{b}_available')>0)['player_id'].n_unique() for b in r.BUCKETS}
        supported=[b for b,n in people.items() if n>0]
        usable=te.filter(pl.any_horizontal([pl.col(f'shape_{b}_available')>0 for b in supported])) if supported else te.head(0)
        cells.append(dict(**c,contact_preflight=note,active_contact_players_by_bucket=people,supported_buckets=supported,
            supported_test_row_ids=usable['row_id'].to_list(),contact_supported_rows=len(usable),active_training_rows=len(active)))
    cases=[]
    for pid,y in FIXED:
        o=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).to_dicts()[0]
        cases.append(dict(player_id=pid,origin_year=y,name=o['player_name'],row_id=o['row_id'],
            actual_contact_inputs={c:o[c] for c in added},shape_history=annual.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).to_dicts(),
            batting_history=official.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).to_dicts()))
    write('source-cases.json',cases)
    p=[fpath,opath,shape_path,OUT/'league-contact-counts.parquet',OUT/'features.parquet',base.OUT/'preflight.json',base.OUT/'predictions.parquet',
        Path(__file__),r.ROOT/'src/universal_baseball/hitter_contact_transfer.py',r.ROOT/'docs/practical-hitter-contact-v41-contract.md',
        r.ROOT/'docs/practical-hitter-contact-v41-source-amendment.md',OUT/'unreconciled-player-leagues.parquet']
    hashes.update({str(p):sha256_file(p) for p in p})
    coverage=f.group_by('origin_year').agg(pl.any_horizontal([pl.col(f'shape_{b}_available')>0 for b in r.BUCKETS]).sum().alias('contact_rows'),
        (pl.col('shape_MLB_available')>0).sum().alias('mlb_contact_rows'),pl.len().alias('rows')).sort('origin_year').to_dicts()
    excessive=[dict(bucket=b,rows=int((f[f'shape_{b}_coverage']>1.05).sum()),max_coverage=float(f[f'shape_{b}_coverage'].max())) for b in r.BUCKETS]
    write('preflight.json',dict(before_fitting=True,old_features=prior['features'],added_features=added,cells=cells,input_hashes=hashes,
        annual_source=summaries,universal_mlb_contacts=int(m['contacts'].sum()),coverage=coverage,coverage_outliers=excessive,
        unreconciled_player_league_seasons=len(unknown),unreconciled_contacts=int(unknown['contacts'].sum()),
        source_walkthrough_status='pending',evaluation_rows=30506,workload_fixed=True,protected_outcomes_used=False))
    print(json.dumps(dict(coverage=coverage,coverage_outliers=excessive,supported_rows=[(c['year'],c['fold'],c['contact_supported_rows']) for c in cells]),indent=2),flush=True)


if __name__=='__main__':main()
