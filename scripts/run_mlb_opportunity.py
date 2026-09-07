"""Run the predeclared O2026D opportunity benchmark; no protected outcomes."""

from pathlib import Path
import sys
import json
from hashlib import sha256

import numpy as np
import polars as pl
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
# ruff: noqa: E402
from universal_baseball.mlb_opportunity import (
    project_pages,
    certify_participation,
    build_cohort,
    label_cohort,
    predict_opportunity,
)

BASE = ROOT / "reports/generated"
OUTPUT = BASE / "hitter-v2-O2026D-unfiltered"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def fetch_participation(year):
    if year not in (2021, 2022, 2023, 2024):
        raise ValueError("Only declared development seasons are allowed")
    frames, captures = [], []
    for league in (None, 103, 104):
        offset, pages = 0, []
        while True:
            params = dict(
                stats="season",
                group="hitting",
                season=year,
                sportIds=1,
                playerPool="ALL",
                gameType="R",
                limit=500,
                offset=offset,
            )
            if league:
                params["leagueId"] = league
            path = OUTPUT / "sources" / f"{year}_{league or 'MLB'}_{offset}.json"
            if not path.exists():
                response = requests.get(
                    "https://statsapi.mlb.com/api/v1/stats", params=params, timeout=45
                )
                response.raise_for_status()
                path.write_bytes(response.content)
            payload = json.loads(path.read_bytes())
            pages.append(payload)
            captures.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": digest(path),
                    "params": params,
                }
            )
            groups = payload.get("stats", [])
            if len(groups) != 1:
                raise ValueError("Invalid stats response")
            group = groups[0]
            total = group.get("totalSplits")
            count = len(group.get("splits", []))
            if not isinstance(total, int) or not count:
                raise ValueError("Invalid pagination")
            offset += count
            if offset >= total:
                break
            if offset > 5000:
                raise ValueError("Pagination overflow")
        frames.append(project_pages(pages, year))
    certified = certify_participation(*frames)
    certified.write_parquet(OUTPUT / "sources" / f"{year}_certified.parquet")
    return certified, {
        "year": year,
        "players": certified.height,
        "positive_pa_players": certified.filter(pl.col("mlb_pa") > 0).height,
        "total_pa": certified["mlb_pa"].sum(),
        "mlb_equals_al_plus_nl": True,
        "captures": captures,
    }


def score(frame, model):
    result = {"players": frame.height, "observed_pa": frame["mlb_pa"].sum()}
    for target in ("any_pa", "pa100"):
        y = frame[target].to_numpy()
        p = frame[f"{model}_{target}"].to_numpy()
        q = np.clip(p, 1e-6, 1 - 1e-6)
        result[target] = dict(
            observed=float(y.mean()),
            predicted=float(p.mean()),
            brier=float(np.mean((p - y) ** 2)),
            log_loss=float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
        )
    error = frame[f"{model}_mlb_pa"].to_numpy() - frame["mlb_pa"].to_numpy()
    result["pa"] = dict(
        mae=float(np.mean(abs(error))),
        rmse=float(np.sqrt(np.mean(error**2))),
        bias=float(error.mean()),
    )
    return result


def summarize(frame):
    groups = {
        "all": frame,
        "no_prior_MLB_PA": frame.filter(pl.col("prior_mlb_pa") == 0),
        "prior_MLB_PA": frame.filter(pl.col("prior_mlb_pa") > 0),
        "no_ability_forecast": frame.filter(~pl.col("has_ability_forecast")),
    }
    groups.update({f"origin_{key[0]}": g for key, g in frame.group_by("origin")})
    result = {
        key: {model: score(g, model) for model in ("REFERENCE", "LEVEL")}
        for key, g in groups.items()
        if g.height
    }
    calibration = []
    for model in ("REFERENCE", "LEVEL"):
        for lower, upper in zip(
            (0, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75),
            (0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.01),
        ):
            g = frame.filter(
                (pl.col(f"{model}_any_pa") >= lower)
                & (pl.col(f"{model}_any_pa") < upper)
            )
            if g.height:
                calibration.append(
                    {
                        "model": model,
                        "lower": lower,
                        "upper": upper,
                        **score(g, model)["any_pa"],
                        "players": g.height,
                    }
                )
    return {"groups": result, "calibration": calibration}


def main():
    if (OUTPUT / "report.json").exists():
        raise ValueError("Do not overwrite a completed experiment")
    (OUTPUT / "sources").mkdir(parents=True, exist_ok=True)
    contract = ROOT / "docs/hitter-v2-O2026D-contract.md"
    report = {
        "status": "development_benchmark",
        "protected_2026_opened": False,
        "release_ready": False,
        "contract_sha256": digest(contract),
        "sources": [],
        "folds": [],
    }
    previous, metadata = fetch_participation(2021)
    report["sources"].append(metadata)
    past, evaluated = [], []
    for year in (2022, 2023, 2024):
        hp = (
            BASE
            / "hitter-v2-stage1-universal/tables/hitter_v2_player_season_outcomes_2021_2023.parquet"
        )
        ap = (
            BASE
            / f"hitter-v2-gap-aware-G0-fit/tables/v{year}/g0_unscored_predictions.parquet"
        )
        history = pl.read_parquet(hp).filter(pl.col("season") < year)
        cohort = build_cohort(history, previous, year)
        ability_ids = pl.read_parquet(ap)["player_id"].to_list()
        cohort = cohort.with_columns(
            pl.col("player_id").is_in(ability_ids).alias("has_ability_forecast")
        )
        cp = OUTPUT / f"{year}_cohort.parquet"
        cohort.write_parquet(cp)
        fold = {
            "year": year,
            "cohort_players": cohort.height,
            "cohort_sha256": digest(cp),
            "history_sha256": digest(hp),
            "ability_population_sha256": digest(ap),
            "players_without_ability_forecast": cohort.filter(
                ~pl.col("has_ability_forecast")
            ).height,
        }
        if past:
            predictions, parameters = predict_opportunity(pl.concat(past), cohort)
            pp = OUTPUT / f"{year}_predictions.parquet"
            predictions.write_parquet(pp)
            fold.update(predictions_sha256=digest(pp), parameters=parameters)
        current, metadata = fetch_participation(year)
        report["sources"].append(metadata)
        labeled = label_cohort(cohort, current)
        labeled.write_parquet(OUTPUT / f"{year}_labels.parquet")
        fold["zero_pa_players"] = labeled.filter(pl.col("mlb_pa") == 0).height
        outside = current.filter(pl.col("mlb_pa") > 0).join(
            cohort.select("player_id"), on="player_id", how="anti"
        )
        fold["MLB_participants_outside_cohort"] = outside.height
        fold["MLB_PA_outside_cohort"] = outside["mlb_pa"].sum()
        if past:
            scored = label_cohort(predictions, current)
            fold["evaluation"] = summarize(scored)
            evaluated.append(scored)
        else:
            fold["status"] = "training_warmup_only"
        report["folds"].append(fold)
        past.append(labeled)
        previous = current
    pooled = pl.concat(evaluated)
    report["pooled"] = summarize(pooled)
    cluster = (
        pooled.with_columns(
            (
                (pl.col("LEVEL_any_pa") - pl.col("any_pa")) ** 2
                - (pl.col("REFERENCE_any_pa") - pl.col("any_pa")) ** 2
            ).alias("delta")
        )
        .group_by("player_id")
        .agg(pl.col("delta").sum(), pl.len().alias("n"))
    )
    rng = np.random.default_rng(260906)
    deltas, ns = cluster["delta"].to_numpy(), cluster["n"].to_numpy()
    draws = []
    for _ in range(1000):
        index = rng.integers(0, cluster.height, cluster.height)
        draws.append(float(deltas[index].sum() / ns[index].sum()))
    report["paired_player_cluster_brier_delta"] = {
        "unique_players": cluster.height,
        "draws": 1000,
        "seed": 260906,
        "mean": float(deltas.sum() / ns.sum()),
        "interval95": np.quantile(draws, [0.025, 0.975]).tolist(),
    }
    scores = report["pooled"]["groups"]["all"]
    report["level_adds_benchmark_value"] = bool(
        scores["LEVEL"]["any_pa"]["brier"] < scores["REFERENCE"]["any_pa"]["brier"]
        and all(
            f["evaluation"]["groups"]["all"]["LEVEL"]["any_pa"]["brier"]
            <= 1.02 * f["evaluation"]["groups"]["all"]["REFERENCE"]["any_pa"]["brier"]
            for f in report["folds"]
            if "evaluation" in f
        )
    )
    content = json.dumps(report, indent=2) + "\n"
    (OUTPUT / "report.json").write_text(content, encoding="utf-8")
    (ROOT / "docs/hitter-v2-O2026D-result.json").write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {
                "folds": [
                    {
                        k: v
                        for k, v in f.items()
                        if k not in ("parameters", "evaluation")
                    }
                    for f in report["folds"]
                ],
                "pooled": scores,
                "adds_value": report["level_adds_benchmark_value"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
