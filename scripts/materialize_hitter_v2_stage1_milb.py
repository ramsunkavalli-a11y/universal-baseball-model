#!/usr/bin/env python3
"""Materialize Hitter v2 Stage 1 affiliated outcome tables.

The script reuses checksum-pinned terminal-contact and historical adjudication
artifacts plus the public player-game release. It emits source/audit tables
only: no estimator, future target, run value, score, rank, or WAR is computed.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
from typing import Any
import zipfile

import polars as pl
from universal_baseball.current_talent_identity_corrections import (
    HISTORICAL_PLAYER_GAME_IDENTITY_CORRECTIONS,
)
from universal_baseball.current_talent_milb_evidence import OUTCOME_FIELDS
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.hitter_v2_outcomes import (
    OFFICIAL_BATTING_FIELDS,
    TERMINAL_OUTCOMES,
    aggregate_player_season_outcomes,
    aggregate_projected_terminal_pas,
    assemble_player_game_outcomes,
    assert_outcome_invariants,
    project_terminal_pa_identities,
    project_official_player_game_outcomes,
    resolve_official_player_game_outcomes,
)
from universal_baseball.storage import write_canonical_parquet


OWNER = "ramsunkavalli-a11y"
REPO = "universal-baseball-model"
CONTACT_RUN_2021_2022 = 32070152452
CONTACT_RUN_2023 = 32082637028
HISTORICAL_RUNS = {2021: 31979609553, 2022: 31971662070, 2023: 31971923778}
LEVELS = ("aaa", "aa", "a+", "a", "rk")
EXPECTED_ARTIFACT_SHA256 = {
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2021-aaa"): "fd6a51a42d6f112168bfba2505acaa1f9547bb268528002cd92349a77d1e2543",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2021-aa"): "a3d970f20b4efcb58c88aa9182a2be69db19d1893bff51ccabdaeaf7ba1349e0",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2021-aplus"): "82f78a583cda7b290972f3f812996ef3eb040a32ea8670b8f3e24304782f7eb7",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2021-a"): "c83a0566dcec085fc87967c2302bbdabb5ab2b26b69afb60688a8736ff9f4e70",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2021-rk"): "f711201b8861e98d34955052c7673c56b5204f50b7f20f5cac3a3ac896b51672",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2022-aaa"): "3b7e339efb195516c9191ce9d4e8a081dd326ad265c3e6bc00ea08eadc7d1053",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2022-aa"): "c11cbc3fcf83fbe91b5c41c3f41413b0da9e0a7fdf5943630e0518554e2de9bd",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2022-aplus"): "84ce2c22d18b1797ececff2305c03a7fcab089ceace030423f7ddb150518eda7",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2022-a"): "66391d02890aea3cfd3bc46f2040793570f787d8c7b46b7b567436f6c5af0649",
    (CONTACT_RUN_2021_2022, "current-talent-contact-value-source-2022-rk"): "25efe974cbe01d10af06bcc6c2821c4840ac805557875679f886143e0b903dde",
    (CONTACT_RUN_2023, "current-talent-contact-value-confirmation-source-v2"): "2052a2a65dd9dfbb59f40ca1e6e50b7f40b86f5a5e2e03ddc93b375a3562a0bf",
    (31979609553, "current-talent-historical-milb-full-season-2021-aaa"): "fa1ae3c6fe1d5e14256fef1e915e256a510f3e1f6290fb77d2fe68c5011e1e05",
    (31979609553, "current-talent-historical-milb-full-season-2021-aa"): "201c02fb923f754f44b1601e1ada83eb0a84f25fcf7f20b50a8ca1551d587fa6",
    (31979609553, "current-talent-historical-milb-full-season-2021-a+"): "01507a26eb6ecac91b35ed834367360967c07a9ad182a60e116cef8cda3f85f1",
    (31979609553, "current-talent-historical-milb-full-season-2021-a"): "b106a37b1f3bc67971856dba8797495e64c8f00f13c829348798ed0750d03b7a",
    (31979609553, "current-talent-historical-milb-full-season-2021-rk"): "6b5dc9368454583f86ee83a6fedc045486601951e56e90ed7bfa774cca85b32c",
    (31971662070, "current-talent-historical-milb-full-season-aaa"): "0957be0ccd10bf6c2f51b1f23fdc30c4e107c3515e147a83afcfb8cf1fa079be",
    (31971662070, "current-talent-historical-milb-full-season-aa"): "bbb943dc14d56297b02977fa5448d30d1731e74f0063df0afb06dce8e964b00c",
    (31971662070, "current-talent-historical-milb-full-season-a+"): "a041a624ee3601bd5de25722a6508c3068cd08f909b0e0c888ffd2cd108e79d2",
    (31971662070, "current-talent-historical-milb-full-season-a"): "2708bbe300aafcdd5dcca36c546c4d2efaf05c580857ee9094a036918838311d",
    (31971662070, "current-talent-historical-milb-full-season-rk"): "a0a38357a6de46e3b747f0fe76b916d3a401a3082f899407d4d55f4dc3c008df",
    (31971923778, "current-talent-historical-milb-full-season-2023-aaa"): "cf5fe4c7b6283033d552d2d14b200a61c8e15fe0e5b118dffe0f8eadb727cdaf",
    (31971923778, "current-talent-historical-milb-full-season-2023-aa"): "6f82f21b350d38dd14f264de205c0fdb7fba0e90b2d73dab60ebaabf33134179",
    (31971923778, "current-talent-historical-milb-full-season-2023-a+"): "ffc25a0d442a69aa328d1079e25e67bc1246350d136857038265bc6956f4f0d5",
    (31971923778, "current-talent-historical-milb-full-season-2023-a"): "ea6d5fd8d478828750e1cc3ae08b05a814ef5533cf00da8994fe8f1d177f926d",
    (31971923778, "current-talent-historical-milb-full-season-2023-rk"): "96c4a2508e4e2c02fdc062e9d083ba5d4e06a189ecb0f2077725d8898efbb6f4",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2021, 2022, 2023])
    parser.add_argument("--levels", nargs="+", choices=LEVELS, default=list(LEVELS))
    parser.add_argument(
        "--work-root", type=Path, default=Path("data/quarantine/hitter-v2-stage1")
    )
    parser.add_argument(
        "--report-root", type=Path, default=Path("reports/generated/hitter-v2-stage1")
    )
    return parser.parse_args()


def _artifact_bytes(
    *,
    run_id: int,
    name: str,
    work_root: Path,
) -> tuple[bytes, dict[str, Any]]:
    expected_digest = EXPECTED_ARTIFACT_SHA256.get((run_id, name))
    if expected_digest is None:
        raise RuntimeError(f"artifact is absent from the frozen digest registry: {run_id}/{name}")
    path = work_root / "artifacts" / f"{run_id}-{name}.zip"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size <= 0:
        url = f"https://nightly.link/{OWNER}/{REPO}/actions/runs/{run_id}/{name}.zip"
        download_file(url, path, timeout_seconds=300)
    content = path.read_bytes()
    actual_digest = sha256(content).hexdigest()
    if actual_digest != expected_digest:
        raise RuntimeError(
            f"artifact digest mismatch for {name}: {actual_digest} != {expected_digest}"
        )
    return content, {
        "run_id": run_id,
        "name": name,
        "size_bytes": len(content),
        "sha256": actual_digest,
        "digest_authority": "committed_checkpoint_or_stage0_verified_github_metadata",
    }


def _contact_artifact_name(season: int, level: str) -> tuple[int, str]:
    if season in {2021, 2022}:
        slug = level.replace("+", "plus")
        return CONTACT_RUN_2021_2022, f"current-talent-contact-value-source-{season}-{slug}"
    if season == 2023:
        return CONTACT_RUN_2023, "current-talent-contact-value-confirmation-source-v2"
    raise ValueError(f"Stage 1 certified contact registry has no season {season}")


def _historical_artifact_name(season: int, level: str) -> str:
    if season == 2022:
        return f"current-talent-historical-milb-full-season-{level}"
    return f"current-talent-historical-milb-full-season-{season}-{level}"


def _contact_report_suffix(season: int, slug: str) -> str:
    if season in {2021, 2022}:
        return "report.json"
    return f"current-talent-contact-value-source-materialization/{season}/{slug}/report.json"


def _read_matching_parquet(content: bytes, suffix: str) -> pl.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"expected one artifact member ending {suffix!r}, got {matches}")
        return pl.read_parquet(io.BytesIO(archive.read(matches[0])))


def _read_matching_json(content: bytes, suffix: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"expected one artifact member ending {suffix!r}, got {matches}")
        payload = json.loads(archive.read(matches[0]))
    if not isinstance(payload, dict):
        raise RuntimeError(f"artifact JSON member {matches[0]} is not an object")
    return payload


def _apply_identity_corrections(frame: pl.DataFrame, *, season: int) -> pl.DataFrame:
    result = frame
    observed_leagues = set(result.get_column("league_id").drop_nulls().unique().to_list())
    for correction in HISTORICAL_PLAYER_GAME_IDENTITY_CORRECTIONS:
        if correction.season != season or correction.league_id not in observed_leagues:
            continue
        source = result.filter(
            (pl.col("game_id") == correction.game_id)
            & (pl.col("league_id") == correction.league_id)
            & (pl.col("player_id") == correction.source_player_id)
        )
        if source.height != 1:
            raise RuntimeError("certified Hitter v2 identity source row is absent or non-unique")
        row = source.row(0, named=True)
        observed = tuple(int(row[field] or 0) for field in OUTCOME_FIELDS)
        if observed != correction.expected_outcome_vector:
            raise RuntimeError("certified Hitter v2 identity outcome vector drifted")
        target = result.filter(
            (pl.col("game_id") == correction.game_id)
            & (pl.col("player_id") == correction.corrected_player_id)
        )
        if target.height > 1 or (
            target.height == 1
            and any(target.item(0, field) is not None for field in OFFICIAL_BATTING_FIELDS)
        ):
            raise RuntimeError("certified Hitter v2 identity correction collides with evidence")
        result = result.filter(
            ~(
                (pl.col("game_id") == correction.game_id)
                & (pl.col("player_id") == correction.corrected_player_id)
            )
        ).with_columns(
            pl.when(
                (pl.col("game_id") == correction.game_id)
                & (pl.col("league_id") == correction.league_id)
                & (pl.col("player_id") == correction.source_player_id)
            )
            .then(pl.lit(correction.corrected_player_id))
            .otherwise(pl.col("player_id"))
            .cast(pl.Int64)
            .alias("player_id")
        )
    duplicate = result.group_by(["game_id", "player_id"]).len().filter(pl.col("len") > 1)
    if not duplicate.is_empty():
        raise RuntimeError("identity corrections created duplicate Hitter v2 player-game keys")
    return result


def _overlay_adjudicated_outcomes(
    resolved: pl.DataFrame, adjudicated: pl.DataFrame
) -> pl.DataFrame:
    duplicate_keys = (
        adjudicated.group_by(["game_id", "player_id"])
        .len()
        .filter(pl.col("len") > 1)
        .select("game_id", "player_id")
    )
    if not duplicate_keys.is_empty():
        selected: list[pl.DataFrame] = []
        duplicate_rows = adjudicated.join(
            duplicate_keys, on=["game_id", "player_id"], how="inner"
        )
        for group in duplicate_rows.partition_by(
            ["game_id", "player_id"], maintain_order=True
        ):
            official = group.filter(pl.col("outcome_authority") == "official_game_log")
            if official.height != 1:
                raise RuntimeError(
                    "duplicate adjudication key lacks one unique official-game-log authority"
                )
            selected.append(official)
        adjudicated = pl.concat(
            [
                adjudicated.join(
                    duplicate_keys, on=["game_id", "player_id"], how="anti"
                ),
                *selected,
            ],
            how="vertical_relaxed",
        )
    authority = adjudicated.select(
        "game_id", "player_id", *OUTCOME_FIELDS, "outcome_authority"
    ).rename({field: f"adjudicated_{field}" for field in OUTCOME_FIELDS})
    joined = resolved.join(authority, on=["game_id", "player_id"], how="left", validate="1:1")
    missing = joined.filter(
        pl.col("batting_PA").is_not_null() & pl.col("adjudicated_batting_PA").is_null()
    )
    if not missing.is_empty():
        raise RuntimeError(
            f"{missing.height} resolved player-games lack certified adjudication coverage"
        )
    return joined.with_columns(
        *[
            pl.col(f"adjudicated_{field}").alias(field)
            for field in OUTCOME_FIELDS
        ]
    ).drop([f"adjudicated_{field}" for field in OUTCOME_FIELDS])


def _load_official_observations(
    *,
    season: int,
    level: str,
    work_root: Path,
    asset_names: list[str],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    if not asset_names:
        raise RuntimeError(f"no player-game assets found for {season} {level}")
    frames: list[pl.DataFrame] = []
    source_records: list[dict[str, Any]] = []
    raw_dir = work_root / "player-game" / str(season) / level.replace("+", "plus")
    raw_dir.mkdir(parents=True, exist_ok=True)
    for asset_name in asset_names:
        path = raw_dir / asset_name
        if not path.exists() or path.stat().st_size <= 0:
            url = (
                "https://github.com/armstjc/milb-data-repository/releases/download/"
                f"game_player_stats/{asset_name}"
            )
            download_file(url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        frames.append(
            project_official_player_game_outcomes(
                raw, source_asset=asset_name, season=season, game_type="R"
            )
        )
        source_records.append(
            {
                "name": asset_name,
                "downloaded_size_bytes": path.stat().st_size,
                "downloaded_sha256": sha256(path.read_bytes()).hexdigest(),
                "selection_authority": "checksum_pinned_contact_artifact_report",
            }
        )
    return pl.concat(frames, how="vertical_relaxed"), {
        "asset_count": len(asset_names),
        "assets": source_records,
    }


def _load_projected_terminal_outcomes(
    *,
    season: int,
    level: str,
    terminal_pas: pl.DataFrame,
    participant_overlay: pl.DataFrame,
    game_leagues: pl.DataFrame,
    work_root: Path,
    asset_names: list[str],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    if not asset_names:
        raise RuntimeError(f"no PBP assets found for {season} {level}")
    raw_dir = work_root / "pbp" / str(season) / level.replace("+", "plus")
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    source_records: list[dict[str, Any]] = []
    columns = ["game_pk", "at_bat_number", "pitch_number", "game_type", "batter"]
    for asset_name in asset_names:
        path = raw_dir / asset_name
        if not path.exists() or path.stat().st_size <= 0:
            url = (
                "https://github.com/armstjc/milb-data-repository/releases/download/"
                f"pbp/{asset_name}"
            )
            download_file(url, path, timeout_seconds=600)
        frame = (
            pl.scan_csv(
                path,
                infer_schema=False,
                null_values=["", "NA", "NaN", "null", "None"],
                truncate_ragged_lines=False,
            )
            .select(columns)
            .collect()
        )
        frames.append(frame)
        source_records.append(
            {
                "name": asset_name,
                "downloaded_size_bytes": path.stat().st_size,
                "downloaded_sha256": sha256(path.read_bytes()).hexdigest(),
                "selection_authority": "checksum_pinned_contact_artifact_report",
            }
        )
    projected = project_terminal_pa_identities(
        pl.concat(frames, how="vertical_relaxed"),
        terminal_pas,
        participant_overlay,
    )
    counts, metrics = aggregate_projected_terminal_pas(projected, game_leagues)
    return counts, {
        **metrics,
        "asset_count": len(asset_names),
        "assets": source_records,
    }


def _coverage(frame: pl.DataFrame, dimensions: list[str]) -> list[dict[str, Any]]:
    return (
        frame.group_by(dimensions)
        .agg(
            pl.len().alias("player_game_rows"),
            pl.col("game_id").n_unique().alias("games"),
            pl.col("player_id").n_unique().alias("players"),
            pl.col("batting_PA").sum().alias("official_pa"),
            pl.col("accepted_terminal_pa").sum().alias("accounted_pa"),
            pl.col("observed_terminal_contact_count").sum().alias("pbp_terminal_contacts"),
        )
        .sort(dimensions)
        .to_dicts()
    )


def main() -> int:
    args = _parse_args()
    seasons = sorted(set(args.seasons))
    levels = list(dict.fromkeys(args.levels))
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "tables").mkdir(parents=True, exist_ok=True)

    frames: list[pl.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    resolution: list[dict[str, Any]] = []
    for season in seasons:
        for level in levels:
                contact_run, contact_name = _contact_artifact_name(season, level)
                contact_zip, contact_provenance = _artifact_bytes(
                    run_id=contact_run,
                    name=contact_name,
                    work_root=args.work_root,
                )
                slug = level.replace("+", "plus")
                contact_report = _read_matching_json(
                    contact_zip, _contact_report_suffix(season, slug)
                )
                contacts = _read_matching_parquet(
                    contact_zip,
                    f"contact_value_target_contacts_{season}_{slug}.parquet",
                )
                terminal_pas = _read_matching_parquet(
                    contact_zip,
                    f"terminal_pas_{season}_{slug}.parquet",
                )

                observations, player_game_provenance = _load_official_observations(
                    season=season,
                    level=level,
                    work_root=args.work_root,
                    asset_names=list(contact_report["player_game_source"]["asset_names"]),
                )
                resolved, metrics = resolve_official_player_game_outcomes(observations)
                hard_unresolved = (
                    metrics["unresolved_player_game_count"]
                    - metrics["positive_pa_team_identity_conflict_player_game_count"]
                )
                if hard_unresolved:
                    raise RuntimeError(
                        f"{season} {level} has unresolved official snapshots: {metrics}"
                    )
                resolved = _apply_identity_corrections(resolved, season=season)

                history_run = HISTORICAL_RUNS[season]
                history_name = _historical_artifact_name(season, level)
                history_zip, history_provenance = _artifact_bytes(
                    run_id=history_run,
                    name=history_name,
                    work_root=args.work_root,
                )
                adjudicated = _read_matching_parquet(
                    history_zip,
                    f"current_talent_outcomes_{season}_{slug}_adjudicated.parquet",
                )
                resolved = _overlay_adjudicated_outcomes(resolved, adjudicated)
                contact_counts, pbp_provenance = _load_projected_terminal_outcomes(
                    season=season,
                    level=level,
                    terminal_pas=terminal_pas,
                    participant_overlay=contacts,
                    game_leagues=resolved.select(
                        pl.col("game_id").alias("game_pk"), "league_id"
                    ),
                    work_root=args.work_root,
                    asset_names=list(contact_report["contact_source"]["asset_names"]),
                )
                player_games = assemble_player_game_outcomes(
                    resolved, contact_counts, season=season, level_group=level
                )
                frames.append(player_games)
                resolution.append({"season": season, "level": level, **metrics})
                provenance.append(
                    {
                        "season": season,
                        "level": level,
                        "contact_artifact": contact_provenance,
                        "pbp_terminal_identity_source": pbp_provenance,
                        "historical_adjudication_artifact": history_provenance,
                        "player_game_release": player_game_provenance,
                    }
                )
                print(
                    json.dumps(
                        {
                            "season": season,
                            "level": level,
                            "rows": player_games.height,
                            "pa": int(player_games.get_column("batting_PA").sum()),
                            "accepted": int(
                                player_games.filter(
                                    pl.col("source_status").str.starts_with("accepted")
                                ).height
                            ),
                            "failed_closed": int(
                                player_games.filter(
                                    ~pl.col("source_status").str.starts_with("accepted")
                                ).height
                            ),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

    player_games = pl.concat(frames, how="vertical_relaxed").sort(
        ["season", "league_id", "game_id", "player_id"]
    )
    assert_outcome_invariants(player_games)
    player_seasons = aggregate_player_season_outcomes(player_games)
    exceptions = player_games.filter(~pl.col("source_status").str.starts_with("accepted"))
    model_ready = player_games.filter(pl.col("source_status").str.starts_with("accepted"))

    player_game_artifact = write_canonical_parquet(
        player_games,
        args.report_root / "tables" / "hitter_v2_player_game_outcomes_2021_2023_milb.parquet",
        table_name="hitter_v2_player_game_outcomes_milb",
    ).as_record()
    player_season_artifact = write_canonical_parquet(
        player_seasons,
        args.report_root / "tables" / "hitter_v2_player_season_outcomes_2021_2023_milb.parquet",
        table_name="hitter_v2_player_season_outcomes_milb",
    ).as_record()
    exception_artifact = write_canonical_parquet(
        exceptions,
        args.report_root / "tables" / "hitter_v2_player_game_exceptions_2021_2023_milb.parquet",
        table_name="hitter_v2_player_game_exceptions_milb",
    ).as_record()
    status_counts = (
        player_games.group_by(["season", "level_group", "source_status"])
        .agg(
            pl.len().alias("player_game_rows"),
            pl.col("batting_PA").sum().alias("official_pa"),
        )
        .sort(["season", "level_group", "source_status"])
        .to_dicts()
    )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 1,
        "scope": "affiliated_milb_2021_2023_source_only",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "taxonomy": list(TERMINAL_OUTCOMES),
        "source_status_policy": "accepted_exact_rows_model_ready_failed_rows_retained_audit_only",
        "totals": {
            "player_game_rows": player_games.height,
            "model_ready_player_game_rows": model_ready.height,
            "failed_closed_player_game_rows": exceptions.height,
            "player_season_rows": player_seasons.height,
            "games": player_games.get_column("game_id").n_unique(),
            "players": player_games.get_column("player_id").n_unique(),
            "official_pa": int(player_games.get_column("batting_PA").sum()),
            "accepted_terminal_pa": int(player_games.get_column("accepted_terminal_pa").sum()),
            "model_ready_official_pa": int(model_ready.get_column("batting_PA").sum()),
            "pbp_terminal_contacts": int(
                player_games.get_column("observed_terminal_contact_count").sum()
            ),
        },
        "status_counts": status_counts,
        "coverage_by_season_level_status": _coverage(
            player_games, ["season", "level_group", "source_status"]
        ),
        "coverage_by_season_league_status": _coverage(
            player_games, ["season", "league_id", "source_status"]
        ),
        "coverage_by_season_team_status": _coverage(
            player_games, ["season", "team_id", "source_status"]
        ),
        "snapshot_resolution": resolution,
        "source_provenance": provenance,
        "storage": {
            "player_game": player_game_artifact,
            "player_season": player_season_artifact,
            "exceptions": exception_artifact,
        },
        "limitations": [
            "This artifact covers affiliated MiLB. The separately certified MLB Savant path must be adapted to the same enum before Stage 1 can close universally.",
            "MULTI_OUT is sourced from terminal PBP; official GIDP/GITP residual is retained as a diagnostic because the opportunity/event definitions are not identical.",
        ],
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
