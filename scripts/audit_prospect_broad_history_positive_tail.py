#!/usr/bin/env python3
"""Run the frozen broad-history conditional positive-WAR test."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)
from universal_baseball.hitter_opportunity_paths import hitter_level_tier
from universal_baseball.prospect_arrival import HITTER_POSITION_BY_STATSAPI_CODE
from universal_baseball.prospect_arrival_validation import (
    calibration_diagnostics,
    paired_bootstrap_difference,
    proper_scores,
)
from universal_baseball.storage import sha256_file


TRAIN_ORIGINS = tuple(range(2008, 2011))
OLD_ORIGINS = tuple(range(2013, 2018))
MODERN_ORIGINS = (2021, 2022, 2023)
HORIZON = 2
THRESHOLD = 0.25
LOGISTIC_C = 0.1
RUNS_PER_WIN_SOURCE = Path("docs/prospect-component-uncertainty-result.json")
PLAN_PATH = Path("docs/prospect-broad-history-positive-tail-plan.md")
CORRECTION_PATH = Path(
    "docs/prospect-broad-history-positive-tail-chronology-correction.md"
)
LEVELS = ("A_OR_BELOW", "AA", "AAA", "INACTIVE", "UNKNOWN")
HITTER_ROLES = ("C", "MIDDLE_INFIELD", "OUTFIELD", "CORNER", "OTHER")
PITCHER_ROLES = ("STARTER", "SWINGMAN", "RELIEVER", "OTHER")
BASE_FEATURES = (
    "age",
    "log_current_workload",
    "log_prior_workload",
    "prior_seasons",
    "level_A_OR_BELOW",
    "level_AA",
    "level_AAA",
    "level_INACTIVE",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-broad-history-positive-tail-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-broad-history-positive-tail-result.md"),
    )
    return parser.parse_args()


def _read_history(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = [
        root / "opportunity-history-sources-pre2020/tables" / str(year)
        / "affiliated_season_stats.parquet"
        for year in range(2008, 2018)
    ] + [
        root / "opportunity-history-sources-v2/tables" / str(year)
        / "affiliated_season_stats.parquet"
        for year in range(2018, 2026)
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing affiliated history: {missing}")
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed"), paths


def _role(position: object, *, player_type: str, games: float = 0, starts: float = 0) -> str:
    if player_type == "pitcher":
        if games <= 0:
            return "OTHER"
        if starts * 2 >= games:
            return "STARTER"
        return "RELIEVER" if starts == 0 else "SWINGMAN"
    value = HITTER_POSITION_BY_STATSAPI_CODE.get(str(position or "").upper(), str(position or "").upper())
    if value == "C":
        return "C"
    if value in {"2B", "SS"}:
        return "MIDDLE_INFIELD"
    if value in {"LF", "CF", "RF", "OF"}:
        return "OUTFIELD"
    if value in {"1B", "3B"}:
        return "CORNER"
    return "OTHER"


def _annual_skeleton(player_ids: list[int], *, player_type: str, origin: int) -> pl.DataFrame:
    return pl.DataFrame([
        {
            "path_player_id": int(player_id),
            "player_type": player_type,
            "outcome_tier_v2": "unknown",
            "career_role": "unknown",
            "path_year": season - origin,
            "source_season": season,
            "adjusted_workload": 0.0,
            "annual_role": "inactive",
        }
        for player_id in player_ids
        for season in range(origin + 1, origin + HORIZON + 1)
    ])


def _outcomes(
    cohort: pl.DataFrame,
    components: pl.DataFrame,
    *,
    player_type: str,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    workload = "batting_plate_appearances" if player_type == "hitter" else "pitching_bf"
    annual = (
        _annual_skeleton(cohort["player_id"].to_list(), player_type=player_type, origin=origin)
        .join(
            components.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col(workload).cast(pl.Float64).alias("raw_workload"),
            ),
            on=["path_player_id", "source_season"], how="left", validate="m:1",
        )
        .with_columns(
            pl.col("raw_workload").fill_null(0.0).alias("adjusted_workload"),
            pl.when(pl.col("raw_workload").fill_null(0.0) > 0)
            .then(pl.lit(player_type)).otherwise(pl.lit("inactive")).alias("annual_role"),
        )
        .drop("raw_workload")
    )
    paths = (
        build_historical_hitter_performance_paths(annual, components, runs_per_win=runs_per_win)
        if player_type == "hitter"
        else build_historical_pitcher_performance_paths(annual, components, runs_per_win=runs_per_win)
    )
    return (
        paths.group_by("path_player_id")
        .agg(
            pl.col("adjusted_workload").sum().alias("future_mlb_workload"),
            pl.col("observed_component_war").sum().alias("two_year_component_war"),
        )
        .rename({"path_player_id": "player_id"})
    )


def _cohort(
    snapshots: pl.DataFrame,
    stats: pl.DataFrame,
    components: pl.DataFrame,
    *,
    player_type: str,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    group = "hitting" if player_type == "hitter" else "pitching"
    workload = "plate_appearances" if player_type == "hitter" else "batters_faced"
    players = snapshots.filter(pl.col("snapshot_year") == origin).select(
        "player_id", "age_years", "as_of_level_group"
    )
    prior_mlb = (
        stats.filter(
            (pl.col("stat_group") == group) & (pl.col("sport_id") == 1)
            & (pl.col("season") <= origin) & (pl.col(workload) > 0)
        ).select("player_id").unique().with_columns(pl.lit(True).alias("prior_mlb"))
    )
    affiliated = stats.filter(
        (pl.col("stat_group") == group) & (pl.col("sport_id") != 1)
        & (pl.col("season") <= origin)
    )
    history = affiliated.group_by("player_id").agg(
        pl.col(workload).filter(pl.col("season") < origin).sum().cast(pl.Float64).alias("prior_workload"),
        pl.col("season").filter(pl.col("season") < origin).n_unique().cast(pl.Float64).alias("prior_seasons"),
    )
    current = affiliated.filter(pl.col("season") == origin)
    if player_type == "hitter":
        role = (
            current.filter(pl.col("position_code").is_not_null())
            .group_by("player_id", "position_code").agg(pl.col("games").sum().alias("role_games"))
            .with_columns(pl.col("position_code").cast(pl.Int64, strict=False).fill_null(99).alias("role_order"))
            .sort(["player_id", "role_games", "role_order"], descending=[False, True, False])
            .unique("player_id", keep="first", maintain_order=True)
            .with_columns(pl.col("position_code").map_elements(lambda x: _role(x, player_type="hitter"), return_dtype=pl.String).alias("role"))
            .select("player_id", "role")
        )
    else:
        role = (
            current.group_by("player_id").agg(pl.col("games").sum(), pl.col("starts").sum())
            .with_columns(pl.struct("games", "starts").map_elements(
                lambda x: _role(None, player_type="pitcher", games=x["games"], starts=x["starts"]),
                return_dtype=pl.String,
            ).alias("role")).select("player_id", "role")
        )
    current_workload = current.group_by("player_id").agg(
        pl.col(workload).sum().cast(pl.Float64).alias("current_workload")
    ).join(role, on="player_id", how="left")
    base = (
        players.join(prior_mlb, on="player_id", how="left")
        .join(history, on="player_id", how="left")
        .join(current_workload, on="player_id", how="left")
        .with_columns(
            pl.col("prior_mlb").fill_null(False),
            pl.col("prior_workload").fill_null(0.0),
            pl.col("prior_seasons").fill_null(0.0),
            pl.col("current_workload").fill_null(0.0),
            pl.col("role").fill_null("OTHER"),
            pl.col("as_of_level_group").map_elements(hitter_level_tier, return_dtype=pl.String).alias("level"),
        )
        .filter(~pl.col("prior_mlb") & (pl.col("level") != "MLB") & pl.col("age_years").is_between(16.0, 30.0))
    )
    outcome = _outcomes(base, components, player_type=player_type, origin=origin, runs_per_win=runs_per_win)
    return (
        base.join(outcome, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("future_mlb_workload").fill_null(0.0),
            pl.col("two_year_component_war").fill_null(0.0),
            pl.lit(origin).alias("origin"),
        )
        .with_columns(
            (pl.col("future_mlb_workload") > 0).alias("arrived"),
            (pl.col("two_year_component_war") >= THRESHOLD).alias("positive_tail"),
        )
        .sort("player_id")
    )


def _design(frame: pl.DataFrame, *, player_type: str) -> np.ndarray:
    roles = HITTER_ROLES if player_type == "hitter" else PITCHER_ROLES
    rows = []
    for row in frame.iter_rows(named=True):
        level = row["level"] if row["level"] in LEVELS else "UNKNOWN"
        role = row["role"] if row["role"] in roles else "OTHER"
        rows.append([
            float(row["age_years"]), np.log1p(float(row["current_workload"])),
            np.log1p(float(row["prior_workload"])), float(row["prior_seasons"]),
            *[float(level == value) for value in LEVELS[:-1]],
            *[float(role == value) for value in roles[:-1]],
        ])
    return np.asarray(rows, dtype=float)


def _feature_names(player_type: str) -> tuple[str, ...]:
    roles = HITTER_ROLES if player_type == "hitter" else PITCHER_ROLES
    return (*BASE_FEATURES, *(f"role_{role}" for role in roles[:-1]))


def _loss_deltas(y: np.ndarray, baseline: np.ndarray, candidate: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    b0 = (baseline - y) ** 2
    b1 = (candidate - y) ** 2
    p0 = np.clip(baseline, 1e-12, 1 - 1e-12)
    p1 = np.clip(candidate, 1e-12, 1 - 1e-12)
    ll0 = -(y * np.log(p0) + (1 - y) * np.log(1 - p0))
    ll1 = -(y * np.log(p1) + (1 - y) * np.log(1 - p1))
    return b1 - b0, ll1 - ll0


def _cluster_bootstrap(frame: pl.DataFrame, *, resamples: int = 2000, seed: int = 20260910) -> dict[str, object]:
    y = frame["positive_tail"].cast(pl.Float64).to_numpy()
    brier, logloss = _loss_deltas(y, frame["baseline_probability"].to_numpy(), frame["candidate_probability"].to_numpy())
    ids = frame["player_id"].to_numpy()
    unique = np.unique(ids)
    player_brier = np.asarray([brier[ids == value].mean() for value in unique])
    player_log = np.asarray([logloss[ids == value].mean() for value in unique])
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, unique.size, size=(resamples, unique.size))
    def summarize(values: np.ndarray) -> dict[str, float]:
        samples = values[indices].mean(axis=1)
        return {"difference": float(values.mean()), "ci_low": float(np.quantile(samples, .025)), "ci_high": float(np.quantile(samples, .975)), "probability_candidate_better": float(np.mean(samples < 0))}
    return {"players": int(unique.size), "rows": frame.height, "resamples": resamples, "brier": summarize(player_brier), "log_loss": summarize(player_log)}


def _score(frame: pl.DataFrame, *, seed: int) -> dict[str, object]:
    y = frame["positive_tail"].cast(pl.Float64).to_numpy()
    baseline = frame["baseline_probability"].to_numpy()
    candidate = frame["candidate_probability"].to_numpy()
    return {
        "players": frame.height,
        "positive_players": int(y.sum()),
        "negative_war_players": int((frame["two_year_component_war"] < 0).sum()),
        "baseline": proper_scores(y, baseline),
        "candidate": proper_scores(y, candidate),
        "candidate_calibration": calibration_diagnostics(y, candidate),
        "paired_bootstrap": paired_bootstrap_difference(y, baseline, candidate, seed=seed),
        "both_scores_improved": bool(
            proper_scores(y, candidate)["brier"] < proper_scores(y, baseline)["brier"]
            and proper_scores(y, candidate)["log_loss"] < proper_scores(y, baseline)["log_loss"]
        ),
    }


def _subgroups(frame: pl.DataFrame) -> list[dict[str, object]]:
    age = ["16-20" if x < 21 else "21-24" if x < 25 else "25-30" for x in frame["age_years"].to_list()]
    dimensions = {"age": age, "level": frame["level"].to_list(), "role": frame["role"].to_list()}
    rows = []
    for dimension, values in dimensions.items():
        for value in sorted(set(values)):
            selected = np.asarray([item == value for item in values])
            cell = frame.filter(pl.Series(selected))
            positives = int(cell["positive_tail"].sum())
            supported = cell.height >= 100 and positives >= 20 and cell.height - positives >= 20
            y = cell["positive_tail"].cast(pl.Float64).to_numpy()
            brier, logloss = _loss_deltas(y, cell["baseline_probability"].to_numpy(), cell["candidate_probability"].to_numpy())
            rows.append({"dimension": dimension, "group": str(value), "rows": cell.height, "positive_rows": positives, "supported": supported, "brier_difference": float(brier.mean()), "log_loss_difference": float(logloss.mean()), "material_reversal": bool(supported and brier.mean() > 0 and logloss.mean() > 0)})
    return rows


def _markdown(report: dict[str, object]) -> str:
    lines = ["# Prospect broad-history positive-tail result", "", f"**Decision:** `{report['decision']}`", "", "The fixed basic StatsAPI feature set was fitted once on 2008–2010 and then left unchanged. A pre-scoring correction removed 2011–2012 because their outcomes overlap the first evaluation snapshot.", "", "| Type | Era | Origins better | Brier difference (95% interval) | Log-loss difference (95% interval) |", "|---|---|---:|---:|---:|"]
    for player_type in ("hitter", "pitcher"):
        item = report["results"][player_type]
        for era in ("old", "modern"):
            pooled = item["pooled"][era]
            improved = sum(item["by_origin"][str(x)]["both_scores_improved"] for x in (OLD_ORIGINS if era == "old" else MODERN_ORIGINS))
            b = pooled["brier"]
            ll = pooled["log_loss"]
            lines.append(f"| {player_type} | {era} | {improved} | {b['difference']:.4f} ({b['ci_low']:.4f}, {b['ci_high']:.4f}) | {ll['difference']:.4f} ({ll['ci_low']:.4f}, {ll['ci_high']:.4f}) |")
    lines += ["", "Negative differences favor the candidate. The production model was not changed.", "", "## Why", ""]
    lines.extend(f"- {reason}" for reason in report["decision_reasons"])
    lines += ["", "## Guardrails", "", "- Outcomes are later than every snapshot; 2020 is outside all evaluation windows.", "- Negative MLB WAR is retained.", "- The model was not refitted on either evaluation era.", "- Training gives each player equal total weight across repeat snapshots.", "- No rankings, outside FV, organization, country, body, or depth-chart fields were used.", ""]
    return "\n".join(lines)


def main() -> int:
    args = _args()
    root = args.generated_root
    stats, stat_paths = _read_history(root)
    old_root = root / "opportunity-history-sources-pre2020/tables"
    modern_root = root / "opportunity-history-sources-v2/tables"
    snapshot_paths = {
        "hitter": [old_root / "hitter_snapshots.parquet", modern_root / "hitter_snapshots.parquet"],
        "pitcher": [old_root / "pitcher_snapshots.parquet", modern_root / "pitcher_snapshots.parquet"],
    }
    component_paths = {
        "hitter": root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet",
        "pitcher": root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet",
    }
    runs_per_win = float(json.loads(RUNS_PER_WIN_SOURCE.read_text(encoding="utf-8"))["runs_per_win"])
    results: dict[str, object] = {}
    all_sources = [PLAN_PATH, CORRECTION_PATH, RUNS_PER_WIN_SOURCE, *stat_paths]
    overall_pass = True
    reasons = []
    for player_type in ("hitter", "pitcher"):
        snapshots = pl.concat([pl.read_parquet(path) for path in snapshot_paths[player_type]], how="vertical_relaxed")
        components = pl.read_parquet(component_paths[player_type])
        all_sources.extend([*snapshot_paths[player_type], component_paths[player_type]])
        cohorts = {origin: _cohort(snapshots, stats, components, player_type=player_type, origin=origin, runs_per_win=runs_per_win) for origin in (*TRAIN_ORIGINS, *OLD_ORIGINS, *MODERN_ORIGINS)}
        training = pl.concat([cohorts[x].filter(pl.col("arrived")) for x in TRAIN_ORIGINS])
        counts = training.group_by("player_id").len().rename({"len": "player_rows"})
        training = training.join(counts, on="player_id", validate="m:1").with_columns((1 / pl.col("player_rows")).alias("weight"))
        y_train = training["positive_tail"].cast(pl.Int64).to_numpy()
        weights = training["weight"].to_numpy()
        baseline_rate = float(np.average(y_train, weights=weights))
        scaler = StandardScaler().fit(_design(training, player_type=player_type), sample_weight=weights)
        model = LogisticRegression(C=LOGISTIC_C, max_iter=2000).fit(scaler.transform(_design(training, player_type=player_type)), y_train, sample_weight=weights)
        scored = {}
        by_origin = {}
        for origin in (*OLD_ORIGINS, *MODERN_ORIGINS):
            frame = cohorts[origin].filter(pl.col("arrived")).with_columns(
                pl.lit(baseline_rate).alias("baseline_probability"),
                pl.Series("candidate_probability", model.predict_proba(scaler.transform(_design(cohorts[origin].filter(pl.col("arrived")), player_type=player_type)))[:, 1]),
            )
            scored[origin] = frame
            by_origin[str(origin)] = _score(frame, seed=20260910 + origin)
        pooled = {}
        subgroup_rows = {}
        for era, origins in (("old", OLD_ORIGINS), ("modern", MODERN_ORIGINS)):
            frame = pl.concat([scored[x] for x in origins])
            pooled[era] = _cluster_bootstrap(frame, seed=20260910 + (0 if era == "old" else 1))
            subgroup_rows[era] = _subgroups(frame)
        old_wins = sum(by_origin[str(x)]["both_scores_improved"] for x in OLD_ORIGINS)
        modern_wins = sum(by_origin[str(x)]["both_scores_improved"] for x in MODERN_ORIGINS)
        interval_pass = all(pooled[era][metric]["ci_high"] < 0 for era in ("old", "modern") for metric in ("brier", "log_loss"))
        reversals = [row for era in subgroup_rows.values() for row in era if row["material_reversal"]]
        player_pass = old_wins >= 4 and modern_wins >= 2 and interval_pass and not reversals
        overall_pass &= player_pass
        if not player_pass:
            reasons.append(f"{player_type}: {old_wins}/5 old and {modern_wins}/3 modern origins improved; pooled_interval_pass={interval_pass}; supported_reversals={len(reversals)}")
        results[player_type] = {
            "training": {"rows": training.height, "players": counts.height, "positive_rows": int(y_train.sum()), "weighted_positive_rate": baseline_rate, "inverse_player_frequency_weighting": True},
            "coefficient_l2_norm": float(np.linalg.norm(model.coef_)),
            "standardized_coefficients": [{"feature": name, "coefficient": float(value)} for name, value in zip(_feature_names(player_type), model.coef_[0], strict=True)],
            "by_origin": by_origin, "pooled": pooled, "subgroups": subgroup_rows, "gate_passed": player_pass,
        }
    if overall_pass:
        reasons = ["Both player types cleared every precommitted support condition; a complete conditional-WAR path and fresh confirmation are still required before production use."]
    report = {
        "status": "prospect_broad_history_positive_tail_tested",
        "as_of_date": args.as_of_date.isoformat(),
        "decision": "support_basic_tail_family_but_do_not_promote" if overall_pass else "reject_basic_tail_family",
        "decision_reasons": reasons,
        "production_changed": False,
        "protocol": {"training_origins": list(TRAIN_ORIGINS), "old_evaluation_origins": list(OLD_ORIGINS), "modern_evaluation_origins": list(MODERN_ORIGINS), "horizon_years": HORIZON, "threshold_component_war": THRESHOLD, "logistic_c": LOGISTIC_C, "features": {player_type: list(_feature_names(player_type)) for player_type in ("hitter", "pitcher")}, "subgroup_support": "at least 100 rows, 20 positives, and 20 negatives", "frozen_plan_sha256": sha256_file(PLAN_PATH), "chronology_correction_sha256": sha256_file(CORRECTION_PATH)},
        "runs_per_win": runs_per_win,
        "law_checks": {"training_outcomes_end_before_first_evaluation_snapshot": max(TRAIN_ORIGINS) + HORIZON < min(OLD_ORIGINS), "all_targets_after_snapshot": True, "shortened_2020_outside_evaluation_targets": True, "negative_component_war_retained": all(results[player_type]["by_origin"][str(origin)]["negative_war_players"] > 0 for player_type in ("hitter", "pitcher") for origin in (*OLD_ORIGINS, *MODERN_ORIGINS)), "no_evaluation_refit": True, "no_outside_fv": True, "no_organization_effect": True, "production_unchanged": True},
        "results": results,
        "sources": [{"path": str(path), "sha256": sha256_file(path)} for path in sorted(set(all_sources), key=str)],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "reasons": reasons}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
