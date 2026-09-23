"""A small predeclared minor-league availability screen; no production changes."""
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

OLD = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated")
S1 = OLD/"affiliated-skill-source-2018-2022/tables/affiliated_hitting_components.parquet"
S2 = OLD/"affiliated-skill-source/tables/affiliated_hitting_components.parquet"
FIELD = OLD/"position-capacity-source/historical/reports/generated/position-role-historical-source/tables/historical_fielding_usage.parquet"
BASE = Path("reports/generated/multiyear-hitter-v1")
OUT = Path("model_artifacts/milb-durability-pilot-v1-2026-09-22")
LEVELS = ["AAA", "AA", "HIGH_A", "SINGLE_A"]
POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]


def build_cohort(stats, fielding, panel, targets):
    if stats["season"].max() > 2024 or fielding["season"].max() > 2024 or targets["season"].max() > 2025:
        raise ValueError("Outside frozen pilot window")
    counts = ["plate_appearances", "at_bats", "hits", "doubles", "triples", "home_runs", "base_on_balls", "hit_by_pitch", "sac_flies"]
    total = stats.group_by("season", "player_id").agg(pl.col("plate_appearances").sum().alias("all_pa"))
    annual = stats.filter(pl.col("level_group").is_in(LEVELS)).group_by("season", "player_id", "level_group").agg(
        *[pl.col(c).sum() for c in counts]).join(total, on=["season", "player_id"], validate="m:1").with_columns(
        ((pl.col("hits")+pl.col("base_on_balls")+pl.col("hit_by_pitch")) /
         (pl.col("at_bats")+pl.col("base_on_balls")+pl.col("hit_by_pitch")+pl.col("sac_flies")).clip(lower_bound=1)
         +(pl.col("hits")+pl.col("doubles")+2*pl.col("triples")+3*pl.col("home_runs"))/pl.col("at_bats").clip(lower_bound=1)).alias("ops"))
    pos = fielding.filter(pl.col("position_abbreviation").is_in(POSITIONS)).group_by(
        "season", "player_id", "level_group", "position_abbreviation").agg(pl.col("games_played").sum(), pl.col("fielding_outs").sum()).sort(
        ["season", "player_id", "level_group", "games_played", "fielding_outs", "position_abbreviation"],
        descending=[False, False, False, True, True, False]).unique(["season", "player_id", "level_group"], keep="first", maintain_order=True).select(
            "season", "player_id", "level_group", "position_abbreviation")
    annual = annual.join(pos, on=["season", "player_id", "level_group"], how="left", validate="1:1")
    peers = annual.filter(pl.col("plate_appearances") >= 100)
    refs = peers.group_by("season", "level_group", "position_abbreviation").agg(pl.len().alias("n"),
        pl.col("plate_appearances").quantile(.75, interpolation="linear").alias("position_ref"))
    pooled = peers.group_by("season", "level_group").agg(pl.col("plate_appearances").quantile(.75, interpolation="linear").alias("pooled_ref"),
        pl.col("ops").quantile(.67, interpolation="linear").alias("good_ops"))
    annual = annual.join(refs, on=["season", "level_group", "position_abbreviation"], how="left", validate="m:1").join(
        pooled, on=["season", "level_group"], validate="m:1").with_columns(
            pl.when(pl.col("n") >= 20).then(pl.col("position_ref")).otherwise(pl.col("pooled_ref")).alias("ref"))
    eligible = annual.filter((pl.col("plate_appearances") >= 100) & (pl.col("plate_appearances") == pl.col("all_pa"))
        & pl.col("position_abbreviation").is_not_null()).with_columns(
            (1-pl.col("plate_appearances")/pl.col("ref")).clip(lower_bound=0).alias("gap"))
    prior = eligible.select((pl.col("season")+1).alias("season"), "player_id", "level_group",
        pl.col("ref").alias("prior_ref"), pl.col("gap").alias("prior_gap"))
    paired = eligible.join(prior, on=["season", "player_id", "level_group"], validate="1:1").rename({"season": "origin_year"}).with_columns(
        (pl.col("ops") >= pl.col("good_ops")).alias("productive"), pl.min_horizontal("gap", "prior_gap").alias("repeated_gap"),
        *[(pl.col("position_abbreviation") == p).cast(pl.Float64).alias("pos_"+p) for p in POSITIONS])
    first_mlb = targets.filter(pl.col("mlb_pa") > 0).group_by("player_id").agg(pl.col("season").min().alias("first_mlb"))
    paired = paired.join(first_mlb, on="player_id", how="left", validate="m:1").filter(
        pl.col("first_mlb").is_null() | (pl.col("first_mlb") > pl.col("origin_year"))).drop("first_mlb")
    return panel.join(paired.select("origin_year", "player_id", "position_abbreviation", "level_group", "productive", "ref", "prior_ref",
        "gap", "prior_gap", "repeated_gap", *["pos_"+p for p in POSITIONS]), on=["origin_year", "player_id"], validate="1:1").sort("origin_year", "player_id")


def mean_year(frame, col):
    return float(np.mean([f[col].to_numpy().mean() for f in frame.sort("origin_year", "player_id").partition_by("origin_year", maintain_order=True)]))


def main():
    paths = [S1, S2, FIELD, BASE/"panel.parquet", BASE/"targets.parquet", BASE/"manifest.json",
        Path("docs/milb-durability-pilot-v1.md"), Path(__file__).relative_to(Path.cwd()),
        Path("src/universal_baseball/multiyear_hitter_followup.py")]
    hashes = {str(p): sha256_file(p) for p in paths}
    stats = pl.concat([pl.read_parquet(S1).filter(pl.col("season").is_between(2021, 2022)),
        pl.read_parquet(S2).filter(pl.col("season").is_between(2023, 2024))], how="vertical_relaxed")
    panel = pl.read_parquet(BASE/"panel.parquet").filter(pl.col("origin_year").is_between(2022, 2024))
    cohort = build_cohort(stats, pl.read_parquet(FIELD), panel, pl.read_parquet(BASE/"targets.parquet"))
    columns = json.loads((BASE/"manifest.json").read_text())["full_features"]+ ["pos_"+p for p in POSITIONS]+["ref", "prior_ref"]
    notes, predictions = [], []
    for year in (2023, 2024):
        train = cohort.filter(pl.col("origin_year")+1 <= year)
        test = cohort.filter(pl.col("origin_year") == year)
        for target, threshold in (("arrival", 1), ("mlb_200pa", 200)):
            label = (train["pa_h1"].to_numpy() >= threshold).astype(int)
            note = {"origin": year, "target": target, "training_rows": train.height, "training_events": int(label.sum()),
                    "test_rows": test.height, "latest_training_label": int(train["origin_year"].max())+1}
            if len(np.unique(label)) < 2:
                notes.append({**note, "status": "unsupported_one_class"})
                continue
            f = test.select("origin_year", "player_id", "level_group", "position_abbreviation", "productive", "repeated_gap", "pa_h1").with_columns(
                pl.lit(target).alias("target"), (pl.col("pa_h1") >= threshold).cast(pl.Float64).alias("actual"))
            for form, features in (("base", columns), ("gap", columns+["gap", "prior_gap", "repeated_gap"])):
                model = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(),
                                      LogisticRegression(C=.1, max_iter=2000, random_state=417))
                model.fit(train.select(features).to_numpy(), label)
                prob = model.predict_proba(test.select(features).to_numpy())[:, 1]
                actual = f["actual"].to_numpy()
                clipped = np.clip(prob, 1e-8, 1-1e-8)
                f = f.with_columns(pl.Series(form+"_p", prob), pl.Series(form+"_brier", (prob-actual)**2),
                    pl.Series(form+"_log", -(actual*np.log(clipped)+(1-actual)*np.log1p(-clipped))))
            predictions.append(f)
            notes.append({**note, "status": "scored"})
    if not predictions:
        raise ValueError("No supported pilot fits")
    predictions = pl.concat(predictions).sort("target", "origin_year", "player_id")
    results = {}
    for target in ("arrival", "mlb_200pa"):
        results[target] = {}
        for group in ("all", "productive"):
            f = predictions.filter(pl.col("target") == target)
            if group == "productive":
                f = f.filter(pl.col("productive"))
            if f.is_empty():
                continue
            result = {"rows": f.height, "players": f["player_id"].n_unique(), "events": int(f["actual"].sum()),
                "by_origin": f.group_by("origin_year").agg(pl.len().alias("rows"), pl.col("actual").sum().alias("events")).sort("origin_year").to_dicts(),
                "metrics": {form: {metric: mean_year(f, form+"_"+metric) for metric in ("brier", "log")} for form in ("base", "gap")},
                "paired": {metric: compare_losses(f, "gap_"+metric, "base_"+metric) for metric in ("brier", "log")}}
            results[target][group] = result
    primary = results["arrival"]["productive"]["paired"]
    promising = all(r["improving_origins"] == 2 and r["interval95"][1] < 0 for r in primary.values())
    report = {"status": "promising_pilot_only" if promising else "no_demonstrated_incremental_gain", "forecast_changed": False,
        "protected_outcomes_used": False, "support": notes, "results": results,
        "limitations": ["Same-level full-season minor leaguers only", "No verified full-year roster tenure", "No diagnosis or career-survival conclusion",
            "Unadjusted level-relative OPS", "Two forward tests only", "Below-100-PA injury spells excluded"]}
    assert all(sha256_file(Path(p)) == digest for p, digest in hashes.items())
    OUT.mkdir(parents=True, exist_ok=True)
    cohort.select("origin_year", "player_id", "level_group", "position_abbreviation", "productive", "ref", "prior_ref", "gap", "prior_gap", "repeated_gap", "pa_h1").write_parquet(OUT/"cohort.parquet")
    predictions.write_parquet(OUT/"predictions.parquet")
    (OUT/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    manifest = {"sources": hashes, "files": {name: sha256_file(OUT/name) for name in ("cohort.parquet", "predictions.parquet", "report.json")}}
    (OUT/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
