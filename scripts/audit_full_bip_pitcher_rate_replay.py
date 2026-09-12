#!/usr/bin/env python3
"""Replay the frozen full-BIP adjustment inside the complete pitcher rate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_full_bip_pitcher_challenger import (
    PITCHER_COMPONENTS,
    _affiliated_components,
    _contact_offsets,
    _load,
    _neutral_bip_estimates,
    _neutral_targets,
)
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    translate_component_probabilities_to_mlb,
)


FROZEN_CONTACT_WEIGHT = 0.78826181766178
MIN_TARGET_CONTACTS = 50


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pitching-source", type=Path, action="append", required=True)
    parser.add_argument("--hitting-translation-source", type=Path, required=True)
    parser.add_argument("--origin-2021", type=Path, required=True)
    parser.add_argument("--target-2022", type=Path, required=True)
    parser.add_argument("--target-2023", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _source(paths: list[Path]) -> pl.DataFrame:
    frames = [_affiliated_components(path, "pitcher") for path in paths]
    source = pl.concat(frames, how="vertical_relaxed").sort(
        "season", "player_id", "sport_id", "team_id"
    )
    duplicate = source.group_by("season", "player_id", "sport_id", "team_id").len()
    if duplicate.filter(pl.col("len") != 1).height:
        raise ValueError("pitching sources contain duplicate canonical rows")
    return source


def _main_offsets(source: pl.DataFrame, origin_year: int) -> pl.DataFrame:
    eligible = source.filter(pl.col("season") <= origin_year)
    return fit_same_season_component_translation(
        eligible,
        exposure_column="batters_faced",
        component_columns=PITCHER_COMPONENTS,
        completed_seasons=tuple(
            int(value)
            for value in eligible.get_column("season").unique().sort().to_list()
        ),
        minimum_level_exposure=30,
    ).offsets


def _active_profiles(
    source: pl.DataFrame,
    players: pl.DataFrame,
    *,
    origin_year: int,
    offsets: pl.DataFrame,
) -> pl.DataFrame:
    return build_translated_affiliated_profiles(
        players,
        source.filter(pl.col("season") <= origin_year),
        offsets,
        exposure_column="batters_faced",
        component_columns=PITCHER_COMPONENTS,
        current_season=origin_year,
        reference_season=origin_year,
        regression_exposure=800.0,
    )


def _future_profiles(
    source: pl.DataFrame,
    *,
    target_year: int,
    offsets: pl.DataFrame,
) -> pl.DataFrame:
    annual = (
        source.filter((pl.col("season") == target_year) & (pl.col("batters_faced") > 0))
        .group_by("player_id", "level_group")
        .agg(
            pl.col("batters_faced").sum().alias("level_bf"),
            *(pl.col(value).sum().alias(value) for value in PITCHER_COMPONENTS),
        )
    )
    rows = []
    for row in annual.iter_rows(named=True):
        exposure = float(row["level_bf"])
        raw = {
            value: (float(row[value]) + 0.5)
            / (exposure + 0.5 * len(PITCHER_COMPONENTS))
            for value in PITCHER_COMPONENTS
        }
        translated = translate_component_probabilities_to_mlb(
            raw, level_group=str(row["level_group"]), offsets=offsets
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "level_bf": exposure,
                **{
                    f"target_{value}": exposure * translated[value]
                    for value in PITCHER_COMPONENTS
                },
            }
        )
    return (
        pl.DataFrame(rows)
        .group_by("player_id")
        .agg(
            pl.col("level_bf").sum().alias("target_bf"),
            *(pl.col(f"target_{value}").sum() for value in PITCHER_COMPONENTS),
        )
        .with_columns(
            *(
                (pl.col(f"target_{value}") / pl.col("target_bf")).alias(
                    f"target_p_{value}"
                )
                for value in PITCHER_COMPONENTS
            )
        )
    )


def _rate_rows(
    source: pl.DataFrame,
    contact_translation_source: pl.DataFrame,
    *,
    origin_root: Path,
    target_root: Path,
) -> pl.DataFrame:
    origin_profile, origin_outcomes = _load(origin_root, "pitcher")
    _, target_outcomes = _load(target_root, "pitcher")
    origin_year = int(origin_profile.get_column("season").max())
    target_year = int(target_outcomes.get_column("season").max())
    contact_offsets = _contact_offsets(contact_translation_source, origin_year)
    bip = _neutral_bip_estimates(origin_profile, origin_outcomes, contact_offsets)
    contact_target = _neutral_targets(target_outcomes, contact_offsets)
    main_offsets = _main_offsets(source, origin_year)
    active = _active_profiles(
        source,
        bip.select("player_id"),
        origin_year=origin_year,
        offsets=main_offsets,
    )
    future = _future_profiles(source, target_year=target_year, offsets=main_offsets)
    reference = source.filter(
        (pl.col("season") == origin_year) & (pl.col("level_group") == "MLB")
    )
    total = float(reference.get_column("batters_faced").sum())
    rates = {
        value: float(reference.get_column(value).sum()) / total
        for value in PITCHER_COMPONENTS
    }
    known = (
        rates["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + rates["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + rates["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    other_value = (0.3188 - known) / rates["other"]
    joined = (
        active.join(bip, on="player_id", validate="1:1")
        .join(contact_target, on="player_id", validate="1:1")
        .join(future, on="player_id", validate="1:1")
        .filter(pl.col("target_contacts") >= MIN_TARGET_CONTACTS)
    )
    active_contact = (pl.col("p_hr") * 0.0 + pl.col("p_other") * other_value) / (
        pl.col("p_hr") + pl.col("p_other")
    )
    blended_contact = active_contact + FROZEN_CONTACT_WEIGHT * (
        pl.col("bip_contact_value") - active_contact
    )
    target_non_contact = (
        pl.col("target_p_ubb") * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + pl.col("target_p_hbp") * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + pl.col("target_p_hr") * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    predicted_non_contact = (
        pl.col("p_ubb") * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + pl.col("p_hbp") * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + pl.col("p_hr") * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    return joined.with_columns(
        (
            predicted_non_contact
            + (pl.col("p_hr") + pl.col("p_other")) * active_contact
        ).alias("baseline_woba_allowed"),
        (
            predicted_non_contact
            + (pl.col("p_hr") + pl.col("p_other")) * blended_contact
        ).alias("candidate_woba_allowed"),
        (
            target_non_contact
            + (pl.col("target_p_hr") + pl.col("target_p_other"))
            * pl.col("target_contact_value")
        ).alias("target_woba_allowed"),
    ).with_columns(
        (
            -(pl.col("baseline_woba_allowed") - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE
        ).alias("baseline_runs_per_800"),
        (
            -(pl.col("candidate_woba_allowed") - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE
        ).alias("candidate_runs_per_800"),
        (-(pl.col("target_woba_allowed") - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE).alias(
            "target_runs_per_800"
        ),
    )


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float | int]:
    error = (
        frame.get_column(prediction).to_numpy()
        - frame.get_column("target_runs_per_800").to_numpy()
    )
    weights = frame.get_column("target_bf").to_numpy()
    return {
        "players": frame.height,
        "target_bf": int(weights.sum()),
        "player_mae": float(np.mean(np.abs(error))),
        "player_rmse": float(np.sqrt(np.mean(error**2))),
        "bf_weighted_mae": float(np.average(np.abs(error), weights=weights)),
        "bf_weighted_rmse": float(np.sqrt(np.average(error**2, weights=weights))),
    }


def _score(frame: pl.DataFrame) -> dict[str, object]:
    baseline = _metrics(frame, "baseline_runs_per_800")
    candidate = _metrics(frame, "candidate_runs_per_800")
    levels = []
    for level in sorted(frame.get_column("origin_level").unique().to_list()):
        group = frame.filter(pl.col("origin_level") == level)
        if group.height < 100:
            continue
        base_level = _metrics(group, "baseline_runs_per_800")
        candidate_level = _metrics(group, "candidate_runs_per_800")
        levels.append(
            {
                "origin_level": level,
                "players": group.height,
                "player_mae_delta": candidate_level["player_mae"]
                - base_level["player_mae"],
                "player_rmse_delta": candidate_level["player_rmse"]
                - base_level["player_rmse"],
                "bf_weighted_mae_delta": candidate_level["bf_weighted_mae"]
                - base_level["bf_weighted_mae"],
                "bf_weighted_rmse_delta": candidate_level["bf_weighted_rmse"]
                - base_level["bf_weighted_rmse"],
            }
        )
    return {
        "baseline": baseline,
        "candidate": candidate,
        "by_origin_level": levels,
        "supported_level_reversals": [
            row["origin_level"]
            for row in levels
            if row["player_mae_delta"] > 0 and row["player_rmse_delta"] > 0
        ],
    }


def main() -> int:
    args = _args()
    source = _source(args.pitching_source)
    contact_translation_source = _affiliated_components(
        args.hitting_translation_source, "hitter"
    )
    development = _rate_rows(
        source,
        contact_translation_source,
        origin_root=args.origin_2021,
        target_root=args.target_2022,
    )
    confirmation = _rate_rows(
        source,
        contact_translation_source,
        origin_root=args.target_2022,
        target_root=args.target_2023,
    )
    report = {
        "status": "full_pitcher_rate_replay_scored",
        "frozen_contact_weight": FROZEN_CONTACT_WEIGHT,
        "development": _score(development),
        "confirmation": _score(confirmation),
        "promotion_pass": False,
    }
    confirmation_score = report["confirmation"]
    report["promotion_pass"] = bool(
        confirmation_score["candidate"]["player_mae"]
        < confirmation_score["baseline"]["player_mae"]
        and confirmation_score["candidate"]["player_rmse"]
        < confirmation_score["baseline"]["player_rmse"]
        and not confirmation_score["supported_level_reversals"]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
