import polars as pl
import pytest

from universal_baseball.hitter_available_season_history import rebuild, AFFILIATED
from universal_baseball.practical_hitter_v30 import EVENTS


def fixture():
    source = dict(row_id=7,origin_year=2022,player_id=1,draft_rank=.9,
        age=17.,stage='Inactive / unknown',last_stat_gap=3,scout_rank_score_0=.95,
        milb_canceled_2=1,MLB_1_pa=10.,next_pa=0,next_value=0.)
    for b in AFFILIATED:
        for k in range(3):
            for field in ['pa','present',*EVENTS]:
                source[f'{b}_{k}_{field}']=0.
        for field in ['pa',*EVENTS]:
            source[f'pooled_{b}_{field}']=0.
        source['games_pool_'+b]=0.
        source['role_pool_'+b]=4.
    for k in range(3):
        source[f'minor_pa_{k}']=0.
        source[f'games_minor_{k}']=0.
        source[f'role_minor_{k}']=4.
    source['draft_rank_low_exposure']=0.
    counts,games=[],[]
    for pid,year,b,pa,gp in [(1,2019,'AAA',100,25),(1,2020,'MLB',10,2),
                            (2,2021,'AAA',30,7),(2,2022,'AAA',70,16)]:
        c=dict(player_id=pid,season=year,bucket=b,plate_appearances=pa)
        for _,(num,den,_) in EVENTS.items():
            c.setdefault(num,1)
            c.setdefault(den,pa)
        counts.append(c)
        games.append(dict(player_id=pid,season=year,bucket=b,plate_appearances=pa,games_played=gp))
    return pl.DataFrame([source]),pl.DataFrame(counts),pl.DataFrame(games)


def test_individual_absence_remains_zero_with_calendar_age_and_mlb_unchanged():
    f,c,g=fixture()
    out,dates,_=rebuild(f,c,g,available=True)
    row=out.row(0,named=True)
    assert [row['AAA_'+str(k)+'_pa'] for k in range(3)]==[0.,0.,100.]
    assert row['pooled_AAA_pa']==60.
    assert row['games_pool_AAA']==15.
    assert row['role_pool_AAA']==100/25
    assert row['draft_rank_low_exposure']==.9*100/210
    assert dates['affiliated_source_year_2'][0]==2019
    for name in ['age','stage','last_stat_gap','scout_rank_score_0','milb_canceled_2','MLB_1_pa','next_pa','next_value']:
        assert row[name]==f[name][0]


def test_future_counts_do_not_change_history():
    f,c,g=fixture()
    out,_,_=rebuild(f,c,g,available=True)
    future_c=c.filter(pl.col('player_id')==1).head(1).with_columns(pl.lit(2023,dtype=pl.Int64).alias('season'),pl.lit(1000,dtype=pl.Int64).alias('plate_appearances'))
    future_g=g.filter(pl.col('player_id')==1).head(1).with_columns(pl.lit(2023,dtype=pl.Int64).alias('season'),pl.lit(1000,dtype=pl.Int64).alias('plate_appearances'))
    changed,_,_=rebuild(f,pl.concat([c,future_c]),pl.concat([g,future_g]),available=True)
    assert out.equals(changed)


def test_duplicate_and_unmatched_games_are_not_accepted():
    f,c,g=fixture()
    with pytest.raises(ValueError,match='Duplicate'):
        rebuild(f,pl.concat([c,c.head(1)]),g,available=True)
    with pytest.raises(ValueError,match='Counts and games disagree'):
        rebuild(f,c,g.with_columns((pl.col('plate_appearances')+1).alias('plate_appearances')),available=True)
