import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_scoring import (
    build_baseline2_vs_richer_scoring_pair,
    relabel_richer_pair_model,
)
from universal_baseball.performance_season import ALL_CORE_BINS


def _profile() -> pl.DataFrame:
    probability = 1.0 / len(ALL_CORE_BINS)
    rows = []
    for player_id, applied in ((10, True), (11, False)):
        for index, core_bin in enumerate(ALL_CORE_BINS):
            richer = probability
            if applied and core_bin == ALL_CORE_BINS[2]:
                richer += 0.01
            if applied and core_bin == ALL_CORE_BINS[3]:
                richer -= 0.01
            rows.append(
                {
                    "player_id": player_id,
                    "core_bin": core_bin,
                    "baseline2_latent_probability": probability,
                    "richer_latent_probability": richer,
                    "richer_adjustment_applied": applied,
                }
            )
    return pl.DataFrame(rows)


def test_primary_pair_keeps_only_richer_applied_players() -> None:
    observed = build_baseline2_vs_richer_scoring_pair(_profile())

    assert set(observed.get_column("player_id")) == {10}
    assert observed.height == len(ALL_CORE_BINS)
    assert observed.get_column("baseline0_latent_probability").sum() == pytest.approx(1.0)
    assert observed.get_column("baseline1_latent_probability").sum() == pytest.approx(1.0)


def test_adapter_can_preserve_fallback_players_for_nonprimary_surfaces() -> None:
    observed = build_baseline2_vs_richer_scoring_pair(
        _profile(),
        richer_eligible_only=False,
    )

    assert set(observed.get_column("player_id")) == {10, 11}
    fallback = observed.filter(pl.col("player_id") == 11)
    assert fallback.get_column("baseline0_latent_probability").to_list() == pytest.approx(
        fallback.get_column("baseline1_latent_probability").to_list(), abs=1e-15
    )


def test_mixed_application_flag_within_player_fails_closed() -> None:
    broken = _profile().with_columns(
        pl.when((pl.col("player_id") == 10) & (pl.col("core_bin") == ALL_CORE_BINS[0]))
        .then(False)
        .otherwise(pl.col("richer_adjustment_applied"))
        .alias("richer_adjustment_applied")
    )

    with pytest.raises(ValueError, match="inconsistent within a player"):
        build_baseline2_vs_richer_scoring_pair(broken)


def test_relabel_richer_pair_model_is_stable() -> None:
    assert relabel_richer_pair_model("baseline0") == "baseline2"
    assert relabel_richer_pair_model("baseline1") == "batted_ball_richer"
    assert relabel_richer_pair_model("baseline2") == "baseline2"
    assert relabel_richer_pair_model("batted_ball_richer") == "batted_ball_richer"
    with pytest.raises(ValueError, match="unsupported"):
        relabel_richer_pair_model("other")
