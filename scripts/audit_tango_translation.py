"""Diagnose saved forecasts by history support and common evaluation centering.

No new model, prediction correction, selection, or protected outcomes. Centering
uses observed evaluation means for scoring ONLY, never a deployable forecast.
"""

from pathlib import Path
import sys
import json
from hashlib import sha256

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
# ruff: noqa: E402
from universal_baseball.hitter_history_transport import canonical_level
from diagnose_hitter_transport import load_fold, OUTCOMES, WEIGHTS

BASE = ROOT / "reports/generated"
PROBS = [f"p_{o}" for o in OUTCOMES]


def errors(prediction, actual, weight):
    weight = weight / weight.sum()
    error = prediction - actual
    return {
        "mae": float(weight @ abs(error)),
        "rmse": float(np.sqrt(weight @ error**2)),
        "bias": float(weight @ error),
    }


def main():
    report = {
        "status": "post_result_diagnostic_only",
        "candidate_fit": False,
        "protected_2026_opened": False,
        "centering_is_evaluation_only": True,
        "folds": [],
    }
    for year in (2022, 2023, 2024):
        reference, _ = load_fold(year)
        paths = {
            "history": BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/gap_aware_training_history.parquet",
            "target": BASE
            / f"hitter-v2-stage2-prescore/tables/v{year}/target_player_league_seasons.parquet",
            "G0": BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet",
            "TRANSPORT": BASE / f"hitter-v2-T2026B/{year}_conditional.parquet",
            "MARCEL_ADAPTED": BASE
            / f"hitter-v2-stage2-final-validation/tables/v{year}/b1_marcel_345_k1200_predictions.parquet",
        }
        history = pl.read_parquet(paths["history"])
        assert history["season"].max() < year
        history = history.with_columns(
            pl.col("level_group").map_elements(canonical_level, return_dtype=pl.String)
        )
        grouped = history.group_by("player_id", "season", "level_group").agg(
            pl.col("hitter_talent_pa").sum()
        )
        pair_support = (
            grouped.filter(pl.col("hitter_talent_pa") >= 50)
            .group_by("player_id", "season")
            .agg(pl.col("level_group").n_unique().alias("levels"))
        )
        movers = set(pair_support.filter(pl.col("levels") >= 2)["player_id"])
        mlb_ids = set(
            history.filter(
                (pl.col("level_group") == "MLB") & (pl.col("hitter_talent_pa") > 0)
            )["player_id"]
        )
        totals = history.group_by("player_id").agg(pl.col("hitter_talent_pa").sum())
        target = pl.read_parquet(paths["target"]).filter(
            pl.col("level_group").str.to_uppercase() == "MLB"
        )
        if "modeling_eligible" in target.columns:
            target = target.filter(pl.col("modeling_eligible"))
        target = target.group_by("player_id").agg(pl.col(o).sum() for o in OUTCOMES)
        frame = (
            target.join(reference.select("player_id", "origin"), on="player_id")
            .join(totals, on="player_id", validate="1:1")
            .sort("player_id")
        )
        counts = frame.select(OUTCOMES).to_numpy()
        pa = counts.sum(axis=1)
        actual = counts @ WEIGHTS / pa
        predictions = {}
        for model in ("G0", "TRANSPORT", "MARCEL_ADAPTED"):
            p = pl.read_parquet(paths[model])
            if model == "TRANSPORT":
                p = p.filter(pl.col("scenario_level") == "MLB")
            joined = frame.select("player_id").join(
                p, on="player_id", how="left", validate="1:1", maintain_order="left"
            )
            vector = joined.select(PROBS).to_numpy()
            assert np.isfinite(vector).all() and np.allclose(vector.sum(axis=1), 1)
            predictions[model] = vector @ WEIGHTS
        prior_minor = (frame["origin"] != "MLB").to_numpy()
        has_mlb = np.array([p in mlb_ids for p in frame["player_id"]])
        moved = np.array([p in movers for p in frame["player_id"]])
        history_pa = frame["hitter_talent_pa"].to_numpy()
        masks = {
            "all": np.ones(frame.height, dtype=bool),
            "prior_minor": prior_minor,
            "minor_no_recorded_MLB": prior_minor & ~has_mlb,
            "minor_with_recorded_MLB": prior_minor & has_mlb,
            "minor_with_translation_pair_history": prior_minor & moved,
            "minor_without_translation_pair_history": prior_minor & ~moved,
        }
        for lower, upper, name in (
            (0, 300, "1-300"),
            (300, 1000, "301-1000"),
            (1000, np.inf, "1001+"),
        ):
            masks[f"minor_history_PA_{name}"] = (
                prior_minor & (history_pa > lower) & (history_pa <= upper)
            )
        rows = []
        for name, mask in masks.items():
            if not mask.any():
                continue
            result = {
                "group": name,
                "players": int(mask.sum()),
                "pa": int(pa[mask].sum()),
                "supported": bool(mask.sum() >= 50 and pa[mask].sum() >= 5000),
                "models": {},
            }
            for model, prediction in predictions.items():
                # Common full evaluated MLB cohort: do not center each subgroup.
                gap = float(pa @ (prediction - actual) / pa.sum())
                result["models"][model] = {
                    "raw": errors(prediction[mask], actual[mask], pa[mask]),
                    "common_MLB_centered": errors(
                        prediction[mask] - gap, actual[mask], pa[mask]
                    ),
                    "full_cohort_mean_error_removed": gap,
                }
            rows.append(result)
        report["folds"].append(
            {
                "year": year,
                "groups": rows,
                "input_hashes": {
                    k: sha256(p.read_bytes()).hexdigest() for k, p in paths.items()
                },
            }
        )
    out = ROOT / "docs/hitter-v2-tango-translation-audit.json"
    if out.exists():
        raise ValueError("Do not overwrite an inspected diagnostic")
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    for fold in report["folds"]:
        for group in fold["groups"]:
            if group["group"] in (
                "prior_minor",
                "minor_no_recorded_MLB",
                "minor_without_translation_pair_history",
            ):
                print(
                    fold["year"],
                    group["group"],
                    group["players"],
                    {
                        m: round(s["common_MLB_centered"]["mae"], 5)
                        for m, s in group["models"].items()
                    },
                )


if __name__ == "__main__":
    main()
