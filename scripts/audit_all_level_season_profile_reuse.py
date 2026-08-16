#!/usr/bin/env python
"""Certify rich season-player aggregate reuse across every affiliated MiLB level.

The existing season-stat gate proved 2024 AAA/Rookie standard outcome counts.
This audit extends the same independent official reconciliation to AA, High-A,
Single-A and tests richer fields preserved by the upstream armstjc extractor.

The key distinction is semantic: fields such as ``groundOuts`` and ``airOuts``
are *outs recorded*, not necessarily one batted-ball event each. This audit does
not promote them as trajectory-event counts merely because they are present.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import polars as pl

import audit_season_stat_official_reconciliation as base
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import new_official_session
from universal_baseball.season_stats import (
    select_reconciliation_players,
    standardize_armstjc_season_stats,
)

SEASON = 2024
LEVEL_SPECS = (
    ("aaa", "Triple-A"),
    ("aa", "Double-A"),
    ("a+", "High-A"),
    ("a", "Single-A"),
    ("rk", "Rookie"),
)
SPECS = tuple(
    {
        "season": SEASON,
        "kind": kind,
        "tag": f"season_player_{kind}",
        "asset": f"{SEASON}_{slug}_season_{kind}_stats.csv",
        "sport_label": sport_label,
        "level_slug": slug,
    }
    for slug, sport_label in LEVEL_SPECS
    for kind in ("batting", "pitching")
)

# The public Stats API person-season representation exposes only a subset of the
# richer BDFED fields. Keep every candidate here; _compare_player compares only
# fields present in both representations.
BATTING_PROFILE_COMPARE = {
    **base.BATTING_COMPARE,
    "groundOuts": "batting_GO",
    "airOuts": "batting_AO",
    "flyOuts": "batting_FO",
    "popOuts": "batting_PO",
    "lineOuts": "batting_LO",
    "groundHits": "batting_ground_hits",
    "flyHits": "batting_fly_hits",
    "popHits": "batting_pop_hits",
    "lineHits": "batting_line_hits",
    "numberOfPitches": "batting_pitches_faced",
    "totalSwings": "batting_swings",
    "swingAndMisses": "batting_whiffs",
    "ballsInPlay": "batting_balls_in_play",
    "reachedOnError": "batting_reached_on_error",
}
PITCHING_PROFILE_COMPARE = {
    **base.PITCHING_COMPARE,
    "flyHits": "pitching_FH",
    "popHits": "pitching_PH",
    "lineHits": "pitching_LH",
    "flyOuts": "pitching_FO",
    "groundOuts": "pitching_GO",
    "airOuts": "pitching_AO",
    "popOuts": "pitching_pop_outs",
    "lineOuts": "pitching_line_outs",
    "numberOfPitches": "pitching_PI",
    "totalSwings": "pitching_total_swings",
    "swingAndMisses": "pitching_swing_and_misses",
    "ballsInPlay": "pitching_balls_in_play",
}


def _num(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Int64, strict=False).fill_null(0)


def _difference_profile(frame: pl.DataFrame, lhs: pl.Expr, rhs: pl.Expr) -> dict[str, Any]:
    differences = frame.select((lhs - rhs).alias("difference")).get_column("difference")
    mismatches = differences.filter(differences != 0)
    counts = Counter(int(value) for value in mismatches.to_list())
    return {
        "row_count": frame.height,
        "exact_match_count": frame.height - len(mismatches),
        "mismatch_count": len(mismatches),
        "mismatch_rate": len(mismatches) / frame.height if frame.height else None,
        "difference_counts": dict(sorted(counts.items())),
        "min_difference": int(differences.min()) if frame.height else None,
        "max_difference": int(differences.max()) if frame.height else None,
    }


def _inequality_profile(frame: pl.DataFrame, lower: pl.Expr, upper: pl.Expr) -> dict[str, Any]:
    violations = frame.select((lower > upper).alias("violation")).get_column("violation")
    count = int(violations.sum() or 0)
    return {
        "row_count": frame.height,
        "violation_count": count,
        "violation_rate": count / frame.height if frame.height else None,
    }


def _raw_profile(frame: pl.DataFrame, kind: str) -> dict[str, Any]:
    if kind == "batting":
        required = {
            "batting_AB", "batting_SO", "batting_HR", "batting_SH", "batting_SF",
            "batting_GiDP", "batting_GO", "batting_AO", "batting_FO", "batting_PO", "batting_LO",
            "batting_ground_hits", "batting_fly_hits", "batting_pop_hits", "batting_line_hits",
            "batting_pitches_faced", "batting_swings", "batting_whiffs",
            "batting_balls_in_play", "batting_reached_on_error",
        }
        missing = sorted(required - set(frame.columns))
        if missing:
            return {"available": False, "missing_columns": missing}

        trajectory_hits = (
            _num("batting_ground_hits") + _num("batting_fly_hits")
            + _num("batting_pop_hits") + _num("batting_line_hits")
        )
        trajectory_outs = (
            _num("batting_GO") + _num("batting_FO")
            + _num("batting_PO") + _num("batting_LO")
        )
        naive_components = trajectory_hits + trajectory_outs + _num("batting_reached_on_error")
        babip_denominator = (
            _num("batting_AB") - _num("batting_SO") - _num("batting_HR") + _num("batting_SF")
        )
        broad_contact_formula = (
            _num("batting_AB") - _num("batting_SO") + _num("batting_SF") + _num("batting_SH")
        )
        return {
            "available": True,
            "semantic_guardrail": (
                "groundOuts/flyOuts/popOuts/lineOuts are outs recorded, not certified "
                "one-row-per-contact event counts; double plays can make their sum exceed BIP"
            ),
            "air_outs_equals_components": _difference_profile(
                frame,
                _num("batting_AO"),
                _num("batting_FO") + _num("batting_PO") + _num("batting_LO"),
            ),
            "source_bip_vs_broad_contact_formula_ab_minus_so_plus_sf_plus_sh": _difference_profile(
                frame, _num("batting_balls_in_play"), broad_contact_formula
            ),
            "source_bip_minus_babip_denominator_vs_hr_plus_sh": _difference_profile(
                frame,
                _num("batting_balls_in_play") - babip_denominator,
                _num("batting_HR") + _num("batting_SH"),
            ),
            "naive_trajectory_components_minus_bip_vs_gidp": _difference_profile(
                frame,
                naive_components - _num("batting_balls_in_play"),
                _num("batting_GiDP"),
            ),
            "whiffs_le_swings": _inequality_profile(
                frame, _num("batting_whiffs"), _num("batting_swings")
            ),
            "swings_le_pitches": _inequality_profile(
                frame, _num("batting_swings"), _num("batting_pitches_faced")
            ),
            "profile_nonnull_counts": {
                column: int(frame.get_column(column).is_not_null().sum())
                for column in sorted(required)
            },
        }

    required = {
        "pitching_AB", "pitching_SO", "pitching_HR", "pitching_SF", "pitching_GiDP",
        "pitching_FO", "pitching_GO", "pitching_AO", "pitching_pop_outs", "pitching_line_outs",
        "pitching_FH", "pitching_PH", "pitching_LH",
        "pitching_PI", "pitching_total_swings", "pitching_swing_and_misses",
        "pitching_balls_in_play", "pitching_PI_strikes", "pitching_PI_balls",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        return {"available": False, "missing_columns": missing}
    return {
        "available": True,
        "semantic_guardrail": (
            "pitching source omits groundHits, so it cannot reconstruct a complete "
            "trajectory-event distribution from season aggregates"
        ),
        "air_outs_equals_components": _difference_profile(
            frame,
            _num("pitching_AO"),
            _num("pitching_FO") + _num("pitching_pop_outs") + _num("pitching_line_outs"),
        ),
        "source_bip_vs_standard_fieldable_bip_formula": _difference_profile(
            frame,
            _num("pitching_balls_in_play"),
            _num("pitching_AB") - _num("pitching_SO") - _num("pitching_HR") + _num("pitching_SF"),
        ),
        "whiffs_le_swings": _inequality_profile(
            frame, _num("pitching_swing_and_misses"), _num("pitching_total_swings")
        ),
        "swings_le_pitches": _inequality_profile(
            frame, _num("pitching_total_swings"), _num("pitching_PI")
        ),
        "called_ball_strike_tally_vs_pitches": _difference_profile(
            frame,
            _num("pitching_PI"),
            _num("pitching_PI_strikes") + _num("pitching_PI_balls"),
        ),
        "profile_nonnull_counts": {
            column: int(frame.get_column(column).is_not_null().sum())
            for column in sorted(required)
        },
    }


def main() -> int:
    work_dir = Path("data/quarantine/all-level-season-profile-reuse")
    report_dir = Path("reports/generated/all-level-season-profile-reuse")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    loaded: list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame, dict[str, Any], dict[str, Any]]] = []
    for spec in SPECS:
        path = work_dir / spec["asset"]
        metadata = download_file(
            f"{base.BASE_URL}/{spec['tag']}/{spec['asset']}", path, timeout_seconds=240
        )
        raw = read_quarantined_csv(path)
        if raw.is_empty():
            raise RuntimeError(f"season-stat source asset is empty: {spec['asset']}")
        standardized, normalization = standardize_armstjc_season_stats(raw, spec["kind"])
        loaded.append((spec, raw, standardized, metadata, normalization))

    original_batting = base.BATTING_COMPARE
    original_pitching = base.PITCHING_COMPARE
    base.BATTING_COMPARE = BATTING_PROFILE_COMPARE
    base.PITCHING_COMPARE = PITCHING_PROFILE_COMPARE
    session = new_official_session()
    try:
        sports = base._sports_map(session)
        source_reports: list[dict[str, Any]] = []
        player_reports: list[dict[str, Any]] = []
        for spec, raw, frame, metadata, normalization in loaded:
            grain = base._grain_profile(frame)
            selected = select_reconciliation_players(frame, spec["kind"], per_league=1)
            expected = int(grain["distinct_league_count"])
            sport_id = sports.get(spec["sport_label"])
            if selected and sport_id is None:
                raise RuntimeError(
                    f"official sports endpoint lacks expected {spec['sport_label']!r}; "
                    f"available={sorted(sports)}"
                )
            source_reports.append(
                {
                    "asset": spec["asset"],
                    "kind": spec["kind"],
                    "level_slug": spec["level_slug"],
                    "sport_label": spec["sport_label"],
                    "source_sha256": metadata["sha256"],
                    "schema_normalization": normalization,
                    "grain": grain,
                    "accounting": base._accounting_profile(frame, spec["kind"]),
                    "rich_profile": _raw_profile(raw, spec["kind"]),
                    "selected_reconciliation_players": selected,
                    "expected_reconciliation_sample_count": expected,
                    "sample_coverage_complete": len(selected) == expected,
                }
            )
            for sample in selected:
                player_reports.append(
                    base._compare_player(
                        frame=frame,
                        kind=spec["kind"],
                        sample=sample,
                        sport_id=int(sport_id),
                        season=SEASON,
                        session=session,
                    )
                )
    finally:
        session.close()
        base.BATTING_COMPARE = original_batting
        base.PITCHING_COMPARE = original_pitching

    exact = [row for row in player_reports if row["exact"]]
    field_counts = Counter()
    difference_counts = Counter()
    for row in player_reports:
        for field in row["compared_fields"]:
            field_counts[field] += 1
        for field in row["differences"]:
            difference_counts[field] += 1

    baseline_batting_fields = set(base.BATTING_COMPARE.values())
    baseline_pitching_fields = set(base.PITCHING_COMPARE.values())
    extra_official_fields = sorted(
        field
        for field in field_counts
        if field not in baseline_batting_fields and field not in baseline_pitching_fields
    )

    payload = {
        "report_schema_version": 2,
        "status": "all_level_completed_season_profile_reuse_audit",
        "season": SEASON,
        "source_reports": source_reports,
        "player_reports": player_reports,
        "reconciliation_sample_count": len(player_reports),
        "exact_sample_count": len(exact),
        "all_samples_exact": len(exact) == len(player_reports) and bool(player_reports),
        "compared_field_sample_counts": dict(sorted(field_counts.items())),
        "field_difference_sample_counts": dict(sorted(difference_counts.items())),
        "extra_fields_independently_exposed_by_stats_api": extra_official_fields,
        "interpretation_guardrail": (
            "Official person-season reconciliation independently supports only mutually exposed "
            "fields. Structural consistency alone does not promote totalSwings, swingAndMisses, "
            "or hit/out trajectory components to physical-process evidence. Ground/air out "
            "columns count outs, not guaranteed one-per-contact events. Direction is absent."
        ),
    }
    (report_dir / "all_level_season_profile_reuse.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# All-level completed-season aggregate reuse audit",
        "",
        f"- Season: {SEASON}",
        f"- Source assets: {len(source_reports)}",
        f"- Official player-league samples: {len(player_reports)}",
        f"- Exact samples across every mutually available compared field: **{len(exact)}/{len(player_reports)}**",
        f"- Extra rich fields independently exposed by Stats API: `{extra_official_fields}`",
        "",
    ]
    for report in source_reports:
        rich = report["rich_profile"]
        lines.extend(
            [
                f"## {report['level_slug']} {report['kind']}",
                "",
                f"- Rows: {report['grain']['row_count']:,}; actual leagues: {report['grain']['distinct_league_count']}; duplicate groups: {report['grain']['duplicate_group_count']}",
                f"- Standard accounting: `{report['accounting']}`",
                f"- Rich profile fields available: **{rich.get('available')}**",
            ]
        )
        if rich.get("available"):
            for name, result in rich.items():
                if name in {"available", "profile_nonnull_counts"}:
                    continue
                lines.append(f"- {name}: `{result}`")
        else:
            lines.append(f"- Missing rich fields: `{rich.get('missing_columns')}`")
        lines.append("")

    lines.extend(["## Official reconciliation", ""])
    for row in player_reports:
        lines.append(
            f"- {row['kind']} player {row['person_id']} league {row['league_id']}: "
            f"fields={row['compared_field_count']}, differences={row['difference_count']}, exact={row['exact']}"
        )
    lines.extend(
        [
            "",
            "Direction / Pull-Center-Opposite is not present in these season aggregates. "
            "Detailed trajectory hit/out fields are not treated as event counts, and swings/whiffs "
            "remain process candidates pending fidelity validation.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "all_level_season_profile_reuse.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
