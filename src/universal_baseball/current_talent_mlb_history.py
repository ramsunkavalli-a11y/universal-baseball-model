"""Historical MLB Current Talent reconciliation against official season totals.

The MLB player-game adapter derives chronology-safe evidence from Baseball Savant.
For historical Current Talent training we do not need to rebuild the contextual
Performance/run-value layer for every season. Instead, this module certifies the
standard outcome backbone directly against bulk MLB Stats API season totals at
actual AL/NL grain.

Acceptance is exact for quantities the official season backbone can determine:

- plate appearances;
- BB + HBP core outcomes;
- strikeouts;
- result-contact opportunities = AB - K + SH + SF;
- known special non-contact PA = PA - AB - BB - HBP - SH - SF.

Observed physical contacts and their residual versus result-contact opportunities
remain diagnostics. A physical-contact residual is not evidence that chronology or
identity should be synthetically rewritten.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import validate_player_game_evidence
from universal_baseball.mlb_season_stats import MLB_BATTING_BACKBONE_SCHEMA


MLB_SEASON_KEY = ("season", "league_id", "player_id")


def _profile_outcome_rollup(profile: pl.DataFrame) -> pl.DataFrame:
    """Return BB/HBP and K counts at player × actual-league × season grain."""

    return (
        profile.filter(pl.col("core_bin").is_in(["BB_HBP", "K"]))
        .group_by(list(MLB_SEASON_KEY))
        .agg(
            pl.col("occurrence_count")
            .filter(pl.col("core_bin") == "BB_HBP")
            .sum()
            .fill_null(0)
            .cast(pl.Int64)
            .alias("game_bb_hbp"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin") == "K")
            .sum()
            .fill_null(0)
            .cast(pl.Int64)
            .alias("game_k"),
        )
    )


def reconcile_mlb_game_evidence_to_official_backbone(
    game_summary: pl.DataFrame,
    game_profile: pl.DataFrame,
    official_backbone: pl.DataFrame,
    *,
    require_exact: bool = True,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Reconcile historical MLB player-game evidence to official season counts.

    Zero-PA official rows are retained in the full comparison but do not create
    fake player-game chronology. All exact fields are filled with zero on either
    side before differences are computed.
    """

    validate_player_game_evidence(game_summary, game_profile)
    missing_backbone = sorted(set(MLB_BATTING_BACKBONE_SCHEMA) - set(official_backbone.columns))
    if missing_backbone:
        raise ValueError(f"official MLB backbone missing fields: {missing_backbone}")

    non_mlb_levels = sorted(
        str(value)
        for value in game_summary.filter(pl.col("level_group") != "MLB")
        .get_column("level_group")
        .unique()
        .to_list()
    )
    if non_mlb_levels:
        raise ValueError(f"historical MLB reconciliation received non-MLB levels: {non_mlb_levels}")

    duplicate_backbone = official_backbone.group_by(list(MLB_SEASON_KEY)).len().filter(
        pl.col("len") > 1
    )
    if not duplicate_backbone.is_empty():
        raise ValueError("official MLB backbone violates player × league × season grain")

    game_rollup = (
        game_summary.group_by(list(MLB_SEASON_KEY))
        .agg(
            pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("game_pa"),
            pl.col("expected_contact_count")
            .sum()
            .cast(pl.Int64)
            .alias("game_expected_contacts"),
            pl.col("observed_contact_count")
            .sum()
            .cast(pl.Int64)
            .alias("game_observed_contacts"),
            pl.col("contact_count_residual")
            .sum()
            .cast(pl.Int64)
            .alias("game_contact_residual"),
            pl.col("special_noncontact_count")
            .sum()
            .cast(pl.Int64)
            .alias("game_special_noncontact"),
            pl.col("pa_accounting_residual")
            .sum()
            .cast(pl.Int64)
            .alias("game_pa_accounting_residual"),
        )
        .join(_profile_outcome_rollup(game_profile), on=list(MLB_SEASON_KEY), how="left")
        .with_columns(
            pl.col("game_bb_hbp").fill_null(0).cast(pl.Int64),
            pl.col("game_k").fill_null(0).cast(pl.Int64),
        )
    )

    official = official_backbone.select(
        *MLB_SEASON_KEY,
        pl.col("batting_plate_appearances").cast(pl.Int64).alias("official_pa"),
        (pl.col("batting_base_on_balls") + pl.col("batting_hit_by_pitch"))
        .cast(pl.Int64)
        .alias("official_bb_hbp"),
        pl.col("batting_strike_outs").cast(pl.Int64).alias("official_k"),
        pl.col("batting_balls_in_play").cast(pl.Int64).alias("official_expected_contacts"),
        (
            pl.col("batting_plate_appearances")
            - pl.col("batting_at_bats")
            - pl.col("batting_base_on_balls")
            - pl.col("batting_hit_by_pitch")
            - pl.col("batting_sac_bunts")
            - pl.col("batting_sac_flies")
        )
        .cast(pl.Int64)
        .alias("official_special_noncontact"),
        pl.col("simple_pa_accounting_residual")
        .cast(pl.Int64)
        .alias("official_simple_pa_accounting_residual"),
    )
    invalid_special = official.filter(pl.col("official_special_noncontact") < 0)
    if not invalid_special.is_empty():
        raise ValueError(
            "official MLB backbone implies negative special non-contact PA for "
            f"{invalid_special.height} player-league-season rows"
        )
    residual_identity = official.filter(
        pl.col("official_special_noncontact")
        != -pl.col("official_simple_pa_accounting_residual")
    )
    if not residual_identity.is_empty():
        raise ValueError("official MLB special non-contact derivation is internally inconsistent")

    fill_columns = (
        "game_pa",
        "game_bb_hbp",
        "game_k",
        "game_expected_contacts",
        "game_observed_contacts",
        "game_contact_residual",
        "game_special_noncontact",
        "game_pa_accounting_residual",
        "official_pa",
        "official_bb_hbp",
        "official_k",
        "official_expected_contacts",
        "official_special_noncontact",
        "official_simple_pa_accounting_residual",
    )
    comparison = (
        game_rollup.join(official, on=list(MLB_SEASON_KEY), how="full", coalesce=True)
        .with_columns(*[pl.col(column).fill_null(0).cast(pl.Int64) for column in fill_columns])
        .with_columns(
            (pl.col("game_pa") - pl.col("official_pa")).alias("pa_difference"),
            (pl.col("game_bb_hbp") - pl.col("official_bb_hbp")).alias("bb_hbp_difference"),
            (pl.col("game_k") - pl.col("official_k")).alias("k_difference"),
            (
                pl.col("game_expected_contacts") - pl.col("official_expected_contacts")
            ).alias("expected_contact_difference"),
            (
                pl.col("game_special_noncontact") - pl.col("official_special_noncontact")
            ).alias("special_noncontact_difference"),
        )
        .with_columns(
            pl.any_horizontal(
                [
                    pl.col("pa_difference") != 0,
                    pl.col("bb_hbp_difference") != 0,
                    pl.col("k_difference") != 0,
                    pl.col("expected_contact_difference") != 0,
                    pl.col("special_noncontact_difference") != 0,
                ]
            ).alias("has_exact_outcome_mismatch")
        )
        .sort(list(MLB_SEASON_KEY))
    )

    # The Current Talent adapter's own PA identity must remain exact even before
    # comparison to the independent season backbone.
    if comparison.filter(pl.col("game_pa_accounting_residual") != 0).height:
        raise ValueError("historical MLB player-game evidence has nonzero internal PA residual")

    mismatches = comparison.filter(pl.col("has_exact_outcome_mismatch"))
    physical_residual_rows = comparison.filter(pl.col("game_contact_residual") != 0)
    metrics: dict[str, Any] = {
        "player_league_season_row_count": int(comparison.height),
        "exact_outcome_mismatch_row_count": int(mismatches.height),
        "pa_mismatch_row_count": int(comparison.filter(pl.col("pa_difference") != 0).height),
        "bb_hbp_mismatch_row_count": int(
            comparison.filter(pl.col("bb_hbp_difference") != 0).height
        ),
        "k_mismatch_row_count": int(comparison.filter(pl.col("k_difference") != 0).height),
        "expected_contact_mismatch_row_count": int(
            comparison.filter(pl.col("expected_contact_difference") != 0).height
        ),
        "special_noncontact_mismatch_row_count": int(
            comparison.filter(pl.col("special_noncontact_difference") != 0).height
        ),
        "game_plate_appearances": int(comparison.get_column("game_pa").sum() or 0),
        "official_plate_appearances": int(comparison.get_column("official_pa").sum() or 0),
        "game_bb_hbp": int(comparison.get_column("game_bb_hbp").sum() or 0),
        "official_bb_hbp": int(comparison.get_column("official_bb_hbp").sum() or 0),
        "game_strikeouts": int(comparison.get_column("game_k").sum() or 0),
        "official_strikeouts": int(comparison.get_column("official_k").sum() or 0),
        "game_expected_contacts": int(
            comparison.get_column("game_expected_contacts").sum() or 0
        ),
        "official_expected_contacts": int(
            comparison.get_column("official_expected_contacts").sum() or 0
        ),
        "game_special_noncontact": int(
            comparison.get_column("game_special_noncontact").sum() or 0
        ),
        "official_special_noncontact": int(
            comparison.get_column("official_special_noncontact").sum() or 0
        ),
        "observed_physical_contacts": int(
            comparison.get_column("game_observed_contacts").sum() or 0
        ),
        "physical_contact_residual": int(
            comparison.get_column("game_contact_residual").sum() or 0
        ),
        "physical_contact_residual_player_league_row_count": int(physical_residual_rows.height),
        "exact_outcome_reconciliation": mismatches.is_empty(),
        "physical_contact_residual_is_diagnostic_only": True,
    }
    if require_exact and not metrics["exact_outcome_reconciliation"]:
        raise ValueError(
            "historical MLB Current Talent game evidence does not reconcile to official season "
            f"backbone: {mismatches.height} player-league-season rows"
        )
    return comparison, metrics
