"""Coverage and provenance checks for universal projection fallback ladders."""

from __future__ import annotations

import polars as pl


def audit_projection_fallbacks(
    paths: pl.DataFrame, *, component: str
) -> dict[str, object]:
    """Require a complete six-year path and explicit model source for every player."""

    if component not in {"hitter", "pitcher"}:
        raise ValueError("fallback audit component must be hitter or pitcher")
    common = {
        "player_id", "season", "horizon", "coverage_tier",
        "probability_model_id", "workload_model_id", "evidence_tier",
        "talent_model_id", "expected_war",
    }
    component_fields = (
        {"baserunning_evidence_tier", "baserunning_model_id", "defense_evidence_tier", "defense_model_id"}
        if component == "hitter"
        else {"role_model_id", "aging_source"}
    )
    required = common | component_fields
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"{component} fallback path missing fields: {missing}")
    if paths.is_empty():
        raise ValueError(f"{component} fallback path is empty")
    if paths.group_by("player_id", "season").len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{component} fallback path violates player-season grain")
    horizons = sorted(paths.get_column("horizon").unique().to_list())
    if horizons != [1, 2, 3, 4, 5, 6]:
        raise ValueError(f"{component} fallback path does not cover horizons 1-6")
    per_player = paths.group_by("player_id").agg(
        pl.col("horizon").n_unique().alias("horizons"),
        pl.col("season").n_unique().alias("seasons"),
    )
    if per_player.filter((pl.col("horizons") != 6) | (pl.col("seasons") != 6)).height:
        raise ValueError(f"{component} fallback path has incomplete players")
    provenance = sorted(
        field for field in required if field.endswith("_id") or field.endswith("_tier")
    )
    if paths.filter(
        pl.any_horizontal(
            *(pl.col(field).is_null() | (pl.col(field).cast(pl.String) == "") for field in provenance),
            pl.col("expected_war").is_null(),
            ~pl.col("expected_war").is_finite(),
        )
    ).height:
        raise ValueError(f"{component} fallback path has missing provenance or WAR")

    def counts(columns: list[str]) -> list[dict[str, object]]:
        return paths.group_by(columns).len().rename({"len": "rows"}).sort(columns).to_dicts()

    first = paths.filter(pl.col("horizon") == 1)
    report: dict[str, object] = {
        "component": component,
        "players": per_player.height,
        "player_seasons": paths.height,
        "complete_six_year_paths": True,
        "missing_provenance_rows": 0,
        "opportunity_coverage_by_horizon": counts(["horizon", "coverage_tier"]),
        "first_year_skill_evidence": (
            first.group_by("evidence_tier")
            .len()
            .rename({"len": "players"})
            .sort("evidence_tier")
            .to_dicts()
        ),
    }
    if component == "hitter":
        report["first_year_baserunning_evidence"] = (
            first.group_by("baserunning_evidence_tier")
            .len().rename({"len": "players"})
            .sort("baserunning_evidence_tier").to_dicts()
        )
        report["first_year_defense_evidence"] = (
            first.group_by("defense_evidence_tier")
            .len().rename({"len": "players"})
            .sort("defense_evidence_tier").to_dicts()
        )
    else:
        report["first_year_projected_role"] = (
            first.group_by("projected_role")
            .len().rename({"len": "players"})
            .sort("projected_role").to_dicts()
        )
    return report
