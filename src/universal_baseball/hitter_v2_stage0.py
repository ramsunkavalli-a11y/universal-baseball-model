"""Outcome-blind Stage 0 audit helpers for the Hitter v2 rebuild.

This module deliberately contains no Hitter v2 candidate model.  It reproduces
the frozen v1 batting-rate surface and evaluates that historical surface against
already-accessed 2024 official MLB outcomes.  The fixed season guard is a
scientific boundary: Stage 0 cannot fetch or score 2025+ offense.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import polars as pl

from universal_baseball.player_value_batting_runs import (
    build_v1_mlb_batting_reference,
    calculate_v1_projected_batting_runs,
)


STAGE0_ALLOWED_OFFICIAL_SEASONS = (2021, 2022, 2023, 2024)
MAR_CEL_RECENCY_WEIGHTS = {2021: 3.0, 2022: 4.0, 2023: 5.0}
MAR_CEL_PRIOR_PA = 1200.0
V1_RATE_BASIS_PA = 600.0


@dataclass(frozen=True, slots=True)
class WobaWeights:
    ubb: float
    hbp: float
    single: float
    double: float
    triple: float
    home_run: float
    scale: float


FANGRAPHS_2024_WOBA = WobaWeights(
    ubb=0.689,
    hbp=0.720,
    single=0.882,
    double=1.254,
    triple=1.590,
    home_run=2.050,
    scale=1.242,
)


OFFICIAL_OUTCOME_COLUMNS = (
    "season",
    "player_id",
    "player_name",
    "pa",
    "ab",
    "h",
    "double",
    "triple",
    "hr",
    "bb",
    "ibb",
    "hbp",
    "k",
    "sf",
    "sh",
)


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_stage0_seasons(seasons: Iterable[int]) -> tuple[int, ...]:
    normalized = tuple(sorted(set(int(season) for season in seasons)))
    if normalized != STAGE0_ALLOWED_OFFICIAL_SEASONS:
        raise ValueError(
            "Stage 0 official-outcome access is fixed to 2021-2024; "
            f"received {normalized}"
        )
    return normalized


def build_frozen_v1_batting_leaderboard(
    *,
    b2_profile_path: Path,
    performance_root: Path,
) -> pl.DataFrame:
    """Reproduce the v1 pure-batting rate surface from immutable artifacts."""

    reference = build_v1_mlb_batting_reference(
        pl.read_parquet(
            performance_root / "tables/batting_performance_summary_2024_mlb.parquet"
        ),
        pl.read_parquet(
            performance_root / "tables/batting_performance_bins_2024_mlb.parquet"
        ),
        pl.read_parquet(performance_root / "tables/league_bin_values_2024_mlb.parquet"),
        season=2024,
    )
    profile = pl.read_parquet(b2_profile_path)
    required = {"player_id", "core_bin", "baseline2_latent_probability"}
    missing = sorted(required - set(profile.columns))
    if missing:
        raise ValueError(f"frozen B2 profile missing required columns: {missing}")

    rows: list[dict[str, float | int]] = []
    for player_key, group in profile.group_by("player_id"):
        player_id = int(player_key[0])
        probabilities = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in group.iter_rows(named=True)
        }
        projection = calculate_v1_projected_batting_runs(
            probabilities,
            projected_expected_mlb_pa=V1_RATE_BASIS_PA,
            reference=reference,
        )
        rows.append(
            {
                "player_id": player_id,
                "v1_batting_runs_per_600_pa": (
                    projection.projected_batting_runs_above_mlb_reference
                ),
                "projected_core_run_value_per_event": (
                    projection.projected_core_run_value_per_event
                ),
            }
        )
    return (
        pl.DataFrame(rows)
        .sort(
            ["v1_batting_runs_per_600_pa", "player_id"],
            descending=[True, False],
        )
        .with_row_index("v1_rank", offset=1)
    )


def validate_official_outcomes(frame: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(set(OFFICIAL_OUTCOME_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"official outcome table missing columns: {missing}")
    result = frame.select(OFFICIAL_OUTCOME_COLUMNS).sort(["season", "player_id"])
    if result.is_empty():
        raise ValueError("official outcome table is empty")
    if result.get_column("season").max() > 2024:
        raise ValueError("Stage 0 cannot inspect post-2024 official outcomes")
    duplicates = result.group_by(["season", "player_id"]).len().filter(
        pl.col("len") > 1
    )
    if not duplicates.is_empty():
        raise ValueError("official outcome table violates player-season grain")
    count_columns = [
        column
        for column in OFFICIAL_OUTCOME_COLUMNS
        if column not in {"season", "player_id", "player_name"}
    ]
    if result.select(pl.any_horizontal(pl.col(count_columns) < 0)).item():
        raise ValueError("official outcome table contains a negative count")
    invalid = result.filter(
        (pl.col("ibb") > pl.col("bb"))
        | (pl.col("double") + pl.col("triple") + pl.col("hr") > pl.col("h"))
    )
    if not invalid.is_empty():
        raise ValueError("official outcome table contains impossible component counts")
    return result


def add_2024_weight_woba(
    frame: pl.DataFrame,
    *,
    weights: WobaWeights = FANGRAPHS_2024_WOBA,
) -> pl.DataFrame:
    single = pl.col("h") - pl.col("double") - pl.col("triple") - pl.col("hr")
    ubb = pl.col("bb") - pl.col("ibb")
    denominator = pl.col("ab") + ubb + pl.col("hbp") + pl.col("sf")
    numerator = (
        weights.ubb * ubb
        + weights.hbp * pl.col("hbp")
        + weights.single * single
        + weights.double * pl.col("double")
        + weights.triple * pl.col("triple")
        + weights.home_run * pl.col("hr")
    )
    return frame.with_columns(
        single.alias("single"),
        ubb.alias("ubb"),
        denominator.cast(pl.Float64).alias("woba_denominator"),
        numerator.cast(pl.Float64).alias("woba_numerator"),
    ).with_columns(
        pl.when(pl.col("woba_denominator") > 0)
        .then(pl.col("woba_numerator") / pl.col("woba_denominator"))
        .otherwise(None)
        .alias("woba_2024_weights"),
        pl.when(pl.col("pa") > 0)
        .then(pl.col("hr") / pl.col("pa"))
        .otherwise(None)
        .alias("hr_per_pa"),
        pl.when(pl.col("pa") > 0)
        .then(pl.col("k") / pl.col("pa"))
        .otherwise(None)
        .alias("k_per_pa"),
    )


def _pearson(left: Iterable[float], right: Iterable[float]) -> float:
    x = np.asarray(list(left), dtype=float)
    y = np.asarray(list(right), dtype=float)
    if x.size != y.size or x.size < 2:
        raise ValueError("correlation requires equal vectors with at least two rows")
    return float(np.corrcoef(x, y)[0, 1])


def _average_ranks(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(array.size, dtype=float)
    start = 0
    while start < array.size:
        end = start + 1
        while end < array.size and array[order[end]] == array[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    return ranks


def _spearman(left: Iterable[float], right: Iterable[float]) -> float:
    return _pearson(_average_ranks(left), _average_ranks(right))


def _correlations(frame: pl.DataFrame, predictor: str, target: str) -> dict[str, float]:
    return {
        "pearson": _pearson(frame.get_column(predictor), frame.get_column(target)),
        "spearman": _spearman(frame.get_column(predictor), frame.get_column(target)),
    }


def _marcel_projection(prior: pl.DataFrame) -> dict[int, float]:
    weighted_numerator = 0.0
    weighted_denominator = 0.0
    players: dict[int, list[float]] = {}
    for row in prior.iter_rows(named=True):
        weight = MAR_CEL_RECENCY_WEIGHTS[int(row["season"])]
        numerator = weight * float(row["woba_numerator"])
        denominator = weight * float(row["woba_denominator"])
        weighted_numerator += numerator
        weighted_denominator += denominator
        player = players.setdefault(int(row["player_id"]), [0.0, 0.0])
        player[0] += numerator
        player[1] += denominator
    league_woba = weighted_numerator / weighted_denominator
    return {
        player_id: (numerator + MAR_CEL_PRIOR_PA * league_woba)
        / (denominator + MAR_CEL_PRIOR_PA)
        for player_id, (numerator, denominator) in players.items()
    }


def compute_v1_external_validity(
    *,
    leaderboard: pl.DataFrame,
    official_outcomes: pl.DataFrame,
) -> dict[str, object]:
    """Verify the disclosed v1 construct-validity diagnostics on 2024 only."""

    official = add_2024_weight_woba(validate_official_outcomes(official_outcomes))
    target = official.filter((pl.col("season") == 2024) & (pl.col("pa") >= 200))
    cohort = leaderboard.join(target, on="player_id", how="inner")
    if cohort.is_empty():
        raise ValueError("2024 external-validity cohort is empty")

    model_woba = _correlations(cohort, "v1_batting_runs_per_600_pa", "woba_2024_weights")
    model_hr = _correlations(cohort, "v1_batting_runs_per_600_pa", "hr_per_pa")
    model_k = _correlations(cohort, "v1_batting_runs_per_600_pa", "k_per_pa")
    model_top = set(
        cohort.sort("v1_batting_runs_per_600_pa", descending=True)
        .head(20)
        .get_column("player_id")
        .to_list()
    )
    actual_top = set(
        cohort.sort("woba_2024_weights", descending=True)
        .head(20)
        .get_column("player_id")
        .to_list()
    )

    prior = official.filter(pl.col("season").is_in(list(MAR_CEL_RECENCY_WEIGHTS)))
    marcel = _marcel_projection(prior)
    raw_2023 = {
        int(row["player_id"]): float(row["woba_2024_weights"])
        for row in prior.filter(pl.col("season") == 2023).iter_rows(named=True)
        if row["woba_2024_weights"] is not None
    }
    history_ids = set(marcel) & set(raw_2023)
    history = cohort.filter(pl.col("player_id").is_in(sorted(history_ids))).with_columns(
        pl.col("player_id")
        .map_elements(lambda value: marcel[int(value)], return_dtype=pl.Float64)
        .alias("marcel_woba"),
        pl.col("player_id")
        .map_elements(lambda value: raw_2023[int(value)], return_dtype=pl.Float64)
        .alias("raw_2023_woba"),
    )

    diagnostic_columns = [
        "player_id",
        "player_name",
        "v1_rank",
        "v1_batting_runs_per_600_pa",
        "pa",
        "woba_2024_weights",
        "hr_per_pa",
        "k_per_pa",
    ]
    named_diagnostics = (
        cohort.sort("woba_2024_weights", descending=True)
        .head(20)
        .select(diagnostic_columns)
        .to_dicts()
    )
    return {
        "woba_definition": {
            "season": 2024,
            "weights": asdict(FANGRAPHS_2024_WOBA),
            "denominator": "AB + BB - IBB + HBP + SF",
        },
        "cohort": {
            "rule": "official 2024 MLB PA >= 200 and frozen v1 B2 profile present",
            "player_count": cohort.height,
        },
        "v1_batting_score": {
            "correlation_with_actual_woba": model_woba,
            "correlation_with_actual_hr_per_pa": model_hr,
            "correlation_with_actual_k_per_pa": model_k,
            "top_20_overlap_with_actual_woba_top_20": len(model_top & actual_top),
        },
        "prior_mlb_history_comparison": {
            "rule": "same cohort with 2021-2023 MLB history and a 2023 MLB row",
            "player_count": history.height,
            "v1_batting_score": _correlations(
                history, "v1_batting_runs_per_600_pa", "woba_2024_weights"
            ),
            "raw_2023_woba": _correlations(
                history, "raw_2023_woba", "woba_2024_weights"
            ),
            "marcel_style_woba": _correlations(
                history, "marcel_woba", "woba_2024_weights"
            ),
            "marcel_contract": {
                "season_weights": MAR_CEL_RECENCY_WEIGHTS,
                "regression_prior_pa": MAR_CEL_PRIOR_PA,
                "prior_mean": "weighted 2021-2023 MLB wOBA using 2024 weights",
            },
        },
        "named_diagnostics_only_not_acceptance_criteria": named_diagnostics,
    }


def summarize_leaderboard(leaderboard: pl.DataFrame) -> Mapping[str, object]:
    return {
        "player_count": leaderboard.height,
        "rate_basis_pa": int(V1_RATE_BASIS_PA),
        "ranking_metric": "v1_batting_runs_per_600_pa",
        "top_20": leaderboard.head(20).to_dicts(),
    }
