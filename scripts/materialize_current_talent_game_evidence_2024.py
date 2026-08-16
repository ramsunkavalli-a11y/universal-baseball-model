#!/usr/bin/env python
"""Live 2024 Current Talent player-game evidence POC for AAA + MLB.

This is the first end-to-end chronology-safe materialization gate. It reuses the
already-certified 2024 Performance source paths, projects them to player-game
Current Talent evidence, and then rolls those games back up against the frozen
Performance artifacts. Acceptance requires exact PA, core-event, 12-bin, and
available contact-classification reconciliation independently for AAA and MLB.

The POC intentionally stops before level translation, age priors, shrinkage,
projection, playing time, defense, WAR, or rankings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

import build_batting_performance_level_poc as milb_performance
import build_mlb_batting_performance_2024 as mlb_performance
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_milb_evidence import (
    build_milb_current_talent_player_game_evidence,
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_mlb_evidence import (
    build_mlb_current_talent_player_game_evidence,
)
from universal_baseball.current_talent_reconciliation import (
    reconcile_player_game_to_performance,
)
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import fetch_mlb_team_leagues
from universal_baseball.performance_level_config import performance_level_spec_2024
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory
from universal_baseball.storage import write_canonical_parquet


SEASON = 2024
AAA_LEVEL = "aaa"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aaa-performance-root", type=Path, required=True)
    parser.add_argument("--mlb-performance-root", type=Path, required=True)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-game-evidence-2024"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-game-evidence-2024"),
    )
    return parser.parse_args()


def _find_unique(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename} under {root}, found {len(matches)}: {matches}"
        )
    return matches[0]


def _load_frozen_performance(
    root: Path,
    *,
    suffix: str,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, str]]:
    summary_path = _find_unique(root, f"batting_performance_summary_{SEASON}_{suffix}.parquet")
    profile_path = _find_unique(root, f"batting_performance_bins_{SEASON}_{suffix}.parquet")
    return (
        pl.read_parquet(summary_path),
        pl.read_parquet(profile_path),
        {"summary_path": str(summary_path), "profile_path": str(profile_path)},
    )


def _load_aaa_current_outcomes(
    *,
    work_dir: Path,
    league_ids: frozenset[int],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    raw_dir = work_dir / "player-game"
    raw_dir.mkdir(parents=True, exist_ok=True)
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == AAA_LEVEL
    ]
    if not assets:
        raise RuntimeError("no reusable 2024 AAA player-game assets found")

    frames: list[pl.DataFrame] = []
    for asset in assets:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        frames.append(
            project_milb_player_game_outcomes(
                raw,
                source_asset=asset.name,
                season=SEASON,
                game_type="R",
            )
        )
        del raw

    observations = pl.concat(frames, how="vertical_relaxed")
    resolved, metrics = resolve_milb_player_game_outcomes(observations)
    if metrics["unresolved_player_game_count"]:
        raise RuntimeError(
            "AAA Current Talent outcome evidence has unresolved player-game snapshots: "
            f"{metrics['unresolved_player_game_count']}"
        )
    eligible = resolved.filter(
        (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    observed = {
        int(value)
        for value in eligible.get_column("league_id").drop_nulls().unique().to_list()
    }
    if observed != set(league_ids):
        raise RuntimeError(
            f"AAA Current Talent actual-league coverage mismatch: observed={sorted(observed)}, "
            f"expected={sorted(league_ids)}"
        )
    return resolved, {
        "asset_count": len(assets),
        "asset_names": [a.name for a in assets],
        **metrics,
    }


def _reconcile_and_persist(
    *,
    label: str,
    game_summary: pl.DataFrame,
    game_profile: pl.DataFrame,
    performance_summary: pl.DataFrame,
    performance_profile: pl.DataFrame,
    report_dir: Path,
) -> dict[str, Any]:
    summary_comparison, bin_comparison, metrics = reconcile_player_game_to_performance(
        game_summary,
        game_profile,
        performance_summary,
        performance_profile,
        require_exact=False,
    )
    mismatch_dir = report_dir / "reconciliation"
    mismatch_dir.mkdir(parents=True, exist_ok=True)
    summary_mismatch = summary_comparison.filter(pl.col("has_any_mismatch"))
    bin_mismatch = bin_comparison.filter(pl.col("occurrence_difference") != 0)
    summary_mismatch.write_csv(mismatch_dir / f"{label}_summary_mismatches.csv")
    bin_mismatch.write_csv(mismatch_dir / f"{label}_bin_mismatches.csv")
    if not metrics["exact_reconciliation"]:
        raise RuntimeError(
            f"{label} player-game evidence failed frozen Performance reconciliation: "
            f"summary={metrics['summary_mismatch_row_count']}, "
            f"bins={metrics['profile_bin_mismatch_row_count']}; "
            f"fields={metrics['summary_field_mismatch_counts']}"
        )
    return metrics


def _build_aaa(
    *,
    work_root: Path,
    report_root: Path,
    performance_root: Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    spec = performance_level_spec_2024(AAA_LEVEL)
    work_dir = work_root / "aaa"
    work_dir.mkdir(parents=True, exist_ok=True)

    contacts, contact_metrics = milb_performance._load_reusable_contacts(
        AAA_LEVEL, spec.league_ids, work_dir
    )
    contact_controls, control_metrics = milb_performance._load_player_game_controls(
        AAA_LEVEL, spec.league_ids, work_dir
    )
    authorized, authority_metrics, _ = milb_performance._participant_authority_and_false_negative_gate(
        contacts,
        contact_controls,
        unflagged_sample_games=0,
    )
    classified = milb_performance._classify_contacts(authorized)

    resolved_outcomes, outcome_metrics = _load_aaa_current_outcomes(
        work_dir=work_dir,
        league_ids=spec.league_ids,
    )
    summary, profile, evidence_metrics = build_milb_current_talent_player_game_evidence(
        resolved_outcomes,
        classified,
    )
    frozen_summary, frozen_profile, frozen_paths = _load_frozen_performance(
        performance_root, suffix="aaa"
    )
    reconciliation = _reconcile_and_persist(
        label="aaa",
        game_summary=summary,
        game_profile=profile,
        performance_summary=frozen_summary,
        performance_profile=frozen_profile,
        report_dir=report_root,
    )
    return summary, profile, {
        "source_contacts": contact_metrics,
        "contact_controls": control_metrics,
        "participant_authority": authority_metrics,
        "current_outcomes": outcome_metrics,
        "evidence": evidence_metrics,
        "frozen_performance": frozen_paths,
        "reconciliation": reconciliation,
    }


def _build_mlb(
    *,
    work_root: Path,
    report_root: Path,
    performance_root: Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    # Reuse the certified Savant loader while relocating its quarantine cache to
    # this Current Talent POC so the existing Performance report tree is untouched.
    mlb_performance.WORK_DIR = work_root / "mlb"
    mlb_performance.WORK_DIR.mkdir(parents=True, exist_ok=True)
    savant, captures = mlb_performance._load_savant_season()
    teams, _ = fetch_mlb_team_leagues(SEASON)
    savant = assign_savant_actual_league(savant, teams)

    summary, profile, evidence_metrics = build_mlb_current_talent_player_game_evidence(savant)
    frozen_summary, frozen_profile, frozen_paths = _load_frozen_performance(
        performance_root, suffix="mlb"
    )
    reconciliation = _reconcile_and_persist(
        label="mlb",
        game_summary=summary,
        game_profile=profile,
        performance_summary=frozen_summary,
        performance_profile=frozen_profile,
        report_dir=report_root,
    )
    return summary, profile, {
        "savant_capture_count": len(captures),
        "evidence": evidence_metrics,
        "frozen_performance": frozen_paths,
        "reconciliation": reconciliation,
    }


def main() -> int:
    args = parse_args()
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.report_root.mkdir(parents=True, exist_ok=True)
    table_dir = args.report_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    aaa_summary, aaa_profile, aaa_metrics = _build_aaa(
        work_root=args.work_root,
        report_root=args.report_root,
        performance_root=args.aaa_performance_root,
    )
    mlb_summary, mlb_profile, mlb_metrics = _build_mlb(
        work_root=args.work_root,
        report_root=args.report_root,
        performance_root=args.mlb_performance_root,
    )

    combined_summary, combined_profile, combined_metrics = combine_universal_player_game_evidence(
        [aaa_summary, mlb_summary],
        [aaa_profile, mlb_profile],
        expected_seasons={SEASON},
        require_all_universal_leagues=False,
    )

    artifacts = {
        "aaa_summary": write_canonical_parquet(
            aaa_summary,
            table_dir / "current_talent_game_summary_2024_aaa.parquet",
            table_name="current_talent_game_summary_aaa",
        ).as_record(),
        "aaa_profile": write_canonical_parquet(
            aaa_profile,
            table_dir / "current_talent_game_profile_2024_aaa.parquet",
            table_name="current_talent_game_profile_aaa",
        ).as_record(),
        "mlb_summary": write_canonical_parquet(
            mlb_summary,
            table_dir / "current_talent_game_summary_2024_mlb.parquet",
            table_name="current_talent_game_summary_mlb",
        ).as_record(),
        "mlb_profile": write_canonical_parquet(
            mlb_profile,
            table_dir / "current_talent_game_profile_2024_mlb.parquet",
            table_name="current_talent_game_profile_mlb",
        ).as_record(),
        "combined_summary": write_canonical_parquet(
            combined_summary,
            table_dir / "current_talent_game_summary_2024_aaa_mlb.parquet",
            table_name="current_talent_game_summary_aaa_mlb",
        ).as_record(),
        "combined_profile": write_canonical_parquet(
            combined_profile,
            table_dir / "current_talent_game_profile_2024_aaa_mlb.parquet",
            table_name="current_talent_game_profile_aaa_mlb",
        ).as_record(),
    }

    report = {
        "report_schema_version": 2,
        "scope": {
            "season": SEASON,
            "levels": ["AAA", "MLB"],
            "purpose": "chronology-safe Current Talent game-evidence live POC",
            "evidence_denominator_policy": "ADR 024 separate PA / expected-contact / observed-contact",
        },
        "aaa": aaa_metrics,
        "mlb": mlb_metrics,
        "combined": combined_metrics,
        "storage": artifacts,
        "acceptance": {
            "aaa_exact_frozen_performance_reconciliation": aaa_metrics["reconciliation"][
                "exact_reconciliation"
            ],
            "mlb_exact_frozen_performance_reconciliation": mlb_metrics["reconciliation"][
                "exact_reconciliation"
            ],
            "accepted": bool(
                aaa_metrics["reconciliation"]["exact_reconciliation"]
                and mlb_metrics["reconciliation"]["exact_reconciliation"]
            ),
        },
        "interpretation": (
            "Game-grain observed Performance evidence only. No Current Talent estimate, "
            "level translation, age adjustment, projection, playing time, defense, WAR, or ranking."
        ),
    }
    report_path = args.report_root / "current_talent_game_evidence_2024.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# 2024 Current Talent player-game evidence POC — AAA + MLB",
        "",
        f"- AAA player-games: {aaa_summary.height:,}",
        f"- AAA PA: {aaa_metrics['reconciliation']['game_plate_appearances']:,}",
        f"- AAA contact residual: {aaa_metrics['evidence']['total_contact_count_residual']:+,}",
        f"- AAA frozen Performance reconciliation: {aaa_metrics['reconciliation']['exact_reconciliation']}",
        f"- MLB player-games: {mlb_summary.height:,}",
        f"- MLB PA: {mlb_metrics['reconciliation']['game_plate_appearances']:,}",
        f"- MLB contact residual: {mlb_metrics['evidence']['total_contact_count_residual']:+,}",
        f"- MLB frozen Performance reconciliation: {mlb_metrics['reconciliation']['exact_reconciliation']}",
        f"- Combined player-games: {combined_summary.height:,}",
        f"- Combined actual leagues: {combined_metrics['actual_league_count']}",
        f"- Acceptance: {report['acceptance']['accepted']}",
    ]
    text = "\n".join(lines)
    (args.report_root / "current_talent_game_evidence_2024.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
