from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value import (
    CONTACT_VALUE_REFERENCE_BIN,
    CONTACT_VALUE_REFERENCE_LEVEL,
    FROZEN_TERMINAL_OUTCOME_VALUES,
    apply_contact_value_residual,
    attach_frozen_terminal_values,
    build_contact_value_residual_player_training,
    fit_contact_value_baseline,
    fit_contact_value_residual_wls,
    predict_contact_value_baseline,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


def test_frozen_terminal_values_are_exhaustive_and_fail_closed() -> None:
    groups = list(FROZEN_TERMINAL_OUTCOME_VALUES)
    frame = pl.DataFrame({"terminal_outcome_group": groups})
    valued = attach_frozen_terminal_values(frame)

    assert valued.height == 9
    lookup = {
        row["terminal_outcome_group"]: row["terminal_value"]
        for row in valued.iter_rows(named=True)
    }
    assert lookup["HR"] == pytest.approx(1.3834396983847337)
    assert lookup["MULTI_OUT"] == pytest.approx(-0.8151401718384932)

    with pytest.raises(ValueError, match="unsupported terminal outcome groups"):
        attach_frozen_terminal_values(
            pl.DataFrame({"terminal_outcome_group": ["single_that_was_not_frozen"]})
        )
    with pytest.raises(ValueError, match="unsupported/null outcome group"):
        attach_frozen_terminal_values(
            pl.DataFrame({"terminal_outcome_group": [None]}, schema={"terminal_outcome_group": pl.String})
        )

    diagnostic = attach_frozen_terminal_values(
        pl.DataFrame(
            {"terminal_outcome_group": ["1B", None]},
            schema={"terminal_outcome_group": pl.String},
        ),
        require_supported=False,
    )
    assert diagnostic.get_column("terminal_value").null_count() == 1


def _synthetic_baseline_contacts() -> pl.DataFrame:
    bin_effect = {
        core_bin: 0.04 * index
        for index, core_bin in enumerate(CONTACT_CORE_BINS)
    }
    bin_effect[CONTACT_VALUE_REFERENCE_BIN] = 0.0
    level_effect = {"MLB": 0.0, "AAA": -0.17}
    rows: list[dict[str, object]] = []
    for level_group, level_value in level_effect.items():
        for core_bin in CONTACT_CORE_BINS:
            rows.append(
                {
                    "event_date": date(2021, 7, 10),
                    "contact_bin": core_bin,
                    "level_group": level_group,
                    "terminal_value": 0.31 + bin_effect[core_bin] + level_value,
                }
            )
    # This deliberately absurd post-cutoff row must have no effect on the fit.
    rows.append(
        {
            "event_date": date(2021, 7, 15),
            "contact_bin": CONTACT_VALUE_REFERENCE_BIN,
            "level_group": CONTACT_VALUE_REFERENCE_LEVEL,
            "terminal_value": 999.0,
        }
    )
    return pl.DataFrame(rows)


def test_contact_value_baseline_is_cutoff_safe_additive_ols_with_fixed_references() -> None:
    cutoff = date(2021, 7, 15)
    fitted = fit_contact_value_baseline(_synthetic_baseline_contacts(), cutoff_date=cutoff)

    assert fitted.fitted_event_count == 20
    assert fitted.max_training_event_date == date(2021, 7, 10)
    assert fitted.intercept == pytest.approx(0.31, abs=1e-10)
    assert fitted.contact_bin_effects[CONTACT_VALUE_REFERENCE_BIN] == 0.0
    assert fitted.level_group_effects[CONTACT_VALUE_REFERENCE_LEVEL] == 0.0
    assert fitted.level_group_effects["AAA"] == pytest.approx(-0.17, abs=1e-10)
    assert fitted.contact_bin_effects["PULL_LD"] == pytest.approx(
        0.04 * CONTACT_CORE_BINS.index("PULL_LD"),
        abs=1e-10,
    )

    target = pl.DataFrame(
        {
            "contact_bin": ["IFFB", "OPPO_GB"],
            "level_group": ["MLB", "AAA"],
        }
    )
    predicted = predict_contact_value_baseline(target, fitted)
    assert predicted.get_column("baseline_contact_value").to_list() == pytest.approx(
        [
            0.31,
            0.31 + 0.04 * CONTACT_CORE_BINS.index("OPPO_GB") - 0.17,
        ],
        abs=1e-10,
    )

    with pytest.raises(ValueError, match="unfitted level group"):
        predict_contact_value_baseline(
            pl.DataFrame({"contact_bin": ["IFFB"], "level_group": ["AA"]}),
            fitted,
        )


def test_contact_value_baseline_fails_when_design_is_not_identifiable() -> None:
    # Every non-MLB level event is one contact bin and MLB never observes it,
    # so the level and bin dummy are exactly collinear.
    rows: list[dict[str, object]] = []
    for core_bin in CONTACT_CORE_BINS:
        if core_bin == "OPPO_GB":
            level_group = "AAA"
        else:
            level_group = "MLB"
        rows.append(
            {
                "event_date": date(2021, 7, 1),
                "contact_bin": core_bin,
                "level_group": level_group,
                "terminal_value": 0.1,
            }
        )
    with pytest.raises(ValueError, match="rank deficient"):
        fit_contact_value_baseline(pl.DataFrame(rows), cutoff_date=date(2021, 7, 15))


def test_contact_value_residual_player_aggregation_and_wls_recover_two_coefficients() -> None:
    # True model: residual = 2*zEV - 1*zSS. Repeated event rows encode the
    # frozen WLS weight: supported future contacts per player.
    player_specs = [
        (1, 1.0, 0.0, 2.0, 3),
        (2, 0.0, 1.0, -1.0, 4),
        (3, 1.0, 1.0, 1.0, 5),
        (4, -1.0, 1.0, -3.0, 2),
    ]
    rows: list[dict[str, object]] = []
    for player_id, z_ev, z_ss, residual, count in player_specs:
        rows.extend(
            {
                "player_id": player_id,
                "z_mean_exit_velocity": z_ev,
                "z_sweet_spot_share": z_ss,
                "contact_value_residual": residual,
            }
            for _ in range(count)
        )
    aggregated = build_contact_value_residual_player_training(pl.DataFrame(rows))
    assert aggregated.get_column("supported_future_target_contacts").sum() == 14

    fitted = fit_contact_value_residual_wls(aggregated)
    assert fitted.beta_mean_exit_velocity == pytest.approx(2.0, abs=1e-12)
    assert fitted.beta_sweet_spot_share == pytest.approx(-1.0, abs=1e-12)
    assert fitted.fitted_player_count == 4
    assert fitted.fitted_future_contact_count == 14
    assert fitted.determinant > 0


def test_contact_value_residual_wls_fails_closed_on_rank_deficiency() -> None:
    frame = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "z_mean_exit_velocity": [1.0, 2.0, 3.0],
            "z_sweet_spot_share": [2.0, 4.0, 6.0],
            "mean_future_contact_value_residual": [0.1, 0.2, 0.3],
            "supported_future_target_contacts": [10, 20, 30],
        }
    )
    with pytest.raises(ValueError, match="full-rank"):
        fit_contact_value_residual_wls(frame)


def test_contact_value_residual_application_has_exact_zero_fallback() -> None:
    player_training = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "z_mean_exit_velocity": [1.0, 0.0, -1.0],
            "z_sweet_spot_share": [0.0, 1.0, 1.0],
            "mean_future_contact_value_residual": [2.0, -1.0, -3.0],
            "supported_future_target_contacts": [10, 10, 10],
        }
    )
    fitted = fit_contact_value_residual_wls(player_training)
    features = pl.DataFrame(
        {
            "player_id": [10, 11, 12],
            "tracked_bbe_eligible": [True, False, True],
            "z_mean_exit_velocity": [0.5, 99.0, None],
            "z_sweet_spot_share": [1.0, 99.0, 0.2],
        }
    )
    applied = apply_contact_value_residual(features, fitted)
    rows = {row["player_id"]: row for row in applied.iter_rows(named=True)}

    assert rows[10]["contact_value_residual_applies"] is True
    assert rows[10]["player_contact_value_residual"] == pytest.approx(0.0, abs=1e-12)
    assert rows[11]["contact_value_residual_applies"] is False
    assert rows[11]["player_contact_value_residual"] == 0.0
    assert rows[12]["contact_value_residual_applies"] is False
    assert rows[12]["player_contact_value_residual"] == 0.0
