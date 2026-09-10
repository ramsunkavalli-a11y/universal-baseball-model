#!/usr/bin/env python3
"""Test age and recent IL recurrence above the validated injury-return cells."""

from __future__ import annotations

from datetime import date, timedelta
import json
import math
from pathlib import Path

import polars as pl

from universal_baseball.injury_return import (
    elapsed_days_band,
    fit_injury_return_references,
    score_injury_return_references,
)


ROOT = Path("reports/generated/injury-return-history")
COHORT = ROOT / "tables/injury-return-cohort.parquet"
PEOPLE = Path("reports/generated/historical-people-control/2025-10-15/tables/people.parquet")
OUTPUT = Path("docs/injury-return-age-recurrence-result.json")
FAMILIES = {
    "age": ("age_band",),
    "recent_recurrence": ("recent_prior_il_band",),
    "age_and_recent_recurrence": ("age_band", "recent_prior_il_band"),
}
PRIOR_GRID = (10.0, 25.0, 50.0, 100.0)


def _age_band(age: float | None) -> str:
    if age is None:
        return "unknown"
    if age < 26:
        return "under_26"
    if age < 31:
        return "26_30"
    if age < 35:
        return "31_34"
    return "35_plus"


def _recurrence_band(count: int) -> str:
    if count == 0:
        return "none"
    if count == 1:
        return "one"
    return "two_plus"


def _placement_history() -> dict[int, list[date]]:
    events: dict[tuple[int, int], date] = {}
    for season in range(2021, 2026):
        payload = json.loads(
            (ROOT / "captures" / f"transactions-{season}.json").read_text(encoding="utf-8")
        )
        for raw in payload.get("transactions", []):
            description = str(raw.get("description") or "").lower()
            person = raw.get("person") or {}
            if " placed " not in f" {description} " or "injured list" not in description:
                continue
            if raw.get("id") is None or person.get("id") is None:
                continue
            transaction_date = str(raw.get("date"))[:10]
            effective_text = str(raw.get("effectiveDate") or transaction_date)[:10]
            if effective_text[:4] != transaction_date[:4]:
                effective_text = transaction_date
            effective = date.fromisoformat(effective_text)
            events[(int(raw["id"]), int(person["id"]))] = effective
    by_player: dict[int, list[date]] = {}
    for (_, player_id), effective in events.items():
        by_player.setdefault(player_id, []).append(effective)
    return {player_id: sorted(values) for player_id, values in by_player.items()}


def _enrich(cohort: pl.DataFrame) -> pl.DataFrame:
    birth_lookup = {
        int(row["player_id"]): row["birth_date"]
        for row in pl.read_parquet(PEOPLE).select("player_id", "birth_date").iter_rows(named=True)
        if row["birth_date"] is not None
    }
    placements = _placement_history()
    rows = []
    for row in cohort.iter_rows(named=True):
        cutoff = row["cutoff_date"]
        il_start = row["il_start_date"]
        player_id = int(row["player_id"])
        assert isinstance(cutoff, date) and isinstance(il_start, date)
        birth = birth_lookup.get(player_id)
        age = (cutoff - birth).days / 365.2425 if isinstance(birth, date) else None
        prior_count = sum(
            cutoff - timedelta(days=365) <= event < il_start
            for event in placements.get(player_id, [])
        )
        rows.append(
            {
                **row,
                "age_years": age,
                "age_band": _age_band(age),
                "recent_prior_il_count": prior_count,
                "recent_prior_il_band": _recurrence_band(prior_count),
                "elapsed_days_band": elapsed_days_band(int(row["days_on_il_at_cutoff"])),
            }
        )
    return pl.DataFrame(rows)


def _metrics(scored: pl.DataFrame, *, prefix: str) -> dict[str, float | int]:
    probability = scored.get_column(f"{prefix}_return_probability").clip(1e-12, 1 - 1e-12)
    outcome = scored.get_column("returned_by_season_end").cast(pl.Float64)
    predicted = scored.get_column(f"{prefix}_availability")
    actual = scored.get_column("remaining_season_availability_fraction")
    error = predicted - actual
    return {
        "players": scored.height,
        "brier": float(((probability - outcome) ** 2).mean()),
        "log_loss": float(
            (-(outcome * probability.log() + (1 - outcome) * (1 - probability).log())).mean()
        ),
        "availability_mae": float(error.abs().mean()),
        "availability_rmse": math.sqrt(float((error**2).mean())),
    }


def _score_candidate(
    train: pl.DataFrame,
    validation: pl.DataFrame,
    *,
    family: str,
    prior_players: float,
) -> dict[str, object]:
    feature_columns = FAMILIES[family]
    base_fit = fit_injury_return_references(train, prior_players=25.0)
    train_scored, _ = score_injury_return_references(train, base_fit)
    validation_scored, _ = score_injury_return_references(validation, base_fit)
    validation_scored = validation_scored.join(
        validation.select(
            "player_id", "season", "elapsed_days_band", *feature_columns
        ),
        on=["player_id", "season"],
        how="inner",
        validate="1:1",
    )
    base_train = train_scored.select(
        "player_id",
        "season",
        "predicted_return_probability",
        "predicted_remaining_availability_fraction",
    )
    training = train.join(base_train, on=["player_id", "season"], how="inner", validate="1:1")
    cell_columns = ["injury_list_type", "elapsed_days_band", *feature_columns]
    cells = training.group_by(cell_columns).agg(
        pl.len().alias("cell_n"),
        pl.col("returned_by_season_end").sum().cast(pl.Float64).alias("return_sum"),
        pl.col("remaining_season_availability_fraction").sum().alias("availability_sum"),
        pl.col("predicted_return_probability").first().alias("parent_return_probability"),
        pl.col("predicted_remaining_availability_fraction").first().alias(
            "parent_availability"
        ),
    ).with_columns(
        (
            (pl.col("return_sum") + prior_players * pl.col("parent_return_probability"))
            / (pl.col("cell_n") + prior_players)
        ).alias("candidate_return_probability"),
        (
            (pl.col("availability_sum") + prior_players * pl.col("parent_availability"))
            / (pl.col("cell_n") + prior_players)
        ).alias("candidate_availability"),
    )
    scored = validation_scored.join(
        cells.select(*cell_columns, "candidate_return_probability", "candidate_availability"),
        on=cell_columns,
        how="left",
        validate="m:1",
    ).with_columns(
        pl.col("candidate_return_probability")
        .fill_null(pl.col("predicted_return_probability"))
        .alias("candidate_return_probability"),
        pl.col("candidate_availability")
        .fill_null(pl.col("predicted_remaining_availability_fraction"))
        .alias("candidate_availability"),
        pl.col("predicted_return_probability").alias("base_return_probability"),
        pl.col("predicted_remaining_availability_fraction").alias("base_availability"),
    )
    candidate = _metrics(scored, prefix="candidate")
    base = _metrics(scored, prefix="base")
    deltas = {
        key: float(candidate[key]) - float(base[key])
        for key in ("brier", "log_loss", "availability_mae", "availability_rmse")
    }
    return {
        "family": family,
        "prior_players": prior_players,
        "training_players": train.height,
        "validation_players": validation.height,
        "detailed_cells": cells.height,
        "candidate": candidate,
        "base_il_type_elapsed": base,
        "candidate_minus_base": deltas,
    }


def _passes(row: dict[str, object]) -> bool:
    return all(float(value) < 0 for value in row["candidate_minus_base"].values())


def main() -> int:
    all_cohort = _enrich(pl.read_parquet(COHORT)).filter(pl.col("season") >= 2022)
    age_coverage_players = int(all_cohort.get_column("age_years").is_not_null().sum())
    cohort = all_cohort.filter(pl.col("age_years").is_not_null())
    development_train = cohort.filter(pl.col("season").is_between(2022, 2023))
    development_target = cohort.filter(pl.col("season") == 2024)
    grid = [
        _score_candidate(
            development_train,
            development_target,
            family=family,
            prior_players=prior,
        )
        for family in FAMILIES
        for prior in PRIOR_GRID
    ]
    eligible = [row for row in grid if _passes(row)]
    selected = min(
        eligible,
        key=lambda row: float(row["candidate_minus_base"]["log_loss"]),
    ) if eligible else None
    confirmation = None
    if selected is not None:
        confirmation = _score_candidate(
            cohort.filter(pl.col("season").is_between(2022, 2024)),
            cohort.filter(pl.col("season") == 2025),
            family=str(selected["family"]),
            prior_players=float(selected["prior_players"]),
        )
    report = {
        "report_schema_version": "0.1",
        "gate": "injury_return_age_recent_recurrence",
        "development_train_seasons": [2022, 2023],
        "development_target": 2024,
        "confirmation_target": 2025,
        "families": {key: list(value) for key, value in FAMILIES.items()},
        "prior_grid": list(PRIOR_GRID),
        "grid": grid,
        "selected_development": selected,
        "confirmation": confirmation,
        "promotion_gate_passed": confirmation is not None and _passes(confirmation),
        "age_coverage_players": age_coverage_players,
        "total_players": all_cohort.height,
        "common_cohort_players": cohort.height,
        "common_cohort_rule": "known stable birth date for all tested families",
        "recurrence_definition": "prior IL placements in [cutoff-365 days, current IL start)",
        "production_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "age_coverage": f"{report['age_coverage_players']}/{report['total_players']}",
                "selected": None
                if selected is None
                else {
                    "family": selected["family"],
                    "prior_players": selected["prior_players"],
                    "development_deltas": selected["candidate_minus_base"],
                },
                "confirmation_deltas": None
                if confirmation is None
                else confirmation["candidate_minus_base"],
                "passed": report["promotion_gate_passed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
