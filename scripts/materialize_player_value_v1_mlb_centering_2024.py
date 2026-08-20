#!/usr/bin/env python
"""Materialize the frozen numerical 2024 MLB-centering reference."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.player_value_advancement_projection import (
    AdvancementCandidate,
    PlayerSeasonAdvancementSummary,
    advancement_candidates,
    projected_advancement_rate,
    score_all_candidates as score_all_advancement_candidates,
    score_candidate as score_advancement_candidate,
)
from universal_baseball.player_value_baserunning_runs import (
    BaserunningReference,
    project_baserunning_runs,
)
from universal_baseball.player_value_baserunning_sources import (
    SAVANT_BASERUNNING_RUN_VALUE_URL,
    audit_savant_baserunning_rows,
    parse_savant_baserunning_csv,
    savant_baserunning_query_params,
)
from universal_baseball.player_value_batting_runs import (
    build_v1_mlb_batting_reference,
    calculate_v1_projected_batting_runs,
)
from universal_baseball.player_value_defense_projection import (
    GENERAL_POSITIONS,
    load_frozen_fielding_profiles,
    predict_catcher_c2_skill,
    predict_framing_skill,
    predict_general_range_skill,
    tracked_framing_z_lookup,
    tracked_range_z_lookup,
)
from universal_baseball.player_value_mlb_centering import (
    CENTERING_TOLERANCE_RUNS,
    build_fixed_mlb_centering_reference,
)
from universal_baseball.player_value_mlb_centering_assembly import (
    FixedMLBReferenceMember,
    assemble_fixed_mlb_reference_components,
)
from universal_baseball.player_value_positional_adjustment import (
    DEFENSIVE_POSITIONS,
    calculate_v1_positional_adjustment,
)
from universal_baseball.player_value_steal_data import build_loo_player_season_summaries
from universal_baseball.player_value_steal_sources import (
    fetch_milb_steal_stints,
    fetch_mlb_steal_stints,
)
from universal_baseball.player_value_steal_projection import (
    PlayerSeasonStealSummary,
    StealCandidate,
    attempt_multiplier,
    success_log_odds_residual,
)


REFERENCE_SEASON = 2024
HISTORY_SEASONS = (2019, 2020, 2021, 2022, 2023)
ADVANCEMENT_SOURCE_SEASONS = (*HISTORY_SEASONS, 2024)
EXPECTED_PLAYER_COUNT = 651
EXPECTED_PROJECTED_PA = 148948.26306286638
EXPECTED_OFFICIAL_PA = 182449
ZERO_EXPOSURE_IDS = (543518, 593934, 622491, 656555, 666158, 808982)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _one_row_by_player(frame: pl.DataFrame, *, label: str) -> dict[int, dict[str, Any]]:
    duplicates = frame.group_by("player_id").len().filter(pl.col("len") != 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} must contain one row per player")
    return {int(row["player_id"]): row for row in frame.iter_rows(named=True)}


def _membership(path: Path) -> tuple[FixedMLBReferenceMember, ...]:
    frame = pl.read_parquet(path).sort("player_id")
    required = {"player_id", "projected_expected_mlb_pa", "playing_time_zero_exposure_fallback"}
    if not required.issubset(frame.columns) or frame.height != EXPECTED_PLAYER_COUNT:
        raise ValueError("frozen membership artifact failed its binding shape contract")
    members = tuple(
        FixedMLBReferenceMember(
            player_id=int(row["player_id"]),
            projected_expected_mlb_pa=float(row["projected_expected_mlb_pa"]),
        )
        for row in frame.iter_rows(named=True)
    )
    total = math.fsum(row.projected_expected_mlb_pa for row in members)
    if not math.isclose(total, EXPECTED_PROJECTED_PA, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"projected PA anchor changed: {total}")
    observed_zero = tuple(
        int(row["player_id"])
        for row in frame.filter(pl.col("playing_time_zero_exposure_fallback")).iter_rows(named=True)
    )
    if observed_zero != ZERO_EXPOSURE_IDS:
        raise ValueError(f"zero-exposure membership changed: {observed_zero}")
    if any(row.projected_expected_mlb_pa != 0.0 for row in members if row.player_id in ZERO_EXPOSURE_IDS):
        raise ValueError("zero-exposure members must retain projected PA 0.0")
    return members


def _batting_runs(
    members: Iterable[FixedMLBReferenceMember],
    *,
    b2_profile: Path,
    performance_root: Path,
) -> tuple[dict[int, float], dict[str, Any]]:
    reference = build_v1_mlb_batting_reference(
        pl.read_parquet(performance_root / "tables/batting_performance_summary_2024_mlb.parquet"),
        pl.read_parquet(performance_root / "tables/batting_performance_bins_2024_mlb.parquet"),
        pl.read_parquet(performance_root / "tables/league_bin_values_2024_mlb.parquet"),
        season=REFERENCE_SEASON,
    )
    profile = pl.read_parquet(b2_profile)
    probabilities: dict[int, dict[str, float]] = {}
    for player_id, rows in profile.group_by("player_id"):
        pid = int(player_id[0])
        probabilities[pid] = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in rows.iter_rows(named=True)
        }
    result: dict[int, float] = {}
    for member in members:
        if member.projected_expected_mlb_pa == 0.0:
            result[member.player_id] = 0.0
            continue
        if member.player_id not in probabilities:
            raise ValueError(f"positive-exposure member missing frozen B2 profile: {member.player_id}")
        projection = calculate_v1_projected_batting_runs(
            probabilities[member.player_id],
            projected_expected_mlb_pa=member.projected_expected_mlb_pa,
            reference=reference,
        )
        result[member.player_id] = projection.projected_batting_runs_above_mlb_reference
    return result, {
        "conversion_id": reference.batting_run_conversion_id,
        "reference_core_event_rate_per_pa": reference.core_event_rate_per_pa,
        "reference_run_value_per_core_event": reference.reference_run_value_per_core_event,
    }


def _position_rows(position_path: Path, dh_path: Path) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    position = pl.read_parquet(position_path).filter(
        (pl.col("current_season") == 2023) & (pl.col("next_season") == 2024)
    )
    dh = pl.read_parquet(dh_path).filter(
        (pl.col("source_year") == 2023) & (pl.col("target_year") == 2024)
    )
    return _one_row_by_player(position, label="position allocation"), _one_row_by_player(dh, label="DH exposure")


def _positional_runs(
    members: Iterable[FixedMLBReferenceMember],
    position_by_id: dict[int, dict[str, Any]],
    dh_by_id: dict[int, dict[str, Any]],
) -> tuple[dict[int, float], dict[int, dict[str, float]]]:
    runs: dict[int, float] = {}
    outs_by_id: dict[int, dict[str, float]] = {}
    for member in members:
        if member.projected_expected_mlb_pa == 0.0:
            outs_by_id[member.player_id] = {position: 0.0 for position in DEFENSIVE_POSITIONS}
            runs[member.player_id] = 0.0
            continue
        if member.player_id not in position_by_id or member.player_id not in dh_by_id:
            raise ValueError(f"positive-exposure member missing position/DH row: {member.player_id}")
        position_row = position_by_id[member.player_id]
        outs = {
            position: float(position_row[f"S0_predicted_outs_{position}"])
            for position in DEFENSIVE_POSITIONS
        }
        adjustment = calculate_v1_positional_adjustment(
            outs,
            projected_dh_role_events=float(
                dh_by_id[member.player_id]["B0_raw_dh_role_event_persistence"]
            ),
        )
        outs_by_id[member.player_id] = outs
        runs[member.player_id] = adjustment.total_runs
    return runs, outs_by_id


def _profile_lookup(frame: pl.DataFrame) -> dict[tuple[int, int, str], dict[str, Any]]:
    return {
        (int(row["season"]), int(row["player_id"]), str(row["position"])): row
        for row in frame.iter_rows(named=True)
    }


def _defense_runs(
    members: Iterable[FixedMLBReferenceMember],
    *,
    fielding_root: Path,
    tracked_range_path: Path,
    tracked_framing_path: Path,
    position_outs: dict[int, dict[str, float]],
    catcher_opportunity_path: Path,
    general_parameters_path: Path,
    catcher_parameters_path: Path,
    framing_parameters_path: Path,
    conversion_path: Path,
) -> tuple[dict[int, float], dict[int, dict[str, Any]], dict[str, int]]:
    profiles, profile_audit = load_frozen_fielding_profiles(fielding_root)
    profile_by_key = _profile_lookup(profiles)
    range_z = tracked_range_z_lookup(pl.read_parquet(tracked_range_path))
    framing_z = tracked_framing_z_lookup(pl.read_parquet(tracked_framing_path))
    general_parameters = _load_json(general_parameters_path)["parameters"]["general"]
    catcher_parameters = _load_json(catcher_parameters_path)["parameters"]
    framing_parameters = _load_json(framing_parameters_path)["parameters"]
    conversion = _load_json(conversion_path)
    opportunity = pl.read_parquet(catcher_opportunity_path).filter(
        (pl.col("source_year") == 2023) & (pl.col("target_year") == 2024)
    )
    opportunity_by_key = {
        (int(row["player_id"]), str(row["component"])): row
        for row in opportunity.iter_rows(named=True)
    }

    result: dict[int, float] = {}
    diagnostics: dict[int, dict[str, Any]] = {}
    family_counts: dict[str, int] = {}
    for member in members:
        pid = member.player_id
        if member.projected_expected_mlb_pa == 0.0:
            result[pid] = 0.0
            diagnostics[pid] = {"range_families": {}, "throwing_family": "B0", "blocking_family": "B0", "framing_family": "F0"}
            continue
        total = 0.0
        range_families: dict[str, str] = {}
        for position in sorted(GENERAL_POSITIONS):
            profile = profile_by_key.get((2023, pid, position))
            tracked = None
            if profile is not None and profile.get("current_level_group") is not None:
                tracked = range_z.get((2023, str(profile["current_level_group"]), pid, position))
            skill, family = predict_general_range_skill(
                profile, tracked_z=tracked, parameters=general_parameters
            )
            range_families[position] = family
            family_counts[f"range_{family}"] = family_counts.get(f"range_{family}", 0) + 1
            rate = float(conversion["general_range"]["parameters_by_position"][position]["run_rate_per_z_opportunity"])
            total += skill * position_outs[pid][position] * rate

        current_c = profile_by_key.get((2023, pid, "C"))
        prior_c = profile_by_key.get((2022, pid, "C"))
        throwing_skill, throwing_family = predict_catcher_c2_skill(
            current_c, prior_c, parameters=catcher_parameters["catcher_throwing"], component="throwing"
        )
        blocking_skill, blocking_family = predict_catcher_c2_skill(
            current_c, prior_c, parameters=catcher_parameters["catcher_blocking"], component="blocking"
        )
        tracked_c = None
        if current_c is not None and current_c.get("current_level_group") is not None:
            tracked_c = framing_z.get((2023, str(current_c["current_level_group"]), pid))
        framing_skill, framing_family = predict_framing_skill(
            current_c, tracked_z=tracked_c, parameters=framing_parameters
        )
        component_specs = (
            ("throwing", throwing_skill, throwing_family, "H1_fixed_50_50_hybrid", "catcher_throwing"),
            ("blocking", blocking_skill, blocking_family, "H1_fixed_50_50_hybrid", "catcher_blocking"),
            ("framing", framing_skill, framing_family, "B0_raw_persistence", "catcher_framing"),
        )
        for component, skill, family, column, conversion_key in component_specs:
            row = opportunity_by_key.get((pid, component))
            projected_opportunity = float(row[column]) if row is not None else 0.0
            total += skill * projected_opportunity * float(conversion[conversion_key]["run_rate_per_z_opportunity"])
            family_counts[f"{component}_{family}"] = family_counts.get(f"{component}_{family}", 0) + 1
        result[pid] = total
        diagnostics[pid] = {
            "range_families": range_families,
            "throwing_family": throwing_family,
            "blocking_family": blocking_family,
            "framing_family": framing_family,
        }
    return result, diagnostics, {**profile_audit, **family_counts}


def _assert_capture_hashes(actual: list[dict[str, Any]], expected: list[dict[str, Any]], *, label: str) -> None:
    keys = ("season", "league_id", "offset", "response_sha256") if label == "MLB" else ("year", "asset_id", "response_sha256")
    actual_projection = sorted(tuple(row.get(key) for key in keys) for row in actual)
    expected_projection = sorted(
        tuple(row.get(key) for key in keys)
        for row in expected
        if int(row.get("season", row.get("year"))) in HISTORY_SEASONS
    )
    if actual_projection != expected_projection:
        raise ValueError(f"{label} steal captures differ from the frozen selection result")


def _advancement_history(
    source_audit_path: Path,
    selection_path: Path,
    session: requests.Session,
) -> tuple[list[PlayerSeasonAdvancementSummary], list[dict[str, Any]]]:
    audit = _load_json(source_audit_path)
    certified = {
        int(row["season"]): str(row["response_sha256"])
        for row in audit["mlb_statcast_advancement"]["captures"]
    }
    summaries: list[PlayerSeasonAdvancementSummary] = []
    captures: list[dict[str, Any]] = []
    for season in ADVANCEMENT_SOURCE_SEASONS:
        response = session.get(
            SAVANT_BASERUNNING_RUN_VALUE_URL,
            params=savant_baserunning_query_params(season),
            timeout=120,
        )
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        rows = parse_savant_baserunning_csv(response.content.decode("utf-8-sig"))
        if not audit_savant_baserunning_rows(rows)["advancement_source_usable"]:
            raise ValueError(f"Savant advancement capture is unusable for {season}")
        summaries.extend(
            PlayerSeasonAdvancementSummary(
                player_id=int(float(row["player_id"])),
                season=season,
                runs_xb=float(row["runner_runs_xb"]),
                opportunities_xb=float(row["n_runner_moved_xb"]),
            )
            for row in rows
        )
        captures.append(
            {
                "season": season,
                "certified_response_sha256": certified[season],
                "live_response_sha256": digest,
                "byte_hash_matches": digest == certified[season],
                "row_count": len(rows),
            }
        )

    # Savant can change non-model CSV bytes (for example names). Fail closed
    # unless every frozen development and confirmation score still reproduces.
    frozen = _load_json(selection_path)
    development = {
        score.candidate_id: asdict(score)
        for score in score_all_advancement_candidates(
            summaries, target_years=(2022, 2023)
        )
    }
    expected_development = {
        row["candidate_id"]: row for row in frozen["development_scores"]
    }
    if development != expected_development:
        changed = [
            candidate_id
            for candidate_id in sorted(development)
            if development[candidate_id] != expected_development.get(candidate_id)
        ]
        first = changed[0]
        raise ValueError(
            "Savant byte drift changed frozen advancement development scores: "
            f"candidates={changed}; first_actual={development[first]}; "
            f"first_expected={expected_development.get(first)}"
        )
    candidates = {row.candidate_id: row for row in advancement_candidates()}
    confirmation = {
        candidate_id: asdict(
            score_advancement_candidate(
                summaries,
                candidates[candidate_id],
                target_years=(2024,),
            )
        )
        for candidate_id in ("A0_neutral", frozen["frozen_candidate_id"])
    }
    expected_confirmation = {
        row["candidate_id"]: row for row in frozen["confirmation_scores"]
    }
    if confirmation != expected_confirmation:
        raise ValueError("Savant byte drift changed frozen advancement confirmation scores")
    return summaries, captures


def _baserunning_runs(
    members: Iterable[FixedMLBReferenceMember],
    *,
    steal_selection_path: Path,
    advancement_audit_path: Path,
    advancement_selection_path: Path,
    conversion_path: Path,
) -> tuple[dict[int, float], dict[str, Any]]:
    selection = _load_json(steal_selection_path)
    with requests.Session() as session:
        session.headers.setdefault("User-Agent", "universal-baseball-model-mlb-centering/0.1")
        mlb_stints, mlb_captures = fetch_mlb_steal_stints(HISTORY_SEASONS, session=session)
        milb_stints, milb_captures = fetch_milb_steal_stints(HISTORY_SEASONS, session=session)
        advancement, advancement_captures = _advancement_history(
            advancement_audit_path, advancement_selection_path, session
        )
    _assert_capture_hashes(mlb_captures, selection["source"]["mlb_captures"], label="MLB")
    _assert_capture_hashes(milb_captures, selection["source"]["milb_captures"], label="MiLB")
    steal_history, environment_audit = build_loo_player_season_summaries([*mlb_stints, *milb_stints])
    conversion = _load_json(conversion_path)
    reference = BaserunningReference(**conversion["reference"])
    attempt_candidate = StealCandidate("B2_k5", "B2", 5.0)
    success_candidate = StealCandidate("B2_k45", "B2", 45.0)
    advancement_candidate = AdvancementCandidate("A2_k25", "A2", 25.0)
    result: dict[int, float] = {}
    for member in members:
        target_steal = PlayerSeasonStealSummary(
            player_id=member.player_id,
            season=REFERENCE_SEASON,
            tier="MLB",
            opportunity_proxy=0.0,
            attempts=0.0,
            successes=0.0,
            expected_attempts=0.0,
            expected_successes=0.0,
        )
        target_advancement = PlayerSeasonAdvancementSummary(
            player_id=member.player_id,
            season=REFERENCE_SEASON,
            runs_xb=0.0,
            opportunities_xb=0.0,
        )
        projection = project_baserunning_runs(
            projected_mlb_pa=member.projected_expected_mlb_pa,
            attempt_multiplier=attempt_multiplier(target_steal, steal_history, attempt_candidate),
            success_logodds_residual=success_log_odds_residual(target_steal, steal_history, success_candidate),
            advancement_rate=projected_advancement_rate(target_advancement, advancement, advancement_candidate),
            reference=reference,
        )
        result[member.player_id] = projection.baserunning_runs
    return result, {
        "models": conversion["frozen_models"],
        "steal_environment_audit": asdict(environment_audit),
        "steal_history_rows": len(steal_history),
        "advancement_history_rows": len(advancement),
        "advancement_capture_replay": advancement_captures,
        "advancement_frozen_selection_scores_reproduced_exactly": True,
        "all_capture_hashes_reconciled": True,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=Path("docs/player-value-v1-mlb-centering-2024.json"))
    parser.add_argument("--output-components", type=Path, default=Path("reports/generated/player-value-v1-mlb-centering-2024-components.parquet"))
    parser.add_argument("--source-map", type=Path, default=Path("docs/player-value-v1-mlb-centering-source-map-2024.json"))
    args = parser.parse_args()
    root = args.input_root
    members = _membership(root / "membership/reports/generated/player-value-v1-mlb-centering-2024-membership.parquet")
    batting, batting_audit = _batting_runs(
        members,
        b2_profile=root / "batting-b2/tables/projection_2023_to_2024/frozen_b2_profile.parquet",
        performance_root=root / "mlb-performance",
    )
    position_by_id, dh_by_id = _position_rows(
        root / "position-allocation/allocation_scored.parquet",
        root / "dh-exposure/scored_dh_exposure.parquet",
    )
    positional, position_outs = _positional_runs(members, position_by_id, dh_by_id)
    defense, defense_diagnostics, defense_audit = _defense_runs(
        members,
        fielding_root=root / "fielding-history",
        tracked_range_path=root / "defense-tracked/tables/tracked_range_proxy_2021_2023.parquet",
        tracked_framing_path=root / "defense-tracked/tables/tracked_framing_proxy_2021_2023.parquet",
        position_outs=position_outs,
        catcher_opportunity_path=root / "catcher-opportunities/scored_opportunities.parquet",
        general_parameters_path=Path("docs/defense-v1-confirmation-parameters.json"),
        catcher_parameters_path=Path("docs/defense-v1-catcher-repair-parameters.json"),
        framing_parameters_path=Path("docs/defense-v1-framing-repair-parameters.json"),
        conversion_path=Path("docs/player-value-v1-defense-native-run-conversion-parameters.json"),
    )
    baserunning, baserunning_audit = _baserunning_runs(
        members,
        steal_selection_path=Path("docs/player-value-v1-steal-projection-selection-result.json"),
        advancement_audit_path=Path("docs/player-value-v1-baserunning-source-audit-result.json"),
        advancement_selection_path=Path("docs/player-value-v1-advancement-projection-selection-result.json"),
        conversion_path=Path("docs/player-value-v1-baserunning-run-conversion-2024.json"),
    )
    assembled = assemble_fixed_mlb_reference_components(
        members,
        batting_runs_by_player=batting,
        baserunning_runs_by_player=baserunning,
        defense_runs_by_player=defense,
        positional_runs_by_player=positional,
    )
    reference = build_fixed_mlb_centering_reference(assembled)
    if reference.reference_player_count != EXPECTED_PLAYER_COUNT:
        raise ValueError("numerical centering player count changed")
    if abs(reference.post_centering_residual_runs) > CENTERING_TOLERANCE_RUNS:
        raise ValueError("numerical centering residual exceeds binding tolerance")
    component_rows = []
    for row in assembled:
        if row.player_id in ZERO_EXPOSURE_IDS and any(
            value != 0.0 for value in (row.batting_runs, row.baserunning_runs, row.defense_runs, row.positional_runs)
        ):
            raise ValueError(f"zero-exposure player has nonzero component: {row.player_id}")
        component_rows.append(
            {
                **asdict(row),
                "raw_above_average_runs": row.batting_runs + row.baserunning_runs + row.defense_runs + row.positional_runs,
                "centering_runs": row.projected_expected_mlb_pa * reference.centering_runs_per_pa,
                "defense_families_json": json.dumps(defense_diagnostics[row.player_id], sort_keys=True),
            }
        )
    args.output_components.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(component_rows).sort("player_id").write_parquet(args.output_components)
    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_mlb_centering_2024_frozen_verified",
        "verified_source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "materialization_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "reference": asdict(reference),
        "membership": {
            "official_positive_pa_player_count": EXPECTED_PLAYER_COUNT,
            "official_observed_pa_anchor": EXPECTED_OFFICIAL_PA,
            "projected_exposure_pa": reference.aggregate_projected_mlb_pa,
            "zero_exposure_player_ids": list(ZERO_EXPOSURE_IDS),
        },
        "component_audits": {
            "batting": batting_audit,
            "baserunning": baserunning_audit,
            "defense": defense_audit,
            "position": {"model": "S0 prior-share allocation + B0 raw DH persistence"},
        },
        "source_map": str(args.source_map).replace("\\", "/"),
        "source_map_sha256": _sha256(args.source_map),
        "components_artifact": str(args.output_components).replace("\\", "/"),
        "verification": {
            "replacement_excluded": True,
            "realized_2024_player_components_excluded": True,
            "projected_pa_denominator_used": True,
            "official_pa_anchor_preserved": True,
            "all_651_component_rows_explicit": len(component_rows) == EXPECTED_PLAYER_COUNT,
            "six_zero_exposure_rows_explicit_and_zero": True,
            "residual_within_tolerance": abs(reference.post_centering_residual_runs) <= reference.tolerance_runs,
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["reference"], indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        failure_path = str(os.environ.get("CENTERING_FAILURE_JSON") or "").strip()
        if failure_path:
            path = Path(failure_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1",
                        "status": "player_value_v1_mlb_centering_2024_failed_closed",
                        "materialization_run_id": int(os.environ["GITHUB_RUN_ID"])
                        if os.environ.get("GITHUB_RUN_ID")
                        else None,
                        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
                        "exception_type": type(exc).__name__,
                        "failure": str(exc),
                        "boundary": {
                            "centering_json_frozen": False,
                            "park_neutrality_audit_opened": False,
                            "replacement_included": False,
                            "model_refit": False,
                            "model_reselection": False,
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        raise
