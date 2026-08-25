#!/usr/bin/env python3
"""Audit affiliated PBP matchup context without fitting or scoring a hitter.

Only PA keys, dates, batter/pitcher identities, and observed matchup handedness
are read.  Terminal outcomes, forecast targets, and protected seasons are not
loaded.  Prior-pitcher evidence is counted strictly before the PA date, so a
same-day game can never supply its own opponent-quality context.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from zipfile import ZipFile

import duckdb


LEVEL_ALIASES = {
    "aaa": "AAA",
    "aa": "AA",
    "aplus": "HIGH_A",
    "a": "SINGLE_A",
    "rk": "ROOKIE_COMPLEX",
}
PRIOR_THRESHOLDS = (1, 50, 100, 200)


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
        "--historical-mlb-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1-mlb/artifacts"),
    )
    parser.add_argument(
        "--mlb-2024-root",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-source/mlb/"
            "current-talent-historical-mlb-2024"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-matchup-context-source-audit"),
    )
    return parser.parse_args()


def _extract_mlb_savant(zip_path: Path, destination: Path) -> list[Path]:
    """Extract only checksum-pinned raw Savant members from an existing artifact."""
    marker = destination / ".complete"
    if marker.exists():
        files = sorted(destination.glob("savant_*.csv"))
        if files:
            return files
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with ZipFile(zip_path) as archive:
        members = [
            item for item in archive.infolist()
            if "/raw/savant/savant_" in item.filename and item.filename.endswith(".csv")
        ]
        if not members:
            raise ValueError(f"no raw Savant members in {zip_path}")
        for item in members:
            target = destination / Path(item.filename).name
            with archive.open(item) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    marker.write_text(zip_path.name + "\n", encoding="utf-8")
    return sorted(destination.glob("savant_*.csv"))


def _stage_files(files: list[Path], destination: Path) -> list[Path]:
    """Copy long-path source files to a DuckDB-safe local audit directory."""
    marker = destination / ".complete"
    if marker.exists():
        staged = sorted(destination.glob("savant_*.csv"))
        if len(staged) == len(files):
            return staged
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for source in files:
        long_source = Path("\\\\?\\" + str(source.resolve()))
        shutil.copy2(long_source, destination / source.name)
    marker.write_text(f"{len(files)} files\n", encoding="utf-8")
    return sorted(destination.glob("savant_*.csv"))


def _source_groups(args: argparse.Namespace) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for season in (2021, 2022, 2023):
        for directory, level_group in LEVEL_ALIASES.items():
            files = sorted((args.historical_milb_root / str(season) / directory).glob("*_pbp.csv"))
            groups.append(
                {
                    "season": season,
                    "level_group": level_group,
                    "source_system": "ARMSTJC_PBP",
                    "files": files,
                    "retained_raw_source": True,
                }
            )
    for directory, level_group in LEVEL_ALIASES.items():
        files = sorted((args.milb_2024_root / directory / "pbp").glob("*_pbp.csv"))
        groups.append(
            {
                "season": 2024,
                "level_group": level_group,
                "source_system": "ARMSTJC_PBP",
                "files": files,
                "retained_raw_source": True,
            }
        )

    extract_root = args.report_root / "extracted-mlb-savant"
    for season in (2021, 2022, 2023):
        artifacts = sorted(
            args.historical_mlb_artifact_root.glob(
                f"*-current-talent-historical-mlb-{season}.zip"
            )
        )
        if len(artifacts) != 1:
            raise ValueError(f"expected one MLB {season} artifact, found {artifacts}")
        files = _extract_mlb_savant(artifacts[0], extract_root / str(season))
        groups.append(
            {
                "season": season,
                "level_group": "MLB",
                "source_system": "BASEBALL_SAVANT",
                "files": files,
                "retained_raw_source": True,
                "container": artifacts[0],
            }
        )
    files_2024 = sorted(args.mlb_2024_root.rglob("savant_*.csv"))
    files_2024 = _stage_files(files_2024, extract_root / "2024")
    groups.append(
        {
            "season": 2024,
            "level_group": "MLB",
            "source_system": "BASEBALL_SAVANT",
            "files": files_2024,
            "retained_raw_source": True,
        }
    )
    missing = [
        f"{group['season']} {group['level_group']}"
        for group in groups
        if not group["files"]
    ]
    if missing:
        raise ValueError(f"missing disclosed source files: {missing}")
    return groups


def _sql_paths(files: list[Path]) -> str:
    quoted = ["'" + str(path.resolve()).replace("\\", "/").replace("'", "''") + "'" for path in files]
    return "[" + ",".join(quoted) + "]"


def _materialize_group(
    connection: duckdb.DuckDBPyConnection,
    group: dict[str, object],
    destination: Path,
) -> dict[str, object]:
    files = group["files"]
    assert isinstance(files, list)
    source = _sql_paths(files)
    output = str(destination.resolve()).replace("\\", "/").replace("'", "''")
    season = int(group["season"])
    level = str(group["level_group"]).replace("'", "''")
    source_system = str(group["source_system"]).replace("'", "''")
    connection.execute(
        f"""
        COPY (
          WITH source AS (
            SELECT
              try_cast(nullif(trim(game_pk), '') AS BIGINT) AS game_pk,
              try_cast(nullif(trim(at_bat_number), '') AS BIGINT) AS at_bat_number,
              try_cast(nullif(trim(pitch_number), '') AS BIGINT) AS pitch_number,
              try_cast(nullif(trim(game_date), '') AS DATE) AS game_date,
              try_cast(nullif(trim(batter), '') AS BIGINT) AS batter_id,
              try_cast(nullif(trim(pitcher), '') AS BIGINT) AS pitcher_id,
              upper(nullif(trim(stand), '')) AS batter_side,
              upper(nullif(trim(p_throws), '')) AS pitcher_hand,
              upper(nullif(trim(game_type), '')) AS game_type
            FROM read_csv({source}, header = true, all_varchar = true,
              union_by_name = true, ignore_errors = false)
          )
          SELECT
            {season}::INTEGER AS season,
            '{level}'::VARCHAR AS level_group,
            '{source_system}'::VARCHAR AS source_system,
            game_pk,
            at_bat_number,
            max(game_date) AS game_date,
            arg_max(batter_id, pitch_number) AS batter_id,
            arg_max(pitcher_id, pitch_number) AS pitcher_id,
            arg_max(batter_side, pitch_number) AS batter_side,
            arg_max(pitcher_hand, pitch_number) AS pitcher_hand,
            count(DISTINCT batter_id) AS distinct_batter_ids,
            count(DISTINCT pitcher_id) AS distinct_pitcher_ids,
            count(DISTINCT batter_side) AS distinct_batter_sides,
            count(DISTINCT pitcher_hand) AS distinct_pitcher_hands
          FROM source
          WHERE game_type = 'R' AND game_pk IS NOT NULL AND at_bat_number IS NOT NULL
          GROUP BY game_pk, at_bat_number
        ) TO '{output}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    return {
        "season": season,
        "level_group": group["level_group"],
        "source_system": group["source_system"],
        "source_files": len(files),
        "source_size_bytes": sum(path.stat().st_size for path in files),
        "retained_raw_source": bool(group["retained_raw_source"]),
        "container": (
            Path(str(group["container"])).name if group.get("container") else ""
        ),
    }


def _write_results(
    connection: duckdb.DuckDBPyConnection,
    pa_root: Path,
    report_root: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    parquet_glob = str((pa_root / "*.parquet").resolve()).replace("\\", "/")
    query = f"""
      WITH pa AS (
        SELECT * FROM read_parquet('{parquet_glob}')
      ), pitcher_date AS (
        SELECT pitcher_id, game_date, count(*) AS date_pa
        FROM pa
        WHERE pitcher_id IS NOT NULL AND pitcher_id > 0 AND game_date IS NOT NULL
        GROUP BY pitcher_id, game_date
      ), pitcher_date_prior AS (
        SELECT *, coalesce(sum(date_pa) OVER (
          PARTITION BY pitcher_id ORDER BY game_date
          ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS prior_pitcher_pa
        FROM pitcher_date
      ), enriched AS (
        SELECT pa.*, coalesce(pdp.prior_pitcher_pa, 0) AS prior_pitcher_pa
        FROM pa
        LEFT JOIN pitcher_date_prior pdp USING (pitcher_id, game_date)
      )
      SELECT
        season, level_group, source_system,
        count(*) AS canonical_pa,
        count(*) FILTER (WHERE batter_id IS NOT NULL AND batter_id > 0) AS batter_identity_pa,
        count(*) FILTER (WHERE pitcher_id IS NOT NULL AND pitcher_id > 0) AS pitcher_identity_pa,
        count(*) FILTER (WHERE batter_side IN ('L', 'R')) AS batter_side_pa,
        count(*) FILTER (WHERE pitcher_hand IN ('L', 'R')) AS pitcher_hand_pa,
        count(*) FILTER (
          WHERE batter_id IS NOT NULL AND batter_id > 0
            AND pitcher_id IS NOT NULL AND pitcher_id > 0
            AND batter_side IN ('L', 'R') AND pitcher_hand IN ('L', 'R')
        ) AS complete_matchup_pa,
        count(*) FILTER (
          WHERE batter_id IS NOT NULL AND batter_id > 0
            AND pitcher_id IS NOT NULL AND pitcher_id > 0
            AND batter_side IN ('L', 'R') AND pitcher_hand IN ('L', 'R')
            AND distinct_batter_ids <= 1 AND distinct_pitcher_ids <= 1
            AND distinct_batter_sides <= 1 AND distinct_pitcher_hands <= 1
        ) AS conflict_free_matchup_pa,
        count(*) FILTER (WHERE prior_pitcher_pa >= 1) AS prior_1_pa,
        count(*) FILTER (WHERE prior_pitcher_pa >= 50) AS prior_50_pa,
        count(*) FILTER (WHERE prior_pitcher_pa >= 100) AS prior_100_pa,
        count(*) FILTER (WHERE prior_pitcher_pa >= 200) AS prior_200_pa,
        count(*) FILTER (WHERE game_date IS NULL) AS missing_game_date_pa,
        count(*) FILTER (WHERE distinct_batter_ids > 1) AS conflicting_batter_pa,
        count(*) FILTER (WHERE distinct_pitcher_ids > 1) AS conflicting_pitcher_pa,
        count(*) FILTER (WHERE distinct_batter_sides > 1) AS conflicting_batter_side_pa,
        count(*) FILTER (WHERE distinct_pitcher_hands > 1) AS conflicting_pitcher_hand_pa
      FROM enriched
      GROUP BY season, level_group, source_system
      ORDER BY season, level_group
    """
    cursor = connection.execute(query)
    columns = [item[0] for item in cursor.description]
    rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    for row in rows:
        denominator = int(row["canonical_pa"])
        for column in (
            "batter_identity_pa",
            "pitcher_identity_pa",
            "batter_side_pa",
            "pitcher_hand_pa",
            "complete_matchup_pa",
            "conflict_free_matchup_pa",
            "prior_1_pa",
            "prior_50_pa",
            "prior_100_pa",
            "prior_200_pa",
        ):
            row[column.replace("_pa", "_rate")] = (
                int(row[column]) / denominator if denominator else None
            )

    total = {"canonical_pa": sum(int(row["canonical_pa"]) for row in rows)}
    for column in (
        "batter_identity_pa",
        "pitcher_identity_pa",
        "batter_side_pa",
        "pitcher_hand_pa",
        "complete_matchup_pa",
        "conflict_free_matchup_pa",
        "prior_1_pa",
        "prior_50_pa",
        "prior_100_pa",
        "prior_200_pa",
        "missing_game_date_pa",
        "conflicting_batter_pa",
        "conflicting_pitcher_pa",
        "conflicting_batter_side_pa",
        "conflicting_pitcher_hand_pa",
    ):
        total[column] = sum(int(row[column]) for row in rows)
    for column in (
        "batter_identity_pa",
        "pitcher_identity_pa",
        "batter_side_pa",
        "pitcher_hand_pa",
        "complete_matchup_pa",
        "conflict_free_matchup_pa",
        "prior_1_pa",
        "prior_50_pa",
        "prior_100_pa",
        "prior_200_pa",
    ):
        total[column.replace("_pa", "_rate")] = total[column] / total["canonical_pa"]

    csv_path = report_root / "coverage_by_season_level.csv"
    connection.execute(
        f"COPY ({query}) TO '{str(csv_path.resolve()).replace('\\', '/')}' (HEADER, DELIMITER ',')"
    )
    return rows, total


def main() -> None:
    args = _parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    pa_root = args.report_root / "pa"
    if pa_root.exists():
        shutil.rmtree(pa_root)
    pa_root.mkdir()
    connection = duckdb.connect()
    groups = _source_groups(args)
    inventory = []
    for index, group in enumerate(groups):
        destination = pa_root / f"{index:02d}_{group['season']}_{group['level_group']}.parquet"
        inventory.append(_materialize_group(connection, group, destination))
    rows, total = _write_results(connection, pa_root, args.report_root)
    result = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "gate": "matchup_context_source_readiness_audit",
        "source_seasons": [2021, 2022, 2023, 2024],
        "protected_2026_opened": False,
        "terminal_outcomes_loaded": False,
        "forecast_targets_loaded": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "chronology_policy": "pitcher evidence dated strictly before PA game_date; same-day evidence excluded",
        "prior_evidence_thresholds": list(PRIOR_THRESHOLDS),
        "source_inventory": inventory,
        "coverage_by_season_level": rows,
        "overall": total,
        "retention_finding": {
            "raw_pbp_has_matchup_fields": True,
            "existing_hitter_v2_stage1_terminal_artifacts_retain_matchup_fields": False,
            "required_action": "certify a matchup-preserving PA sidecar before any opponent adjustment candidate",
        },
        "readiness_decision": "source_capable_sidecar_not_yet_certified",
    }
    output = args.report_root / "report.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    digest = sha256(output.read_bytes()).hexdigest()
    print(json.dumps({"report": str(output), "sha256": digest, "overall": total}, indent=2))


if __name__ == "__main__":
    main()
