"""Compare original 2024 opportunity forecasts on verified identical targets."""

from pathlib import Path
import json
from hashlib import sha256

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/generated"


def main():
    paths = {
        "old": BASE
        / "playing-time-v1-validation-2024/tables/candidate_2024_scored.parquet",
        "new": BASE / "hitter-v2-O2026D-unfiltered/2024_predictions.parquet",
        "labels": BASE / "hitter-v2-O2026D-unfiltered/2024_labels.parquet",
    }
    record = json.loads(
        (ROOT / "docs/playing-time-v1-validation-2024-result.json").read_text()
    )
    assert (
        sha256(paths["old"].read_bytes()).hexdigest()
        == record["storage"]["candidate_2024_scored"]["file_sha256"]
    )
    current = json.loads((ROOT / "docs/hitter-v2-O2026D-result.json").read_text())
    fold = next(f for f in current["folds"] if f["year"] == 2024)
    assert sha256(paths["new"].read_bytes()).hexdigest() == fold["predictions_sha256"]
    old, new, labels = (pl.read_parquet(paths[k]) for k in ("old", "new", "labels"))
    assert (
        old.height
        == old["player_id"].n_unique()
        == new.height
        == new["player_id"].n_unique()
    )
    assert set(old["player_id"]) == set(new["player_id"]) == set(labels["player_id"])
    frame = (
        new.join(old, on="player_id", validate="1:1")
        .join(
            labels.select("player_id", "mlb_pa", "any_pa"),
            on="player_id",
            validate="1:1",
        )
        .sort("player_id")
    )
    assert (frame["observed_mlb_pa"] == frame["mlb_pa"]).all()
    assert (frame["observed_any_mlb_pa"] == (frame["mlb_pa"] > 0)).all()
    assert np.allclose(
        frame["predicted_any_mlb_pa_probability"]
        * frame["predicted_positive_mlb_pa_mean"],
        frame["predicted_expected_mlb_pa"],
        atol=1e-10,
    )
    models = {
        "OLD_SELECTED": (
            "predicted_any_mlb_pa_probability",
            "predicted_expected_mlb_pa",
        ),
        "O2026D_LEVEL": ("LEVEL_any_pa", "LEVEL_mlb_pa"),
    }
    groups = {
        "all": frame,
        "no_prior_MLB_PA": frame.filter(pl.col("prior_mlb_pa") == 0),
        "prior_MLB_PA": frame.filter(pl.col("prior_mlb_pa") > 0),
    }
    groups.update({f"origin_{k[0]}": g for k, g in frame.group_by("origin")})
    scores = {}
    for group, data in groups.items():
        y, pa = data["any_pa"].to_numpy(), data["mlb_pa"].to_numpy()
        scores[group] = {"players": data.height, "models": {}}
        for model, (pc, ec) in models.items():
            p, e = data[pc].to_numpy(), data[ec].to_numpy()
            assert np.isfinite(p).all() and np.isfinite(e).all()
            assert ((p >= 0) & (p <= 1) & (e >= 0)).all()
            q = np.clip(p, 1e-6, 1 - 1e-6)
            scores[group]["models"][model] = {
                "brier": float(np.mean((p - y) ** 2)),
                "log_loss": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
                "pa_rmse": float(np.sqrt(np.mean((e - pa) ** 2))),
                "pa_mae": float(np.mean(abs(e - pa))),
                "participation_bias": float(np.mean(p - y)),
            }
    expected = record["candidate_2024_metrics"]
    assert (
        abs(
            scores["all"]["models"]["OLD_SELECTED"]["brier"]
            - expected["participation_brier"]
        )
        < 1e-12
    )
    assert (
        abs(
            scores["all"]["models"]["OLD_SELECTED"]["pa_rmse"]
            - expected["unconditional_mlb_pa_rmse"]
        )
        < 1e-10
    )
    y = frame["any_pa"].to_numpy()
    a = (frame[models["OLD_SELECTED"][0]].to_numpy() - y) ** 2
    b = (frame[models["O2026D_LEVEL"][0]].to_numpy() - y) ** 2
    rng = np.random.default_rng(260906)
    draws = [
        float((a - b)[rng.integers(0, len(y), len(y))].mean()) for _ in range(1000)
    ]
    report = {
        "status": "recovered_frozen_forecast_comparison",
        "year": 2024,
        "refit": False,
        "protected_2026_opened": False,
        "release_ready": False,
        "identical_player_ids": True,
        "identical_official_PA_targets": True,
        "old_published_scores_reproduced": True,
        "input_hashes": {
            k: sha256(p.read_bytes()).hexdigest() for k, p in paths.items()
        },
        "scores": scores,
        "paired_player_bootstrap_brier_old_minus_new": {
            "mean": float((a - b).mean()),
            "interval95": np.quantile(draws, [0.025, 0.975]).tolist(),
            "draws": 1000,
            "seed": 260906,
        },
        "limitation": "One disclosed year; different original model-selection histories; no new promotion.",
    }
    out = ROOT / "docs/recovered-opportunity-comparison.json"
    if out.exists():
        raise ValueError("Do not overwrite inspected results")
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report["scores"], indent=2))


if __name__ == "__main__":
    main()
