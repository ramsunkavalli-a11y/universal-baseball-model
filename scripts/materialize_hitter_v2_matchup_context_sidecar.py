#!/usr/bin/env python3
"""Materialize a target-free Hitter v2 terminal-PA matchup sidecar."""

from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

import polars as pl

import materialize_hitter_v2_stage1_milb as stage1_milb
import materialize_hitter_v2_stage1_mlb as stage1_mlb
from universal_baseball.current_talent_mlb_evidence import (
    MLB_OUTCOME_IDENTITY_POLICY,
    _with_official_outcome_batter,
)
from universal_baseball.hitter_v2_matchup_context import (
    add_strict_prior_pitcher_evidence,
    build_terminal_matchup_sidecar,
    reconcile_sidecar_to_player_games,
)
from universal_baseball.storage import write_canonical_parquet


SEASONS = (2021, 2022, 2023, 2024)
LEVELS = ("aaa", "aa", "a+", "a", "rk")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-milb-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1/pbp"),
    )
    parser.add_argument(
        "--milb-2024-root",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-2024-milb/"
            "reconstructed-terminal-source/2024"
        ),
    )
    parser.add_argument(
        "--contact-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1/artifacts"),
    )
    parser.add_argument(
        "--mlb-2021-2023-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1-mlb/artifacts"),
    )
    parser.add_argument(
        "--mlb-2024-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage2-2024-mlb/artifacts"),
    )
    parser.add_argument(
        "--player-game-2021-2023",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--player-game-2024",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-2024-universal/tables/"
            "hitter_v2_player_game_outcomes_2024.parquet"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-matchup-context-sidecar"),
    )
    return parser.parse_args()


def _read_matching_parquet(archive: zipfile.ZipFile, suffix: str) -> pl.DataFrame:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise ValueError(f"expected one {suffix} in archive, found {names}")
    return pl.read_parquet(io.BytesIO(archive.read(names[0])))


def _contact_archive(
    root: Path, season: int, level: str
) -> tuple[zipfile.ZipFile, str]:
    slug = level.replace("+", "plus")
    if season in (2021, 2022):
        pattern = f"*-current-talent-contact-value-source-{season}-{slug}.zip"
    elif season == 2023:
        pattern = "*-current-talent-contact-value-confirmation-source-v2.zip"
    else:
        raise ValueError(f"no retained contact archive for season {season}")
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f"expected one contact archive matching {pattern}, found {paths}")
    return zipfile.ZipFile(paths[0]), paths[0].name


def _integer_like(column: str, alias: str) -> pl.Expr:
    value = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(value.is_not_null() & (value == value.floor()))
        .then(value.cast(pl.Int64))
        .otherwise(None)
        .alias(alias)
    )


def _load_milb_raw(files: list[Path]) -> pl.DataFrame:
    if not files:
        raise ValueError("MiLB matchup sidecar has no raw PBP files")
    scans = [
        pl.scan_csv(
            path,
            infer_schema=False,
            null_values=["", "NA", "NaN", "null", "None"],
            truncate_ragged_lines=False,
        ).select(
            "game_pk",
            "at_bat_number",
            "pitch_number",
            "game_date",
            "game_type",
            "batter",
            "pitcher",
            "stand",
            "p_throws",
        )
        for path in files
    ]
    return pl.concat(scans, how="vertical_relaxed").collect()


def _normalize_milb_pitches(raw: pl.DataFrame) -> pl.DataFrame:
    return (
        raw.select(
            _integer_like("game_pk", "game_pk"),
            _integer_like("at_bat_number", "at_bat_index"),
            _integer_like("pitch_number", "pitch_number"),
            pl.col("game_date").cast(pl.String).str.to_date(strict=False),
            _integer_like("batter", "source_batter_id"),
            _integer_like("pitcher", "pitcher_id"),
            pl.col("stand").cast(pl.String).alias("batter_side"),
            pl.col("p_throws").cast(pl.String).alias("pitcher_hand"),
            pl.col("game_type").cast(pl.String),
        )
        .drop_nulls(["game_pk", "at_bat_index", "pitch_number"])
        .filter(pl.col("game_type") == "R")
        .drop("game_type")
    )


def _game_authority(player_games: pl.DataFrame) -> pl.DataFrame:
    game_map = player_games.select(
        "season",
        pl.col("game_id").cast(pl.Int64).alias("game_pk"),
        pl.col("league_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        "level_group",
    ).unique()
    conflicts = game_map.group_by(["season", "game_pk", "player_id"]).agg(
        pl.col("league_id").n_unique().alias("league_count"),
        pl.col("level_group").n_unique().alias("level_count"),
    ).filter((pl.col("league_count") != 1) | (pl.col("level_count") != 1))
    if not conflicts.is_empty():
        raise ValueError("player-game authority conflicts at season/game/player grain")
    return game_map.unique(["season", "game_pk", "player_id"], keep="first")


def _milb_game_authority(game_map: pl.DataFrame, season: int) -> pl.DataFrame:
    authority = game_map.filter(
        (pl.col("season") == season) & (pl.col("level_group") != "MLB")
    ).select("game_pk", "league_id").unique()
    conflicts = authority.group_by("game_pk").agg(
        pl.col("league_id").n_unique().alias("league_count")
    ).filter(pl.col("league_count") != 1)
    if not conflicts.is_empty():
        raise ValueError("MiLB game authority conflicts at game grain")
    return authority.unique("game_pk", keep="first")


def _historical_milb_sidecar(
    *,
    season: int,
    level: str,
    raw_root: Path,
    contact_root: Path,
    game_map: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, object]]:
    directory = level.replace("+", "plus")
    files = sorted((raw_root / str(season) / directory).glob("*_pbp.csv"))
    raw = _load_milb_raw(files)
    with _contact_archive(contact_root, season, level)[0] as archive:
        slug = level.replace("+", "plus")
        terminal = _read_matching_parquet(
            archive, f"terminal_pas_{season}_{slug}.parquet"
        )
        contacts = _read_matching_parquet(
            archive, f"contact_value_target_contacts_{season}_{slug}.parquet"
        )
    projected = stage1_milb.project_terminal_pa_identities(raw, terminal, contacts)
    authority = (
        projected.join(
            terminal.select("game_pk", "at_bat_index", "terminal_pitch_number"),
            on=["game_pk", "at_bat_index"],
            how="left",
            validate="1:1",
        ).select(
            "game_pk",
            "at_bat_index",
            pl.col("terminal_pitch_number").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64, strict=False),
            "participant_authority",
        )
        .join(
            _milb_game_authority(game_map, season),
            on="game_pk",
            how="inner",
            validate="m:1",
        )
    )
    sidecar = build_terminal_matchup_sidecar(
        _normalize_milb_pitches(raw),
        authority,
        season=season,
        level_group=level,
        source_system="ARMSTJC_PBP",
        capability_tier="universal_affiliated_pbp_terminal_matchup_v1",
    )
    return sidecar, {
        "season": season,
        "level_group": level,
        "source_system": "ARMSTJC_PBP",
        "source_files": len(files),
        "source_size_bytes": sum(path.stat().st_size for path in files),
        "terminal_authority_rows": authority.height,
        "sidecar_rows": sidecar.height,
        "source_method": "retained_terminal_pa_and_contact_participant_authority",
    }


def _milb_2024_sidecar(
    *,
    level: str,
    raw_root: Path,
    game_map: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, object]]:
    directory = level.replace("+", "plus")
    files = sorted((raw_root / directory / "pbp").glob("*_pbp.csv"))
    raw = _load_milb_raw(files)
    pitches = _normalize_milb_pitches(raw)
    terminal = pitches.group_by(["game_pk", "at_bat_index"]).agg(
        pl.col("pitch_number").max().alias("terminal_pitch_number")
    )
    terminal_source = terminal.join(
        pitches.select(
            "game_pk", "at_bat_index", "pitch_number", "source_batter_id"
        ),
        left_on=["game_pk", "at_bat_index", "terminal_pitch_number"],
        right_on=["game_pk", "at_bat_index", "pitch_number"],
        how="left",
        validate="1:m",
    ).group_by(["game_pk", "at_bat_index", "terminal_pitch_number"]).agg(
        pl.col("source_batter_id").drop_nulls().n_unique().alias("players"),
        pl.col("source_batter_id").drop_nulls().first().alias("player_id"),
    )
    authority = (
        terminal_source.with_columns(
            pl.when(pl.col("players") == 1)
            .then(pl.lit("source_terminal_batter"))
            .otherwise(pl.lit("unresolved_terminal_batter"))
            .alias("participant_authority")
        )
        .join(
            _milb_game_authority(game_map, 2024),
            on="game_pk",
            how="inner",
            validate="m:1",
        )
        .select(
            "game_pk",
            "at_bat_index",
            "terminal_pitch_number",
            "player_id",
            "league_id",
            "participant_authority",
        )
    )
    sidecar = build_terminal_matchup_sidecar(
        pitches,
        authority,
        season=2024,
        level_group=level,
        source_system="ARMSTJC_PBP",
        capability_tier="universal_affiliated_pbp_terminal_matchup_v1",
    )
    return sidecar, {
        "season": 2024,
        "level_group": level,
        "source_system": "ARMSTJC_PBP",
        "source_files": len(files),
        "source_size_bytes": sum(path.stat().st_size for path in files),
        "terminal_authority_rows": authority.height,
        "sidecar_rows": sidecar.height,
        "source_method": "reconstructed_max_structured_pitch_authorized_games",
    }


def _mlb_sidecar(
    *,
    season: int,
    artifact_root: Path,
    game_map: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, object]]:
    paths = sorted(artifact_root.glob(f"*-current-talent-historical-mlb-{season}.zip"))
    if len(paths) != 1:
        raise ValueError(f"expected one MLB {season} artifact, found {paths}")
    with zipfile.ZipFile(paths[0]) as archive:
        savant, chunks = stage1_mlb._savant(archive, season)
    attributed = _with_official_outcome_batter(savant)
    terminal = attributed.filter(pl.col("is_plate_appearance_terminal"))
    authority = (
        terminal.select(
            "game_pk",
            "at_bat_index",
            pl.col("pitch_number").alias("terminal_pitch_number"),
            pl.col("_outcome_player_id").alias("player_id"),
            pl.when(pl.col("_outcome_player_id") != pl.col("_terminal_batter_id"))
            .then(pl.lit(MLB_OUTCOME_IDENTITY_POLICY))
            .otherwise(pl.lit("savant_official_terminal_batter"))
            .alias("participant_authority"),
        )
        .join(
            game_map.filter(
                (pl.col("season") == season) & (pl.col("level_group") == "MLB")
            ).select("game_pk", "player_id", "league_id"),
            on=["game_pk", "player_id"],
            how="inner",
            validate="m:1",
        )
    )
    pitches = attributed.select(
        "game_pk",
        "at_bat_index",
        "pitch_number",
        pl.col("game_date").cast(pl.String).str.to_date(strict=False),
        pl.col("batter_mlbam_id").alias("source_batter_id"),
        pl.col("pitcher_mlbam_id").alias("pitcher_id"),
        "batter_side",
        "pitcher_hand",
    )
    sidecar = build_terminal_matchup_sidecar(
        pitches,
        authority,
        season=season,
        level_group="MLB",
        source_system="BASEBALL_SAVANT",
        capability_tier="mlb_savant_terminal_matchup_v1",
    )
    return sidecar, {
        "season": season,
        "level_group": "MLB",
        "source_system": "BASEBALL_SAVANT",
        "source_container": paths[0].name,
        "source_files": len(chunks),
        "source_size_bytes": sum(int(row["size_bytes"]) for row in chunks),
        "terminal_authority_rows": authority.height,
        "sidecar_rows": sidecar.height,
        "two_strike_outcome_reassignments": terminal.filter(
            pl.col("_outcome_player_id") != pl.col("_terminal_batter_id")
        ).height,
        "source_method": "structured_savant_true_pa_terminal_with_official_batter_policy",
    }


def _coverage(frame: pl.DataFrame) -> list[dict[str, object]]:
    return (
        frame.group_by(["season", "level_group"])
        .agg(
            pl.len().alias("sidecar_pa"),
            pl.col("matchup_ready").sum().alias("matchup_ready_pa"),
            pl.col("modeling_join_ready").sum().alias("modeling_join_ready_pa"),
            (pl.col("prior_pitcher_pa") >= 1).sum().alias("prior_1_pa"),
            (pl.col("prior_pitcher_pa") >= 50).sum().alias("prior_50_pa"),
            (pl.col("prior_pitcher_pa") >= 100).sum().alias("prior_100_pa"),
            (pl.col("prior_outcome_ready_pitcher_pa") >= 50).sum().alias(
                "prior_outcome_ready_50_pa"
            ),
            (pl.col("prior_outcome_ready_pitcher_pa") >= 100).sum().alias(
                "prior_outcome_ready_100_pa"
            ),
            pl.col("source_matchup_conflict").sum().alias("source_conflict_pa"),
        )
        .with_columns(
            (pl.col("matchup_ready_pa") / pl.col("sidecar_pa")).alias(
                "matchup_ready_rate"
            ),
            (pl.col("modeling_join_ready_pa") / pl.col("sidecar_pa")).alias(
                "modeling_join_ready_rate"
            ),
            (pl.col("prior_50_pa") / pl.col("sidecar_pa")).alias("prior_50_rate"),
            (pl.col("prior_100_pa") / pl.col("sidecar_pa")).alias("prior_100_rate"),
            (
                pl.col("prior_outcome_ready_50_pa") / pl.col("sidecar_pa")
            ).alias("prior_outcome_ready_50_rate"),
            (
                pl.col("prior_outcome_ready_100_pa") / pl.col("sidecar_pa")
            ).alias("prior_outcome_ready_100_rate"),
        )
        .sort(["season", "level_group"])
        .to_dicts()
    )


def main() -> int:
    args = _parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    slice_root = args.report_root / "slices"
    slice_root.mkdir(exist_ok=True)
    player_games = pl.concat(
        [
            pl.read_parquet(args.player_game_2021_2023),
            pl.read_parquet(args.player_game_2024),
        ],
        how="vertical_relaxed",
    )
    game_map = _game_authority(player_games)
    frames: list[pl.DataFrame] = []
    provenance: list[dict[str, object]] = []
    for season in (2021, 2022, 2023):
        for level in LEVELS:
            frame, record = _historical_milb_sidecar(
                season=season,
                level=level,
                raw_root=args.historical_milb_root,
                contact_root=args.contact_artifact_root,
                game_map=game_map,
            )
            frames.append(frame)
            provenance.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
    for level in LEVELS:
        frame, record = _milb_2024_sidecar(
            level=level,
            raw_root=args.milb_2024_root,
            game_map=game_map,
        )
        frames.append(frame)
        provenance.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
    for season in SEASONS:
        root = (
            args.mlb_2024_artifact_root
            if season == 2024
            else args.mlb_2021_2023_artifact_root
        )
        frame, record = _mlb_sidecar(
            season=season,
            artifact_root=root,
            game_map=game_map,
        )
        frames.append(frame)
        provenance.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)

    sidecar = add_strict_prior_pitcher_evidence(
        pl.concat(frames, how="vertical_relaxed")
    )
    sidecar, reconciliation = reconcile_sidecar_to_player_games(sidecar, player_games)
    sidecar = add_strict_prior_pitcher_evidence(
        sidecar,
        evidence_ready_column="modeling_join_ready",
        output_column="prior_outcome_ready_pitcher_pa",
        date_count_column="outcome_ready_pitcher_pa_on_date",
    )
    duplicate = sidecar.group_by(["game_pk", "at_bat_index"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise RuntimeError("affiliated sidecar is not globally unique at game/PA grain")
    if sidecar.filter(pl.col("season") >= 2025).height:
        raise RuntimeError("matchup sidecar crossed the disclosed 2021-2024 boundary")

    sidecar_artifact = write_canonical_parquet(
        sidecar,
        args.report_root / "tables" / "hitter_v2_matchup_context_sidecar_2021_2024.parquet",
        table_name="hitter_v2_matchup_context_sidecar",
    ).as_record()
    reconciliation_artifact = write_canonical_parquet(
        reconciliation,
        args.report_root / "tables" / "hitter_v2_matchup_context_reconciliation_2021_2024.parquet",
        table_name="hitter_v2_matchup_context_reconciliation",
    ).as_record()
    coverage = _coverage(sidecar)
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "gate": "matchup_context_sidecar_materialization",
        "accepted": True,
        "source_seasons": list(SEASONS),
        "terminal_outcomes_scored": False,
        "forecast_targets_loaded": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "chronology_policy": "strictly_before_game_date_same_day_excluded",
        "source_audit_result_sha256": sha256(
            Path("docs/hitter-v2-matchup-context-source-result.json").read_bytes()
        ).hexdigest(),
        "source_provenance": provenance,
        "coverage_by_season_level": coverage,
        "totals": {
            "sidecar_pa": sidecar.height,
            "matchup_ready_pa": int(sidecar["matchup_ready"].sum()),
            "modeling_join_ready_pa": int(sidecar["modeling_join_ready"].sum()),
            "source_conflict_pa": int(sidecar["source_matchup_conflict"].sum()),
            "prior_1_pa": int((sidecar["prior_pitcher_pa"] >= 1).sum()),
            "prior_50_pa": int((sidecar["prior_pitcher_pa"] >= 50).sum()),
            "prior_100_pa": int((sidecar["prior_pitcher_pa"] >= 100).sum()),
            "prior_outcome_ready_50_pa": int(
                (sidecar["prior_outcome_ready_pitcher_pa"] >= 50).sum()
            ),
            "prior_outcome_ready_100_pa": int(
                (sidecar["prior_outcome_ready_pitcher_pa"] >= 100).sum()
            ),
            "player_game_reconciliation_rows": reconciliation.height,
            "exact_accepted_player_games": reconciliation.filter(
                pl.col("sidecar_reconciliation_status") == "exact_accepted_player_game"
            ).height,
            "failed_closed_player_games": reconciliation.filter(
                pl.col("sidecar_reconciliation_status") != "exact_accepted_player_game"
            ).height,
        },
        "reconciliation_status": (
            reconciliation.group_by("sidecar_reconciliation_status")
            .agg(
                pl.len().alias("player_games"),
                pl.col("accepted_terminal_pa").fill_null(0).sum().alias("official_pa"),
                pl.col("sidecar_terminal_pa").sum().alias("sidecar_pa"),
            )
            .sort("sidecar_reconciliation_status")
            .to_dicts()
        ),
        "storage": {
            "sidecar": sidecar_artifact,
            "reconciliation": reconciliation_artifact,
        },
        "next_gate": "pre_register_joint_contextual_candidate_contract_no_scoring",
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(report_path),
                "sha256": sha256(report_path.read_bytes()).hexdigest(),
                "totals": report["totals"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
