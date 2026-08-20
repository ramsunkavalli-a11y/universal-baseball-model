#!/usr/bin/env python
"""Audit whether Rookie/complex Stats API playEvents are real pitch sequences.

The source PBP release is used only as a deterministic game inventory. The
actual diagnostic is computed from current official MLB Stats API playByPlay so
we can detect a limitation in the underlying game-entry feed itself rather than
confusing it with an armstjc parser defect.

2024 June is used for both the Rookie/complex sample and a Single-A control.
For every actual league in the two source assets we spread a modest sample of
games across the observed date range and measure:

- recorded pitch-event count distributions for strikeouts, walks and BIP;
- outcome-minimal signatures (3-pitch Ks, 4-pitch BBs, 1-pitch BIP);
- whether official ``pitchNumber`` reveals gaps beyond the recorded events;
- pitchData coverage, reported only as a diagnostic rather than a fidelity
  requirement because tracking availability is structurally level-dependent.

This script does not reject any league automatically. It produces evidence for
an explicit coverage-tier decision.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any


import audit_milb_bin_value_stability as stability
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.pitch_sequence_fidelity import (
    summarize_game_pitch_sequences,
    summarize_league,
)


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
ROOKIE_ASSET = "2024_6_rk_pbp.csv"
SINGLE_A_ASSET = "2024_6_a_pbp.csv"
DEFAULT_GAMES_PER_LEAGUE = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-per-league", type=int, default=DEFAULT_GAMES_PER_LEAGUE)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/pitch-sequence-fidelity"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/pitch-sequence-fidelity"),
    )
    return parser.parse_args()


def _load_inventory(asset: str, work_dir: Path, max_games: int) -> dict[str, Any]:
    path = work_dir / asset
    metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=240)
    frame = read_quarantined_csv(path)
    if frame.is_empty():
        raise RuntimeError(f"source inventory asset is empty: {asset}")
    orders = stability._inventory_orders(frame, asset, max_games=max_games)
    if not orders:
        raise RuntimeError(f"source inventory has no leagues/games: {asset}")
    return {"metadata": metadata, "orders": orders}


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def _metric(summary: dict[str, Any], outcome: str, metric: str) -> float | None:
    value = summary["outcomes"][outcome].get(metric)
    return None if value is None else float(value)


def _comparison_row(
    league: dict[str, Any],
    summary: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    result = {
        "league_id": league["league_id"],
        "league_name": league["league_name"],
        "source_class": league["source_class"],
        "pa_count": summary["pa_count"],
        "game_count": summary["game_count"],
    }
    for outcome, prefix in (
        ("strikeout", "k"),
        ("walk", "bb"),
        ("batted_ball", "bip"),
    ):
        for metric in (
            "mean_recorded_pitch_events",
            "exact_minimum_pitch_count_rate",
            "outcome_minimal_clean_signature_rate",
            "any_pitch_number_gap_rate",
        ):
            own = _metric(summary, outcome, metric)
            baseline = _metric(control, outcome, metric)
            result[f"{prefix}_{metric}"] = own
            result[f"{prefix}_{metric}_delta_vs_single_a"] = (
                own - baseline if own is not None and baseline is not None else None
            )
    return result


def _examples(rows: list[dict[str, Any]], *, limit_per_group: int = 5) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: dict[str, int] = defaultdict(int)
    for row in rows:
        group = str(row["outcome_group"])
        if group not in {"strikeout", "walk", "batted_ball"}:
            continue
        if not bool(row["outcome_minimal_clean_signature"]):
            continue
        if seen[group] >= limit_per_group:
            continue
        seen[group] += 1
        result.append(
            {
                "game_pk": row["game_pk"],
                "at_bat_index": row["at_bat_index"],
                "outcome_group": group,
                "event_type": row["event_type"],
                "description": row["description"],
                "recorded_pitch_event_count": row["recorded_pitch_event_count"],
                "pitch_numbers": row["pitch_numbers"],
                "pitch_number_gap": row["pitch_number_gap"],
                "ball_flag_count": row["ball_flag_count"],
                "strike_flag_count": row["strike_flag_count"],
                "pitch_codes": row["pitch_codes"],
            }
        )
    return result


def main() -> int:
    args = parse_args()
    if args.games_per_league < 5:
        raise ValueError("games-per-league must be at least 5")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    rookie = _load_inventory(ROOKIE_ASSET, args.work_dir, args.games_per_league)
    single_a = _load_inventory(SINGLE_A_ASSET, args.work_dir, args.games_per_league)

    selected: list[dict[str, Any]] = []
    league_meta: dict[str, dict[str, Any]] = {}
    for source_class, inventory in (("rookie_complex", rookie), ("single_a_control", single_a)):
        for key, games in sorted(inventory["orders"].items()):
            season, league_id, league_name = key
            if len(games) < args.games_per_league:
                raise RuntimeError(
                    f"{source_class} {league_name} has only {len(games)} sampled games; "
                    f"expected {args.games_per_league}"
                )
            environment_id = f"{season}:{league_id}"
            league_meta[environment_id] = {
                "season": int(season),
                "league_id": int(league_id),
                "league_name": str(league_name),
                "source_class": source_class,
                "game_count": len(games),
            }
            for game in games:
                selected.append(
                    {
                        **game,
                        "environment_id": environment_id,
                        "source_class": source_class,
                    }
                )

    rows_by_environment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    official_sha256: dict[int, str] = {}
    session = new_official_session()
    try:
        for game in sorted(
            selected,
            key=lambda item: (
                item["environment_id"],
                item["game_date"],
                item["game_pk"],
            ),
        ):
            capture = capture_official_json(
                f"game/{game['game_pk']}/playByPlay",
                session=session,
            )
            if not isinstance(capture.data, dict):
                raise RuntimeError(f"official game {game['game_pk']} PBP is not an object")
            official_sha256[int(game["game_pk"])] = capture.content_sha256
            rows_by_environment[str(game["environment_id"])].extend(
                summarize_game_pitch_sequences(
                    int(game["game_pk"]),
                    capture.data,
                    season=int(game["season"]),
                    league_id=int(game["league_id"]),
                    league_name=str(game["league_name"]),
                )
            )
    finally:
        session.close()

    summaries = {
        environment_id: summarize_league(rows)
        for environment_id, rows in sorted(rows_by_environment.items())
    }
    single_a_rows = [
        row
        for environment_id, rows in rows_by_environment.items()
        if league_meta[environment_id]["source_class"] == "single_a_control"
        for row in rows
    ]
    if not single_a_rows:
        raise RuntimeError("Single-A control produced no official true PAs")
    control = summarize_league(single_a_rows)

    comparisons = [
        _comparison_row(league_meta[environment_id], summaries[environment_id], control)
        for environment_id in sorted(summaries)
        if league_meta[environment_id]["source_class"] == "rookie_complex"
    ]

    payload = {
        "report_schema_version": 1,
        "status": "official_pitch_sequence_fidelity_diagnostic",
        "interpretation_guardrail": (
            "The source release is used only to select games/league labels. Pitch-sequence "
            "metrics come from official Stats API playByPlay. A correct PA outcome does not "
            "imply complete pitch-by-pitch entry. No league is auto-certified from this report."
        ),
        "games_per_league": args.games_per_league,
        "assets": {
            "rookie_complex": {
                "name": ROOKIE_ASSET,
                "sha256": rookie["metadata"]["sha256"],
            },
            "single_a_control": {
                "name": SINGLE_A_ASSET,
                "sha256": single_a["metadata"]["sha256"],
            },
        },
        "league_meta": league_meta,
        "league_summaries": summaries,
        "single_a_pooled_control": control,
        "rookie_vs_single_a": comparisons,
        "minimal_signature_examples": {
            environment_id: _examples(rows)
            for environment_id, rows in sorted(rows_by_environment.items())
        },
        "official_game_snapshot_sha256": {
            str(game_pk): sha for game_pk, sha in sorted(official_sha256.items())
        },
    }
    (args.report_dir / "pitch_sequence_fidelity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Official MiLB pitch-sequence fidelity diagnostic",
        "",
        f"- Games per actual league: {args.games_per_league}",
        f"- Rookie/complex inventory: `{ROOKIE_ASSET}`",
        f"- Single-A control inventory: `{SINGLE_A_ASSET}`",
        "- Pitch evidence: current official MLB Stats API `game/{gamePk}/playByPlay`",
        "",
        "## Pooled Single-A control",
        "",
    ]
    for outcome, label in (
        ("strikeout", "K"),
        ("walk", "BB"),
        ("batted_ball", "BIP"),
    ):
        value = control["outcomes"][outcome]
        lines.append(
            f"- {label}: n={value['pa_count']:,}; mean recorded pitches={value['mean_recorded_pitch_events']:.3f}; "
            f"minimum-count share={_pct(value['exact_minimum_pitch_count_rate'])}; "
            f"minimal-clean share={_pct(value['outcome_minimal_clean_signature_rate'])}; "
            f"pitch-number-gap share={_pct(value['any_pitch_number_gap_rate'])}"
        )

    lines.extend(["", "## Rookie / complex leagues", ""])
    for row in comparisons:
        lines.extend(
            [
                f"### {row['league_name']} (league_id={row['league_id']})",
                "",
                f"- Games: {row['game_count']}; true PAs: {row['pa_count']:,}",
                f"- K mean recorded pitches: {row['k_mean_recorded_pitch_events']:.3f}; exact-3 share: {_pct(row['k_exact_minimum_pitch_count_rate'])}; minimal-clean: {_pct(row['k_outcome_minimal_clean_signature_rate'])}; gap share: {_pct(row['k_any_pitch_number_gap_rate'])}",
                f"- BB mean recorded pitches: {row['bb_mean_recorded_pitch_events']:.3f}; exact-4 share: {_pct(row['bb_exact_minimum_pitch_count_rate'])}; minimal-clean: {_pct(row['bb_outcome_minimal_clean_signature_rate'])}; gap share: {_pct(row['bb_any_pitch_number_gap_rate'])}",
                f"- BIP mean recorded pitches: {row['bip_mean_recorded_pitch_events']:.3f}; one-pitch share: {_pct(row['bip_exact_minimum_pitch_count_rate'])}; gap share: {_pct(row['bip_any_pitch_number_gap_rate'])}",
                f"- Delta vs pooled Single-A exact-minimum share: K {row['k_exact_minimum_pitch_count_rate_delta_vs_single_a']:+.3f}; BB {row['bb_exact_minimum_pitch_count_rate_delta_vs_single_a']:+.3f}; BIP {row['bip_exact_minimum_pitch_count_rate_delta_vs_single_a']:+.3f}",
                "",
            ]
        )

    lines.extend(
        [
            "## Reading the report",
            "",
            "A very high concentration at exactly 3 recorded pitches for strikeouts, 4 for walks, and 1 for batted balls—especially far above the Single-A control—would be evidence of outcome-minimal/manual sequence entry. A positive pitch-number-gap rate would instead indicate that official pitchNumber retains information about omitted intermediate events. Neither PA outcomes nor terminal BIP evidence are invalidated merely because intermediate pitches are compressed.",
            "",
        ]
    )
    summary_text = "\n".join(lines)
    (args.report_dir / "pitch_sequence_fidelity.md").write_text(
        summary_text, encoding="utf-8"
    )
    print(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
