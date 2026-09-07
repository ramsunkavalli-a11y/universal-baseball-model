"""Diagnose existing MLB scenario forecasts; no fitting or new predictions."""

from pathlib import Path
import sys
import json
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
# ruff: noqa: E402 -- Prefer this checkout over a separate editable installation.
from universal_baseball.hitter_calibration_batch import cluster_rmse_interval
from diagnose_hitter_transport import load_fold, metrics, OUTCOMES, WEIGHTS

BASE = ROOT / "reports/generated"
PROBS = [f"p_{o}" for o in OUTCOMES]


def main():
    report = {
        "status": "post_result_diagnostic_only",
        "candidate_fit": False,
        "protected_2026_opened": False,
        "folds": [],
    }
    pooled = []
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
            .join(reference.select("player_id", "origin"), on="player_id")
            .sort("player_id")
        )
        counts = target.select(OUTCOMES).to_numpy()
        predictions = {}
        paths = {
            "G0": BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet",
            "C0": BASE
            / f"hitter-v2-stage2-final-validation/tables/v{year}/c0_nested_eb_predictions.parquet",
            "MARCEL": BASE
            / f"hitter-v2-stage2-final-validation/tables/v{year}/b1_marcel_345_k1200_predictions.parquet",
            "TRANSPORT": BASE / f"hitter-v2-T2026B/{year}_conditional.parquet",
        }
        for model, path in paths.items():
            p = pl.read_parquet(path)
            if model == "TRANSPORT":
                p = p.filter(pl.col("scenario_level") == "MLB")
            predictions[model] = (
                target.select("player_id")
                .join(p, on="player_id", validate="1:1", maintain_order="left")
                .select(PROBS)
                .to_numpy()
            )
        groups = {
            "all": np.ones(target.height, dtype=bool),
            "prior_MLB": (target["origin"] == "MLB").to_numpy(),
            "prior_minor": (target["origin"] != "MLB").to_numpy(),
        }
        history = pl.read_parquet(
            BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/gap_aware_training_history.parquet"
        )
        recorded_mlb = set(
            history.filter(
                (pl.col("level_group").str.to_uppercase() == "MLB")
                & (pl.col("hitter_talent_pa") > 0)
            )["player_id"]
        )
        has_mlb = np.array([pid in recorded_mlb for pid in target["player_id"]])
        groups["prior_minor_no_recorded_MLB"] = groups["prior_minor"] & ~has_mlb
        groups["prior_minor_recorded_MLB"] = groups["prior_minor"] & has_mlb
        groups.update(
            {
                level: (target["origin"] == level).to_numpy()
                for level in target["origin"].unique()
            }
        )
        fold = {"year": year, "groups": []}
        for name, mask in groups.items():
            if not mask.any():
                continue
            fold["groups"].append(
                {
                    "group": name,
                    "models": {
                        model: {
                            view: metrics(p[mask], counts[mask], view)
                            for view in ("pa", "player")
                        }
                        for model, p in predictions.items()
                    },
                }
            )
        mask = groups["prior_minor"]
        pa = counts[mask].sum(axis=1)
        actual = counts[mask] @ WEIGHTS / pa
        pooled.append(
            (
                target["player_id"].to_numpy()[mask],
                pa,
                predictions["TRANSPORT"][mask] @ WEIGHTS - actual,
                predictions["G0"][mask] @ WEIGHTS - actual,
            )
        )
        report["folds"].append(fold)
    args = [np.concatenate([p[i] for p in pooled]) for i in range(4)]
    report["prior_minor_paired_cluster_rmse_interval"] = cluster_rmse_interval(*args)
    pa = args[1]
    report["prior_minor_pooled_pa_rmse"] = {
        "TRANSPORT": float(np.sqrt(pa @ (args[2] ** 2) / pa.sum())),
        "G0": float(np.sqrt(pa @ (args[3] ** 2) / pa.sum())),
    }
    (ROOT / "docs/hitter-v2-MLB-transport-audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    for fold in report["folds"]:
        for g in fold["groups"]:
            if g["group"] in ("all", "prior_MLB", "prior_minor"):
                print(
                    fold["year"],
                    g["group"],
                    g["models"]["G0"]["pa"]["players"],
                    {m: round(s["pa"]["rmse"], 6) for m, s in g["models"].items()},
                )
    print(
        report["prior_minor_pooled_pa_rmse"],
        report["prior_minor_paired_cluster_rmse_interval"],
    )


if __name__ == "__main__":
    main()
