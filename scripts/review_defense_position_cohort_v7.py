"""Distinguish matched forecast totals from full MLB positional totals."""

import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file
from prepare_defense_position_opportunity_v7 import OUT, POSITIONS, read, receipt
from run_hitter_finite_return_baseline import protections


def main():
    protections()
    assert not (OUT / "cohort-coverage-review.json").exists()
    verification = read(OUT / "independent-source-verification.json")
    assert verification["source_preparation_complete"]
    for p, h in verification["hashes"].items():
        assert sha256_file(Path(p)) == h
    contexts = pl.read_parquet(OUT / "origin-context.parquet")
    labels = pl.read_parquet(OUT / "exposure-labels.parquet")
    source = pl.read_parquet(OUT / "source.parquet")
    rows = []
    for y in sorted(contexts["origin_year"].unique()):
        q = contexts.filter(pl.col("origin_year") == y).join(labels, on="row_id", validate="1:1")
        full = source.filter((pl.col("season") == y + 1) & pl.col("is_mlb") &
                             pl.col("position_code").is_in([str(p) for p in POSITIONS]))
        missing = full.filter(~pl.col("player_id").is_in(q["player_id"].implode()))
        absent = missing.group_by("player_id", "player_name").agg(pl.col("fielding_outs").sum()).filter(
                    pl.col("fielding_outs") > 0).sort(["fielding_outs", "player_id"], descending=[True, False])
        assert q["actual_defensive_outs"].sum() + missing["fielding_outs"].sum() == full["fielding_outs"].sum()
        rows.append(dict(origin=y, target_year=y + 1, forecast_people=q.height,
            fixed_forecast_PA=float(q["preseason_pa"].sum()), matched_actual_PA=int(q["next_pa"].sum()),
            matched_defensive_outs=int(q["actual_defensive_outs"].sum()),
            all_MLB_defensive_outs=int(full["fielding_outs"].sum()),
            matched_outs_fraction=float(q["actual_defensive_outs"].sum() / full["fielding_outs"].sum()),
            unrepresented_actual_defenders=absent.to_dicts(),
            zero_PA_positive_defense_rows=q.filter((pl.col("next_pa") == 0) & (pl.col("actual_defensive_outs") > 0)).select(
                "row_id", "player_id", "player_name", "actual_defensive_outs").to_dicts(),
            past_stage_support=context_stage_counts(q)))
    receipt("cohort-coverage-review.json", dict(origins=rows, opportunity_fits_run=0,
        all_MLB_totals_reconciled=True, full_MLB_population_claim=False,
        source_walkthrough_status="complete", protected_outcomes_used=False, forecast_or_explorer_changed=False,
        next_comparison_boundary="Use identical fixed forecast membership and report the remainder. Do not insert missing players with invented PA, normalize away their omission, or claim that matching these forecasts proves whole-MLB coverage.",
        hashes={str(p): sha256_file(p) for p in [Path(__file__), OUT / "independent-source-verification.json", OUT / "origin-context.parquet", OUT / "exposure-labels.parquet", OUT / "source.parquet"]}))
    protections()
    print(json.dumps([dict(origin=r["origin"], matched_fraction=r["matched_outs_fraction"],
                          omitted=len(r["unrepresented_actual_defenders"])) for r in rows]))


def context_stage_counts(q):
    return q.group_by("stage").agg(pl.len().alias("forecasts"),
        (pl.col("next_pa") > 0).sum().alias("actual_MLB_batters"),
        pl.col("actual_defensive_outs").sum(), pl.col("preseason_pa").sum()).sort("stage").to_dicts()


if __name__ == "__main__":
    main()
