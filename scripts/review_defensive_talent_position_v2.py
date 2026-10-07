"""Independent reconstruction, saved-fit replay and deterministic player/peer walks."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.defensive_talent_position import origin_context, label, matrix, person_weights, preflight
from universal_baseball.minor_infield_play_share import pooled
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify, FIXED
from run_hitter_finite_return_baseline import protections, save
from fit_defensive_talent_position_v2 import scores

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports/generated/defensive-talent-position-v2/qualified"
OUT = DATA / "comparison"
PUBLIC = ROOT / "reports/model-evidence/defensive-talent-position-v2/comparison"


def main():
    protections()
    report = json.loads((OUT / "report.json").read_text(encoding="utf8"))
    source_final = json.loads((DATA / "source-final-review.json").read_text(encoding="utf8"))
    verify(report["hashes"]); verify(source_final["hashes"])
    assert not (OUT / "review-checks.json").exists()
    q = pl.read_parquet(OUT / "predictions.parquet")
    origins = pl.read_parquet(DATA / "origins.parquet")
    labels = pl.read_parquet(DATA / "labels.parquet")
    minor = pl.read_parquet(ROOT / "reports/generated/minor-infield-play-share/annual.parquet")
    raw_origins = pl.read_parquet(ROOT / "reports/generated/defensive-talent-support/origins.parquet")
    native_frame = pl.read_parquet(DATA / "annual.parquet")
    bio = {r["player_id"]: r for r in pl.read_parquet(DATA / "identity.parquet").to_dicts()}
    from collections import defaultdict
    native, minor_by_key = defaultdict(dict), defaultdict(list)
    for r in native_frame.to_dicts():
        native[r["player_id"], r["position"]][r["season"]] = r
    for r in minor.to_dicts():
        minor_by_key[r["player_id"], r["position"]].append(r)
    audit = json.loads((ROOT / "reports/generated/multiyear-hitter-components-v1/source-audit.json").read_text(encoding="utf8"))
    usage_frame = pl.read_parquet(audit["mlb_fielding"]["path"]).group_by("season", "player_id", "position_code").agg(pl.col("fielding_outs").sum())
    official = {(r["season"], r["player_id"], int(r["position_code"])): r["fielding_outs"] for r in usage_frame.to_dicts() if r["position_code"].isdigit()}
    key = lambda r: (r["origin_year"], r["player_id"], r["position"])
    o = {key(r): r for r in origins.to_dicts()}
    ls = {(key(r), r["horizon"]): r for r in labels.to_dicts()}
    predictions = {key(r): r for r in q.to_dicts()}
    fits = json.loads((OUT / "fits.json").read_text(encoding="utf8"))
    models = {(r["origin"], r["fold"], r["arm"]): r for r in fits}
    replayed = 0
    for year in sorted(origins["origin_year"].unique()):
        pool = pooled(minor, year).filter(pl.col("ground_balls") >= 25)
        rows = origins.filter(pl.col("origin_year") == year)
        assert set(pool.select("player_id", "position").rows()) == set(rows.select("player_id", "position").rows())
        matched = pool.join(rows, on=["player_id", "position"], suffix="_saved")
        for c in ("ground_balls", "credits", "touches", "expected_credits", "complete_rate"):
            assert matched.select((pl.col(c) - pl.col(c + "_saved")).abs().max()).item() < 1e-8
    for original in raw_origins.to_dicts():
        reconstructed = origin_context(original, minor_by_key, bio, native, official)
        assert reconstructed == o[key(original)]
        for horizon in (3, 5, 7):
            computed, _ = label(reconstructed, horizon, native, official)
            assert computed == ls[key(original), horizon]
    pre = json.loads((OUT / "fit-preflight.json").read_text(encoding="utf8"))
    label3 = labels.filter(pl.col("horizon") == 3).to_dicts()
    range_checks = []
    for c in pre["folds"]:
        year, fold = c["origin"], c["fold"]
        train = [r for r in label3 if r["window_end"] <= year and r["origin_year"] < year and r["player_id"] % 5 != fold and r["quality_rate"] is not None]
        test = [r for r in label3 if r["origin_year"] == year and r["player_id"] % 5 == fold]
        check, support = preflight(train, test, year, fold, 3)
        assert c == check
        if year not in pre["allowed_origins"]:
            continue
        for arm in ("baseline", "raw_share", "candidate"):
            f = models[year, fold, arm]
            assert f["training_keys"] == [list(key(r)) for r in train]
            estimated = matrix(test, f["features"]) @ f["coefficient"] + f["intercept"]
            assert np.allclose(estimated, [predictions[key(r)][arm] for r in test], atol=1e-10)
            # Independently solve the weighted ridge normal equations.
            x = (matrix(train, f["features"]) - f["scaler_mean"]) / f["scaler_scale"]
            w = person_weights(train); target = np.array([r["quality_rate"] for r in train])
            design = np.column_stack([np.ones(len(train)), x])
            penalty = np.diag([0., *([100.] * x.shape[1])])
            beta = np.linalg.solve(design.T @ (w[:, None] * design) + penalty, design.T @ (w * target))
            independent = np.column_stack([np.ones(len(test)), (matrix(test, f["features"]) - f["scaler_mean"]) / f["scaler_scale"]]) @ beta
            assert np.allclose(independent, estimated, atol=1e-8)
            replayed += len(test)
        ranges = {field: (min(r[field] for r in train), max(r[field] for r in train)) for field in ("age", "ground_balls", "complete_rate", "prior_rate")}
        range_checks.append(dict(origin=year, fold=fold, ranges=ranges,
                                 outside_measured={field: sum(not low <= r[field] <= high for r in test if r["quality_rate"] is not None) for field, (low, high) in ranges.items()}))
    for year, score in report["origins"].items():
        assert scores([r for r in q.to_dicts() if r["origin_year"] == int(year) and r["quality_rate"] is not None]) == score
    selected = {}
    def add(r, category):
        selected.setdefault(key(r), []).append(category)
    for pid, year in FIXED + [(678662, 2019), (678662, 2021), (678662, 2022), (677951, 2022), (622761, 2021)]:
        available = [r for r in o.values() if r["player_id"] == pid and r["origin_year"] == year]
        if available:
            add(max(available, key=lambda r: (r["ground_balls"], -r["position"])), "fixed_before_fit")
    measured = [r for r in q.to_dicts() if r["origin_year"] == 2022 and r["quality_rate"] is not None]
    tie = lambda r: (r["player_id"], r["position"])
    improvement = lambda r: (r["baseline"] - r["quality_rate"]) ** 2 - (r["candidate"] - r["quality_rate"]) ** 2
    add(sorted(measured, key=lambda r: (-improvement(r), *tie(r)))[0], "largest_improvement_2022")
    add(sorted(measured, key=lambda r: (improvement(r), *tie(r)))[0], "largest_deterioration_2022")
    add(sorted(measured, key=lambda r: (-(r["candidate"] - r["quality_rate"]), *tie(r)))[0], "largest_false_high_2022")
    add(sorted(measured, key=lambda r: ((r["candidate"] - r["quality_rate"]), *tie(r)))[0], "largest_false_low_2022")
    ordinary = sorted(measured, key=lambda r: (abs(r["candidate"] - r["quality_rate"]), *tie(r)))[len(measured) // 2]
    add(ordinary, "median_absolute_error_2022")
    # Input-selected DSL cases from the preceding audit, not outcome-selected failures.
    for pid in (664331, 666695, 665846):
        if (2016, pid, 6) in o:
            add(o[2016, pid, 6], "prior_input_selected_dsl")
    walks = []
    def trace(r):
        record = ls[key(r), 3]
        value = predictions.get(key(r))
        fixed_probe = None
        contributions = None
        if value:
            f = models[r["origin_year"], r["player_id"] % 5, "candidate"]
            contributions = {field: r[field] * coefficient for field, coefficient in zip(f["features"], f["coefficient"])}
            assert np.isclose(sum(contributions.values()) + f["intercept"], value["candidate"])
            fixed_probe = dict(signal_coefficient=f["coefficient"][-1], direct_signal_contribution=contributions["complete_rate"],
                               candidate_if_signal_set_zero=value["candidate"] - contributions["complete_rate"],
                               explanation="Fixed-fit diagnostic, not a new model or causal player forecast")
        _, future = label(r, 3, native, official)
        return dict(inputs=r, prediction=value, label=record, future_path=future,
                    minor_source=[x for x in minor_by_key[r["player_id"], r["position"]] if r["origin_year"] - 2 <= x["season"] <= r["origin_year"]],
                    prior_range_source=[x for x in native[r["player_id"], r["position"]].values() if r["origin_year"] - 2 <= x["season"] <= r["origin_year"]],
                    fixed_fit_probe=fixed_probe, contributions=contributions,
                    unscored_reason=None if record["quality_rate"] is not None else record["quality_status"],
                    unavailable_forecast_reason=None if value else "origin_not_in_supported_mature_comparison")
    for k, categories in selected.items():
        r = o[k]
        peers = [x for x in o.values() if x["origin_year"] == r["origin_year"] and x["position"] == r["position"] and x["player_id"] != r["player_id"]
                 and x["fielding_level"] == r["fielding_level"] and x["prior_mlb_defense"] == r["prior_mlb_defense"]]
        peers.sort(key=lambda x: (abs(x["age"] - r["age"]), abs(x["ground_balls"] - r["ground_balls"]), x["player_id"]))
        walks.append(dict(categories=categories, focal=trace(r), peers=[trace(x) for x in peers[:3]],
                          peer_selection="same origin/position/current fielding level/prior MLB fielding; nearest age then exposure then ID; no outcomes"))
    save(OUT / "player-walkthrough.json", walks)
    checks = dict(origin_replays=origins.height, label_replays=labels.height, prediction_replays=replayed,
                  independent_ridge_replays=len(fits), scores_and_cluster_uncertainty_replayed=True,
                  profile_preflights_replayed=len(pre["folds"]), range_support=range_checks,
                  reviewed_focal_cases=len(walks), production_changed=False, additional_2026_data_ingested_or_used=False,
                  hashes={str(p): sha256_file(p) for p in [Path(__file__), OUT / "player-walkthrough.json", OUT / "report.json"]})
    save(OUT / "review-checks.json", checks)
    save(PUBLIC / "review-checks.json", checks)
    save(PUBLIC / "player-case-manifest.json", [dict(categories=w["categories"], player_id=w["focal"]["inputs"]["player_id"], player_name=w["focal"]["inputs"]["player_name"], origin=w["focal"]["inputs"]["origin_year"], position=w["focal"]["inputs"]["position"], peer_ids=[x["inputs"]["player_id"] for x in w["peers"]]) for w in walks])
    protections()
    print(json.dumps([{ "categories": w["categories"], "name": w["focal"]["inputs"]["player_name"], "origin": w["focal"]["inputs"]["origin_year"],
                       "position": w["focal"]["inputs"]["position"], "gb": w["focal"]["inputs"]["ground_balls"],
                       "signal": w["focal"]["inputs"]["complete_rate"],
                       "baseline": w["focal"]["prediction"]["baseline"] if w["focal"]["prediction"] else None,
                       "candidate": w["focal"]["prediction"]["candidate"] if w["focal"]["prediction"] else None,
                       "quality": w["focal"]["label"]["quality_rate"],
                       "probe": w["focal"]["fixed_fit_probe"],
                       "peers": [(p["inputs"]["player_name"], p["label"]["quality_rate"]) for p in w["peers"]] } for w in walks], indent=2))


if __name__ == "__main__":
    main()
