#!/usr/bin/env python
"""Materialize final Player Value v1 WAR on the frozen 2024 scoring surface."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import polars as pl

from materialize_player_value_v1_mlb_centering_2024 import (
    ZERO_EXPOSURE_IDS,
    _baserunning_runs,
    _batting_runs,
    _load_json,
    _one_row_by_player,
    _position_rows,
    _profile_lookup,
)
from universal_baseball.player_value_defense_projection import (
    CATCHER_OPPORTUNITY_COMPONENT_KEYS,
    GENERAL_POSITIONS,
    load_frozen_fielding_profiles,
    predict_catcher_c2_skill,
    predict_framing_skill,
    predict_general_range_skill,
    tracked_framing_z_lookup,
    tracked_range_z_lookup,
)
from universal_baseball.player_value_final_aggregation import (
    FINAL_AGGREGATION_ID,
    calculate_final_player_value,
)
from universal_baseball.player_value_mlb_centering_assembly import FixedMLBReferenceMember
from universal_baseball.player_value_positional_adjustment import (
    DEFENSIVE_POSITIONS,
    SCHEDULE_ID,
    calculate_v1_positional_adjustment,
)


EXPECTED_COMPLETE_PLAYER_COUNT = 3045
EXPECTED_FINAL_PLAYER_COUNT = 3051
EXPECTED_OFFICIAL_REFERENCE_COUNT = 651
EXPECTED_POSITION_ONLY_ID = 592205
COMPONENT_TOLERANCE = 1e-10


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _final_members(
    *,
    b2_profile_path: Path,
    playing_time_path: Path,
    position_path: Path,
    dh_path: Path,
) -> tuple[tuple[FixedMLBReferenceMember, ...], dict[str, Any]]:
    b2_ids = set(
        int(value)
        for value in pl.read_parquet(b2_profile_path).get_column("player_id").unique()
    )
    playing_time = _one_row_by_player(
        pl.read_parquet(playing_time_path), label="Playing Time final surface"
    )
    position = pl.read_parquet(position_path).filter(
        (pl.col("current_season") == 2023) & (pl.col("next_season") == 2024)
    )
    dh = pl.read_parquet(dh_path).filter(
        (pl.col("source_year") == 2023) & (pl.col("target_year") == 2024)
    )
    position_ids = set(int(value) for value in position.get_column("player_id"))
    dh_ids = set(int(value) for value in dh.get_column("player_id"))
    complete_ids = b2_ids & set(playing_time) & position_ids & dh_ids
    if len(complete_ids) != EXPECTED_COMPLETE_PLAYER_COUNT:
        raise ValueError(f"complete frozen surface changed: {len(complete_ids)}")
    position_only = (position_ids & dh_ids) - b2_ids - set(playing_time)
    if position_only != {EXPECTED_POSITION_ONLY_ID}:
        raise ValueError(f"Position/Role-only exclusion changed: {sorted(position_only)}")
    if set(ZERO_EXPOSURE_IDS) & complete_ids:
        raise ValueError("outside-snapshot zero rows unexpectedly entered complete surface")
    members = [
        FixedMLBReferenceMember(
            player_id=player_id,
            projected_expected_mlb_pa=float(playing_time[player_id]["predicted_expected_mlb_pa"]),
        )
        for player_id in sorted(complete_ids)
    ]
    members.extend(
        FixedMLBReferenceMember(player_id=player_id, projected_expected_mlb_pa=0.0)
        for player_id in ZERO_EXPOSURE_IDS
    )
    members.sort(key=lambda row: row.player_id)
    if len(members) != EXPECTED_FINAL_PLAYER_COUNT:
        raise ValueError("final population count changed")
    return tuple(members), {
        "b2_player_count": len(b2_ids),
        "playing_time_player_count": len(playing_time),
        "position_player_count": len(position_ids),
        "dh_player_count": len(dh_ids),
        "complete_surface_player_count": len(complete_ids),
        "b2_playing_time_outside_position_role_count": len(
            (b2_ids & set(playing_time)) - (position_ids & dh_ids)
        ),
        "position_role_without_b2_playing_time_ids": sorted(position_only),
        "appended_zero_exposure_ids": list(ZERO_EXPOSURE_IDS),
        "final_player_count": len(members),
    }


def _positional_breakdown(
    members: Iterable[FixedMLBReferenceMember],
    position_by_id: dict[int, dict[str, Any]],
    dh_by_id: dict[int, dict[str, Any]],
) -> tuple[dict[int, float], dict[int, dict[str, float]], dict[int, float]]:
    totals: dict[int, float] = {}
    runs: dict[int, dict[str, float]] = {}
    dh_events: dict[int, float] = {}
    for member in members:
        pid = member.player_id
        if member.projected_expected_mlb_pa == 0:
            outs = {position: 0.0 for position in DEFENSIVE_POSITIONS}
            events = 0.0
        else:
            if pid not in position_by_id or pid not in dh_by_id:
                raise ValueError(f"complete-surface player missing position/DH row: {pid}")
            outs = {
                position: float(position_by_id[pid][f"S0_predicted_outs_{position}"])
                for position in DEFENSIVE_POSITIONS
            }
            events = float(dh_by_id[pid]["B0_raw_dh_role_event_persistence"])
        result = calculate_v1_positional_adjustment(
            outs, projected_dh_role_events=events
        )
        totals[pid] = result.total_runs
        runs[pid] = {**outs, **{f"runs_{key}": value for key, value in result.runs_by_position.items()}}
        dh_events[pid] = events
    return totals, runs, dh_events


def _defense_breakdown(
    members: Iterable[FixedMLBReferenceMember],
    *,
    fielding_root: Path,
    tracked_range_path: Path,
    tracked_framing_path: Path,
    position_rows: dict[int, dict[str, float]],
    catcher_opportunity_path: Path,
    general_parameters_path: Path,
    catcher_parameters_path: Path,
    framing_parameters_path: Path,
    conversion_path: Path,
) -> tuple[dict[int, float], dict[int, dict[str, float]], dict[int, dict[str, Any]], dict[str, int]]:
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
    totals: dict[int, float] = {}
    breakdown: dict[int, dict[str, float]] = {}
    diagnostics: dict[int, dict[str, Any]] = {}
    family_counts: dict[str, int] = {}
    for member in members:
        pid = member.player_id
        if member.projected_expected_mlb_pa == 0:
            totals[pid] = 0.0
            breakdown[pid] = {
                "general_range_runs": 0.0,
                "catcher_throwing_runs": 0.0,
                "catcher_blocking_runs": 0.0,
                "catcher_framing_runs": 0.0,
            }
            diagnostics[pid] = {
                "range_families": {},
                "throwing_family": "B0",
                "blocking_family": "B0",
                "framing_family": "F0",
            }
            continue
        total = 0.0
        general_range_runs = 0.0
        catcher_runs = {"throwing": 0.0, "blocking": 0.0, "framing": 0.0}
        range_families: dict[str, str] = {}
        for position in sorted(GENERAL_POSITIONS):
            profile = profile_by_key.get((2023, pid, position))
            tracked = None
            if profile is not None and profile.get("current_level_group") is not None:
                tracked = range_z.get(
                    (2023, str(profile["current_level_group"]), pid, position)
                )
            skill, family = predict_general_range_skill(
                profile, tracked_z=tracked, parameters=general_parameters
            )
            range_families[position] = family
            family_counts[f"range_{family}"] = family_counts.get(f"range_{family}", 0) + 1
            rate = float(
                conversion["general_range"]["parameters_by_position"][position][
                    "run_rate_per_z_opportunity"
                ]
            )
            component_runs = skill * position_rows[pid][position] * rate
            general_range_runs += component_runs
            total += component_runs

        current_c = profile_by_key.get((2023, pid, "C"))
        prior_c = profile_by_key.get((2022, pid, "C"))
        throwing_skill, throwing_family = predict_catcher_c2_skill(
            current_c,
            prior_c,
            parameters=catcher_parameters["catcher_throwing"],
            component="throwing",
        )
        blocking_skill, blocking_family = predict_catcher_c2_skill(
            current_c,
            prior_c,
            parameters=catcher_parameters["catcher_blocking"],
            component="blocking",
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
            row = opportunity_by_key.get(
                (pid, CATCHER_OPPORTUNITY_COMPONENT_KEYS[component])
            )
            projected_opportunity = float(row[column]) if row is not None else 0.0
            component_runs = (
                skill
                * projected_opportunity
                * float(conversion[conversion_key]["run_rate_per_z_opportunity"])
            )
            catcher_runs[component] = component_runs
            total += component_runs
            family_counts[f"{component}_{family}"] = family_counts.get(
                f"{component}_{family}", 0
            ) + 1
        totals[pid] = total
        breakdown[pid] = {
            "general_range_runs": general_range_runs,
            "catcher_throwing_runs": catcher_runs["throwing"],
            "catcher_blocking_runs": catcher_runs["blocking"],
            "catcher_framing_runs": catcher_runs["framing"],
        }
        diagnostics[pid] = {
            "range_families": range_families,
            "throwing_family": throwing_family,
            "blocking_family": blocking_family,
            "framing_family": framing_family,
        }
    return totals, breakdown, diagnostics, {**profile_audit, **family_counts}


def _distribution(series: pl.Series) -> dict[str, float]:
    return {
        "minimum": float(series.min()),
        "p05": float(series.quantile(0.05, interpolation="linear")),
        "median": float(series.median()),
        "mean": float(series.mean()),
        "p95": float(series.quantile(0.95, interpolation="linear")),
        "maximum": float(series.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--centering-components", type=Path, required=True)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/player-value-v1-final-2024.json"),
    )
    parser.add_argument(
        "--output-table",
        type=Path,
        default=Path("reports/generated/player-value-v1-final-2024.parquet"),
    )
    args = parser.parse_args()
    root = args.input_root
    b2_path = root / "batting-b2/tables/projection_2023_to_2024/frozen_b2_profile.parquet"
    playing_time_path = root / "playing-time/tables/candidate_2024_scored.parquet"
    position_path = root / "position-allocation/allocation_scored.parquet"
    dh_path = root / "dh-exposure/scored_dh_exposure.parquet"
    members, population_audit = _final_members(
        b2_profile_path=b2_path,
        playing_time_path=playing_time_path,
        position_path=position_path,
        dh_path=dh_path,
    )
    batting, batting_audit = _batting_runs(
        members, b2_profile=b2_path, performance_root=root / "mlb-performance"
    )
    position_by_id, dh_by_id = _position_rows(position_path, dh_path)
    positional, position_detail, dh_events = _positional_breakdown(
        members, position_by_id, dh_by_id
    )
    defense, defense_detail, defense_diagnostics, defense_audit = _defense_breakdown(
        members,
        fielding_root=root / "fielding-history",
        tracked_range_path=root / "defense-tracked/tables/tracked_range_proxy_2021_2023.parquet",
        tracked_framing_path=root / "defense-tracked/tables/tracked_framing_proxy_2021_2023.parquet",
        position_rows=position_detail,
        catcher_opportunity_path=root / "catcher-opportunities/scored_opportunities.parquet",
        general_parameters_path=Path("docs/defense-v1-confirmation-parameters.json"),
        catcher_parameters_path=Path("docs/defense-v1-catcher-repair-parameters.json"),
        framing_parameters_path=Path("docs/defense-v1-framing-repair-parameters.json"),
        conversion_path=Path("docs/player-value-v1-defense-native-run-conversion-parameters.json"),
    )
    baserunning, baserunning_audit = _baserunning_runs(
        members,
        steal_selection_path=Path("docs/player-value-v1-steal-projection-selection-result.json"),
        advancement_history_path=root
        / "advancement-recertified/player-value-v1-advancement-history-recertified-2019-2024.parquet",
        advancement_recertification_path=Path(
            "docs/player-value-v1-advancement-source-recertification-result.json"
        ),
        conversion_path=Path("docs/player-value-v1-baserunning-run-conversion-2024.json"),
    )

    centering = _load_json(Path("docs/player-value-v1-mlb-centering-2024.json"))
    environment = _load_json(Path("docs/player-value-v1-mlb-run-environment-2024.json"))
    replacement = _load_json(Path("docs/player-value-v1-replacement-level-2024.json"))
    park = _load_json(Path("docs/player-value-v1-park-neutrality-audit-result.json"))
    centering_rate = float(centering["reference"]["centering_runs_per_pa"])
    replacement_rate = float(replacement["binding"]["replacement_runs_per_pa"])
    rpw = float(environment["runs_per_win"])
    if not park["decision"]["Rpark_frozen_zero"]:
        raise ValueError("park audit no longer freezes Rpark at zero")

    official = pl.read_parquet(args.centering_components)
    if official.height != EXPECTED_OFFICIAL_REFERENCE_COUNT:
        raise ValueError("frozen official component table count changed")
    official_by_id = _one_row_by_player(official, label="official centering components")
    member_ids = {row.player_id for row in members}
    if not set(official_by_id).issubset(member_ids):
        raise ValueError("final population does not contain all official centering members")
    component_deltas: list[float] = []
    for pid, row in official_by_id.items():
        component_deltas.extend(
            (
                abs(batting[pid] - float(row["batting_runs"])),
                abs(baserunning[pid] - float(row["baserunning_runs"])),
                abs(defense[pid] - float(row["defense_runs"])),
                abs(positional[pid] - float(row["positional_runs"])),
            )
        )
    max_component_delta = max(component_deltas)
    if max_component_delta > COMPONENT_TOLERANCE:
        raise ValueError(f"official centering component reproduction failed: {max_component_delta}")

    rows: list[dict[str, Any]] = []
    max_defense_residual = 0.0
    max_rar_residual = 0.0
    for member in members:
        pid = member.player_id
        pa = member.projected_expected_mlb_pa
        detail = defense_detail[pid]
        defense_sum = math.fsum(detail.values())
        max_defense_residual = max(max_defense_residual, abs(defense_sum - defense[pid]))
        centering_runs = pa * centering_rate
        replacement_runs = pa * replacement_rate
        final = calculate_final_player_value(
            batting_runs=batting[pid],
            baserunning_runs=baserunning[pid],
            defense_runs=defense[pid],
            positional_runs=positional[pid],
            centering_runs=centering_runs,
            park_runs=0.0,
            replacement_runs=replacement_runs,
            runs_per_win=rpw,
        )
        direct_sum = (
            batting[pid]
            + baserunning[pid]
            + defense[pid]
            + positional[pid]
            + centering_runs
            + replacement_runs
        )
        max_rar_residual = max(
            max_rar_residual, abs(final.runs_above_replacement - direct_sum)
        )
        position_values = position_detail[pid]
        rows.append(
            {
                "player_id": pid,
                "projected_expected_mlb_pa": pa,
                "batting_runs": batting[pid],
                "baserunning_runs": baserunning[pid],
                **detail,
                "defense_runs": defense[pid],
                **{f"projected_outs_{p}": position_values[p] for p in DEFENSIVE_POSITIONS},
                "projected_dh_role_events": dh_events[pid],
                **{f"positional_{p}": position_values[f"runs_{p}"] for p in (*DEFENSIVE_POSITIONS, "DH")},
                "positional_runs": positional[pid],
                "centering_runs": centering_runs,
                "park_runs": 0.0,
                "replacement_runs": replacement_runs,
                "runs_above_replacement": final.runs_above_replacement,
                "runs_per_win": final.runs_per_win,
                "war": final.war,
                "defense_families_json": json.dumps(defense_diagnostics[pid], sort_keys=True),
                "outside_snapshot_zero_exposure": pid in ZERO_EXPOSURE_IDS,
            }
        )
    if max_defense_residual > COMPONENT_TOLERANCE or max_rar_residual > COMPONENT_TOLERANCE:
        raise ValueError("final additive reconciliation tolerance failed")
    table = pl.DataFrame(rows).sort("player_id")
    zero = table.filter(pl.col("outside_snapshot_zero_exposure"))
    numeric_zero_columns = [
        column
        for column, dtype in table.schema.items()
        if dtype.is_numeric() and column not in {"player_id", "runs_per_win"}
    ]
    if zero.height != 6 or any(zero.get_column(column).abs().max() != 0 for column in numeric_zero_columns):
        raise ValueError("six outside-snapshot rows are not explicit all-zero values")

    ranked = table.sort(["war", "player_id"], descending=[True, False]).with_row_index(
        "rank", offset=1
    )
    war_series = table.get_column("war")
    component_columns = (
        "batting_runs",
        "baserunning_runs",
        "general_range_runs",
        "catcher_throwing_runs",
        "catcher_blocking_runs",
        "catcher_framing_runs",
        "defense_runs",
        "positional_runs",
        "centering_runs",
        "park_runs",
        "replacement_runs",
        "runs_above_replacement",
        "war",
    )
    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_final_2024_frozen_verified",
        "contract": "docs/player-value-v1-final-aggregation-contract.md",
        "reference_season": 2024,
        "aggregation_id": FINAL_AGGREGATION_ID,
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "actions_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "population": population_audit,
        "formula": {
            "runs_above_replacement": "Rbat + Rbr + Rdef + Rpos + Rlg + Rpark + Rrep",
            "runs_per_win": rpw,
            "centering_runs_per_pa": centering_rate,
            "park_runs": 0.0,
            "replacement_runs_per_pa": replacement_rate,
            "gidp_residual_authorized": False,
            "positional_schedule_id": SCHEDULE_ID,
        },
        "aggregate": {
            column: float(table.get_column(column).sum()) for column in component_columns
        },
        "war_distribution": _distribution(war_series),
        "top_25": ranked.select(
            "rank",
            "player_id",
            "projected_expected_mlb_pa",
            "runs_above_replacement",
            "war",
        ).head(25).to_dicts(),
        "qa": {
            "official_reference_player_count": official.height,
            "maximum_official_component_reproduction_delta_runs": max_component_delta,
            "maximum_defense_subtotal_residual_runs": max_defense_residual,
            "maximum_rar_identity_residual_runs": max_rar_residual,
            "tolerance_runs": COMPONENT_TOLERANCE,
            "all_651_official_rows_reproduced": True,
            "six_zero_exposure_rows_preserved": True,
            "park_zero_for_all_rows": table.get_column("park_runs").abs().max() == 0,
        },
        "audits": {
            "batting": batting_audit,
            "baserunning": baserunning_audit,
            "defense": defense_audit,
        },
        "inputs": {
            "centering_components": {
                "run_id": 32384563289,
                "artifact_id": 9412396481,
                "sha256": _sha256(args.centering_components),
            },
            "batting_b2": {"run_id": 32099733186, "artifact_id": 9311172007},
            "playing_time": {"run_id": 32142089669, "artifact_id": 9326300207},
            "position_allocation": {"run_id": 32266007594, "artifact_id": 9370211679},
            "dh_exposure": {"run_id": 32270141291, "artifact_id": 9371840453},
            "catcher_opportunities": {"run_id": 32269076231, "artifact_id": 9371426672},
        },
        "boundary": {
            "upstream_refit": False,
            "2025_outcomes_accessed": False,
            "partial_component_rows_ranked": False,
            "ranking_order": "descending_unrounded_war_then_ascending_player_id",
        },
    }
    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    ranked.write_parquet(args.output_table)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"aggregate": payload["aggregate"], "qa": payload["qa"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
