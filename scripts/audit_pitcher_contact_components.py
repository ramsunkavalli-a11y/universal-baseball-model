#!/usr/bin/env python3
"""Test a heavily regressed eight-outcome affiliated pitcher profile."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)
from universal_baseball.opportunity_history_source import SPORT_LEVEL


FIVE = ("so", "ubb", "hbp", "hr", "other")
EIGHT = ("so", "ubb", "hbp", "single", "double", "triple", "hr", "other")
CANDIDATES = (800.0, 1600.0, 2400.0, 4000.0)
CAPTURES = Path("reports/generated/affiliated-skill-source/captures")
OUTPUT = Path("docs/pitcher-contact-components-result.json")


def _count(stat: dict[str, object], key: str) -> int:
    value = float(str(stat[key]))
    if not value.is_integer() or value < 0:
        raise ValueError(f"invalid official pitching count: {key}={value}")
    return int(value)


def _load_source() -> pl.DataFrame:
    rows = []
    for season in (2023, 2024, 2025):
        paths = sorted((CAPTURES / str(season)).glob("pitching-*.json.gz"))
        if not paths:
            raise FileNotFoundError(f"missing saved pitching captures for {season}")
        for path in paths:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
            for split in payload["stats"][0]["splits"]:
                stat = split["stat"]
                sport_id = int(split["sport"]["id"])
                hits = _count(stat, "hits")
                doubles = _count(stat, "doubles")
                triples = _count(stat, "triples")
                home_runs = _count(stat, "homeRuns")
                single = hits - doubles - triples - home_runs
                bf = _count(stat, "battersFaced")
                so = _count(stat, "strikeOuts")
                ubb = _count(stat, "baseOnBalls") - _count(
                    stat, "intentionalWalks"
                )
                hbp = _count(stat, "hitBatsmen")
                other = bf - so - ubb - hbp - single - doubles - triples - home_runs
                if single < 0 or ubb < 0 or other < 0:
                    raise ValueError(f"pitching contact accounting failed in {path}")
                rows.append(
                    {
                        "season": season,
                        "player_id": int(split["player"]["id"]),
                        "sport_id": sport_id,
                        "level_group": SPORT_LEVEL[sport_id],
                        "batters_faced": bf,
                        "so": so,
                        "ubb": ubb,
                        "hbp": hbp,
                        "single": single,
                        "double": doubles,
                        "triple": triples,
                        "hr": home_runs,
                        "other": other,
                    }
                )
    result = pl.DataFrame(rows).sort("season", "player_id", "sport_id")
    if result.filter(pl.sum_horizontal(*EIGHT) != pl.col("batters_faced")).height:
        raise ValueError("eight pitching outcomes do not reconcile to BF")
    return result


def _population(
    source: pl.DataFrame, cutoff: int
) -> tuple[pl.DataFrame, pl.DataFrame]:
    evidence = source.filter(pl.col("season") <= cutoff)
    exposure = evidence.group_by("player_id").agg(
        pl.col("batters_faced").sum().alias("all_bf"),
        pl.col("batters_faced")
        .filter(pl.col("level_group") == "MLB")
        .sum()
        .alias("mlb_bf"),
    )
    players = exposure.filter(
        (pl.col("all_bf") > 0) & (pl.col("mlb_bf") == 0)
    ).select("player_id")
    return players, evidence


def _profiles(
    source: pl.DataFrame,
    *,
    target_season: int,
    components: tuple[str, ...],
    regression_bf: float,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    model_source = source
    if components == FIVE:
        model_source = source.with_columns(
            (
                pl.col("batters_faced")
                - pl.sum_horizontal("so", "ubb", "hbp", "hr")
            ).alias("other")
        )
    cutoff = target_season - 1
    players, evidence = _population(model_source, cutoff)
    fit = fit_same_season_component_translation(
        model_source,
        exposure_column="batters_faced",
        component_columns=components,
        completed_seasons=tuple(
            int(value)
            for value in evidence.get_column("season").unique().sort().to_list()
        ),
        minimum_level_exposure=30,
    )
    predictions = build_translated_affiliated_profiles(
        players,
        evidence,
        fit.offsets,
        exposure_column="batters_faced",
        component_columns=components,
        current_season=cutoff,
        reference_season=cutoff,
        regression_exposure=regression_bf,
    )
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    reference = source.filter(
        (pl.col("season") == cutoff) & (pl.col("level_group") == "MLB")
    )
    return predictions, target, reference


def _expand_incumbent(
    five: pl.DataFrame, reference: pl.DataFrame
) -> pl.DataFrame:
    totals = {
        component: float(reference.get_column(component).sum())
        for component in EIGHT
    }
    broad_other = sum(totals[value] for value in ("single", "double", "triple", "other"))
    shares = {
        value: totals[value] / broad_other
        for value in ("single", "double", "triple", "other")
    }
    return five.with_columns(
        *((pl.col("p_other") * shares[value]).alias(f"p_{value}") for value in shares)
    ).select("player_id", *(f"p_{value}" for value in EIGHT))


def _score_rows(
    predictions: pl.DataFrame, target: pl.DataFrame
) -> pl.DataFrame:
    actual = target.group_by("player_id").agg(
        pl.col("batters_faced").sum(),
        *(pl.col(component).sum() for component in EIGHT),
    ).filter(pl.col("batters_faced") > 0)
    return actual.join(predictions, on="player_id", how="inner", validate="1:1").sort(
        "player_id"
    ).with_columns(
        pl.sum_horizontal(
            *(
                -pl.col(component) * pl.col(f"p_{component}").log()
                for component in EIGHT
            )
        ).alias("log_loss_total"),
        (
            pl.col("batters_faced")
            * (
                1.0
                + pl.sum_horizontal(
                    *(pl.col(f"p_{component}") ** 2 for component in EIGHT)
                )
            )
            - 2.0
            * pl.sum_horizontal(
                *(
                    pl.col(component) * pl.col(f"p_{component}")
                    for component in EIGHT
                )
            )
        ).alias("brier_total"),
    )


def _bootstrap(candidate: pl.DataFrame, incumbent: pl.DataFrame) -> dict[str, object]:
    joined = candidate.select(
        "player_id", "batters_faced", "log_loss_total", "brier_total"
    ).join(
        incumbent.select(
            "player_id",
            pl.col("log_loss_total").alias("incumbent_ll"),
            pl.col("brier_total").alias("incumbent_brier"),
        ),
        on="player_id",
        validate="1:1",
    ).select(
        "batters_faced",
        (pl.col("log_loss_total") - pl.col("incumbent_ll")).alias("ll_delta"),
        (pl.col("brier_total") - pl.col("incumbent_brier")).alias("brier_delta"),
    ).to_numpy()
    rng = np.random.default_rng(20250912)
    draws = np.empty((2000, 2))
    for index in range(len(draws)):
        sample = joined[rng.integers(0, len(joined), len(joined))]
        draws[index] = sample[:, 1:].sum(axis=0) / sample[:, 0].sum()
    return {
        name: {
            "lower_95": float(np.quantile(draws[:, column], 0.025)),
            "median": float(np.quantile(draws[:, column], 0.5)),
            "upper_95": float(np.quantile(draws[:, column], 0.975)),
        }
        for column, name in enumerate(("component_log_loss", "component_brier"))
    }


def _run_rates(
    predictions: pl.DataFrame, target: pl.DataFrame, reference: pl.DataFrame
) -> dict[str, object]:
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"],
        "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": 0.0,
    }
    total = float(reference.get_column("batters_faced").sum())
    reference_woba = sum(
        float(reference.get_column(key).sum()) / total * value
        for key, value in weights.items()
    )
    rows = _score_rows(predictions, target).with_columns(
        (
            -(pl.sum_horizontal(
                *(pl.col(f"p_{key}") * value for key, value in weights.items())
            ) - reference_woba)
            * 800.0 / NEUTRAL_WOBA_SCALE
        ).alias("predicted_raa"),
        (
            -(pl.sum_horizontal(
                *(
                    pl.col(key) / pl.col("batters_faced") * value
                    for key, value in weights.items()
                )
            ) - reference_woba)
            * 800.0 / NEUTRAL_WOBA_SCALE
        ).alias("observed_raa"),
    )
    bf = rows.get_column("batters_faced").to_numpy()
    predicted = rows.get_column("predicted_raa").to_numpy()
    observed = rows.get_column("observed_raa").to_numpy()
    order = np.argsort(predicted, kind="stable")
    return {
        "predicted_player_rate_sd": float(np.std(predicted, ddof=1)),
        "bf_weighted_predicted_mean": float(np.average(predicted, weights=bf)),
        "bf_weighted_observed_mean": float(np.average(observed, weights=bf)),
        "quintiles": [
            {
                "quintile": number,
                "players": int(len(indices)),
                "target_bf": int(bf[indices].sum()),
                "predicted_raa_per_800": float(
                    np.average(predicted[indices], weights=bf[indices])
                ),
                "observed_raa_per_800": float(
                    np.average(observed[indices], weights=bf[indices])
                ),
            }
            for number, indices in enumerate(np.array_split(order, 5), start=1)
        ],
    }


def _fold(
    source: pl.DataFrame,
    target_season: int,
    regressions: tuple[float, ...],
) -> dict[str, object]:
    five, target, reference = _profiles(
        source, target_season=target_season, components=FIVE, regression_bf=800.0
    )
    incumbent = _expand_incumbent(five, reference)
    candidates = {}
    for regression in regressions:
        candidate, candidate_target, candidate_reference = _profiles(
            source,
            target_season=target_season,
            components=EIGHT,
            regression_bf=regression,
        )
        if candidate_target.height != target.height or candidate_reference.height != reference.height:
            raise RuntimeError("contact candidate fold inputs drifted")
        candidates[int(regression)] = candidate
    return {
        "target": target,
        "reference": reference,
        "incumbent": incumbent,
        "candidates": candidates,
        "incumbent_score": score_component_profiles(
            incumbent, target,
            exposure_column="batters_faced", component_columns=EIGHT,
        ),
        "candidate_scores": {
            str(key): score_component_profiles(
                value, target,
                exposure_column="batters_faced", component_columns=EIGHT,
            )
            for key, value in candidates.items()
        },
    }


def main() -> int:
    source = _load_source()
    development = _fold(source, 2024, CANDIDATES)
    incumbent_dev = development["incumbent_score"]
    eligible = [
        regression for regression in CANDIDATES
        if float(development["candidate_scores"][str(int(regression))]["component_brier_score"])
        < float(incumbent_dev["component_brier_score"])
    ]
    selected = min(
        eligible,
        key=lambda value: float(
            development["candidate_scores"][str(int(value))]["component_log_loss"]
        ),
    ) if eligible else None
    confirmation_report = None
    promoted = False
    if selected is not None:
        confirmation = _fold(source, 2025, (selected,))
        candidate = confirmation["candidates"][int(selected)]
        candidate_score = confirmation["candidate_scores"][str(int(selected))]
        incumbent_score = confirmation["incumbent_score"]
        ll_delta = float(candidate_score["component_log_loss"]) - float(
            incumbent_score["component_log_loss"]
        )
        brier_delta = float(candidate_score["component_brier_score"]) - float(
            incumbent_score["component_brier_score"]
        )
        promoted = ll_delta < 0 and brier_delta < 0
        confirmation_report = {
            "incumbent_score": incumbent_score,
            "candidate_score": candidate_score,
            "candidate_minus_incumbent_log_loss": ll_delta,
            "candidate_minus_incumbent_brier": brier_delta,
            "bootstrap_candidate_minus_incumbent": _bootstrap(
                _score_rows(candidate, confirmation["target"]),
                _score_rows(confirmation["incumbent"], confirmation["target"]),
            ),
            "incumbent_run_rate_diagnostic": _run_rates(
                confirmation["incumbent"], confirmation["target"],
                confirmation["reference"],
            ),
            "candidate_run_rate_diagnostic": _run_rates(
                candidate, confirmation["target"], confirmation["reference"]
            ),
        }
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_contact_component_audit_complete",
        "contract": "docs/pitcher-contact-components-plan.md",
        "source_rows": source.height,
        "development_2024": {
            "incumbent_score": incumbent_dev,
            "candidate_scores": development["candidate_scores"],
            "selected_regression_bf": None if selected is None else int(selected),
        },
        "confirmation_2025": confirmation_report,
        "decision": {
            "promoted": promoted,
            "reason": (
                "no_development_candidate_improved_both_scores"
                if selected is None
                else "confirmation_gate_applied"
            ),
        },
        "boundaries": {
            "saved_official_captures_reprojected": True,
            "current_2026_outcomes_used": False,
            "uncertified_pitch_process_used": False,
            "outside_fv_used": False,
            "target_grade_count_used": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "selected_regression_bf": None if selected is None else int(selected),
        "confirmation_scored": confirmation_report is not None,
        "promoted": promoted,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
