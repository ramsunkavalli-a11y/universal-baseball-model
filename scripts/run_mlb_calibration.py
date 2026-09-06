"""Run the two predeclared C2026C MLB-conditional calibration candidates."""

# ruff: noqa: E402 -- Use the current checkout rather than another editable install.
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
)
from universal_baseball.hitter_mlb_value_calibration import fit_value, predict_value
from diagnose_hitter_transport import load_fold, metrics, OUTCOMES, WEIGHTS

BASE = ROOT / "reports/generated"
OUTPUT = BASE / "hitter-v2-C2026C"
PROBS = [f"p_{o}" for o in OUTCOMES]
MODELS = ("TRANSPORT", "MLB_EVENT", "MLB_VALUE", "G0", "C0", "MARCEL")


def scores(frame, p):
    return {
        v: metrics(p, frame.select(OUTCOMES).to_numpy(), v) for v in ("pa", "player")
    }


def main():
    if OUTPUT.exists():
        raise RuntimeError("Do not overwrite an inspected batch")
    source_manifest = ROOT / "docs/hitter-v2-MLB-calibration-inputs.json"
    for item in json.loads(source_manifest.read_text()):
        if (
            hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
            != item["sha256"]
        ):
            raise ValueError("Input hash changed")
    OUTPUT.mkdir(parents=True)
    report = {
        "status": "disclosed_development_only",
        "protected_2026_opened": False,
        "contract_sha256": hashlib.sha256(
            (ROOT / "docs/hitter-v2-MLB-calibration-contract.md").read_bytes()
        ).hexdigest(),
        "input_manifest_sha256": hashlib.sha256(
            source_manifest.read_bytes()
        ).hexdigest(),
        "folds": [],
    }
    past = []
    active = []
    pooled = {m: [] for m in MODELS}
    for year in (2022, 2023, 2024):
        forecast = (
            pl.read_parquet(BASE / f"hitter-v2-T2026B/{year}_conditional.parquet")
            .filter(pl.col("scenario_level") == "MLB")
            .sort("player_id")
        )
        original = pl.read_parquet(
            BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet"
        )
        if (
            set(original["predictor_cutoff_season"]) != {year - 1}
            or set(original["player_id"]) != set(forecast["player_id"])
            or forecast["origin_season"].max() >= year
        ):
            raise ValueError("Wrong predictor cutoff")
        # The hash-bound T2026B file stores origin season, not forecast cutoff.
        forecast = forecast.with_columns(
            pl.lit(year - 1).alias("predictor_cutoff_season")
        )
        p = forecast.select(PROBS).to_numpy()
        minor = (forecast["origin"] != "MLB").to_numpy()
        predicted = {"TRANSPORT": p}
        fit_records = {}
        if year == 2022:
            predicted.update({"MLB_EVENT": p.copy(), "MLB_VALUE": p.copy()})
            fit_records["identity_warmup"] = True
        else:
            training = pl.concat(past)
            tp = training.select(PROBS).to_numpy()
            counts = training.select(OUTCOMES).to_numpy()
            tm = (training["origin"] != "MLB").to_numpy()
            event = fit_calibration(
                tp,
                counts,
                tm.astype(int),
                by_origin=False,
                forecast_year=year,
                training_years=list(range(2022, year)),
            )
            value = fit_value(
                tp,
                counts,
                tm,
                forecast_year=year,
                training_years=list(range(2022, year)),
            )
            predicted["MLB_EVENT"] = event.predict(p, minor.astype(int))
            predicted["MLB_VALUE"], clipped = predict_value(p, minor, value)
            fit_records = {
                "training_years": list(range(2022, year)),
                "training_rows": training.height,
                "event_theta": event.theta.tolist(),
                "value_parameters": value.tolist(),
                "value_forecasts_clipped": clipped,
            }
        for model in ("MLB_EVENT", "MLB_VALUE"):
            forecast.select("player_id", "origin", "predictor_cutoff_season").hstack(
                pl.DataFrame(predicted[model], schema=PROBS)
            ).write_parquet(OUTPUT / f"{year}_{model}.parquet")
        # Current-year candidate forecasts are now fixed. Load the disclosed target.
        reference, _ = load_fold(year)
        target = pl.read_parquet(
            BASE
            / f"hitter-v2-stage2-prescore/tables/v{year}/target_player_league_seasons.parquet"
        )
        if set(target["season"]) != {year}:
            raise ValueError("Wrong outcome season")
        target = target.filter(pl.col("level_group").str.to_uppercase() == "MLB")
        if "modeling_eligible" in target.columns:
            target = target.filter(pl.col("modeling_eligible"))
        target = (
            target.group_by("player_id")
            .agg(pl.col(o).sum() for o in OUTCOMES)
            .join(reference.select("player_id"), on="player_id")
            .join(
                forecast.select("player_id", "origin", *PROBS),
                on="player_id",
                validate="1:1",
            )
            .sort("player_id")
        )
        index = {pid: i for i, pid in enumerate(forecast["player_id"])}
        idx = np.array([index[pid] for pid in target["player_id"]])
        current = {m: q[idx] for m, q in predicted.items()}
        for model, name in [
            ("G0", None),
            ("C0", "c0_nested_eb_predictions"),
            ("MARCEL", "b1_marcel_345_k1200_predictions"),
        ]:
            source = (
                reference
                if name is None
                else pl.read_parquet(
                    BASE
                    / f"hitter-v2-stage2-final-validation/tables/v{year}/{name}.parquet"
                )
            )
            current[model] = (
                target.select("player_id")
                .join(
                    source.select("player_id", *PROBS),
                    on="player_id",
                    validate="1:1",
                    maintain_order="left",
                )
                .select(PROBS)
                .to_numpy()
            )
        masks = {
            "all": np.ones(target.height, dtype=bool),
            "prior_minor": (target["origin"] != "MLB").to_numpy(),
            "prior_MLB": (target["origin"] == "MLB").to_numpy(),
        }
        masks.update(
            {
                "origin_" + o: (target["origin"] == o).to_numpy()
                for o in target["origin"].unique()
            }
        )
        fold = {"year": year, "fit": fit_records, "groups": {}}
        for group, mask in masks.items():
            sub = target.filter(pl.Series(mask))
            if not sub.height:
                continue
            fold["groups"][group] = {
                "supported": bool(
                    sub.height >= 50 and sub.select(OUTCOMES).to_numpy().sum() >= 5000
                ),
                "models": {m: scores(sub, q[mask]) for m, q in current.items()},
            }
        report["folds"].append(fold)
        if year > 2022:
            active.append(target)
            for m, q in current.items():
                pooled[m].append(q)
        past.append(target)
    frame = pl.concat(active)
    pooled = {m: np.vstack(q) for m, q in pooled.items()}
    mask = (frame["origin"] != "MLB").to_numpy()
    sub = frame.filter(pl.Series(mask))
    report["pooled"] = {
        group: {
            m: scores(f, q if group == "all" else q[mask]) for m, q in pooled.items()
        }
        for group, f in [("all", frame), ("prior_minor", sub)]
    }
    report["decisions"] = {}
    for model in ("MLB_EVENT", "MLB_VALUE"):
        ref = report["pooled"]["prior_minor"]["TRANSPORT"]["pa"]
        candidate = report["pooled"]["prior_minor"][model]["pa"]
        improvement = 1 - candidate["rmse"] / ref["rmse"]
        fold_ok = all(
            f["groups"]["prior_minor"]["models"][model]["pa"]["rmse"]
            <= 1.02 * f["groups"]["prior_minor"]["models"]["TRANSPORT"]["pa"]["rmse"]
            for f in report["folds"][1:]
        )
        all_ok = (
            report["pooled"]["all"][model]["pa"]["rmse"]
            <= 1.01 * report["pooled"]["all"]["TRANSPORT"]["pa"]["rmse"]
        )
        loss_ok = all(
            report["pooled"][g][model]["pa"]["log_loss"]
            <= 1.0025 * report["pooled"][g]["TRANSPORT"]["pa"]["log_loss"]
            for g in ("all", "prior_minor")
        )
        reversals = []
        calibration_flags = []
        for f in report["folds"][1:]:
            for group, g in f["groups"].items():
                for view in ("pa", "player"):
                    m = g["models"][model][view]
                    r = g["models"]["TRANSPORT"][view]
                    if (
                        g["supported"]
                        or (group in ("all", "prior_minor") and view == "player")
                    ) and m["rmse"] > 1.05 * r["rmse"]:
                        reversals.append(
                            {"year": f["year"], "group": group, "view": view}
                        )
                    if group in ("all", "prior_minor") and (
                        abs(m["bias"]) > 0.01
                        or m["slope"] is None
                        or not 0.85 <= m["slope"] <= 1.15
                    ):
                        calibration_flags.append(
                            {
                                "year": f["year"],
                                "group": group,
                                "view": view,
                                "bias": m["bias"],
                                "slope": m["slope"],
                            }
                        )
        primary = improvement >= 0.05 and fold_ok and all_ok and loss_ok
        counts = sub.select(OUTCOMES).to_numpy()
        pa = counts.sum(axis=1)
        actual = counts @ WEIGHTS / pa
        report["decisions"][model] = {
            "relative_minor_rmse_improvement": improvement,
            "primary_pass": bool(primary),
            "fold_guardrail_pass": bool(fold_ok),
            "all_MLB_guardrail_pass": bool(all_ok),
            "event_loss_guardrail_pass": bool(loss_ok),
            "subgroup_reversals": reversals,
            "retain_for_development": bool(primary and not reversals),
            "calibration_flags": calibration_flags,
            "release_ready": False,
            "paired_cluster_interval": cluster_rmse_interval(
                sub["player_id"].to_numpy(),
                pa,
                pooled[model][mask] @ WEIGHTS - actual,
                pooled["TRANSPORT"][mask] @ WEIGHTS - actual,
            ),
        }
    payload = json.dumps(report, indent=2) + "\n"
    (OUTPUT / "report.json").write_text(payload, encoding="utf-8", newline="\n")
    (ROOT / "docs/hitter-v2-C2026C-result.json").write_text(
        payload, encoding="utf-8", newline="\n"
    )
    print(json.dumps(report["decisions"], indent=2))


if __name__ == "__main__":
    main()
