#!/usr/bin/env python3
"""Select Player Value v1 DH role-equivalent-game exposure on pre-2025 folds.

Non-DH positional exposure is already frozen as projected defensive outs by position.
This script only selects the DH exposure quantity needed by positional adjustment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path

import numpy as np
import polars as pl

CONTRACT_GIT_BLOB_SHA1 = "3f872dc62b90dca23160933ecc2ab08b0a7385fe"
PRIMARY_SHARE_THRESHOLD = 0.65
ROLE_POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH")
FORMS = (
    "B0_raw_dh_role_event_persistence",
    "R1_frozen_role_share_persistent_volume",
    "P1_frozen_role_share_playing_time_ratio",
    "H1_fixed_50_50_B0_P1_hybrid",
)
FOLDS = (
    {
        "name": "projection_2022_to_2023",
        "source_year": 2022,
        "target_year": 2023,
        "validation_file": "candidate_scored.parquet",
    },
    {
        "name": "projection_2023_to_2024",
        "source_year": 2023,
        "target_year": 2024,
        "validation_file": "candidate_2024_scored.parquet",
    },
)

PROVENANCE = {
    "position_role": {
        "run_id": 32152125644,
        "artifact_name": "position-role-transition-challenger-development",
        "artifact_digest": "sha256:4e98081cb1800d45f3668595e4e61a169dbce68a8b565aa1e8f60d7dcd1417e5",
    },
    "playing_time_selection": {
        "run_id": 32141616127,
        "artifact_name": "playing-time-v1-candidate-selection",
        "artifact_digest": "sha256:a8719576ef7ed7377a6376556d34e1fd377d5e27ca88535543a43c615f4cb5d8",
    },
    "playing_time_validation_2023": {
        "run_id": 32141934868,
        "artifact_name": "playing-time-v1-validation-2023",
        "artifact_digest": "sha256:738c631f5b4fbaa7875219ee452996e487799c4a323b0cafa57a7500583c5b39",
    },
    "playing_time_validation_2024": {
        "run_id": 32142089669,
        "artifact_name": "playing-time-v1-validation-2024",
        "artifact_digest": "sha256:979386377b5c2fa7f8f411bcd3284c6f4e68d532a5585e002b493f3cfffe0366",
    },
    "fielding_role_source": {
        "run_id": 32148467330,
        "artifact_name": "position-role-historical-source-2021-2024",
        "artifact_digest": "sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3",
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--position-role-root", type=Path, required=True)
    parser.add_argument("--playing-time-selection-root", type=Path, required=True)
    parser.add_argument("--validation-2023-root", type=Path, required=True)
    parser.add_argument("--validation-2024-root", type=Path, required=True)
    parser.add_argument("--fielding-root", type=Path, required=True)
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-dh-positional-exposure-selection-contract.md"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/player-value-v1-dh-positional-exposure-selection"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob_sha1(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _verify_contract(path: Path) -> str:
    blob_sha = _git_blob_sha1(path)
    if blob_sha != CONTRACT_GIT_BLOB_SHA1:
        raise RuntimeError(
            f"DH exposure contract changed: expected git blob {CONTRACT_GIT_BLOB_SHA1}, observed {blob_sha}"
        )
    return _sha256(path)


def _unique_file(root: Path, filename: str, *, contains_part: str | None = None) -> Path:
    matches = sorted(
        path
        for path in root.rglob(filename)
        if path.is_file() and (contains_part is None or contains_part in path.parts)
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename!r} under {root}"
            + (f" containing {contains_part!r}" if contains_part else "")
            + f"; found {matches}"
        )
    return matches[0]


def _load_role_predictions(root: Path) -> pl.DataFrame:
    frame = pl.read_parquet(_unique_file(root, "predictions.parquet"))
    required = {"current_season", "next_season", "player_id", "current_primary_share"}
    for position in ROLE_POSITIONS:
        required.update({f"current_{position}", f"candidate_{position}"})
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Position/Role predictions missing {missing}")
    frame = frame.select(
        pl.col("current_season").cast(pl.Int64),
        pl.col("next_season").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("current_primary_share").cast(pl.Float64),
        *[
            pl.col(column).cast(pl.Float64)
            for position in ROLE_POSITIONS
            for column in (f"current_{position}", f"candidate_{position}")
        ],
    )
    if frame.group_by(["current_season", "next_season", "player_id"]).len().filter(
        pl.col("len") != 1
    ).height:
        raise RuntimeError("Position/Role prediction grain violation")
    return frame


def _load_fielding(root: Path) -> pl.DataFrame:
    frame = pl.read_parquet(_unique_file(root, "historical_fielding_usage.parquet"))
    required = {
        "season",
        "level_group",
        "player_id",
        "position_abbreviation",
        "games_played",
        "games_started",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"historical fielding usage missing {missing}")
    return frame.select(
        pl.col("season").cast(pl.Int64),
        pl.col("level_group").cast(pl.Utf8),
        pl.col("player_id").cast(pl.Int64),
        pl.col("position_abbreviation").cast(pl.Utf8),
        pl.col("games_played").cast(pl.Int64),
        pl.col("games_started").cast(pl.Int64),
    )


def _role_events(fielding: pl.DataFrame, year: int, prefix: str) -> pl.DataFrame:
    filtered = (
        fielding.filter(
            (pl.col("season") == year)
            & (pl.col("level_group") == "MLB")
            & pl.col("position_abbreviation").is_in(ROLE_POSITIONS)
        )
        .group_by(["player_id", "position_abbreviation"])
        .agg(
            pl.col("games_started").sum().alias("games_started"),
            pl.col("games_played").sum().alias("games_played"),
        )
    )
    totals = filtered.group_by("player_id").agg(
        pl.col("games_started").sum().alias("total_games_started")
    )
    events = filtered.join(totals, on="player_id", how="left").with_columns(
        pl.when(pl.col("total_games_started") > 0)
        .then(pl.col("games_started"))
        .otherwise(pl.col("games_played"))
        .cast(pl.Float64)
        .alias("role_events")
    )
    total = events.group_by("player_id").agg(
        pl.col("role_events").sum().alias(f"{prefix}_total_role_events")
    )
    dh = (
        events.filter(pl.col("position_abbreviation") == "DH")
        .select("player_id", pl.col("role_events").alias(f"{prefix}_dh_role_events"))
    )
    return total.join(dh, on="player_id", how="left").with_columns(
        pl.col(f"{prefix}_dh_role_events").fill_null(0.0)
    )


def _load_playing_time(
    selection_root: Path,
    validation_root: Path,
    fold: dict[str, object],
) -> pl.DataFrame:
    fold_name = str(fold["name"])
    predictors = pl.read_parquet(
        _unique_file(selection_root, "predictors.parquet", contains_part=fold_name)
    ).select(
        pl.col("player_id").cast(pl.Int64),
        pl.col("current_season_mlb_pa").cast(pl.Float64),
    )
    scored = pl.read_parquet(
        _unique_file(validation_root, str(fold["validation_file"]))
    ).select(
        pl.col("player_id").cast(pl.Int64),
        pl.col("predicted_expected_mlb_pa").cast(pl.Float64),
    )
    if predictors.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_name} Playing Time predictors violate player grain")
    if scored.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_name} Playing Time scores violate player grain")
    return predictors.join(scored, on="player_id", how="inner")


def _build_fold(
    *,
    role_predictions: pl.DataFrame,
    fielding: pl.DataFrame,
    playing_time: pl.DataFrame,
    source_year: int,
    target_year: int,
) -> tuple[pl.DataFrame, dict[str, object]]:
    role = role_predictions.filter(
        (pl.col("current_season") == source_year) & (pl.col("next_season") == target_year)
    )
    if role.is_empty():
        raise RuntimeError(f"empty Position/Role fold {source_year}->{target_year}")
    role = role.with_columns(
        pl.when(pl.col("current_primary_share") >= PRIMARY_SHARE_THRESHOLD)
        .then(pl.col("candidate_DH"))
        .otherwise(pl.col("current_DH"))
        .alias("frozen_projected_dh_role_probability")
    )
    prior = _role_events(fielding, source_year, "prior")
    target = _role_events(fielding, target_year, "observed")
    frame = (
        role.select(
            "player_id",
            "frozen_projected_dh_role_probability",
            "current_primary_share",
        )
        .join(prior, on="player_id", how="left")
        .join(target, on="player_id", how="left")
        .join(playing_time, on="player_id", how="left")
        .with_columns(
            pl.col("prior_total_role_events").fill_null(0.0),
            pl.col("prior_dh_role_events").fill_null(0.0),
            pl.col("observed_total_role_events").fill_null(0.0),
            pl.col("observed_dh_role_events").fill_null(0.0),
        )
        .with_columns(
            pl.col("prior_dh_role_events").alias("B0_raw_dh_role_event_persistence"),
            (
                pl.col("frozen_projected_dh_role_probability")
                * pl.col("prior_total_role_events")
            ).alias("R1_frozen_role_share_persistent_volume"),
            (
                pl.col("current_season_mlb_pa").is_null()
                | pl.col("predicted_expected_mlb_pa").is_null()
                | (pl.col("current_season_mlb_pa") <= 0)
            ).alias("P1_fallback_to_R1"),
        )
        .with_columns(
            pl.when(~pl.col("P1_fallback_to_R1"))
            .then(
                pl.col("R1_frozen_role_share_persistent_volume")
                * pl.col("predicted_expected_mlb_pa")
                / pl.col("current_season_mlb_pa")
            )
            .otherwise(pl.col("R1_frozen_role_share_persistent_volume"))
            .alias("P1_frozen_role_share_playing_time_ratio")
        )
        .with_columns(
            (
                0.5 * pl.col("B0_raw_dh_role_event_persistence")
                + 0.5 * pl.col("P1_frozen_role_share_playing_time_ratio")
            ).alias("H1_fixed_50_50_B0_P1_hybrid"),
            pl.lit(source_year).alias("source_year"),
            pl.lit(target_year).alias("target_year"),
        )
        .sort("player_id")
    )
    for form in FORMS:
        if frame.filter(pl.col(form).is_null() | (pl.col(form) < 0)).height:
            raise RuntimeError(f"invalid {form} values in {source_year}->{target_year}")
    diagnostics = {
        "position_role_players": int(role.height),
        "prior_role_source_missing": int(frame.filter(pl.col("prior_total_role_events") == 0).height),
        "playing_time_available": int(
            frame.filter(pl.col("predicted_expected_mlb_pa").is_not_null()).height
        ),
        "playing_time_missing": int(
            frame.filter(pl.col("predicted_expected_mlb_pa").is_null()).height
        ),
        "P1_fallback_to_R1_count": int(frame.get_column("P1_fallback_to_R1").sum()),
        "observed_dh_positive": int(frame.filter(pl.col("observed_dh_role_events") > 0).height),
        "prior_dh_positive": int(frame.filter(pl.col("prior_dh_role_events") > 0).height),
    }
    return frame, diagnostics


def _subset_metric(frame: pl.DataFrame, form: str, mask: pl.Expr) -> dict[str, object]:
    subset = frame.filter(mask)
    if subset.is_empty():
        return {"n": 0, "mae": None, "rmse": None}
    observed = subset.get_column("observed_dh_role_events").to_numpy().astype(np.float64)
    predicted = subset.get_column(form).to_numpy().astype(np.float64)
    error = predicted - observed
    return {
        "n": int(subset.height),
        "mae": float(np.abs(error).mean()),
        "rmse": float(sqrt(float(np.square(error).mean()))),
    }


def _metrics(frame: pl.DataFrame, form: str) -> dict[str, object]:
    observed = frame.get_column("observed_dh_role_events").to_numpy().astype(np.float64)
    predicted = frame.get_column(form).to_numpy().astype(np.float64)
    error = predicted - observed
    return {
        "n": int(frame.height),
        "mae": float(np.abs(error).mean()),
        "rmse": float(sqrt(float(np.square(error).mean()))),
        "observed_mean": float(observed.mean()),
        "predicted_mean": float(predicted.mean()),
        "target_positive": _subset_metric(frame, form, pl.col("observed_dh_role_events") > 0),
        "incumbent_dh": _subset_metric(frame, form, pl.col("prior_dh_role_events") > 0),
        "entrant_dh": _subset_metric(
            frame,
            form,
            (pl.col("prior_dh_role_events") == 0) & (pl.col("observed_dh_role_events") > 0),
        ),
        "exit_dh": _subset_metric(
            frame,
            form,
            (pl.col("prior_dh_role_events") > 0) & (pl.col("observed_dh_role_events") == 0),
        ),
    }


def _equal_fold_means(folds: dict[str, dict[str, object]]) -> dict[str, dict[str, float]]:
    return {
        form: {
            "mae": float(np.mean([folds[name]["metrics"][form]["mae"] for name in folds])),
            "rmse": float(np.mean([folds[name]["metrics"][form]["rmse"] for name in folds])),
        }
        for form in FORMS
    }


def _select(
    folds: dict[str, dict[str, object]], equal: dict[str, dict[str, float]]
) -> dict[str, object]:
    baseline = "B0_raw_dh_role_event_persistence"
    challengers = (
        "R1_frozen_role_share_persistent_volume",
        "P1_frozen_role_share_playing_time_ratio",
        "H1_fixed_50_50_B0_P1_hybrid",
    )
    evaluations: dict[str, object] = {}
    passing: list[str] = []
    for challenger in challengers:
        overall_guard = True
        positive_guard = True
        entrant_guard = True
        per_fold: dict[str, object] = {}
        for fold_name, fold in folds.items():
            b0 = fold["metrics"][baseline]
            c = fold["metrics"][challenger]
            overall_ok = float(c["mae"]) <= 1.02 * float(b0["mae"])
            b0_positive, c_positive = b0["target_positive"], c["target_positive"]
            positive_ok = (
                True
                if int(b0_positive["n"]) == 0
                else float(c_positive["mae"]) <= 1.02 * float(b0_positive["mae"])
            )
            b0_entrant, c_entrant = b0["entrant_dh"], c["entrant_dh"]
            entrant_ok = (
                True
                if int(b0_entrant["n"]) == 0
                else float(c_entrant["mae"]) < float(b0_entrant["mae"])
            )
            overall_guard &= overall_ok
            positive_guard &= positive_ok
            entrant_guard &= entrant_ok
            per_fold[fold_name] = {
                "overall_mae_within_2pct": overall_ok,
                "target_positive_mae_within_2pct": positive_ok,
                "entrant_mae_strictly_lower": entrant_ok,
            }
        mean_mae_lower = float(equal[challenger]["mae"]) < float(equal[baseline]["mae"])
        mean_rmse_lower = float(equal[challenger]["rmse"]) < float(equal[baseline]["rmse"])
        passes = bool(
            overall_guard
            and mean_mae_lower
            and mean_rmse_lower
            and positive_guard
            and entrant_guard
        )
        evaluations[challenger] = {
            "per_fold": per_fold,
            "fold_overall_mae_guard": overall_guard,
            "equal_fold_mae_strictly_lower": mean_mae_lower,
            "equal_fold_rmse_strictly_lower": mean_rmse_lower,
            "target_positive_mae_guard": positive_guard,
            "entrant_mae_guard": entrant_guard,
            "passes": passes,
        }
        if passes:
            passing.append(challenger)

    if not passing:
        selected = baseline
        reason = "no challenger passed all predeclared gates"
    else:
        order = {challengers[0]: 0, challengers[1]: 1, challengers[2]: 2}
        selected = min(
            passing,
            key=lambda form: (float(equal[form]["mae"]), order[form]),
        )
        reason = "passing challenger with lowest equal-fold MAE; preregistered simplicity order breaks ties"
    return {
        "selected_form": selected,
        "reason": reason,
        "passing_challengers": passing,
        "challenger_evaluations": evaluations,
    }


def _formula(selected: str) -> str:
    mapping = {
        "B0_raw_dh_role_event_persistence": "projected_dh_role_events = prior_dh_role_events",
        "R1_frozen_role_share_persistent_volume": "projected_dh_role_events = frozen_projected_DH_role_probability * prior_total_role_events",
        "P1_frozen_role_share_playing_time_ratio": "projected_dh_role_events = frozen_projected_DH_role_probability * prior_total_role_events * projected_expected_mlb_pa / source_year_mlb_pa; fallback to R1 when Playing Time ratio unavailable",
        "H1_fixed_50_50_B0_P1_hybrid": "projected_dh_role_events = 0.5 * prior_dh_role_events + 0.5 * P1; P1 fallback semantics unchanged",
    }
    return mapping[selected]


def main() -> int:
    args = _parse_args()
    contract_sha256 = _verify_contract(args.contract_path)
    role_predictions = _load_role_predictions(args.position_role_root)
    fielding = _load_fielding(args.fielding_root)

    fold_results: dict[str, dict[str, object]] = {}
    scored_frames: list[pl.DataFrame] = []
    for fold in FOLDS:
        source_year = int(fold["source_year"])
        target_year = int(fold["target_year"])
        validation_root = (
            args.validation_2023_root if target_year == 2023 else args.validation_2024_root
        )
        playing_time = _load_playing_time(
            args.playing_time_selection_root, validation_root, fold
        )
        frame, diagnostics = _build_fold(
            role_predictions=role_predictions,
            fielding=fielding,
            playing_time=playing_time,
            source_year=source_year,
            target_year=target_year,
        )
        fold_name = f"{source_year}_to_{target_year}"
        fold_results[fold_name] = {
            "diagnostics": diagnostics,
            "metrics": {form: _metrics(frame, form) for form in FORMS},
        }
        scored_frames.append(frame.with_columns(pl.lit(fold_name).alias("fold")))

    equal = _equal_fold_means(fold_results)
    selection = _select(fold_results, equal)
    report = {
        "schema_version": "0.1",
        "status": "player_value_v1_dh_positional_exposure_frozen",
        "contract": "docs/player-value-v1-dh-positional-exposure-selection-contract.md",
        "contract_git_blob_sha1": CONTRACT_GIT_BLOB_SHA1,
        "contract_sha256": contract_sha256,
        "provenance": PROVENANCE,
        "role_semantics": "games_started by position when total starts > 0; otherwise games_played fallback",
        "folds": fold_results,
        "equal_fold_means": equal,
        "selection": {
            **selection,
            "selected_formula": _formula(selection["selected_form"]),
        },
        "boundary": {
            "2025_outcomes_accessed": False,
            "current_talent_refit": False,
            "projection_refit": False,
            "playing_time_refit": False,
            "position_role_refit": False,
            "defense_refit": False,
            "general_defensive_exposure_changed": False,
            "positional_run_schedule_selected": False,
            "positional_adjustment_runs_calculated": False,
            "replacement_level_selected": False,
            "runs_per_win_selected": False,
            "war_value_calculated": False,
        },
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pl.concat(scored_frames, how="vertical_relaxed").write_parquet(
        args.output_root / "scored_dh_exposure.parquet"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
