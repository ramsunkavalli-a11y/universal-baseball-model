"""Run the single fixed T2026B candidate; preserve prospective and conditional tasks."""

# ruff: noqa: E402 -- Use this checkout, not another editable installation.
from pathlib import Path
import sys
import json
import hashlib
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from universal_baseball.hitter_history_transport import (
    fit_effects,
    normalize_history,
    transition_matrix,
    transform,
    LEVELS,
)
from universal_baseball.hitter_calibration_batch import cluster_rmse_interval
from universal_baseball.hitter_v2_model import predict_c0_nested_eb
from fit_hitter_v2_gap_aware_G0 import _parameters
from diagnose_hitter_transport import load_fold, origins, metrics, OUTCOMES, WEIGHTS

BASE = ROOT / "reports/generated"
OUTPUT = BASE / "hitter-v2-T2026B"
PROBS = [f"p_{o}" for o in OUTCOMES]


def score(frame, p):
    return {
        v: metrics(p, frame.select(OUTCOMES).to_numpy(), v) for v in ("pa", "player")
    }


def main():
    if OUTPUT.exists():
        raise RuntimeError("Do not overwrite an inspected experiment")
    OUTPUT.mkdir(parents=True)
    record_path = BASE / "hitter-v2-gap-aware-G0-fit/report.json"
    if (
        hashlib.sha256(record_path.read_bytes()).hexdigest()
        != "392fcdbac750e90770b003114e4d38d0854b0ea24ab272ed0626f0c367dad86f"
    ):
        raise ValueError("G0 fit provenance changed")
    record = json.loads(record_path.read_text())
    selection = json.loads(
        (ROOT / "docs/hitter-v2-stage2-component-selection-result.json").read_text()
    )
    report = {
        "status": "disclosed_development_only",
        "protected_2026_opened": False,
        "contract_sha256": hashlib.sha256(
            (ROOT / "docs/hitter-v2-history-transport-contract.md").read_bytes()
        ).hexdigest(),
        "folds": [],
    }
    pooled = {m: [] for m in ("G0", "TRANSPORT", "MARCEL")}
    frames = []
    for year, source in zip((2022, 2023, 2024), record["folds"]):
        hp = (
            BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/gap_aware_training_history.parquet"
        )
        if (
            hashlib.sha256(hp.read_bytes()).hexdigest()
            != source["storage"]["history"]["file_sha256"]
        ):
            raise ValueError("G0 history changed")
        history = pl.read_parquet(hp)
        frozen = pl.read_parquet(
            BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet"
        ).sort("player_id")
        half, prior = _parameters(selection, f"V{year}")
        kwargs = {
            "predictor_cutoff_season": year - 1,
            "half_life_seasons": half,
            "component_prior_pa": prior,
        }
        # Ensure this runtime reproduces G0 before attributing any change to transport.
        reproduction = predict_c0_nested_eb(
            history, frozen["player_id"].to_list(), **kwargs
        ).sort("player_id")
        delta = float(
            np.max(
                np.abs(
                    reproduction.select(PROBS).to_numpy()
                    - frozen.select(PROBS).to_numpy()
                )
            )
        )
        if delta > 1e-12:
            raise ValueError("G0 reproduction failed")
        effects, fit = fit_effects(history, year - 1)
        neutral = predict_c0_nested_eb(
            normalize_history(history, effects), frozen["player_id"].to_list(), **kwargs
        ).sort("player_id")
        p = neutral.select(PROBS).to_numpy()
        conditional = np.stack([transform(p, effects[i]) for i in range(6)], axis=1)
        transitions, support = transition_matrix(history, year - 1)
        context = frozen.select("player_id").join(
            origins(history), on="player_id", how="left", maintain_order="left"
        )
        if context["origin"].null_count():
            raise ValueError("Unexpected missing G0 history")
        index = np.array([LEVELS.index(x) for x in context["origin"]])
        q = np.sum(conditional * transitions[index, :, None], axis=1)
        candidate = context.hstack(pl.DataFrame(q, schema=PROBS))
        candidate.write_parquet(OUTPUT / f"{year}_prospective.parquet")
        scenarios = pl.concat(
            [
                context.with_columns(pl.lit(level).alias("scenario_level")).hstack(
                    pl.DataFrame(conditional[:, i, :], schema=PROBS)
                )
                for i, level in enumerate(LEVELS)
            ]
        )
        scenarios.write_parquet(OUTPUT / f"{year}_conditional.parquet")
        # All scenarios and prospective mixtures are saved before current outcomes load.
        frame, _ = load_fold(year)
        arrays = {
            "G0": frame.select(PROBS).to_numpy(),
            "TRANSPORT": frame.select("player_id")
            .join(candidate, on="player_id", validate="1:1", maintain_order="left")
            .select(PROBS)
            .to_numpy(),
        }
        marcel = pl.read_parquet(
            BASE
            / f"hitter-v2-stage2-final-validation/tables/v{year}/b1_marcel_345_k1200_predictions.parquet"
        )
        arrays["MARCEL"] = (
            frame.select("player_id")
            .join(marcel, on="player_id", validate="1:1", maintain_order="left")
            .select(PROBS)
            .to_numpy()
        )
        fold = {
            "year": year,
            "G0_reproduction_maximum_delta": delta,
            "transport_fit": fit,
            "transitions": transitions.tolist(),
            "transition_returning_players": support,
            "models": {m: score(frame, p) for m, p in arrays.items()},
            "groups": [],
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
                        "models": {m: score(sub, p[mask]) for m, p in arrays.items()},
                    }
                )
        tp = (
            BASE
            / f"hitter-v2-stage2-prescore/tables/v{year}/target_player_league_seasons.parquet"
        )
        target = pl.read_parquet(tp)
        if set(target["season"]) != {year}:
            raise ValueError("Wrong conditional target season")
        if "modeling_eligible" in target.columns:
            target = target.filter(pl.col("modeling_eligible"))
        target = (
            target.with_columns(pl.col("level_group").str.to_uppercase())
            .group_by("player_id", "level_group")
            .agg(pl.col(o).sum() for o in OUTCOMES)
            .join(frame.select("player_id"), on="player_id")
        )
        paired = target.join(
            scenarios,
            left_on=["player_id", "level_group"],
            right_on=["player_id", "scenario_level"],
            validate="1:1",
        )
        fold["conditional_diagnostic"] = {
            "target_sha256": hashlib.sha256(tp.read_bytes()).hexdigest(),
            "levels": [],
        }
        for (level,), sub in paired.group_by("level_group"):
            baseline = (
                sub.select("player_id")
                .join(frozen, on="player_id", validate="1:1", maintain_order="left")
                .select(PROBS)
                .to_numpy()
            )
            fold["conditional_diagnostic"]["levels"].append(
                {
                    "level": level,
                    "G0": score(sub, baseline),
                    "TRANSPORT": score(sub, sub.select(PROBS).to_numpy()),
                }
            )
        report["folds"].append(fold)
        frames.append(frame)
        for m, p in arrays.items():
            pooled[m].append(p)
        print("Completed", year, flush=True)
    frame = pl.concat(frames, how="diagonal_relaxed")
    pooled = {m: np.vstack(p) for m, p in pooled.items()}
    report["pooled"] = {m: score(frame, p) for m, p in pooled.items()}
    ref = report["pooled"]["G0"]["pa"]
    candidate = report["pooled"]["TRANSPORT"]["pa"]
    improvement = 1 - candidate["rmse"] / ref["rmse"]
    fold_ok = all(
        f["models"]["TRANSPORT"]["pa"]["rmse"] <= 1.02 * f["models"]["G0"]["pa"]["rmse"]
        for f in report["folds"]
    )
    calibration_ok = all(
        abs(f["models"]["TRANSPORT"][v]["bias"]) <= 0.01
        and 0.85 <= f["models"]["TRANSPORT"][v]["slope"] <= 1.15
        for f in report["folds"]
        for v in ("pa", "player")
    )
    reversals = [
        {"year": f["year"], "dimension": g["dimension"], "group": g["group"], "view": v}
        for f in report["folds"]
        for g in f["groups"]
        for v in ("pa", "player")
        if g["supported"]
        and g["models"]["TRANSPORT"][v]["rmse"] > 1.05 * g["models"]["G0"][v]["rmse"]
    ]
    primary = (
        improvement >= 0.01
        and fold_ok
        and candidate["log_loss"] <= ref["log_loss"] * 1.0025
    )
    pa = frame["hitter_talent_pa"].to_numpy()
    actual = frame.select(OUTCOMES).to_numpy() @ WEIGHTS / pa
    report["decision"] = {
        "relative_rmse_improvement": improvement,
        "primary_pass": bool(primary),
        "calibration_pass": bool(calibration_ok),
        "subgroup_reversals": reversals,
        "readiness_pass": bool(primary and calibration_ok and not reversals),
        "paired_cluster_rmse_interval": cluster_rmse_interval(
            frame["player_id"].to_numpy(),
            pa,
            pooled["TRANSPORT"] @ WEIGHTS - actual,
            pooled["G0"] @ WEIGHTS - actual,
        ),
    }
    payload = json.dumps(report, indent=2) + "\n"
    (OUTPUT / "report.json").write_text(payload, encoding="utf-8", newline="\n")
    (ROOT / "docs/hitter-v2-T2026B-result.json").write_text(
        payload, encoding="utf-8", newline="\n"
    )
    print(json.dumps(report["decision"], indent=2))


if __name__ == "__main__":
    main()
