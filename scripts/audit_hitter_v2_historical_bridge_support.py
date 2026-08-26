"""Measure historical same-player support without fitting or scoring a model."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_historical_bridge import (
    canonicalize_stints,
    matched_pair,
    player_seasons,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ROOT = Path(__file__).resolve().parents[1]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--milb-2019",
        type=Path,
        default=ROOT / "reports/generated/hitter-v2-historical-materialization/milb/tables/hitter_v2_player_season_outcomes_2019_milb.parquet",
    )
    parser.add_argument(
        "--mlb-2019",
        type=Path,
        default=ROOT / "reports/generated/hitter-v2-historical-materialization/mlb/2019/tables/current_talent_game_summary_2019_mlb.parquet",
    )
    parser.add_argument(
        "--mlb-2020",
        type=Path,
        default=ROOT / "reports/generated/hitter-v2-historical-materialization/mlb/2020/tables/current_talent_game_summary_2020_mlb.parquet",
    )
    parser.add_argument(
        "--universal-2021",
        type=Path,
        default=ROOT / "reports/generated/hitter-v2-stage1-universal/tables/hitter_v2_player_season_outcomes_2021_2023.parquet",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=ROOT / "reports/generated/hitter-v2-historical-bridge-support",
    )
    return parser.parse_args()


def _season_source(path: Path, season: int, source: str, mlb: bool) -> pl.DataFrame:
    frame = pl.read_parquet(path)
    level_aliases = {
        "rk": "ROOKIE_COMPLEX",
        "a": "SINGLE_A",
        "a+": "HIGH_A",
        "aa": "AA",
        "aaa": "AAA",
        "MLB": "MLB",
    }
    if mlb:
        frame = frame.filter(pl.col("season") == season).select(
            pl.col("season").cast(pl.Int32),
            pl.col("player_id").cast(pl.Int64),
            "level_group",
            pl.col("batting_plate_appearances").cast(pl.Int64).alias("pa"),
            pl.lit(source).alias("source"),
        )
    else:
        frame = frame.filter(
            (pl.col("season") == season) & pl.col("modeling_eligible")
        ).select(
            pl.col("season").cast(pl.Int32),
            pl.col("player_id").cast(pl.Int64),
            "level_group",
            pl.col("accepted_terminal_pa").cast(pl.Int64).alias("pa"),
            pl.lit(source).alias("source"),
        )
    return frame.with_columns(
        pl.col("level_group").replace(level_aliases).alias("level_group")
    )


def _count_by_level(stints: pl.DataFrame, season: int) -> dict[str, int]:
    return {
        row["level_group"]: row["players"]
        for row in (
            stints.filter(pl.col("season") == season)
            .group_by("level_group")
            .agg(pl.col("player_id").n_unique().alias("players"))
            .sort("level_group")
            .to_dicts()
        )
    }


def main() -> None:
    args = _args()
    source_paths = {
        "milb_2019": args.milb_2019,
        "mlb_2019": args.mlb_2019,
        "mlb_2020": args.mlb_2020,
        "universal_2021": args.universal_2021,
    }
    missing = [str(path) for path in source_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing bridge sources: {missing}")

    stints = canonicalize_stints(
        pl.concat(
            [
                _season_source(args.milb_2019, 2019, "MILB_2019", False),
                _season_source(args.mlb_2019, 2019, "MLB_2019", True),
                _season_source(args.mlb_2020, 2020, "MLB_2020", True),
                _season_source(args.universal_2021, 2021, "UNIVERSAL_2021", False),
            ]
        )
    )
    seasons = player_seasons(stints)
    comparisons = [
        (2019, 2020, "2019_TO_2020"),
        (2020, 2021, "2020_TO_2021"),
        (2019, 2021, "2019_TO_2021_TWO_YEAR"),
    ]
    pairs = pl.concat(
        [
            matched_pair(
                seasons,
                origin_season=origin,
                destination_season=destination,
                comparison=label,
            )
            for origin, destination, label in comparisons
        ]
    )
    summary_rows = []
    for origin, destination, label in comparisons:
        pair = pairs.filter(pl.col("comparison") == label)
        origin_players = seasons.filter(pl.col("season") == origin).height
        destination_players = seasons.filter(pl.col("season") == destination).height
        summary_rows.append(
            {
                "comparison": label,
                "origin_season": origin,
                "destination_season": destination,
                "origin_players": origin_players,
                "destination_players": destination_players,
                "matched_players": pair.height,
                "origin_player_match_rate": pair.height / origin_players,
                "matched_origin_pa": pair.get_column("origin_pa").sum(),
                "matched_destination_pa": pair.get_column("destination_pa").sum(),
            }
        )
    pair_summary = pl.DataFrame(summary_rows)
    transition_matrix = (
        pairs.group_by(
            "comparison", "origin_level", "destination_level", "transition"
        )
        .len(name="matched_players")
        .sort("comparison", "origin_level", "destination_level", "transition")
    )
    evidence_bands = (
        pairs.group_by("comparison", "origin_evidence_band")
        .len(name="matched_players")
        .sort("comparison", "origin_evidence_band")
    )

    milb_2019_ids = set(
        stints.filter(pl.col("source") == "MILB_2019")["player_id"].unique()
    )
    mlb_2020_ids = set(
        stints.filter(pl.col("source") == "MLB_2020")["player_id"].unique()
    )
    mlb_2021_ids = set(
        stints.filter(
            (pl.col("season") == 2021) & (pl.col("level_group") == "MLB")
        )["player_id"].unique()
    )
    all_three = set(seasons.filter(pl.col("season") == 2019)["player_id"])
    all_three &= set(seasons.filter(pl.col("season") == 2020)["player_id"])
    all_three &= set(seasons.filter(pl.col("season") == 2021)["player_id"])

    tables = args.report_root / "tables"
    storage = {
        "canonical_stints": write_canonical_parquet(
            stints, tables / "canonical_stints.parquet", table_name="hitter_v2_historical_bridge_stints"
        ).as_record(),
        "player_seasons": write_canonical_parquet(
            seasons, tables / "player_seasons.parquet", table_name="hitter_v2_historical_bridge_player_seasons"
        ).as_record(),
        "matched_pairs": write_canonical_parquet(
            pairs, tables / "matched_pairs.parquet", table_name="hitter_v2_historical_bridge_pairs"
        ).as_record(),
        "pair_summary": write_canonical_parquet(
            pair_summary, tables / "pair_summary.parquet", table_name="hitter_v2_historical_bridge_pair_summary"
        ).as_record(),
        "transition_matrix": write_canonical_parquet(
            transition_matrix, tables / "transition_matrix.parquet", table_name="hitter_v2_historical_bridge_transition_matrix"
        ).as_record(),
        "evidence_bands": write_canonical_parquet(
            evidence_bands, tables / "evidence_bands.parquet", table_name="hitter_v2_historical_bridge_evidence_bands"
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "generated_date": date.today().isoformat(),
        "accepted": True,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "historical_model_use_authorized": False,
        "identity": "integer_player_id_only_no_names",
        "gap_policy": "2020_milb_missing_not_zero_two_year_pair_excluded_from_adjacent_fitter",
        "sources": {
            key: {"path": str(path), "sha256": sha256_file(path)}
            for key, path in source_paths.items()
        },
        "season_players": {
            str(season): seasons.filter(pl.col("season") == season).height
            for season in (2019, 2020, 2021)
        },
        "players_by_level": {
            str(season): _count_by_level(stints, season)
            for season in (2019, 2020, 2021)
        },
        "comparisons": pair_summary.to_dicts(),
        "transition_counts": (
            pairs.group_by("comparison", "transition")
            .len(name="matched_players")
            .sort("comparison", "transition")
            .to_dicts()
        ),
        "specific_support": {
            "2019_milb_players": len(milb_2019_ids),
            "2019_milb_reaching_2020_mlb": len(milb_2019_ids & mlb_2020_ids),
            "2019_milb_reaching_2021_mlb": len(milb_2019_ids & mlb_2021_ids),
            "players_present_2019_2020_2021": len(all_three),
        },
        "storage": storage,
        "interpretation": "Support and movement counts only; presence does not establish predictive value or authorize model integration.",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
