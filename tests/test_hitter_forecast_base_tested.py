from datetime import date
import polars as pl
import pytest
from universal_baseball.hitter_forecast_base import population
from universal_baseball.hitter_forecast_base_tested import tested_base_inputs as build


def sources():
    snapshot = pl.DataFrame([dict(row_id=1, origin_year=2025, player_id=10, age=23., snapshot_level='AAA')])
    stints = pl.DataFrame([dict(season=y, player_id=10, plate_appearances=pa, team_id=team,
        reported_age=float(y-2002), player_name='Split Player', position='9', sport_id=sport)
        for y in [2023,2024,2025] for pa,team,sport in [(100,1,1),(200,2,11)]])
    counts = pl.DataFrame([dict(season=y, player_id=10, bucket=bucket, plate_appearances=pa,
        strike_outs=20, unintentional_walks=10, hit_by_pitch=1, home_runs=5,
        babip_hits=25, babip_opportunities=60, doubles=5, triples=1)
        for y in [2023,2024,2025] for bucket,pa in [('MLB',100),('AAA',200)]])
    values = pl.DataFrame([dict(season=y, player_id=10, mlb_pa=100,
        component_war=1., schedule_fraction=1., league_pa=180000) for y in [2023,2024,2025]])
    debut = pl.DataFrame([dict(player_id=10, mlb_debut_date=date(2023,5,1))])
    roster = pl.DataFrame([dict(season=2025, player_id=10, team_id=1)])
    return snapshot,stints,counts,values,debut,roster


def test_all_mlb_exposure_in_split_level_seasons_and_no_forecast_labels():
    out = build(*sources(), source_cutoff=2025)
    r = out.row(0,named=True)
    assert r['career_mlb_observed_pa']==300 and r['pa_0']==100 and r['minor_pa_0']==200
    assert r['stage']=='Current MLB' and r['elapsed']==2 and r['on_40man']==1
    assert not any(c.startswith('next_') for c in out.columns)


@pytest.mark.parametrize('which',[0,1,2,3,4,5])
def test_future_predictor_evidence_rejected(which):
    args = list(sources())
    if which==0:
        args[which]=args[which].with_columns(pl.lit(2026).alias('origin_year'))
    elif which==4:
        args[which]=args[which].with_columns(pl.lit(date(2026,5,1)).alias('mlb_debut_date'))
    else:
        args[which]=args[which].with_columns(pl.lit(2026).alias('season'))
    with pytest.raises(ValueError):
        build(*args,source_cutoff=2025)


def test_missing_quality_is_not_zero_and_duplicate_count_is_not_extra_exposure():
    args = list(sources()); args[3]=args[3].filter(pl.col('season')!=2025)
    with pytest.raises(ValueError): build(*args,source_cutoff=2025)
    args=list(sources()); args[2]=pl.concat([args[2],args[2].head(1)])
    with pytest.raises(ValueError): build(*args,source_cutoff=2025)


def test_special_canceled_origin_cannot_be_silently_treated_as_a_normal_season():
    args=list(sources()); args[0]=args[0].with_columns(pl.lit(2020).alias('origin_year'))
    with pytest.raises(ValueError,match='Canceled-origin'):
        build(*args,source_cutoff=2025)


def test_current_snapshot_wins_and_inactive_recent_exit_is_retained():
    snapshots=pl.DataFrame([dict(snapshot_year=2025,player_id=10,age_years=23.,as_of_level_group='AAA')])
    exits=pl.DataFrame([dict(origin_year=2024,player_id=pid,age=age,entry_year=entry,window_complete=True)
        for pid,age,entry in [(10,50.,2024),(11,26.,2021),(12,35.,2019)]])
    out=population(snapshots,exits,source_cutoff=2025)
    assert set(out['player_id'])=={10,11}
    a,b=out.sort('player_id').to_dicts()
    assert a['age']==23 and a['membership_source']=='saved_hitter_snapshot'
    assert b['age']==27 and b['snapshot_level']=='INACTIVE'
    assert b['membership_source']=='continued_recent_debut_exit'
