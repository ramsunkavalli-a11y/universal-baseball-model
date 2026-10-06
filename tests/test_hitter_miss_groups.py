import polars as pl
import pytest

from universal_baseball.hitter_miss_groups import account, groups, FIELDS


def fixture():
    q = pl.DataFrame(dict(row_id=[1, 2, 3], player_id=[11, 12, 13], prior_debut=[0, 1, 1],
                          pa_0=[0, 0, 60], age=[22., 30., 28.], status_retired=[0, 0, 0], status_hard_unavailable=[0, 0, 0]))
    f = pl.DataFrame({n: [0., 0., 0.] for n in FIELDS if n != "row_id"}).with_columns(pl.Series("row_id", [1, 2, 3]))
    f = f.with_columns(pl.Series("work_1", [0., 550., 400.]), pl.Series("AAA_0_pa", [300., 0., 0.]))
    m = pl.DataFrame(dict(row_id=[1, 2, 3], observation_state=["no_captured_medical_entry"] * 3, recent_history_coverage_complete=[True] * 3))
    return q, f, m


def test_future_results_do_not_set_group():
    q, f, m = fixture()
    expected = groups(q, f, m)["career_group"]
    assert expected.to_list() == ["no_debut_upper_minors", "established_MLB_gap", "established_brief_current_MLB"]
    assert groups(q.with_columns(pl.lit(700).alias("next_pa")), f, m)["career_group"].equals(expected)


def test_signed_accounting_keeps_zero_outcomes():
    f = pl.DataFrame(dict(observation_pa=[200., 50.], next_pa=[100., 0.], observation_rate=[3., -1.],
                          origin_replacement_rate=[.003, .003], observation_value=[1.6, .06666666666666667],
                          actual_relative_value=[.9, 0.]))
    r = account(f)
    assert r["value_PA_term"][0] == pytest.approx(.8)
    assert r["value_rate_term"][0] == pytest.approx(-.1)
    assert r["value_rate_term"][1] == 0
    with pytest.raises(ValueError):
        account(f.with_columns(pl.lit(999.).alias("observation_value")))


def test_release_not_retirement_and_missing_history_not_health():
    q, f, m = fixture()
    f = f.with_columns(pl.Series("status_released", [0., 1., 0.]))
    g = groups(q, f, m)
    assert g["opportunity_group"][1] == "reported_release"
    assert "healthy" not in g["opportunity_group"].to_list()
