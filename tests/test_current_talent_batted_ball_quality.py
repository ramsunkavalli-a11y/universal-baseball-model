from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_quality import (
    apply_batted_ball_quality_residual,
    build_batted_ball_quality_features,
    project_complete_tracked_bbe,
)
from universal_baseball.performance_season import ALL_CORE_BINS, CONTACT_CORE_BINS


def _raw(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows).with_columns(
        pl.col("game_pk").cast(pl.String),
        pl.col("batter").cast(pl.String),
        pl.col("at_bat_number").cast(pl.String),
        pl.col("pitch_number").cast(pl.String),
        pl.col("launch_speed").cast(pl.String),
        pl.col("launch_angle").cast(pl.String),
    )


def _result_row(
    *,
    game_date: str,
    game_pk: int,
    batter: int,
    at_bat_number: int,
    pitch_number: int = 1,
    launch_speed: float | None = 95.0,
    launch_angle: float | None = 20.0,
    events: str | None = "single",
    pitch_type: str = "X",
    des: str = "Batter singles on a line drive to center field.",
) -> dict[str, object]:
    return {
        "game_date": game_date,
        "game_pk": game_pk,
        "batter": batter,
        "at_bat_number": at_bat_number,
        "pitch_number": pitch_number,
        "events": events,
        "type": pitch_type,
        "des": des,
        "launch_speed": launch_speed,
        "launch_angle": launch_angle,
    }


def _b2_profile(player_ids: tuple[int, ...] = (10, 11)) -> pl.DataFrame:
    weights = {
        "BB_HBP": 0.10,
        "K": 0.20,
        "IFFB": 0.05,
        "PULL_OFFB": 0.08,
        "CENTER_OFFB": 0.07,
        "OPPO_OFFB": 0.05,
        "PULL_LD": 0.08,
        "CENTER_LD": 0.09,
        "OPPO_LD": 0.06,
        "PULL_GB": 0.09,
        "CENTER_GB": 0.08,
        "OPPO_GB": 0.05,
    }
    assert abs(sum(weights.values()) - 1.0) < 1e-12
    return pl.DataFrame(
        [
            {
                "player_id": player_id,
                "core_bin": core_bin,
                "baseline2_latent_probability": weights[core_bin],
            }
            for player_id in player_ids
            for core_bin in ALL_CORE_BINS
        ]
    )


def _coefficients(*, nonzero: bool) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "core_bin": core_bin,
                "beta_mean_exit_velocity": 0.20 if nonzero and core_bin == "PULL_LD" else 0.0,
                "beta_sweet_spot_share": 0.15 if nonzero and core_bin == "CENTER_LD" else 0.0,
            }
            for core_bin in CONTACT_CORE_BINS
        ]
    )


def test_project_complete_tracked_bbe_keeps_only_complete_result_bbe() -> None:
    raw = _raw(
        [
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                launch_speed=101.5,
                launch_angle=20.0,
            ),
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=2,
                launch_speed=88.0,
                launch_angle=None,
            ),
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=11,
                at_bat_number=1,
                launch_speed=90.0,
                launch_angle=40.0,
                events="field_out",
            ),
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=12,
                at_bat_number=1,
                launch_speed=99.0,
                launch_angle=15.0,
                events=None,
            ),
        ]
    )

    observed = project_complete_tracked_bbe(raw)

    assert observed.height == 2
    assert observed.get_column("player_id").to_list() == [10, 11]
    assert observed.get_column("sweet_spot").to_list() == [True, False]


def test_complete_ev_la_foul_contact_is_not_a_bbe() -> None:
    raw = _raw(
        [
            _result_row(
                game_date="2021-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=7,
                pitch_number=4,
                launch_speed=72.0,
                launch_angle=-12.0,
                events=None,
                pitch_type="S",
                des="Batter hits a foul ball.",
            ),
            _result_row(
                game_date="2021-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=7,
                pitch_number=6,
                launch_speed=103.0,
                launch_angle=18.0,
                events="double",
                pitch_type="X",
                des="Batter doubles on a line drive to left field.",
            ),
        ]
    )

    observed = project_complete_tracked_bbe(raw)

    assert observed.height == 1
    row = observed.row(0, named=True)
    assert row["pitch_number"] == 6
    assert row["launch_speed"] == pytest.approx(103.0)


def test_result_producing_bunt_is_excluded_from_richer_contact_evidence() -> None:
    raw = _raw(
        [
            _result_row(
                game_date="2021-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=2,
                launch_speed=42.0,
                launch_angle=-35.0,
                events="sac_bunt",
                des="Batter out on a sacrifice bunt, pitcher to first baseman.",
            ),
            _result_row(
                game_date="2021-06-02",
                game_pk=2,
                batter=10,
                at_bat_number=1,
                pitch_number=3,
                launch_speed=96.0,
                launch_angle=16.0,
                events="single",
                des="Batter singles on a line drive to center field.",
            ),
        ]
    )

    observed = project_complete_tracked_bbe(raw)

    assert observed.height == 1
    assert observed.row(0, named=True)["game_pk"] == 2


def test_project_complete_tracked_bbe_rejects_duplicate_pitch_key() -> None:
    row = _result_row(
        game_date="2023-06-01",
        game_pk=1,
        batter=10,
        at_bat_number=1,
        pitch_number=3,
        launch_speed=100.0,
        launch_angle=20.0,
    )
    raw = _raw([row, {**row, "launch_speed": 99.0, "launch_angle": 19.0}])

    with pytest.raises(ValueError, match=r"duplicate result-producing EV\+LA rows"):
        project_complete_tracked_bbe(raw)


def test_project_complete_tracked_bbe_rejects_multiple_result_bbe_in_same_pa() -> None:
    raw = _raw(
        [
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=2,
                events="single",
            ),
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=3,
                events="double",
            ),
        ]
    )

    with pytest.raises(ValueError, match="multiple result-producing BBE"):
        project_complete_tracked_bbe(raw)


def test_features_exclude_cutoff_and_future_rows_and_apply_threshold() -> None:
    raw = _raw(
        [
            _result_row(
                game_date="2023-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                launch_speed=100.0,
                launch_angle=20.0,
            ),
            _result_row(
                game_date="2023-06-20",
                game_pk=2,
                batter=10,
                at_bat_number=1,
                launch_speed=90.0,
                launch_angle=0.0,
            ),
            _result_row(
                game_date="2023-07-01",
                game_pk=3,
                batter=10,
                at_bat_number=1,
                launch_speed=120.0,
                launch_angle=25.0,
            ),
            _result_row(
                game_date="2023-07-02",
                game_pk=4,
                batter=10,
                at_bat_number=1,
                launch_speed=120.0,
                launch_angle=25.0,
            ),
        ]
    )
    tracked = project_complete_tracked_bbe(raw)

    features = build_batted_ball_quality_features(
        tracked,
        cutoff=date(2023, 7, 1),
        min_complete_tracked_bbe=2,
    )

    row = features.row(0, named=True)
    assert row["raw_complete_tracked_bbe"] == 2
    assert row["last_tracked_bbe_date"] == date(2023, 6, 20)
    assert row["tracked_bbe_eligible"] is True
    assert 90.0 < row["recency_weighted_mean_exit_velocity"] < 100.0
    assert 0.0 < row["recency_weighted_sweet_spot_share"] < 1.0


def test_features_use_raw_count_for_primary_eligibility() -> None:
    raw = _raw(
        [
            _result_row(
                game_date=f"2023-06-{day:02d}",
                game_pk=day,
                batter=10,
                at_bat_number=1,
                launch_speed=95.0,
                launch_angle=20.0,
            )
            for day in range(1, 21)
        ]
    )
    tracked = project_complete_tracked_bbe(raw)

    features = build_batted_ball_quality_features(tracked, cutoff=date(2023, 7, 1))

    row = features.row(0, named=True)
    assert row["raw_complete_tracked_bbe"] == 20
    assert row["effective_complete_tracked_bbe"] < 20.0
    assert row["tracked_bbe_eligible"] is True


def test_zero_residual_coefficients_leave_b2_exactly_unchanged() -> None:
    features = pl.DataFrame(
        {
            "player_id": [10],
            "tracked_bbe_eligible": [True],
            "z_mean_exit_velocity": [1.2],
            "z_sweet_spot_share": [-0.3],
        }
    )

    observed = apply_batted_ball_quality_residual(
        _b2_profile((10,)),
        features,
        _coefficients(nonzero=False),
    )

    assert observed.get_column("richer_adjustment_applied").all()
    assert observed.get_column("baseline2_latent_probability").to_list() == pytest.approx(
        observed.get_column("richer_latent_probability").to_list(), abs=1e-15
    )


def test_residual_keeps_walk_strikeout_and_total_contact_mass_fixed() -> None:
    features = pl.DataFrame(
        {
            "player_id": [10],
            "tracked_bbe_eligible": [True],
            "z_mean_exit_velocity": [1.0],
            "z_sweet_spot_share": [1.0],
        }
    )
    observed = apply_batted_ball_quality_residual(
        _b2_profile((10,)),
        features,
        _coefficients(nonzero=True),
    )

    lookup = {row["core_bin"]: row for row in observed.iter_rows(named=True)}
    assert lookup["BB_HBP"]["richer_latent_probability"] == lookup["BB_HBP"][
        "baseline2_latent_probability"
    ]
    assert lookup["K"]["richer_latent_probability"] == lookup["K"][
        "baseline2_latent_probability"
    ]
    b2_contact_mass = sum(
        lookup[core_bin]["baseline2_latent_probability"] for core_bin in CONTACT_CORE_BINS
    )
    richer_contact_mass = sum(
        lookup[core_bin]["richer_latent_probability"] for core_bin in CONTACT_CORE_BINS
    )
    assert richer_contact_mass == pytest.approx(b2_contact_mass, abs=1e-15)
    assert sum(row["richer_latent_probability"] for row in lookup.values()) == pytest.approx(
        1.0, abs=1e-15
    )
    assert lookup["PULL_LD"]["richer_latent_probability"] > lookup["PULL_LD"][
        "baseline2_latent_probability"
    ]


def test_missing_or_ineligible_features_fall_back_exactly_to_b2() -> None:
    features = pl.DataFrame(
        {
            "player_id": [10],
            "tracked_bbe_eligible": [False],
            "z_mean_exit_velocity": [1.0],
            "z_sweet_spot_share": [1.0],
        }
    )
    observed = apply_batted_ball_quality_residual(
        _b2_profile((10, 11)),
        features,
        _coefficients(nonzero=True),
    )

    assert not observed.get_column("richer_adjustment_applied").any()
    assert observed.get_column("baseline2_latent_probability").to_list() == pytest.approx(
        observed.get_column("richer_latent_probability").to_list(), abs=1e-15
    )
    assert set(observed.get_column("richer_method").to_list()) == {"baseline2_fallback"}
