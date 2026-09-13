#!/usr/bin/env python3
"""Build current Phase 1 skill rates and join them to opportunity/control paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_one_year_talent_development import PITCHER_COMPONENTS as PROCESS_COMPONENTS
from audit_pitcher_process_challenger import _load_process, _process_features
from materialize_current_future_talent import _model_predict, _prepare

from universal_baseball.conditional_war_rates import (
    apply_tango_pitcher_aging,
    build_hitter_conditional_war_rates,
    build_pitcher_conditional_war_rates,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
)
from universal_baseball.pitcher_demographic_adjustment import (
    PITCHER_DEMOGRAPHIC_ADJUSTMENT_ID,
    apply_pitcher_demographic_adjustment,
    build_pitcher_age_level_features,
)
from universal_baseball.projection_lineage import (
    PLAYABLE_OPPORTUNITY_MODEL_ID,
    validate_opportunity_source,
)
from universal_baseball.storage import write_canonical_parquet
from universal_baseball.projection_composition import ilr_transform, inverse_ilr_transform


NON_CONTROL_STATUSES = {"free_agent", "free_agent_eligible"}
HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--forecast-seasons", default="2027,2028,2029,2030,2031,2032")
    parser.add_argument(
        "--skill-source-root", type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    parser.add_argument(
        "--current-source-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--opportunity-root", type=Path,
        default=Path("reports/generated/phase2-workload-paths/2026-09-08/tables"),
    )
    parser.add_argument(
        "--expected-opportunity-model-id",
        default=PLAYABLE_OPPORTUNITY_MODEL_ID,
        help="Fail instead of silently joining an unexpected opportunity model",
    )
    parser.add_argument(
        "--affiliated-skill-root", type=Path,
        default=Path("reports/generated/affiliated-skill-source/tables"),
    )
    parser.add_argument(
        "--translation-root", type=Path,
        default=Path("reports/generated/affiliated-level-translations/tables"),
    )
    parser.add_argument(
        "--demographics-path", type=Path,
        default=Path(
            "reports/generated/player-demographics/tables/player-demographics.parquet"
        ),
    )
    demographic_group = parser.add_mutually_exclusive_group()
    demographic_group.add_argument(
        "--disable-pitcher-demographic-adjustment",
        dest="disable_pitcher_demographic_adjustment",
        action="store_true",
        help="Keep the weak private demographic adjustment off (the default)",
    )
    demographic_group.add_argument(
        "--enable-pitcher-demographic-adjustment",
        dest="disable_pitcher_demographic_adjustment",
        action="store_false",
        help="Build the retained research counterfactual with the weak adjustment on",
    )
    parser.set_defaults(disable_pitcher_demographic_adjustment=True)
    parser.add_argument(
        "--control-path", type=Path,
        default=Path("reports/generated/league-control/2026-09-08/future-control-path.parquet"),
    )
    parser.add_argument(
        "--baserunning-root", type=Path,
        default=Path("reports/generated/current-baserunning-rates"),
    )
    parser.add_argument(
        "--defense-root", type=Path,
        default=Path("reports/generated/current-defense-rates"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-conditional-war-paths"),
    )
    parser.add_argument(
        "--pitcher-process-artifact",
        type=Path,
        default=Path("model_artifacts/pitcher-next-year-process-v1.json"),
    )
    parser.add_argument(
        "--current-basic-talent-root",
        type=Path,
        default=Path("reports/generated/current-basic-talent/2026-09-08/tables"),
    )
    return parser.parse_args()


def _pitcher_process_next_year_profiles(
    basic_path: Path, artifact_path: Path, *, current_season: int
) -> pl.DataFrame | None:
    if not artifact_path.exists():
        return None
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    if artifact.get("status") != "promoted_optional_high_minors_next_year_input":
        return None
    frame = _prepare(
        basic_path, PROCESS_COMPONENTS, player_type="pitcher"
    ).with_columns(pl.lit(current_season).alias("origin_year"))
    process = (
        _process_features(_load_process())
        .filter(pl.col("season") == current_season)
        .drop("season", "bf")
    )
    frame = frame.join(
        process,
        on=["player_id", "level_group"],
        how="inner",
        validate="m:1",
    )
    candidate = _model_predict(frame, PROCESS_COMPONENTS, artifact["fit"])
    reference = _model_predict(
        frame, PROCESS_COMPONENTS, artifact["same_cohort_reference_fit"]
    )
    basis = np.asarray(artifact["fit"]["ilr_basis"], dtype=float)
    present = frame.select([f"p_{key}" for key in PROCESS_COMPONENTS]).to_numpy()
    ages = frame.get_column("age_years").to_numpy()
    baseline_rows = []
    for profile, age in zip(present, ages, strict=True):
        aged = apply_tango_pitcher_aging(
            dict(zip(PROCESS_COMPONENTS, profile, strict=True)),
            current_age=float(age),
            target_age=float(age) + 1.0,
        )
        baseline_rows.append([aged[key] for key in PROCESS_COMPONENTS])
    baseline = np.asarray(baseline_rows)
    adjusted = np.asarray([
        inverse_ilr_transform(
            np.asarray(ilr_transform(base, basis=basis))
            + np.asarray(ilr_transform(candidate[index], basis=basis))
            - np.asarray(ilr_transform(reference[index], basis=basis)),
            basis=basis,
        )
        for index, base in enumerate(baseline)
    ])
    return frame.select("player_id").with_columns(
        *(
            pl.Series(f"next_p_{key}", adjusted[:, index])
            for index, key in enumerate(PROCESS_COMPONENTS)
        )
    )


def _parse_seasons(raw: str) -> tuple[int, ...]:
    seasons = tuple(sorted({int(value.strip()) for value in raw.split(",") if value.strip()}))
    if not seasons:
        raise ValueError("forecast-seasons must not be empty")
    return seasons


def _position_source(roster: pl.DataFrame) -> pl.DataFrame:
    return roster.group_by("player_id").agg(
        pl.col("position_codes").n_unique().alias("position_count"),
        pl.col("position_codes").first().alias("first_position_code"),
    ).with_columns(
        pl.when(pl.col("position_count") == 1)
        .then(pl.col("first_position_code"))
        .otherwise(pl.lit(""))
        .alias("position_code")
    ).select("player_id", "position_code")


def _attach_control(expected: pl.DataFrame, control: pl.DataFrame) -> pl.DataFrame:
    normalized = control.select(
        "player_id",
        pl.col("control_year").alias("season"),
        "control_status",
    ).with_columns(
        (~pl.col("control_status").is_in(sorted(NON_CONTROL_STATUSES))).alias(
            "is_controlled_season"
        )
    )
    return expected.join(normalized, on=["player_id", "season"], how="left").with_columns(
        pl.when(pl.col("control_status").is_null())
        .then(pl.lit("missing"))
        .otherwise(pl.lit("matched"))
        .alias("control_coverage"),
        pl.when(pl.col("control_status").is_null())
        .then(None)
        .when(pl.col("is_controlled_season"))
        .then(pl.col("expected_war"))
        .otherwise(0.0)
        .alias("controlled_expected_war"),
    )


def _coverage(frame: pl.DataFrame) -> dict[str, int]:
    return {
        "player_years": frame.height,
        "control_matched_player_years": frame.filter(pl.col("control_coverage") == "matched").height,
        "control_missing_player_years": frame.filter(pl.col("control_coverage") == "missing").height,
        "population_prior_player_years": frame.filter(pl.col("evidence_tier") == "population_prior").height,
        "affiliated_translated_player_years": frame.filter(
            pl.col("evidence_tier") == "affiliated_translated"
        ).height,
    }


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"), pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"), pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"), pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def main() -> int:
    args = _args()
    seasons = _parse_seasons(args.forecast_seasons)
    skill_root = args.skill_source_root / args.as_of_date.isoformat()
    source_report = json.loads((skill_root / "report.json").read_text(encoding="utf-8"))
    reference = source_report["reference_environment"]
    hitting = pl.read_parquet(skill_root / "tables/mlb_hitting_components.parquet")
    pitching = pl.read_parquet(skill_root / "tables/mlb_pitching_components.parquet")
    hitter_snapshot = pl.read_parquet(args.current_source_root / "hitter_snapshot.parquet")
    pitcher_snapshot = pl.read_parquet(args.current_source_root / "pitcher_snapshot.parquet")
    roster = pl.read_parquet(args.current_source_root / "full_roster_details.parquet")
    hitter_players = hitter_snapshot.select("player_id", "age_years").join(
        _position_source(roster), on="player_id", how="left"
    ).with_columns(pl.col("position_code").fill_null(""))
    pitcher_players = pitcher_snapshot.select("player_id", "age_years")
    affiliated_hitters = _hitter_components(
        pl.read_parquet(args.affiliated_skill_root / "affiliated_hitting_components.parquet")
    )
    affiliated_pitchers = _pitcher_components(
        pl.read_parquet(args.affiliated_skill_root / "affiliated_pitching_components.parquet")
    )
    hitter_profiles = build_translated_affiliated_profiles(
        hitter_players.select("player_id"), affiliated_hitters,
        pl.read_parquet(args.translation_root / "hitter_level_offsets.parquet"),
        exposure_column="plate_appearances", component_columns=HITTER_COMPONENTS,
        current_season=args.as_of_date.year, reference_season=args.as_of_date.year - 1,
        regression_exposure=1200.0,
    )
    pitcher_profiles = build_translated_affiliated_profiles(
        pitcher_players.select("player_id"), affiliated_pitchers,
        pl.read_parquet(args.translation_root / "pitcher_level_offsets.parquet"),
        exposure_column="batters_faced", component_columns=PITCHER_COMPONENTS,
        current_season=args.as_of_date.year, reference_season=args.as_of_date.year - 1,
        regression_exposure=800.0,
    )
    pitcher_features = build_pitcher_age_level_features(
        affiliated_pitchers,
        pl.read_parquet(args.demographics_path),
        pitcher_players.select("player_id"),
        current_season=args.as_of_date.year,
    )
    if not args.disable_pitcher_demographic_adjustment:
        pitcher_profiles = apply_pitcher_demographic_adjustment(
            pitcher_profiles, pitcher_features
        )
        demographic_adjustment_count = pitcher_profiles.filter(
            pl.col("pitcher_demographic_adjustment_applied")
        ).height
    else:
        demographic_adjustment_count = 0

    baserunning_rates = pl.read_parquet(
        args.baserunning_root / args.as_of_date.isoformat()
        / "tables/hitter_baserunning_rates.parquet"
    )
    defense_rates = pl.read_parquet(
        args.defense_root / args.as_of_date.isoformat()
        / "tables/hitter-defense-rates.parquet"
    )
    pitcher_process_profiles = _pitcher_process_next_year_profiles(
        args.current_basic_talent_root / "current_pitcher_talent.parquet",
        args.pitcher_process_artifact,
        current_season=args.as_of_date.year,
    )
    hitter_rates = build_hitter_conditional_war_rates(
        hitter_players, hitting, current_season=args.as_of_date.year,
        forecast_seasons=seasons,
        reference_plate_appearances=int(reference["batting_plate_appearances"]),
        runs_per_win=float(reference["runs_per_win"]),
        affiliated_profiles=hitter_profiles,
        baserunning_rates=baserunning_rates,
        defense_rates=defense_rates,
    )
    pitcher_rates = build_pitcher_conditional_war_rates(
        pitcher_players, pitching, current_season=args.as_of_date.year,
        forecast_seasons=seasons,
        reference_batters_faced=int(reference["pitching_batters_faced"]),
        runs_per_win=float(reference["runs_per_win"]),
        affiliated_profiles=pitcher_profiles,
        affiliated_next_year_profiles=pitcher_process_profiles,
    ).with_columns(
        pl.when(
            (pl.col("evidence_tier") == "affiliated_translated")
            & pl.lit(not args.disable_pitcher_demographic_adjustment)
        )
        .then(pl.lit(PITCHER_DEMOGRAPHIC_ADJUSTMENT_ID))
        .otherwise(None)
        .alias("pitcher_demographic_adjustment_id")
    )
    hitter_opportunity = pl.read_parquet(args.opportunity_root / "hitter_opportunity_paths.parquet")
    pitcher_opportunity = pl.read_parquet(args.opportunity_root / "pitcher_opportunity_paths.parquet")
    opportunity_source = validate_opportunity_source(
        args.opportunity_root,
        expected_model_id=args.expected_opportunity_model_id,
    )
    hitter_expected = hitter_opportunity.join(
        hitter_rates, on=["player_id", "season"], how="inner", validate="1:1"
    ).with_columns(
        (pl.col("mlb_active_probability") * pl.col("conditional_mlb_pa")
         * pl.col("conditional_war_per_600_pa") / 600.0).alias("expected_war")
    )
    pitcher_expected = pitcher_opportunity.join(
        pitcher_rates, on=["player_id", "season"], how="inner", validate="1:1"
    ).with_columns(
        (pl.col("mlb_active_probability") * pl.col("conditional_mlb_bf")
         * pl.col("conditional_war_per_800_bf") / 800.0).alias("expected_war")
    )
    if hitter_expected.height != hitter_opportunity.height or pitcher_expected.height != pitcher_opportunity.height:
        raise RuntimeError("conditional rate coverage differs from opportunity coverage")
    control = pl.read_parquet(args.control_path)
    hitter_paths = _attach_control(hitter_expected, control)
    pitcher_paths = _attach_control(pitcher_expected, control)

    output_root = args.output_root / args.as_of_date.isoformat()
    tables = output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_rates": write_canonical_parquet(hitter_rates, tables / "hitter_conditional_war_rates.parquet", table_name="hitter_conditional_war_rates").as_record(),
        "pitcher_rates": write_canonical_parquet(pitcher_rates, tables / "pitcher_conditional_war_rates.parquet", table_name="pitcher_conditional_war_rates").as_record(),
        "hitter_paths": write_canonical_parquet(hitter_paths, tables / "hitter_expected_war_paths.parquet", table_name="hitter_expected_war_paths").as_record(),
        "pitcher_paths": write_canonical_parquet(pitcher_paths, tables / "pitcher_expected_war_paths.parquet", table_name="pitcher_expected_war_paths").as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_phase1_conditional_war_and_expected_war_paths",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_seasons": list(seasons),
        "reference_environment": reference,
        "hitter": _coverage(hitter_paths),
        "pitcher": _coverage(pitcher_paths),
        "baserunning": baserunning_rates.group_by(
            "baserunning_evidence_tier"
        ).len().sort("baserunning_evidence_tier").to_dicts(),
        "defense": defense_rates.group_by(
            "defense_evidence_tier"
        ).len().sort("defense_evidence_tier").to_dicts(),
        "current_team_depth_used": False,
        "current_season_included": False,
        "control_missing_policy": "null; never inferred uncontrolled",
        "ranking_status": "not_publishable_baseline",
        "opportunity_source": opportunity_source,
        "affiliated_rate_evidence": {
            "hitter_regression_pa": 1200.0,
            "pitcher_regression_bf": 800.0,
            "pitcher_demographic_adjustment_id": (
                None if args.disable_pitcher_demographic_adjustment
                else PITCHER_DEMOGRAPHIC_ADJUSTMENT_ID
            ),
            "pitcher_demographic_adjustment_applied_players": (
                demographic_adjustment_count
            ),
            "pitcher_process_artifact": (
                str(args.pitcher_process_artifact)
                if pitcher_process_profiles is not None else None
            ),
            "pitcher_process_applied_players": (
                0 if pitcher_process_profiles is None else pitcher_rates.filter(
                    pl.col("pitch_process_applied")
                ).get_column("player_id").n_unique()
            ),
            "pitcher_demographic_adjustment_warning": (
                "small 2025 point-score gain; player-bootstrap intervals cross zero; "
                "left-handed confirmation subgroup worsened"
            ),
            "level_evidence_multipliers": {
                "MLB": 1.0, "AAA": 0.5, "AA": 0.3, "HIGH_A": 0.2,
                "SINGLE_A": 0.1, "ROOKIE_COMPLEX": 0.05,
            },
        },
        "limitations": [
            "Catcher defense and defense beyond the adjacent year remain neutral.",
            "Players without recent MLB rate history receive an explicit population prior.",
            "Pitcher contact quality and role-specific replacement/leverage are deferred.",
            "2032 and identities outside the dated control source retain null controlled WAR.",
        ],
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "hitter": report["hitter"], "pitcher": report["pitcher"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
