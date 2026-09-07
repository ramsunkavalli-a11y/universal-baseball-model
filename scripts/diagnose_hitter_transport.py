"""Disclosed row-level diagnosis; never fits or loads protected seasons."""

from pathlib import Path
import json
import hashlib
import numpy as np
import polars as pl
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS

ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = list(HITTER_TALENT_OUTCOMES)
WEIGHTS = np.array([NEUTRAL_WOBA_WEIGHTS[o] for o in OUTCOMES])
LEVELS = ["RK", "A", "A+", "AA", "AAA", "MLB"]


def origins(history):
    history = history.with_columns(pl.col("level_group").str.to_uppercase())
    grouped = history.group_by("player_id", "season", "level_group").agg(
        pl.col("hitter_talent_pa").sum()
    )
    return (
        grouped.sort(
            ["player_id", "season", "hitter_talent_pa", "level_group"],
            descending=[False, True, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("level_group").alias("origin"),
            pl.col("season").alias("origin_season"),
        )
    )


def metrics(p, counts, weighting):
    pa = counts.sum(axis=1)
    y = counts / pa[:, None]
    w = pa if weighting == "pa" else np.ones(len(pa))
    w = w / w.sum()
    pred, actual = p @ WEIGHTS, y @ WEIGHTS
    pm, am = w @ pred, w @ actual
    variance = w @ ((pred - pm) ** 2)
    return {
        "players": len(pa),
        "pa": float(pa.sum()),
        "rmse": float(np.sqrt(w @ ((pred - actual) ** 2))),
        "bias": float(pm - am),
        "slope": float(w @ ((pred - pm) * (actual - am)) / variance)
        if variance > 1e-14
        else None,
        "log_loss": float(w @ -(y * np.log(np.clip(p, 1e-15, 1))).sum(axis=1)),
        "brier": float(w @ (1 - 2 * (y * p).sum(axis=1) + (p * p).sum(axis=1))),
        "component_bias": dict(zip(OUTCOMES, (w @ (p - y)).tolist())),
    }


def load_fold(year):
    if year not in (2022, 2023, 2024):
        raise ValueError("Only disclosed folds are allowed")
    contract = json.loads(
        (ROOT / "docs/hitter-v2-gap-aware-G0-scoring-contract.json").read_text()
    )
    for row in contract["folds"][f"V{year}"]["inputs"]:
        assert (
            hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
            == row["sha256"]
        )
    base = ROOT / "reports/generated"
    history = pl.read_parquet(
        base
        / f"hitter-v2-stage2-prescore/tables/v{year}/training_player_league_seasons.parquet"
    )
    target = pl.read_parquet(
        base / f"hitter-v2-stage2-prescore/tables/v{year}/target_players.parquet"
    )
    pred = pl.read_parquet(
        base
        / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet"
    )
    assert history["season"].max() < year
    assert set(target["season"]) == {year}
    joined = (
        target.join(pred, on="player_id", validate="1:1")
        .join(origins(history), on="player_id", how="left")
        .with_columns(pl.col("primary_target_level_group").str.to_uppercase())
    )

    def movement(row):
        if row["origin"] is None:
            return "unknown"
        if row["target_level_count"] != 1:
            return "mixed_target_levels"
        a, b = (
            LEVELS.index(row["origin"]),
            LEVELS.index(row["primary_target_level_group"]),
        )
        return "same_level" if a == b else "up" if b > a else "down"

    joined = joined.with_columns(
        pl.Series("movement", [movement(r) for r in joined.to_dicts()])
    )
    return joined, history


def main():
    report = {
        "status": "disclosed_diagnosis",
        "protected_2026_opened": False,
        "folds": [],
    }
    for year in (2022, 2023, 2024):
        frame, history = load_fold(year)
        groups = [("all", "all", frame)]
        for dim in ["movement", "origin", "primary_target_level_group"]:
            groups.extend((dim, key[0], g) for key, g in frame.group_by(dim))
        groups.extend(
            ("same_level_origin", key[0], g)
            for key, g in frame.filter(pl.col("movement") == "same_level").group_by(
                "origin"
            )
        )
        scores = []
        for dim, name, group in groups:
            p = group.select([f"p_{o}" for o in OUTCOMES]).to_numpy()
            counts = group.select(OUTCOMES).to_numpy()
            scores.append(
                {
                    "dimension": dim,
                    "group": name,
                    "supported": bool(len(p) >= 50 and counts.sum() >= 5000),
                    "views": {v: metrics(p, counts, v) for v in ["pa", "player"]},
                }
            )
        environments = (
            history.filter(pl.col("modeling_eligible"))
            .with_columns(pl.col("level_group").str.to_uppercase())
            .group_by("season", "level_group")
            .agg(pl.col(o).sum() for o in OUTCOMES)
            .sort("season", "level_group")
            .to_dicts()
        )
        for row in environments:
            total = sum(row[o] for o in OUTCOMES)
            row["pa"] = total
            row["woba"] = (
                sum(row[o] * WEIGHTS[i] for i, o in enumerate(OUTCOMES)) / total
            )
        report["folds"].append(
            {"year": year, "groups": scores, "predictor_environments": environments}
        )
    output = ROOT / "docs/hitter-v2-transport-diagnosis.json"
    output.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    for fold in report["folds"]:
        print(fold["year"])
        for g in fold["groups"]:
            if g["dimension"] in ["all", "movement", "same_level_origin"]:
                m = g["views"]["pa"]
                print(
                    g["dimension"],
                    g["group"],
                    m["players"],
                    {
                        k: round(m[k], 5)
                        for k in ["rmse", "bias", "slope"]
                        if m[k] is not None
                    },
                )


if __name__ == "__main__":
    main()
