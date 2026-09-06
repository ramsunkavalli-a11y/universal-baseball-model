"""Execute the fixed C2026A batch; forecasts precede each fold's evaluation."""
# ruff: noqa: E402 -- Prefer this checkout over a different editable installation.

from pathlib import Path
import sys
import json
import hashlib
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from universal_baseball.hitter_calibration_batch import (
    fit_calibration,
    cluster_rmse_interval,
    LEVELS,
)
from diagnose_hitter_transport import load_fold, origins, metrics, OUTCOMES, WEIGHTS

BASE = ROOT / "reports/generated"
OUTPUT = BASE / "hitter-v2-C2026A"
CANDIDATES = ("CAL_GLOBAL", "CAL_ORIGIN")
PROBS = [f"p_{o}" for o in OUTCOMES]


def groups(frame):
    return np.array([LEVELS.index(o or "UNKNOWN") for o in frame["origin"]], dtype=int)


def array(frame):
    return frame.select(PROBS).to_numpy()


def summarize(frame, prediction):
    counts = frame.select(OUTCOMES).to_numpy()
    return {view: metrics(prediction, counts, view) for view in ("pa", "player")}


def main():
    if OUTPUT.exists():
        raise RuntimeError(
            "Batch output already exists; do not overwrite an inspected experiment"
        )
    OUTPUT.mkdir(parents=True)
    contract = ROOT / "docs/hitter-v2-calibration-batch-contract.md"
    report = {
        "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
        "status": "disclosed_development_only",
        "protected_2026_opened": False,
        "folds": [],
    }
    past = []
    pooled = {m: [] for m in (*CANDIDATES, "G0", "C0", "MARCEL")}
    all_frames = []
    for year in (2022, 2023, 2024):
        history = pl.read_parquet(
            BASE
            / f"hitter-v2-stage2-prescore/tables/v{year}/training_player_league_seasons.parquet"
        )
        forecast = pl.read_parquet(
            BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet"
        ).join(origins(history), on="player_id", how="left")
        if history["season"].max() >= year or set(
            forecast["predictor_cutoff_season"]
        ) != {year - 1}:
            raise ValueError("Predictor chronology violated")
        fits = {}
        predictions = {}
        for model in CANDIDATES:
            if year == 2022:
                q = array(forecast)
                fits[model] = {"identity_warmup": True}
            else:
                train = pl.concat(past, how="diagonal_relaxed")
                fitted = fit_calibration(
                    array(train),
                    train.select(OUTCOMES).to_numpy(),
                    groups(train),
                    by_origin=model == "CAL_ORIGIN",
                    forecast_year=year,
                    training_years=list(range(2022, year)),
                )
                q = fitted.predict(array(forecast), groups(forecast))
                fits[model] = {
                    "theta": fitted.theta.tolist(),
                    "training_years": list(fitted.training_years),
                    "training_players": train.height,
                    "iterations": fitted.iterations,
                }
            result = forecast.select(
                "player_id", "predictor_cutoff_season", "origin"
            ).hstack(pl.DataFrame(q, schema=PROBS))
            result.write_parquet(OUTPUT / f"{year}_{model}.parquet")
            predictions[model] = result
        # All current-year candidate forecasts now exist; evaluate disclosed outcomes.
        frame, _ = load_fold(year)
        scored = {"G0": array(frame)}
        for model, result in predictions.items():
            scored[model] = array(
                frame.select("player_id").join(
                    result, on="player_id", validate="1:1", maintain_order="left"
                )
            )
        for model, name in [
            ("C0", "c0_nested_eb_predictions"),
            ("MARCEL", "b1_marcel_345_k1200_predictions"),
        ]:
            result = pl.read_parquet(
                BASE
                / f"hitter-v2-stage2-final-validation/tables/v{year}/{name}.parquet"
            )
            scored[model] = array(
                frame.select("player_id").join(
                    result, on="player_id", validate="1:1", maintain_order="left"
                )
            )
        fold = {
            "year": year,
            "fits": fits,
            "models": {m: summarize(frame, p) for m, p in scored.items()},
            "groups": [],
        }
        targets = pl.read_parquet(
            BASE / f"hitter-v2-stage2-prescore/tables/v{year}/target_players.parquet"
        )
        fold["coverage"] = {
            "target_players": targets.height,
            "paired_players": frame.height,
            "without_G0_forecast": targets.height - frame.height,
        }
        for dim in ("movement", "origin"):
            for key in sorted(frame[dim].drop_nulls().unique().to_list()):
                mask = (frame[dim] == key).to_numpy()
                sub = frame.filter(pl.col(dim) == key)
                fold["groups"].append(
                    {
                        "dimension": dim,
                        "group": key,
                        "supported": bool(
                            sub.height >= 50 and sub["hitter_talent_pa"].sum() >= 5000
                        ),
                        "models": {
                            m: summarize(sub, p[mask]) for m, p in scored.items()
                        },
                    }
                )
        report["folds"].append(fold)
        if year > 2022:
            all_frames.append(frame)
            for m, p in scored.items():
                pooled[m].append(p)
        past.append(frame)
    combined = pl.concat(all_frames, how="diagonal_relaxed")
    pooled = {m: np.vstack(p) for m, p in pooled.items()}
    report["pooled_active_years"] = {
        m: summarize(combined, p) for m, p in pooled.items()
    }
    pa = combined["hitter_talent_pa"].to_numpy()
    actual = combined.select(OUTCOMES).to_numpy() @ WEIGHTS / pa
    report["decisions"] = {}
    for model in CANDIDATES:
        base = report["pooled_active_years"]["G0"]["pa"]
        current = report["pooled_active_years"][model]["pa"]
        improvement = 1 - current["rmse"] / base["rmse"]
        fold_ok = all(
            f["models"][model]["pa"]["rmse"] <= f["models"]["G0"]["pa"]["rmse"] * 1.02
            for f in report["folds"][1:]
        )
        calibration_ok = all(
            abs(f["models"][model][v]["bias"]) <= 0.010
            and 0.85 <= f["models"][model][v]["slope"] <= 1.15
            for f in report["folds"][1:]
            for v in ("pa", "player")
        )
        reversals = []
        for f in report["folds"][1:]:
            for g in f["groups"]:
                for v in ("pa", "player"):
                    if (
                        g["supported"]
                        and g["models"][model][v]["rmse"]
                        > 1.05 * g["models"]["G0"][v]["rmse"]
                    ):
                        reversals.append(
                            {
                                "year": f["year"],
                                "dimension": g["dimension"],
                                "group": g["group"],
                                "view": v,
                            }
                        )
        primary = (
            improvement >= 0.01
            and fold_ok
            and current["log_loss"] <= base["log_loss"] * 1.0025
        )
        interval = cluster_rmse_interval(
            combined["player_id"].to_numpy(),
            pa,
            pooled[model] @ WEIGHTS - actual,
            pooled["G0"] @ WEIGHTS - actual,
        )
        report["decisions"][model] = {
            "relative_rmse_improvement": improvement,
            "primary_pass": bool(primary),
            "calibration_pass": bool(calibration_ok),
            "subgroup_reversals": reversals,
            "readiness_pass": bool(primary and calibration_ok and not reversals),
            "paired_cluster_rmse_interval": interval,
            "minimum_prediction": float(pooled[model].min()),
        }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (ROOT / "docs/hitter-v2-C2026A-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {"decisions": report["decisions"], "pooled": report["pooled_active_years"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
