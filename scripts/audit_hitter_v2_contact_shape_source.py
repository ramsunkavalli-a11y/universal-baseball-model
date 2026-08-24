#!/usr/bin/env python3
"""Audit and consolidate chronology-safe Hitter v2 contact-shape evidence.

The source is the already-certified 2021-2024 Current Talent player-game
profile surface.  This gate materializes auxiliary PBP evidence only; it does
not fit or score a batting candidate.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import zipfile

import polars as pl

import materialize_hitter_v2_stage1_milb as stage1_milb
import materialize_hitter_v2_stage1_mlb as stage1_mlb
from universal_baseball.performance_season import CONTACT_CORE_BINS
from universal_baseball.storage import write_canonical_parquet


LEVEL_MAP = {
    "MLB": "MLB",
    "AAA": "aaa",
    "AA": "aa",
    "HIGH_A": "a+",
    "SINGLE_A": "a",
    "ROOKIE_COMPLEX": "rk",
}
EXPECTED_SEASONS = (2021, 2022, 2023, 2024)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--milb-zip-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1/artifacts"),
    )
    parser.add_argument(
        "--mlb-zip-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1-mlb/artifacts"),
    )
    parser.add_argument(
        "--source-2024-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage2-source"),
    )
    parser.add_argument(
        "--outcomes-2021-2023",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--outcomes-2024",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-2024-universal/tables/"
            "hitter_v2_player_game_outcomes_2024.parquet"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2b-contact-shape-source"),
    )
    return parser.parse_args()


def _digest(content: bytes) -> str:
    return sha256(content).hexdigest()


def _read_bytes(path: Path) -> bytes:
    """Read a local artifact, including Windows paths beyond MAX_PATH."""

    resolved = str(path.resolve())
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        resolved = f"\\\\?\\{resolved}"
    return Path(resolved).read_bytes()


def _zip_profile(
    path: Path, season: int, *, expected_sha256: str
) -> tuple[pl.DataFrame, dict[str, object]]:
    content = _read_bytes(path)
    actual = _digest(content)
    if actual != expected_sha256:
        raise ValueError(f"frozen artifact digest mismatch: {path}")
    with zipfile.ZipFile(BytesIO(content)) as archive:
        members = [
            name
            for name in archive.namelist()
            if f"current_talent_game_profile_{season}_" in name
            and name.endswith(".parquet")
        ]
        if len(members) != 1:
            raise ValueError(f"expected one {season} profile in {path}, found {members}")
        member = members[0]
        profile_content = archive.read(member)
    return pl.read_parquet(BytesIO(profile_content)), {
        "season": season,
        "path": str(path),
        "artifact_sha256": actual,
        "profile_member": member,
        "profile_member_sha256": _digest(profile_content),
        "profile_member_size_bytes": len(profile_content),
    }


def _historical_profiles(
    milb_root: Path, mlb_root: Path
) -> tuple[list[pl.DataFrame], list[dict[str, object]]]:
    profiles: list[pl.DataFrame] = []
    sources: list[dict[str, object]] = []
    for season in (2021, 2022, 2023):
        for path in sorted(milb_root.glob("*.zip")):
            prefix, name = path.stem.split("-", maxsplit=1)
            run_id = int(prefix)
            expected = stage1_milb.EXPECTED_ARTIFACT_SHA256.get((run_id, name))
            if expected is None:
                continue
            with zipfile.ZipFile(path) as archive:
                if not any(
                    f"current_talent_game_profile_{season}_" in member
                    for member in archive.namelist()
                ):
                    continue
            profile, record = _zip_profile(path, season, expected_sha256=expected)
            profiles.append(profile)
            sources.append({**record, "capability_tier": "affiliated_pbp"})

        registry = stage1_mlb.ARTIFACTS[season]
        mlb_path = mlb_root / f"{registry['run_id']}-{registry['name']}.zip"
        profile, record = _zip_profile(
            mlb_path, season, expected_sha256=str(registry["sha256"])
        )
        profiles.append(profile)
        sources.append({**record, "capability_tier": "mlb_pbp_statcast_source"})
    return profiles, sources


def _profiles_2024(root: Path) -> tuple[list[pl.DataFrame], list[dict[str, object]]]:
    paths = sorted(root.rglob("current_talent_game_profile_2024_*.parquet"))
    if len(paths) != 6:
        raise ValueError(f"expected six 2024 profile tables, found {len(paths)}")
    profiles: list[pl.DataFrame] = []
    records: list[dict[str, object]] = []
    for path in paths:
        content = _read_bytes(path)
        profiles.append(pl.read_parquet(BytesIO(content)))
        records.append(
            {
                "season": 2024,
                "path": str(path),
                "profile_member_sha256": _digest(content),
                "profile_member_size_bytes": len(content),
                "capability_tier": (
                    "mlb_pbp_statcast_source"
                    if path.name.endswith("_mlb.parquet")
                    else "affiliated_pbp"
                ),
            }
        )
    return profiles, records


def _coverage_rows(
    outcomes: pl.DataFrame, profile_counts: pl.DataFrame
) -> list[dict[str, object]]:
    joined = outcomes.join(
        profile_counts.select(
            "season",
            "game_pk",
            "league_id",
            "player_id",
            pl.col("level_group").alias("profile_level_group"),
            "shape_contact_count",
        ),
        left_on=["season", "game_id", "league_id", "player_id"],
        right_on=["season", "game_pk", "league_id", "player_id"],
        how="left",
    )
    level_conflicts = joined.filter(
        pl.col("profile_level_group").is_not_null()
        & (pl.col("profile_level_group") != pl.col("level_group"))
    )
    if level_conflicts.height:
        raise ValueError("contact-shape profile and terminal outcome levels conflict")

    rows: list[dict[str, object]] = []
    for keys, subset in (
        (("ALL", "ALL"), joined),
        *(
            ((str(season), str(level)), frame)
            for (season, level), frame in joined.group_by(
                "season", "level_group", maintain_order=True
            )
        ),
    ):
        positive = subset.filter(pl.col("observed_terminal_contact_count") > 0)
        covered = positive.filter(pl.col("shape_contact_count").is_not_null())
        exact = covered.filter(
            pl.col("shape_contact_count")
            == pl.col("observed_terminal_contact_count")
        )
        target_contacts = int(positive["observed_terminal_contact_count"].sum())
        shape_contacts = int(covered["shape_contact_count"].sum())
        rows.append(
            {
                "season": keys[0],
                "level_group": keys[1],
                "positive_terminal_contact_player_games": positive.height,
                "profile_covered_player_games": covered.height,
                "player_game_coverage_rate": (
                    covered.height / positive.height if positive.height else None
                ),
                "terminal_contact_count": target_contacts,
                "shape_contact_count": shape_contacts,
                "event_coverage_rate": (
                    shape_contacts / target_contacts if target_contacts else None
                ),
                "exact_count_player_games": exact.height,
                "exact_count_rate_among_covered": (
                    exact.height / covered.height if covered.height else None
                ),
                "covered_players": covered["player_id"].n_unique(),
            }
        )
    return rows


def main() -> int:
    args = _parse_args()
    profiles, source_records = _historical_profiles(
        args.milb_zip_root, args.mlb_zip_root
    )
    profiles_2024, sources_2024 = _profiles_2024(args.source_2024_root)
    profiles.extend(profiles_2024)
    source_records.extend(sources_2024)
    raw = pl.concat(profiles, how="vertical_relaxed")
    required = {
        "season",
        "game_date",
        "game_pk",
        "league_id",
        "player_id",
        "level_group",
        "core_bin",
        "occurrence_count",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"contact-shape profiles are missing columns: {missing}")
    observed_seasons = tuple(sorted(int(value) for value in raw["season"].unique()))
    if observed_seasons != EXPECTED_SEASONS:
        raise ValueError(f"contact-shape seasons differ: {observed_seasons}")
    unknown_levels = sorted(set(raw["level_group"].unique()) - set(LEVEL_MAP))
    if unknown_levels:
        raise ValueError(f"unrecognized contact-shape levels: {unknown_levels}")

    contact = (
        raw.filter(pl.col("core_bin").is_in(list(CONTACT_CORE_BINS)))
        .with_columns(
            pl.col("level_group").replace_strict(LEVEL_MAP),
            pl.col("occurrence_count").cast(pl.Int64),
        )
        .group_by(
            "season",
            "game_date",
            "game_pk",
            "league_id",
            "player_id",
            "level_group",
            "core_bin",
        )
        .agg(pl.col("occurrence_count").sum())
        .sort(
            "season",
            "game_date",
            "game_pk",
            "league_id",
            "player_id",
            "core_bin",
        )
    )
    duplicate_grain = (
        contact.group_by(
            "season", "game_pk", "league_id", "player_id", "core_bin"
        )
        .len()
        .filter(pl.col("len") != 1)
    )
    if duplicate_grain.height:
        raise ValueError("contact-shape player-game-bin grain is not unique")
    if contact.filter(pl.col("occurrence_count") < 0).height:
        raise ValueError("contact-shape counts must be nonnegative")

    player_game = contact.group_by(
        "season", "game_pk", "league_id", "player_id", "level_group"
    ).agg(pl.col("occurrence_count").sum().alias("shape_contact_count"))
    outcomes = pl.concat(
        [
            pl.read_parquet(args.outcomes_2021_2023),
            pl.read_parquet(args.outcomes_2024),
        ],
        how="vertical_relaxed",
    ).filter(pl.col("modeling_eligible"))
    coverage = pl.DataFrame(_coverage_rows(outcomes, player_game))
    season_contact = (
        contact.group_by(
            "season", "league_id", "player_id", "level_group", "core_bin"
        )
        .agg(pl.col("occurrence_count").sum())
        .sort("season", "league_id", "player_id", "core_bin")
    )

    game_artifact = write_canonical_parquet(
        contact,
        args.report_root / "tables" / "contact_shape_player_game.parquet",
        table_name="hitter_v2_stage2b_contact_shape_player_game",
    )
    season_artifact = write_canonical_parquet(
        season_contact,
        args.report_root / "tables" / "contact_shape_player_season.parquet",
        table_name="hitter_v2_stage2b_contact_shape_player_season",
    )
    coverage_artifact = write_canonical_parquet(
        coverage,
        args.report_root / "tables" / "contact_shape_coverage.parquet",
        table_name="hitter_v2_stage2b_contact_shape_coverage",
    )
    all_coverage = coverage.filter(
        (pl.col("season") == "ALL") & (pl.col("level_group") == "ALL")
    ).row(0, named=True)
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2b_contact_shape_source_audit",
        "status": "contact_shape_source_accepted_for_auxiliary_development",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "source_seasons": list(EXPECTED_SEASONS),
        "source_artifacts": source_records,
        "contact_bins": list(CONTACT_CORE_BINS),
        "player_game_bin_rows": contact.height,
        "player_season_bin_rows": season_contact.height,
        "shape_contact_events": int(contact["occurrence_count"].sum()),
        "players": contact["player_id"].n_unique(),
        "games": contact["game_pk"].n_unique(),
        "leagues": contact["league_id"].n_unique(),
        "coverage_summary": all_coverage,
        "coverage_by_season_level": coverage.to_dicts(),
        "artifacts": {
            "player_game": game_artifact.as_record(),
            "player_season": season_artifact.as_record(),
            "coverage": coverage_artifact.as_record(),
        },
        "contract": {
            "role": "optional_pbp_auxiliary_only",
            "chronology": "only source season <= predictor cutoff may enter a forecast",
            "fallback": "zero residual and exact universal outcome forecast when usable shape evidence is absent",
            "availability_as_talent_predictor": False,
            "literal_zero_imputation_for_missing_shape": False,
            "terminal_outcome_replacement": False,
        },
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
