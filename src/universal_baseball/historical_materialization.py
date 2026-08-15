"""Small materialization helpers for the first historical database slices."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from universal_baseball.storage import ParquetArtifact, write_canonical_parquet


def write_event_table_by_game_month(
    frame: pl.DataFrame,
    resolved_games: pl.DataFrame,
    root: Path,
    *,
    table_name: str,
) -> list[ParquetArtifact]:
    """Write a game-keyed table to Hive-style event-month partitions.

    Event tables intentionally do not duplicate game date on every row. The
    partition assignment therefore comes from the resolved game view. A missing
    or conflicting (null) game date fails instead of assigning a source-file
    month or guessing from ingestion time.
    """

    if "game_pk" not in frame.columns:
        raise ValueError(f"{table_name} must contain game_pk for event partitioning")
    required_game = {"game_pk", "official_date"}
    missing_game = sorted(required_game - set(resolved_games.columns))
    if missing_game:
        raise ValueError(f"resolved game view missing partition columns: {missing_game}")

    date_map = resolved_games.select(["game_pk", "official_date"])
    duplicate_games = date_map.group_by("game_pk").len().filter(pl.col("len") > 1)
    if not duplicate_games.is_empty():
        raise ValueError("resolved game view has duplicate game_pk rows")

    required_games = frame.select("game_pk").unique()
    linked = required_games.join(date_map, on="game_pk", how="left")
    missing_dates = linked.filter(pl.col("official_date").is_null())
    if not missing_dates.is_empty():
        raise ValueError(
            f"{table_name} has {missing_dates.height} games without resolved official_date"
        )

    assignments = linked.with_columns(
        pl.col("official_date").dt.year().alias("partition_year"),
        pl.col("official_date").dt.month().alias("partition_month"),
    )
    artifacts: list[ParquetArtifact] = []
    for partition in (
        assignments.group_by(["partition_year", "partition_month"])
        .agg(pl.col("game_pk").sort().alias("game_ids"))
        .sort(["partition_year", "partition_month"])
        .to_dicts()
    ):
        year = int(partition["partition_year"])
        month = int(partition["partition_month"])
        game_ids = [int(value) for value in partition["game_ids"]]
        partition_frame = frame.filter(pl.col("game_pk").is_in(game_ids))
        path = (
            root
            / f"year={year:04d}"
            / f"month={month:02d}"
            / "part-00000.parquet"
        )
        artifacts.append(
            write_canonical_parquet(
                partition_frame,
                path,
                table_name=table_name,
            )
        )
    return artifacts
