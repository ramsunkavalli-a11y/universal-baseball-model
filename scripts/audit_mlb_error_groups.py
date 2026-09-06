"""Post-C2026C diagnosis by known age/evidence and observed exposure; no fitting."""

from pathlib import Path
import json
import polars as pl
from diagnose_hitter_transport import load_fold, metrics, OUTCOMES

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/generated"
PROBS = [f"p_{o}" for o in OUTCOMES]


def main():
    result = {
        "status": "post_result_diagnostic_only",
        "future_PA_is_diagnostic_not_predictor": True,
        "protected_2026_opened": False,
        "folds": [],
    }
    for year in (2022, 2023, 2024):
        reference, _ = load_fold(year)
        target = pl.read_parquet(
            BASE
            / f"hitter-v2-stage2-prescore/tables/v{year}/target_player_league_seasons.parquet"
        )
        target = target.filter(pl.col("level_group").str.to_uppercase() == "MLB")
        if "modeling_eligible" in target.columns:
            target = target.filter(pl.col("modeling_eligible"))
        target = (
            target.group_by("player_id")
            .agg(pl.col(o).sum() for o in OUTCOMES)
            .with_columns(pl.sum_horizontal(OUTCOMES).alias("MLB_pa"))
        )
        predictions = pl.read_parquet(
            BASE / f"hitter-v2-T2026B/{year}_conditional.parquet"
        ).filter(pl.col("scenario_level") == "MLB")
        ages = pl.read_parquet(
            BASE / f"hitter-v2-stage2-age/tables/v{year}/forecast_player_ages.parquet"
        )
        frame = (
            target.join(
                reference.select("player_id", "origin", "prior_hitter_talent_pa"),
                on="player_id",
            )
            .filter(pl.col("origin") != "MLB")
            .join(ages, on="player_id", how="left")
            .join(predictions.select("player_id", *PROBS), on="player_id")
        )
        frame = frame.with_columns(
            pl.when(pl.col("age_years").is_null())
            .then(pl.lit("unknown"))
            .when(pl.col("age_years") <= 23)
            .then(pl.lit("<=23"))
            .when(pl.col("age_years") <= 26)
            .then(pl.lit("24-26"))
            .otherwise(pl.lit("27+"))
            .alias("age_band"),
            pl.when(pl.col("prior_hitter_talent_pa") <= 300)
            .then(pl.lit("<=300"))
            .when(pl.col("prior_hitter_talent_pa") <= 1000)
            .then(pl.lit("301-1000"))
            .otherwise(pl.lit(">1000"))
            .alias("weighted_history_PA"),
            pl.when(pl.col("MLB_pa") < 100)
            .then(pl.lit("<100"))
            .otherwise(pl.lit(">=100"))
            .alias("observed_MLB_PA"),
        )
        rows = []
        for dim in ("age_band", "weighted_history_PA", "observed_MLB_PA"):
            for (label,), sub in frame.group_by(dim):
                p = sub.select(PROBS).to_numpy()
                counts = sub.select(OUTCOMES).to_numpy()
                rows.append(
                    {
                        "dimension": dim,
                        "group": label,
                        "supported": bool(sub.height >= 50 and counts.sum() >= 5000),
                        "views": {v: metrics(p, counts, v) for v in ("pa", "player")},
                    }
                )
        result["folds"].append({"year": year, "groups": rows})
        for row in rows:
            m = row["views"]["pa"]
            print(
                year,
                row["dimension"],
                row["group"],
                m["players"],
                round(m["bias"], 4),
                round(m["rmse"], 4),
            )
    (ROOT / "docs/hitter-v2-MLB-error-groups.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
