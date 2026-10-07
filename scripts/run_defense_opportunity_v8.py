"""One locked exposure comparison; saved support, means, forecasts and walks."""

from collections import defaultdict
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.defense_opportunity_bridge import (
    CHANNELS, POSITIONS, ROLES, MIN_PEOPLE, MIN_EFFECTIVE, role_mix,
    support_tables, fit_tables, sufficient, predict, native_conversion, native_from_outs,
)
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/generated/defense-position-opportunity-v7"
OUT = ROOT / "reports/generated/defense-opportunity-v8"
PUBLIC = ROOT / "reports/model-evidence/defense-opportunity-v8"
ORIGINS = (2022, 2023, 2024)
FIXED = [(662139, 2022), (605141, 2023), (656941, 2023),
         (682829, 2022), (682626, 2022), (805811, 2024)]


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def write(name, data):
    save(OUT / name, data)
    save(PUBLIC / name, data)


def verify(hashes):
    for p, h in hashes.items():
        assert sha256_file(Path(p)) == h, p


def native_exposure(pos, channel):
    return int(pos.get(2, 0)) if channel in ("framing", "throwing", "blocking") else (
        sum(int(pos.get(p, 0)) for p in (7, 8, 9)) if channel == "arm" else int(pos.get(3, 0)))


def native_records(source, paths):
    official = defaultdict(lambda: defaultdict(int))
    for r in source.filter(pl.col("is_mlb")).iter_rows(named=True):
        official[r["season"], r["player_id"]][int(r["position_code"])] += r["fielding_outs"]
    native_paths = [ROOT / "reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet",
                    ROOT / "reports/generated/catcher-throw-block-v5/extension-annual.parquet",
                    ROOT / "reports/generated/arm-receiving-v6/official-scope/annual.parquet"]
    paths.extend(native_paths)
    out = []
    for path in native_paths:
        for r in pl.read_parquet(path).iter_rows(named=True):
            if "pitches" in r:
                channel, opportunities = "framing", r["pitches"]
                valid = r["exposure_valid"] and r["framing_measurement_valid"]
            elif "component" in r:
                channel, opportunities = r["component"], r["opportunities"]
                valid = r["exposure_valid"] and r["measurement_valid"]
            else:
                channel, opportunities = r["kind"], r["opportunities"]
                valid = r["isolated_outfield_quality_valid"] if channel == "arm" else r["quality_valid"]
            assert channel in CHANNELS and r["season"] <= 2025
            exposure = native_exposure(official[r["season"], r["player_id"]], channel)
            out.append(dict(channel=channel, season=int(r["season"]), player_id=int(r["player_id"]),
                player_name=r["player_name"], opportunities=opportunities, official_exposure=exposure,
                valid=bool(valid) and exposure > 0 and opportunities is not None and opportunities >= 0,
                source_path=str(path), source_valid=bool(valid), origin_fold=player_fold(r["player_id"])))
    keys = [(r["channel"], r["season"], r["player_id"]) for r in out]
    assert len(keys) == len(set(keys))
    return out, official


def choose_native_rows(records, y, k):
    selected = [r for r in records if r["valid"] and r["origin_fold"] != k and y - 2 <= r["season"] <= y]
    fallback = len({r["player_id"] for r in selected}) < 20 or len({r["season"] for r in selected}) < 2
    if fallback:
        selected = [r for r in records if r["valid"] and r["origin_fold"] != k and r["season"] <= y]
    assert len({r["player_id"] for r in selected}) >= 20 and len({r["season"] for r in selected}) >= 2
    return selected, fallback


def prepare():
    protections()
    assert not (OUT / "preflight.json").exists()
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    previous = read(SOURCE / "independent-source-verification.json")
    assert previous["source_preparation_complete"] and previous["player_walkthrough_status"] == "complete"
    verify(previous["hashes"])
    source_seal = read(SOURCE / "source-review.json")
    verify(source_seal["input_hashes"])
    verify(source_seal["output_hashes"])
    paths = [Path(__file__), ROOT / "src/universal_baseball/defense_opportunity_bridge.py",
             ROOT / "tests/test_defense_opportunity_bridge.py", ROOT / "docs/defense-opportunity-v8-contract.md",
             SOURCE / "source.parquet", SOURCE / "origin-context.parquet", SOURCE / "exposure-labels.parquet",
             SOURCE / "independent-source-verification.json", SOURCE / "cohort-coverage-review.json"]
    contexts = pl.read_parquet(SOURCE / "origin-context.parquet")
    labels = pl.read_parquet(SOURCE / "exposure-labels.parquet")
    source = pl.read_parquet(SOURCE / "source.parquet")
    panel_path = ROOT / "reports/generated/hitter-preseason-readiness-v68/predictions.parquet"
    paths.append(panel_path)
    pa = pl.read_parquet(panel_path, columns=["row_id", "player_id", "pa_0"])
    contexts = contexts.join(pa, on=["row_id", "player_id"], how="left", validate="1:1")
    assert contexts.height == 30506 and contexts["pa_0"].null_count() == 0
    assert (contexts["target_year"] <= 2025).all() and (contexts["preseason_pa"] >= 0).all()
    native, official = native_records(source, paths)
    pl.DataFrame(native, infer_schema_length=None).write_parquet(OUT / "opportunity-records.parquet")
    native_index = {(r["channel"], r["season"], r["player_id"]): r for r in native}
    role_labels = {r["row_id"]: r for r in labels.iter_rows(named=True)}
    features = []
    dh_starts = defaultdict(int)
    for s in source.filter(pl.col("is_mlb") & (pl.col("position_code") == "10")).iter_rows(named=True):
        dh_starts[s["season"], s["player_id"]] += s["games_started"]
    for r in contexts.iter_rows(named=True):
        shares, kind = role_mix(r)
        target = [role_labels[r["row_id"]][f"actual_outs_{p}"] for p in POSITIONS] + [dh_starts[r["target_year"], r["player_id"]]]
        origin = [official[r["origin_year"], r["player_id"]].get(p, 0) for p in POSITIONS] + [dh_starts[r["origin_year"], r["player_id"]]]
        r.update(bridge_role_shares=shares, bridge_role_kind=kind)
        for p, a, b in zip(ROLES, target, origin):
            r[f"actual_{p}"], r[f"carry_{p}"] = a, b
        for channel in CHANNELS:
            measured = native_index.get((channel, r["target_year"], r["player_id"]))
            exposure = native_exposure(official[r["target_year"], r["player_id"]], channel)
            if measured and measured["valid"]:
                actual, reason = float(measured["opportunities"]), "measured_native"
            elif exposure == 0 and not (measured and measured["opportunities"] and measured["opportunities"] > 0):
                actual, reason = 0., "no_corresponding_defense"
            else:
                actual, reason = None, "unmeasured_positive_position_or_scope_conflict"
            origin_n = native_index.get((channel, r["origin_year"], r["player_id"]))
            prior = float(origin_n["opportunities"]) if origin_n and origin_n["valid"] else 0.
            r[f"actual_native_{channel}"] = actual
            r[f"native_label_{channel}"] = reason
            r[f"carry_native_{channel}"] = prior
            r[f"origin_native_observed_{channel}"] = bool(origin_n and origin_n["valid"])
            factor = r["preseason_pa"] / r["pa_0"] if r["pa_0"] > 0 else 1.
            r[f"legacy_native_{channel}"] = prior * (.5 + .5 * factor) if channel in ("throwing", "blocking") else prior
        features.append(r)
    frame = pl.DataFrame(features, infer_schema_length=None)
    frame.write_parquet(OUT / "features.parquet")
    checks, native_checks = [], []
    for y in ORIGINS:
        for k in range(5):
            train = frame.filter((pl.col("target_year") <= y) & (pl.col("outer_fold") != k) & (pl.col("next_pa") > 0))
            test = frame.filter((pl.col("origin_year") == y) & (pl.col("outer_fold") == k))
            assert not set(train["player_id"]) & set(test["player_id"])
            assert train["target_year"].max() <= y and test.height > 0 and train["player_id"].n_unique() >= 100
            tables = support_tables(train.to_dicts(), test.to_dicts())
            assert sufficient(tables[("all",)])
            checks.append(dict(origin=y, fold=k, training_rows=train.height, training_people=train["player_id"].n_unique(),
                test_rows=test.height, training_row_ids=train["row_id"].to_list(), test_row_ids=test["row_id"].to_list(),
                support=list(tables.values()), outcome_numerators_used=False,
                maximum_training_target_year=int(train["target_year"].max()), player_disjoint=True))
            for channel in CHANNELS:
                selected, fallback = choose_native_rows([r for r in native if r["channel"] == channel], y, k)
                native_checks.append(dict(origin=y, fold=k, channel=channel, rows=len(selected),
                    people=len({r["player_id"] for r in selected}), seasons=sorted({r["season"] for r in selected}),
                    expanded_history_fallback=fallback,
                    source_keys=[[r["season"], r["player_id"]] for r in selected],
                    held_players_excluded=True, maximum_source_year=max(r["season"] for r in selected)))
    write("preflight.json", dict(before_fitting=True, role_cells=checks, native_cells=native_checks,
        min_distinct_people=MIN_PEOPLE, min_effective_people=MIN_EFFECTIVE, origins=list(ORIGINS),
        fixed_cases=[list(p) for p in FIXED], role_sample_weights="origin role shares; conditional PA denominator",
        contextual_fit_not_started=True, protected_outcomes_used=False, all_test_players_retained=True,
        upstream_playing_time_changed=False, future_talent_not_tested_here=True,
        hash_inputs={str(p): sha256_file(p) for p in paths},
        hash_features=sha256_file(OUT / "features.parquet"), hash_opportunities=sha256_file(OUT / "opportunity-records.parquet")))
    protections()
    print(json.dumps(dict(role_folds=len(checks), native_folds=len(native_checks), feature_rows=frame.height, status="ready_before_fitting")))


def score(frame, arm):
    pred = frame.select([f"{arm}_{p}" for p in POSITIONS]).to_numpy()
    actual = frame.select([f"actual_{p}" for p in POSITIONS]).to_numpy()
    e = pred - actual
    total_error = pred.sum(axis=1) - actual.sum(axis=1)
    return dict(rows=frame.height, cell_rmse=float(np.sqrt(np.mean(e ** 2))), cell_mae=float(np.mean(abs(e))),
        total_out_rmse=float(np.sqrt(np.mean(total_error ** 2))), total_out_mae=float(np.mean(abs(total_error))),
        predicted_total_outs=float(pred.sum()), actual_total_outs=float(actual.sum()),
        dh_start_rmse=float(np.sqrt(np.mean((frame[f"{arm}_10"].to_numpy() - frame["actual_10"].to_numpy()) ** 2))),
        per_position=[dict(position=p, rmse=float(np.sqrt(np.mean(e[:, j] ** 2))), mae=float(np.mean(abs(e[:, j]))),
                           predicted=float(pred[:, j].sum()), actual=float(actual[:, j].sum())) for j, p in enumerate(POSITIONS)])


def native_score(frame, arm, channel, positive=False):
    q = frame.filter(pl.col(f"actual_native_{channel}").is_not_null())
    if positive:
        q = q.filter(pl.col(f"actual_native_{channel}") > 0)
    if q.is_empty():
        return None
    actual = q[f"actual_native_{channel}"].to_numpy()
    pred = q[f"{arm}_native_{channel}"].to_numpy()
    return dict(rows=q.height, rmse=float(np.sqrt(np.mean((pred - actual) ** 2))), mae=float(np.mean(abs(pred - actual))),
                predicted_total=float(pred.sum()), actual_total=float(actual.sum()),
                measurement_label="known_positive" if positive else "known_counts_including_certified_position_absence")


def paired_interval(frame):
    people = sorted(frame["player_id"].unique())
    person_map = {p: j for j, p in enumerate(people)}
    losses = np.zeros((len(people), len(ORIGINS), 2))
    present = np.zeros((len(people), len(ORIGINS)))
    for r in frame.iter_rows(named=True):
        i, j = person_map[r["player_id"]], ORIGINS.index(r["origin_year"])
        present[i, j] = 1
        for k, arm in enumerate(("context", "pooled")):
            losses[i, j, k] = np.mean([(r[f"{arm}_{p}"] - r[f"actual_{p}"]) ** 2 for p in POSITIONS])
    rng = np.random.default_rng(708006)
    changes = []
    for _ in range(2000):
        count = rng.multinomial(len(people), np.full(len(people), 1 / len(people)))
        den = count @ present
        rmses = np.sqrt(np.einsum("i,ijk->jk", count, losses) / den[:, None])
        changes.append(float(np.mean(rmses[:, 0] - rmses[:, 1])))
    rmses = np.sqrt(losses.sum(axis=0) / present.sum(axis=0)[:, None])
    return dict(contrast="context_minus_pooled", equal_origin_rmse_change=float(np.mean(rmses[:, 0] - rmses[:, 1])),
                interval_95=np.quantile(changes, [.025, .975]).tolist(), draws=2000, seed=708006,
                people=len(people), person_clustered=True, development_not_fresh_confirmation=True)


def fit():
    protections()
    assert not (OUT / "fit-report.json").exists(), "Preserve fitted comparison"
    pre = read(OUT / "preflight.json")
    assert pre["before_fitting"] and len(pre["role_cells"]) == 15 and len(pre["native_cells"]) == 75
    verify(pre["hash_inputs"])
    assert sha256_file(OUT / "features.parquet") == pre["hash_features"]
    assert sha256_file(OUT / "opportunity-records.parquet") == pre["hash_opportunities"]
    frame = pl.read_parquet(OUT / "features.parquet")
    native = pl.read_parquet(OUT / "opportunity-records.parquet").to_dicts()
    targets = {r["row_id"]: [r[f"actual_{p}"] for p in ROLES] for r in frame.iter_rows(named=True)}
    predictions, cells = [], []
    source = pl.read_parquet(SOURCE / "source.parquet")
    for cell in pre["role_cells"]:
        y, k = cell["origin"], cell["fold"]
        train = frame.filter(pl.col("row_id").is_in(cell["training_row_ids"]))
        test = frame.filter(pl.col("row_id").is_in(cell["test_row_ids"]))
        assert (train["target_year"] <= y).all() and not set(train["player_id"]) & set(test["player_id"])
        assert (test["outer_fold"] == k).all() and (train["outer_fold"] != k).all()
        tables = fit_tables(train.to_dicts(), test.to_dicts(), targets)
        before = {tuple(v["scope"]): v for v in cell["support"]}
        for key, fitted in tables.items():
            for field in ("people", "effective_people", "denominator_PA", "rows"):
                assert fitted[field] == before[key][field]
        conversions = {c: native_conversion([r for r in native if r["channel"] == c], y, k, player_fold) for c in CHANNELS}
        for c, calibration in conversions.items():
            check = next(v for v in pre["native_cells"] if (v["origin"], v["fold"], v["channel"]) == (y, k, c))
            assert calibration["people"] == check["people"] and calibration["seasons"] == check["seasons"]
            assert calibration["rows"] == check["rows"]
            # Expose denominator selection instead of silently treating missing
            # opportunity records as measured zero opportunity.
            denominator = 0.
            for r in source.filter(pl.col("is_mlb") & pl.col("season").is_in(calibration["seasons"])).iter_rows(named=True):
                p = int(r["position_code"])
                belongs = p == 2 if c in ("framing", "throwing", "blocking") else p in (7, 8, 9) if c == "arm" else p == 3
                if belongs and player_fold(r["player_id"]) != k:
                    denominator += r["fielding_outs"] * .5 ** (y - r["season"])
            calibration["all_corresponding_official_outs"] = denominator
            calibration["measured_out_coverage_fraction"] = calibration["official_outs"] / denominator
        model_path = OUT / f"model-{y}-{k}.json"
        save(model_path, dict(origin=y, fold=k, role_tables=list(tables.values()), conversions=conversions,
                             training_row_ids=cell["training_row_ids"], test_row_ids=cell["test_row_ids"]))
        for r in test.iter_rows(named=True):
            reference, candidate = predict(tables, r, False), predict(tables, r, True)
            r.update(pooled_trace=json.dumps(reference["trace"]), context_trace=json.dumps(candidate["trace"]),
                     contextual_coarse_mass=candidate["coarse_mass"])
            forecasts = {"pooled": reference["values"], "context": candidate["values"], "carry": [r[f"carry_{p}"] for p in ROLES]}
            forecasts["ratio"] = [r[f"carry_{p}"] * r["preseason_pa"] / r["pa_0"] for p in ROLES] if r["pa_0"] > 0 else reference["values"]
            r["ratio_fallback"] = r["pa_0"] <= 0
            for arm, values in forecasts.items():
                for p, v in zip(ROLES, values):
                    r[f"{arm}_{p}"] = float(v)
                if arm != "carry":
                    for c, v in native_from_outs(values, conversions).items():
                        r[f"{arm}_native_{c}"] = float(v)
            for arm in ("pooled", "context", "ratio", "carry"):
                r[f"{arm}_total_outs"] = sum(r[f"{arm}_{p}"] for p in POSITIONS)
                r[f"{arm}_cell_squared_error"] = float(np.mean([(r[f"{arm}_{p}"] - r[f"actual_{p}"]) ** 2 for p in POSITIONS]))
            r["actual_total_outs"] = sum(r[f"actual_{p}"] for p in POSITIONS)
            predictions.append(r)
        cells.append(dict(origin=y, fold=k, model_path=str(model_path), model_sha256=sha256_file(model_path),
                          forecast_rows=test.height, contextual_coarse_rows=sum(p["contextual_coarse_mass"] > 0 for p in predictions if p["origin_year"] == y and p["outer_fold"] == k),
                          conversions=conversions))
        print(f"Finished fixed opportunity fold {y}/{k}", flush=True)
    result = pl.DataFrame(predictions, infer_schema_length=None).sort("row_id")
    assert result.unique("row_id").height == result.height == frame.filter(pl.col("origin_year").is_in(ORIGINS)).height
    for arm in ("carry", "ratio", "pooled", "context"):
        assert np.isfinite(result.select([f"{arm}_{p}" for p in ROLES]).to_numpy()).all()
        assert result.select([f"{arm}_{p}" for p in ROLES]).to_numpy().min() >= 0
    result.write_parquet(OUT / "predictions.parquet")
    overall, groups, natives = [], [], []
    for y in ORIGINS:
        q = result.filter(pl.col("origin_year") == y)
        for arm in ("carry", "ratio", "pooled", "context"):
            overall.append(dict(origin=y, arm=arm, **score(q, arm)))
        for field in ("stage", "age_band"):
            for value in q[field].unique().to_list():
                g = q.filter(pl.col(field) == value)
                for arm in ("carry", "ratio", "pooled", "context"):
                    groups.append(dict(origin=y, field=field, value=value, arm=arm, **score(g, arm)))
        for c in CHANNELS:
            for arm in ("carry", "legacy", "ratio", "pooled", "context"):
                for positive in (False, True):
                    natives.append(dict(origin=y, channel=c, arm=arm, positive_only=positive,
                                        unknown_rows=q[f"actual_native_{c}"].null_count(), score=native_score(q, arm, c, positive)))
    write("fit-report.json", dict(cells=cells, overall=overall, groups=groups, native_scores=natives,
        paired_interval=paired_interval(result), player_walkthrough_status="pending", disposition="pending_player_review",
        new_role_bridge_families=1, upstream_PA_refitted=False, defensive_skill_changed=False,
        no_forecast_or_explorer_change=True, protected_outcomes_used=False,
        predictions_sha256=sha256_file(OUT / "predictions.parquet"), preflight_sha256=sha256_file(OUT / "preflight.json")))
    protections()
    print(json.dumps(dict(rows=result.height, report="provisional_until_walkthrough")))


def review():
    protections()
    assert not (OUT / "player-walkthrough.json").exists()
    pre, report = read(OUT / "preflight.json"), read(OUT / "fit-report.json")
    verify(pre["hash_inputs"])
    assert sha256_file(OUT / "predictions.parquet") == report["predictions_sha256"]
    q = pl.read_parquet(OUT / "predictions.parquet")
    source = pl.read_parquet(SOURCE / "source.parquet")
    records = q.to_dicts()
    by_case = {(r["player_id"], r["origin_year"]): r for r in records}
    selected = {key: {"fixed_diagnostic"} for key in FIXED if key in by_case}
    dev = [r for r in records if r["origin_year"] in (2022, 2023)]
    gain = lambda r: r["pooled_cell_squared_error"] - r["context_cell_squared_error"]
    total_error = lambda r: r["context_total_outs"] - r["actual_total_outs"]
    choices = [(max(dev, key=gain), "largest_gain"), (min(dev, key=gain), "largest_deterioration"),
               (max(dev, key=total_error), "largest_false_high"), (min(dev, key=total_error), "largest_false_low")]
    ordinary = [r for r in dev if r["stage"] == "Current MLB" and r["next_pa"] >= 300]
    median = float(np.median([r["context_cell_squared_error"] for r in ordinary]))
    choices.append((min(ordinary, key=lambda r: (abs(r["context_cell_squared_error"] - median), r["row_id"])), "ordinary_active_case"))
    exits = [r for r in dev if r["carry_total_outs"] > 0 and r["actual_total_outs"] == 0]
    choices.append((max(exits, key=lambda r: r["carry_total_outs"]), "exit"))
    nonarrivals = [r for r in dev if r["stage"] in ("Lower minors", "Upper minors") and r["actual_total_outs"] == 0]
    choices.append((max(nonarrivals, key=lambda r: r["context_total_outs"]), "minor_nonarrival_not_zero_talent"))
    for r, reason in choices:
        selected.setdefault((r["player_id"], r["origin_year"]), set()).add(reason)
    cases = []
    for key, reasons in sorted(selected.items()):
        r = by_case[key]
        pool = []
        for other in records:
            if other["origin_year"] != r["origin_year"] or other["stage"] != r["stage"] or other["player_id"] == r["player_id"]:
                continue
            if r["age"] is not None and (other["age"] is None or abs(other["age"] - r["age"]) > 3):
                continue
            a, b = r["bridge_role_shares"], other["bridge_role_shares"]
            if np.argmax(a) != np.argmax(b):
                continue
            distance = sum(abs(x - y) for x, y in zip(a, b))
            distance += .1 * abs(math.log1p(r["role_defensive_sample"]) - math.log1p(other["role_defensive_sample"]))
            if r["age"] is not None:
                distance += abs(r["age"] - other["age"]) / 3
            pool.append((distance, other["row_id"], other))
        peers = sorted(pool, key=lambda p: (p[0], p[1]))[:3]
        trace = []
        for who in [r] + [p[2] for p in peers]:
            y, pid = who["origin_year"], who["player_id"]
            model = read(OUT / f"model-{y}-{who['outer_fold']}.json")
            tables = {tuple(c["scope"]): c for c in model["role_tables"]}
            candidate, reference = predict(tables, who, True), predict(tables, who, False)
            assert np.allclose(candidate["values"], [who[f"context_{p}"] for p in ROLES], rtol=0, atol=1e-10)
            assert np.allclose(reference["values"], [who[f"pooled_{p}"] for p in ROLES], rtol=0, atol=1e-10)
            known = source.filter((pl.col("player_id") == pid) & pl.col("season").is_between(y - 2, y))
            target = source.filter((pl.col("player_id") == pid) & (pl.col("season") == y + 1) & pl.col("is_mlb"))
            oracle_rate = [v / who["preseason_pa"] * who["next_pa"] if who["preseason_pa"] else 0 for v in candidate["values"]]
            trace.append(dict(player_id=pid, player_name=who["player_name"], origin=y, fold=who["outer_fold"],
                stage=who["stage"], age=who["age"], fixed_expected_PA=who["preseason_pa"], actual_PA=who["next_pa"],
                role_kind=who["bridge_role_kind"], origin_role_shares=dict(zip(map(str, ROLES), who["bridge_role_shares"])),
                chosen_support_and_rate=candidate["trace"], pooled_support_and_rate=reference["trace"],
                known_source_rows=known.select("season", "normalized_level", "usage_scope", "position_code", "games_started", "fielding_outs").to_dicts(),
                target_source_rows=target.select("season", "position_code", "games_started", "fielding_outs").to_dicts(),
                position_forecasts={arm: {str(p): who[f"{arm}_{p}"] for p in ROLES} for arm in ("carry", "ratio", "pooled", "context")},
                actual_position_outs_and_DH_starts={str(p): who[f"actual_{p}"] for p in ROLES},
                actual_PA_sensitivity_values=oracle_rate, sensitivity_not_forecast=True,
                native_forecasts={arm: {c: who[f"{arm}_native_{c}"] for c in CHANNELS} for arm in ("carry", "legacy", "ratio", "pooled", "context")},
                native_actuals={c: who[f"actual_native_{c}"] for c in CHANNELS},
                native_measurement_status={c: who[f"native_label_{c}"] for c in CHANNELS},
                native_conversions=model["conversions"], unknown_future_skill_on_nonarrival=True))
        cases.append(dict(player_id=r["player_id"], player_name=r["player_name"], origin=r["origin_year"],
                          reasons=sorted(reasons), eligible_peer_count=len(pool), peers_selected=len(peers), records=trace))
    write("player-walkthrough.json", dict(status="mechanical_trace_complete_baseball_judgment_pending", cases=cases,
        peer_rule="Same origin and stage, dominant observed role and age within 3 years when known; role-mix L1 plus age/exposure distance. No outcome filter.",
        gain_loss_selection="Development origin diagnostics chosen by paired position-cell MSE; false highs/lows by total exposure error.",
        fixed_case_shortfalls=[list(p) for p in FIXED if p not in by_case], protected_outcomes_used=False))
    protections()
    print(json.dumps(dict(focal_cases=len(cases), peers=sum(c["peers_selected"] for c in cases), status="mechanics_traced_needs_baseball_review")))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "fit", "review"])
    args = parser.parse_args()
    {"prepare": prepare, "fit": fit, "review": review}[args.action]()
