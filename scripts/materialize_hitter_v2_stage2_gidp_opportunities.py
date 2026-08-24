#!/usr/bin/env python3
"""Materialize observed GIDP opportunities from certified 2021-2024 PBP."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

import polars as pl

from universal_baseball.current_talent_identity_corrections import (
    HISTORICAL_PLAYER_GAME_IDENTITY_CORRECTIONS,
)
from universal_baseball.hitter_v2_opportunity import (
    aggregate_player_game_gidp_opportunities,
    project_gidp_opportunities,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


MLB_ARCHIVES = {
    2021: Path(
        "data/quarantine/hitter-v2-stage1-mlb/artifacts/"
        "31986504169-current-talent-historical-mlb-2021.zip"
    ),
    2022: Path(
        "data/quarantine/hitter-v2-stage1-mlb/artifacts/"
        "31988255280-current-talent-historical-mlb-2022.zip"
    ),
    2023: Path(
        "data/quarantine/hitter-v2-stage1-mlb/artifacts/"
        "31989561396-current-talent-historical-mlb-2023.zip"
    ),
    2024: Path(
        "data/quarantine/hitter-v2-stage2-2024-mlb/artifacts/"
        "32096473700-current-talent-historical-mlb-2024.zip"
    ),
}
PBP_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "pitch_number",
    "inning",
    "game_type",
    "batter",
    "on_1b",
    "outs_when_up",
)
PBP_HALF_COLUMNS = ("inning_top_bot", "inning_topbot")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history-player-game",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--target-2024-player-game",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-2024-universal/tables/"
            "hitter_v2_player_game_outcomes_2024.parquet"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-gidp-opportunities"),
    )
    return parser.parse_args()


def _read_pbp_csv(source: Path | bytes) -> pl.DataFrame:
    if isinstance(source, Path):
        with source.open("r", encoding="utf-8-sig") as handle:
            source_columns = next(csv.reader([handle.readline()]))
        reader: Path | BytesIO = source
    else:
        source_columns = next(
            csv.reader([source.splitlines()[0].decode("utf-8-sig")])
        )
        reader = BytesIO(source)
    half_columns = [column for column in PBP_HALF_COLUMNS if column in source_columns]
    if len(half_columns) != 1:
        raise RuntimeError(
            f"PBP asset must expose exactly one inning-half field: {half_columns}"
        )
    return pl.read_csv(
        reader,
        columns=(*PBP_COLUMNS, half_columns[0]),
        infer_schema_length=10_000,
    ).rename({half_columns[0]: "inning_half"})


def _minimal(
    frame: pl.DataFrame,
    *,
    base_state_semantics: Literal["pre_pa", "post_pa"],
) -> pl.DataFrame:
    return project_gidp_opportunities(
        frame.select((*PBP_COLUMNS, "inning_half")),
        base_state_semantics=base_state_semantics,
    )


def _milb_paths(season: int) -> list[Path]:
    roots = (
        Path("data/quarantine/hitter-v2-stage1/pbp"),
        Path("data/quarantine/hitter-v2-stage2-2024-milb"),
        Path("data/quarantine/hitter-v2-stage2-2024-milb-rk"),
    )
    candidates = [
        path
        for root in roots
        for path in root.rglob(f"{season}_*_pbp.csv")
        if path.is_file()
    ]
    by_name: dict[str, list[Path]] = {}
    for path in candidates:
        by_name.setdefault(path.name, []).append(path)
    selected = []
    for name, paths in sorted(by_name.items()):
        hashes = {sha256_file(path) for path in paths}
        if len(hashes) != 1:
            raise RuntimeError(f"duplicate MiLB PBP asset {name} has different bytes")
        selected.append(sorted(paths)[0])
    if not selected:
        raise RuntimeError(f"no MiLB PBP assets found for {season}")
    return selected


def _resolve_cross_asset_duplicates(frame: pl.DataFrame) -> pl.DataFrame:
    state = frame.unique(
        [
            "game_id",
            "at_bat_index",
            "player_id",
            "runner_on_first_id",
            "outs_when_up",
            "gidp_opportunity",
        ]
    )
    conflicts = (
        state.group_by(["game_id", "at_bat_index"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if conflicts.is_empty():
        return state.sort(["game_id", "at_bat_index"])
    selected = []
    conflict_rows = state.join(
        conflicts.select("game_id", "at_bat_index"),
        on=["game_id", "at_bat_index"],
        how="inner",
    )
    for group in conflict_rows.partition_by(
        ["game_id", "at_bat_index"], maintain_order=True
    ):
        if group["player_id"].n_unique() != 1:
            raise RuntimeError("cross-asset opening state has conflicting batter identity")
        selected.append(
            group.head(1).with_columns(
                pl.lit(None, dtype=pl.Int64).alias("gidp_opportunity"),
                pl.lit("failed_closed_cross_asset_state_conflict").alias(
                    "opportunity_source_status"
                ),
                pl.col("raw_opening_row_count").sum().alias(
                    "raw_opening_row_count"
                ),
            )
        )
    clean = state.join(
        conflicts.select("game_id", "at_bat_index"),
        on=["game_id", "at_bat_index"],
        how="anti",
    )
    return pl.concat([clean, *selected], how="vertical_relaxed").sort(
        ["game_id", "at_bat_index"]
    )


def _apply_identity_corrections(frame: pl.DataFrame, season: int) -> pl.DataFrame:
    result = frame
    for correction in HISTORICAL_PLAYER_GAME_IDENTITY_CORRECTIONS:
        if correction.season != season:
            continue
        result = result.with_columns(
            pl.when(
                (pl.col("game_id") == correction.game_id)
                & (pl.col("player_id") == correction.source_player_id)
            )
            .then(pl.lit(correction.corrected_player_id))
            .otherwise(pl.col("player_id"))
            .alias("player_id")
        )
    return result


def _load_milb(season: int) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    frames = []
    sources = []
    for path in _milb_paths(season):
        frames.append(
            _minimal(
                _read_pbp_csv(path), base_state_semantics="post_pa"
            )
        )
        sources.append(
            {
                "name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "base_state_semantics": "post_pa_shift_prior_within_half_inning",
            }
        )
    terminal = _resolve_cross_asset_duplicates(pl.concat(frames, how="vertical_relaxed"))
    return _apply_identity_corrections(terminal, season), sources


def _load_mlb(season: int) -> tuple[pl.DataFrame, dict[str, object]]:
    path = MLB_ARCHIVES[season]
    frames = []
    with ZipFile(path) as archive:
        members = sorted(
            name
            for name in archive.namelist()
            if "/raw/savant/" in name and name.endswith(".csv")
        )
        if not members:
            raise RuntimeError(f"MLB {season} archive has no raw Savant PBP")
        for member in members:
            frames.append(
                _minimal(
                    _read_pbp_csv(archive.read(member)),
                    base_state_semantics="pre_pa",
                )
            )
    return _resolve_cross_asset_duplicates(pl.concat(frames, how="vertical_relaxed")), {
        "archive_path": path.as_posix(),
        "archive_sha256": sha256_file(path),
        "raw_savant_members": len(members),
        "base_state_semantics": "pre_pa_direct",
    }


def main() -> int:
    args = _parse_args()
    canonical = pl.concat(
        [
            pl.read_parquet(args.history_player_game),
            pl.read_parquet(args.target_2024_player_game),
        ],
        how="vertical",
    )
    evidence = []
    provenance = []
    for season in (2021, 2022, 2023, 2024):
        milb, milb_sources = _load_milb(season)
        mlb, mlb_source = _load_mlb(season)
        combined = _resolve_cross_asset_duplicates(
            pl.concat([milb, mlb], how="vertical_relaxed")
        )
        player_games = aggregate_player_game_gidp_opportunities(combined).with_columns(
            pl.lit(season).cast(pl.Int64).alias("season")
        )
        evidence.append(player_games)
        provenance.append(
            {
                "season": season,
                "milb_assets": milb_sources,
                "mlb_source": mlb_source,
                "observed_pbp_pa": combined.height,
                "player_game_rows": player_games.height,
            }
        )
        print(json.dumps(provenance[-1], sort_keys=True), flush=True)
    opportunities = pl.concat(evidence, how="vertical").sort(
        ["season", "game_id", "player_id"]
    )
    joined = canonical.join(
        opportunities,
        on=["season", "game_id", "player_id"],
        how="left",
        validate="1:1",
    )
    accepted = joined.filter(pl.col("modeling_eligible")).with_columns(
        pl.when(pl.col("gidp_opportunities").is_null())
        .then(
            pl.when(pl.col("ambiguous_opening_pa").fill_null(0) > 0)
            .then(pl.lit("failed_closed_ambiguous_opening_state"))
            .otherwise(pl.lit("failed_closed_missing_pbp_identity"))
        )
        .when(pl.col("observed_pbp_pa") != pl.col("accepted_terminal_pa"))
        .then(pl.lit("failed_closed_pa_identity_reconciliation"))
        .when(pl.col("batting_GiDP") > pl.col("gidp_opportunities"))
        .then(pl.lit("failed_closed_official_gidp_definition"))
        .otherwise(pl.lit("accepted_capability_declared_pa_start_state"))
        .alias("gidp_opportunity_status")
    ).with_columns(
        (
            pl.col("gidp_opportunity_status")
            == "accepted_capability_declared_pa_start_state"
        ).alias(
            "gidp_opportunity_modeling_eligible"
        )
    )
    output = accepted.select(
        "season",
        "game_date",
        "game_id",
        "league_id",
        "level_group",
        "team_id",
        "player_id",
        "gidp_opportunities",
        "batting_GiDP",
        "MULTI_OUT",
        "observed_pbp_pa",
        "accepted_terminal_pa",
        "ambiguous_opening_pa",
        "gidp_opportunity_status",
        "gidp_opportunity_modeling_eligible",
        "source_capability_tier",
    ).sort(["season", "league_id", "game_id", "player_id"])
    ready = output.filter(pl.col("gidp_opportunity_modeling_eligible"))
    if ready.is_empty():
        raise RuntimeError("GIDP opportunity source produced no eligible player-games")
    if ready.filter(
        pl.col("gidp_opportunities").is_null()
        | (pl.col("gidp_opportunities") < 0)
        | (pl.col("batting_GiDP") > pl.col("gidp_opportunities"))
    ).height:
        raise RuntimeError("eligible GIDP opportunity rows violate source invariants")
    status_counts = {
        row["gidp_opportunity_status"]: row["len"]
        for row in output.group_by("gidp_opportunity_status").len().to_dicts()
    }
    artifact = write_canonical_parquet(
        output,
        args.report_root / "tables" / "hitter_v2_player_game_gidp_opportunities_2021_2024.parquet",
        table_name="hitter_v2_player_game_gidp_opportunities",
    ).as_record()
    report = {
        "report_schema_version": "0.2",
        "program": "hitter_v2",
        "stage": 2,
        "status": "gidp_opportunity_source_ready",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "definition": "runner on first and fewer than two outs at PA start",
        "source_semantics": (
            "MLB Savant on_1b is direct pre-PA state; affiliated MiLB PBP on_1b "
            "is post-play state and is shifted from the preceding PA within "
            "the same half-inning; the first PA starts empty"
        ),
        "failure_policy": (
            "retain canonical player-games but exclude ambiguous, missing-identity, "
            "PA-reconciliation, and official-definition conflicts from GIDP modeling"
        ),
        "source_provenance": provenance,
        "totals": {
            "canonical_model_ready_player_games": output.height,
            "opportunity_ready_player_games": ready.height,
            "opportunity_ready_players": ready["player_id"].n_unique(),
            "opportunity_ready_games": ready["game_id"].n_unique(),
            "opportunity_ready_official_pa": int(ready["accepted_terminal_pa"].sum()),
            "opportunity_ready_observed_pbp_pa": int(ready["observed_pbp_pa"].sum()),
            "gidp_opportunities": int(ready["gidp_opportunities"].sum()),
            "official_gidp": int(ready["batting_GiDP"].sum()),
            "multi_out": int(ready["MULTI_OUT"].sum()),
            "player_game_coverage": ready.height / output.height,
            "official_pa_coverage": (
                int(ready["accepted_terminal_pa"].sum())
                / int(output["accepted_terminal_pa"].sum())
            ),
        },
        "reconciliation": {
            "status_counts": status_counts,
            "eligible_rows_have_exact_pa_reconciliation": bool(
                ready.select(
                    (pl.col("observed_pbp_pa") == pl.col("accepted_terminal_pa")).all()
                ).item()
            ),
            "eligible_rows_have_gidp_not_above_opportunity": bool(
                ready.select(
                    (pl.col("batting_GiDP") <= pl.col("gidp_opportunities")).all()
                ).item()
            ),
        },
        "storage": artifact,
        "input_sha256": {
            "history_player_game": sha256_file(args.history_player_game),
            "target_2024_player_game": sha256_file(args.target_2024_player_game),
        },
        "raw_manifest_sha256": sha256(
            json.dumps(provenance, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest(),
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
