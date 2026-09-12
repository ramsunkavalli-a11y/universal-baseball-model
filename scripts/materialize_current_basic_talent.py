#!/usr/bin/env python3
"""Build current, rate-only hitter and pitcher talent diagnostics from StatsAPI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_SCALE, NEUTRAL_WOBA_WEIGHTS
from universal_baseball.level_component_translation import build_translated_affiliated_profiles
from universal_baseball.prospect_hitter_talent import (
    RANKING_MINIMUM_EFFECTIVE_EVENTS,
    evidence_band,
)
from universal_baseball.storage import write_canonical_parquet


HITTER_COMPONENTS = ("so", "ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument(
        "--affiliated-skill-root",
        type=Path,
        default=Path("reports/generated/affiliated-skill-source/tables"),
    )
    parser.add_argument(
        "--translation-root",
        type=Path,
        default=Path("reports/generated/affiliated-level-translations/tables"),
    )
    parser.add_argument(
        "--current-source-root",
        type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--external-audit",
        type=Path,
        default=Path("reports/generated/phase2-prospect-source/2026-09-08/fangraphs-top-100.parquet"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-basic-talent/2026-09-08"),
    )
    return parser.parse_args()


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
        pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _reference_rates(
    frame: pl.DataFrame,
    *,
    season: int,
    exposure: str,
    components: tuple[str, ...],
) -> dict[str, float]:
    reference = frame.filter((pl.col("season") == season) & (pl.col("level_group") == "MLB"))
    total = float(reference.get_column(exposure).sum() or 0.0)
    if total <= 0:
        raise ValueError("current basic talent requires positive prior-season MLB reference")
    return {component: float(reference.get_column(component).sum()) / total for component in components}


def _rank(frame: pl.DataFrame, score: str, rank_name: str) -> pl.DataFrame:
    ready = (
        frame.filter(pl.col("ranking_status") == "ranked")
        .sort([score, "effective_evidence", "player_id"], descending=[True, True, False])
        .with_row_index(rank_name, offset=1)
    )
    unresolved = frame.filter(pl.col("ranking_status") == "unresolved").with_columns(
        pl.lit(None, dtype=pl.UInt32).alias(rank_name)
    )
    return pl.concat([ready, unresolved], how="diagonal_relaxed")


def _score_hitters(
    profiles: pl.DataFrame,
    players: pl.DataFrame,
    reference: dict[str, float],
) -> pl.DataFrame:
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"],
        "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": 0.0,
    }
    reference_woba = sum(reference[key] * weights[key] for key in HITTER_COMPONENTS)
    rows = []
    for row in profiles.join(players, on="player_id", how="left").iter_rows(named=True):
        evidence = float(row["weighted_affiliated_exposure"])
        probabilities = {key: float(row[f"p_{key}"]) for key in HITTER_COMPONENTS}
        woba = sum(probabilities[key] * weights[key] for key in HITTER_COMPONENTS)
        contributions = {
            key: (probabilities[key] - reference[key]) * 600.0 * weights[key] / NEUTRAL_WOBA_SCALE
            for key in HITTER_COMPONENTS
        }
        best = max(contributions, key=contributions.get)
        worst = min(contributions, key=contributions.get)
        rows.append({
            "player_id": int(row["player_id"]),
            "player_name": row.get("player_name"),
            "player_type": "hitter",
            "as_of_level_group": row.get("as_of_level_group"),
            "age_years": row.get("age_years"),
            "present_offense_runs_per_600_pa": (woba - reference_woba) * 600.0 / NEUTRAL_WOBA_SCALE,
            "effective_evidence": evidence,
            "reliability": float(row["affiliated_reliability"]),
            "evidence_band": evidence_band(evidence),
            "ranking_status": "ranked" if evidence >= RANKING_MINIMUM_EFFECTIVE_EVENTS else "unresolved",
            "strongest_component": best,
            "largest_weakness": worst,
            **{f"predicted_{key}_rate": probabilities[key] for key in HITTER_COMPONENTS},
        })
    return _rank(pl.DataFrame(rows), "present_offense_runs_per_600_pa", "present_hitter_rank")


def _score_pitchers(
    profiles: pl.DataFrame,
    players: pl.DataFrame,
    reference: dict[str, float],
) -> pl.DataFrame:
    known = (
        reference["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + reference["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + reference["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": (0.3188 - known) / reference["other"],
    }
    rows = []
    for row in profiles.join(players, on="player_id", how="left").iter_rows(named=True):
        evidence = float(row["weighted_affiliated_exposure"])
        probabilities = {key: float(row[f"p_{key}"]) for key in PITCHER_COMPONENTS}
        woba_allowed = sum(probabilities[key] * weights[key] for key in PITCHER_COMPONENTS)
        contributions = {
            key: -(probabilities[key] - reference[key]) * 800.0 * weights[key] / NEUTRAL_WOBA_SCALE
            for key in PITCHER_COMPONENTS
        }
        best = max(contributions, key=contributions.get)
        worst = min(contributions, key=contributions.get)
        rows.append({
            "player_id": int(row["player_id"]),
            "player_name": row.get("player_name"),
            "player_type": "pitcher",
            "as_of_level_group": row.get("as_of_level_group"),
            "age_years": row.get("age_years"),
            "present_pitching_runs_per_800_bf": -(woba_allowed - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE,
            "effective_evidence": evidence,
            "reliability": float(row["affiliated_reliability"]),
            "evidence_band": evidence_band(evidence),
            "ranking_status": "ranked" if evidence >= RANKING_MINIMUM_EFFECTIVE_EVENTS else "unresolved",
            "strongest_component": best,
            "largest_weakness": worst,
            **{f"predicted_{key}_rate": probabilities[key] for key in PITCHER_COMPONENTS},
        })
    return _rank(pl.DataFrame(rows), "present_pitching_runs_per_800_bf", "present_pitcher_rank")


def main() -> int:
    args = _args()
    current_year = int(args.as_of_date[:4])
    source_hitting = _hitter_components(
        pl.read_parquet(args.affiliated_skill_root / "affiliated_hitting_components.parquet")
    )
    source_pitching = _pitcher_components(
        pl.read_parquet(args.affiliated_skill_root / "affiliated_pitching_components.parquet")
    )
    hitter_snapshot = pl.read_parquet(args.current_source_root / "hitter_snapshot.parquet")
    pitcher_snapshot = pl.read_parquet(args.current_source_root / "pitcher_snapshot.parquet")
    hitter_profiles = build_translated_affiliated_profiles(
        hitter_snapshot.select("player_id"),
        source_hitting,
        pl.read_parquet(args.translation_root / "hitter_level_offsets.parquet"),
        exposure_column="plate_appearances",
        component_columns=HITTER_COMPONENTS,
        current_season=current_year,
        reference_season=current_year - 1,
        regression_exposure=1200.0,
    )
    pitcher_profiles = build_translated_affiliated_profiles(
        pitcher_snapshot.select("player_id"),
        source_pitching,
        pl.read_parquet(args.translation_root / "pitcher_level_offsets.parquet"),
        exposure_column="batters_faced",
        component_columns=PITCHER_COMPONENTS,
        current_season=current_year,
        reference_season=current_year - 1,
        regression_exposure=800.0,
    )
    latest_names = pl.concat([
        source_hitting.select("season", "player_id", "player_name"),
        source_pitching.select("season", "player_id", "player_name"),
    ], how="vertical_relaxed").sort("season", descending=True).unique("player_id", keep="first")
    hitter_players = hitter_snapshot.join(latest_names.select("player_id", "player_name"), on="player_id", how="left")
    pitcher_players = pitcher_snapshot.join(latest_names.select("player_id", "player_name"), on="player_id", how="left")
    hitters = _score_hitters(
        hitter_profiles,
        hitter_players,
        _reference_rates(source_hitting, season=current_year - 1, exposure="plate_appearances", components=HITTER_COMPONENTS),
    )
    pitchers = _score_pitchers(
        pitcher_profiles,
        pitcher_players,
        _reference_rates(source_pitching, season=current_year - 1, exposure="batters_faced", components=PITCHER_COMPONENTS),
    )
    if args.external_audit.exists():
        external = pl.read_parquet(args.external_audit).select(
            "player_id",
            pl.col("rank").alias("external_rank_audit_only"),
            pl.col("future_value").alias("external_fv_audit_only"),
        )
        hitters = hitters.join(external, on="player_id", how="left")
        pitchers = pitchers.join(external, on="player_id", how="left")

    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitters": write_canonical_parquet(hitters, table_root / "current_hitter_talent.parquet", table_name="current_basic_hitter_talent").as_record(),
        "pitchers": write_canonical_parquet(pitchers, table_root / "current_pitcher_talent.parquet", table_name="current_basic_pitcher_talent").as_record(),
    }
    hitters.write_csv(table_root / "current_hitter_talent.csv")
    pitchers.write_csv(table_root / "current_pitcher_talent.csv")
    report = {
        "report_schema_version": "0.1",
        "status": "current_present_rate_diagnostic_not_future_ceiling",
        "as_of_date": args.as_of_date,
        "hitters": {
            "players": hitters.height,
            "ranked": hitters.filter(pl.col("ranking_status") == "ranked").height,
        },
        "pitchers": {
            "players": pitchers.height,
            "ranked": pitchers.filter(pl.col("ranking_status") == "ranked").height,
        },
        "method": "validated StatsAPI level translation plus fixed heavy regression; no age or opportunity adjustment",
        "excluded": ["playing time", "position", "defense", "arrival", "contracts", "public FV inputs"],
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "hitters", "pitchers")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
