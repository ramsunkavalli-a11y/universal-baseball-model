import polars as pl
from universal_baseball.hitter_talent_opportunity import rate_membership, estimable


def fixture():
    return pl.DataFrame(dict(row_id=[1,2,3,4,5,6], player_id=[10,20,10,30,40,50],
        origin_year=[2017,2017,2018,2018,2019,2020], target_year=[2018,2018,2019,2019,2020,2021],
        outer_fold=[1,2,1,3,3,2], next_pa=[200,400,500,0,100,300]))


def test_generated_talent_excludes_all_held_player_seasons_and_future_labels():
    f = fixture()
    selected = rate_membership(f, 2019, 1)
    assert selected['row_id'].to_list() == [2]
    assert 10 not in selected['player_id']
    changed = f.with_columns(pl.when(pl.col('target_year') > 2019).then(750)
        .otherwise(pl.col('next_pa')).alias('next_pa'))
    assert rate_membership(changed, 2019, 1).equals(selected)


def test_shortened_target_is_not_used_and_sparse_history_is_not_an_estimate():
    assert 5 not in rate_membership(fixture(), 2021, 1)['row_id'].to_list()
    assert not estimable(rate_membership(fixture(), 2019, 1))
    assert not estimable(fixture().head(0))
