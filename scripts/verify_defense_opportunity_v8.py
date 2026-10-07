"""Independently replay empirical means, exposure forecasts and held-person checks.

This appends diagnostics to the sealed comparison; it does not refit or change it.
"""

from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defense-opportunity-v8"
PUBLIC = ROOT / "reports/model-evidence/defense-opportunity-v8"
POSITIONS = tuple(range(2, 10))
ROLES = (*POSITIONS, 10)
ARMS = ("carry", "ratio", "pooled", "context")
CHANNELS = ("framing", "throwing", "blocking", "arm", "receiving")


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def fold(pid):
    return int.from_bytes(hashlib.sha256(f"ubm-prospect-v8:{pid}".encode()).digest()[:8], "big") % 5


def independent_shares(row):
    starts = np.array([row[f"mlb_weighted_starts_{p}"] + row[f"minor_weighted_starts_{p}"] for p in ROLES], float)
    kind = "observed_starts"
    if starts.sum() == 0:
        starts = np.array([row[f"mlb_weighted_outs_{p}"] + row[f"minor_weighted_outs_{p}"] for p in POSITIONS] + [0.], float)
        kind = "observed_outs_fallback"
    if starts.sum() == 0:
        starts = np.array([str(p) == str(row.get("source_position")) for p in ROLES], float)
        kind = "roster_fallback" if starts.sum() else "unknown_role"
    return (starts / starts.sum() if starts.sum() else starts), kind


def sufficient(cell):
    return cell["people"] >= 20 and cell["effective_people"] >= 10 and cell["denominator_PA"] > 0


def chosen(tables, row, role, contextual):
    candidates = [("role_stage_age", str(role), row["stage"], row["age_band"]),
                  ("role_stage", str(role), row["stage"])] if contextual else []
    candidates += [("role", str(role)), ("all",)]
    return next(tables[key] for key in candidates if sufficient(tables[key]))


def vector(tables, row, shares, contextual):
    if shares.sum() == 0:
        rates = np.array(tables[("all",)]["rates"])
    else:
        rates = sum((shares[j] * np.array(chosen(tables, row, p, contextual)["rates"])
                     for j, p in enumerate(ROLES) if shares[j] > 0), np.zeros(9))
    return rates * row["preseason_pa"]


def scores(frame, arm):
    p = frame.select([f"{arm}_{i}" for i in POSITIONS]).to_numpy()
    a = frame.select([f"actual_{i}" for i in POSITIONS]).to_numpy()
    e = p - a
    return dict(rows=frame.height, cell_rmse=float(np.sqrt(np.mean(e*e))), cell_mae=float(np.mean(abs(e))),
                predicted_total_outs=float(p.sum()), actual_total_outs=float(a.sum()),
                total_out_rmse=float(np.sqrt(np.mean(e.sum(axis=1)**2))))


def main():
    protections()
    assert not (OUT / "independent-verification.json").exists()
    pre, report = read(OUT / "preflight.json"), read(OUT / "fit-report.json")
    for p, digest in pre["hash_inputs"].items():
        assert sha256_file(Path(p)) == digest, p
    assert sha256_file(OUT / "features.parquet") == pre["hash_features"]
    assert sha256_file(OUT / "opportunity-records.parquet") == pre["hash_opportunities"]
    assert sha256_file(OUT / "predictions.parquet") == report["predictions_sha256"]
    features = pl.read_parquet(OUT / "features.parquet")
    predictions = pl.read_parquet(OUT / "predictions.parquet")
    native = pl.read_parquet(OUT / "opportunity-records.parquet")
    source = pl.read_parquet(ROOT / "reports/generated/defense-position-opportunity-v7/source.parquet")
    official = source.filter(pl.col("is_mlb")).group_by("season", "player_id").agg(
        *[pl.col("fielding_outs").filter(pl.col("position_code") == str(p)).sum().alias(f"out_{p}") for p in POSITIONS],
        pl.col("games_started").filter(pl.col("position_code") == "10").sum().alias("DH_starts"))
    official_map = {(r["season"], r["player_id"]): r for r in official.to_dicts()}
    expected = features.filter(pl.col("origin_year").is_in([2022, 2023, 2024]))
    assert sorted(expected["row_id"]) == sorted(predictions["row_id"])
    assert predictions.unique(["origin_year", "player_id"]).height == predictions.height
    assert features.group_by("player_id").agg(pl.col("outer_fold").n_unique()).filter(pl.col("outer_fold") != 1).is_empty()
    shares = {}
    for r in features.to_dicts():
        v, kind = independent_shares(r)
        assert np.allclose(v, r["bridge_role_shares"], atol=1e-15, rtol=0)
        assert kind == r["bridge_role_kind"] and fold(r["player_id"]) == r["outer_fold"]
        shares[r["row_id"]] = v
        actual = official_map.get((r["target_year"], r["player_id"]), {})
        old = official_map.get((r["origin_year"], r["player_id"]), {})
        for p in POSITIONS:
            assert r[f"actual_{p}"] == actual.get(f"out_{p}", 0)
            assert r[f"carry_{p}"] == old.get(f"out_{p}", 0)
        assert r["actual_10"] == actual.get("DH_starts", 0)
        assert r["carry_10"] == old.get("DH_starts", 0)
    # Reconstruct the native source qualification, counts and official denominator
    # instead of just trusting the generated opportunity-records table.
    source_maps = {}
    for path in native["source_path"].unique():
        q = pl.read_parquet(path)
        source_maps[path] = {(r["season"], r["player_id"], r.get("component", r.get("kind", "framing"))): r for r in q.to_dicts()}
    native_map = {}
    for r in native.to_dicts():
        n = source_maps[r["source_path"]][r["season"], r["player_id"], r["channel"]]
        count = n.get("opportunities", n.get("pitches"))
        if r["channel"] == "framing":
            valid = n["exposure_valid"] and n["framing_measurement_valid"]
        elif r["channel"] in ("throwing", "blocking"):
            valid = n["exposure_valid"] and n["measurement_valid"]
        else:
            valid = n["isolated_outfield_quality_valid"] if r["channel"] == "arm" else n["quality_valid"]
        obs = official_map.get((r["season"], r["player_id"]), {})
        exposure = obs.get("out_2", 0) if r["channel"] in ("framing", "throwing", "blocking") else (
            sum(obs.get(f"out_{p}", 0) for p in (7, 8, 9)) if r["channel"] == "arm" else obs.get("out_3", 0))
        assert r["opportunities"] == count and r["official_exposure"] == exposure
        assert r["valid"] == bool(valid and exposure > 0 and count is not None and count >= 0)
        native_map[r["channel"], r["season"], r["player_id"]] = r
    table_count = forecast_count = native_cells = 0
    extrapolation = []
    for note in report["cells"]:
        y, k = note["origin"], note["fold"]
        model_path = Path(note["model_path"])
        assert sha256_file(model_path) == note["model_sha256"]
        m = read(model_path)
        tr = features.filter((pl.col("target_year") <= y) & (pl.col("next_pa") > 0) & (pl.col("outer_fold") != k))
        te = predictions.filter((pl.col("origin_year") == y) & (pl.col("outer_fold") == k))
        assert sorted(tr["row_id"]) == sorted(m["training_row_ids"])
        assert sorted(te["row_id"]) == sorted(m["test_row_ids"])
        assert not set(tr["player_id"]) & set(te["player_id"])
        rows = tr.to_dicts()
        S = np.array([shares[r["row_id"]] for r in rows])
        PA = tr["next_pa"].to_numpy()
        T = tr.select([f"actual_{p}" for p in ROLES]).to_numpy()
        rebuilt = {}
        for c in m["role_tables"]:
            scope = c["scope"]
            weight = np.ones(tr.height) if scope[0] == "all" else S[:, ROLES.index(int(scope[1]))].copy()
            if scope[0] in ("role_stage", "role_stage_age"):
                weight *= np.array([r["stage"] == scope[2] for r in rows])
            if scope[0] == "role_stage_age":
                weight *= np.array([r["age_band"] == scope[3] for r in rows])
            masses = defaultdict(float)
            for r, mass in zip(rows, weight * PA):
                if mass > 0:
                    masses[r["player_id"]] += mass
            den = float(weight @ PA)
            num = weight @ T
            effective = den**2 / sum(x*x for x in masses.values()) if den else 0.
            assert c["people"] == len(masses) and c["rows"] == int((weight > 0).sum())
            assert np.isclose(c["effective_people"], effective, atol=1e-9, rtol=1e-12)
            assert np.isclose(c["denominator_PA"], den, atol=1e-8, rtol=1e-12)
            assert np.allclose(c["numerator"], num, atol=1e-8, rtol=1e-12)
            if den:
                assert np.allclose(c["rates"], num / den, atol=1e-10, rtol=0)
            else:
                assert c["rates"] is None
            rebuilt[tuple(scope)] = c
            table_count += 1
        for channel, conv in m["conversions"].items():
            valid = native.filter((pl.col("channel") == channel) & pl.col("valid") & (pl.col("season") <= y) & (pl.col("origin_fold") != k))
            recent = valid.filter(pl.col("season") >= y - 2)
            expand = recent["player_id"].n_unique() < 20 or recent["season"].n_unique() < 2
            selected = valid if expand else recent
            check = next(c for c in pre["native_cells"] if (c["origin"], c["fold"], c["channel"]) == (y, k, channel))
            assert sorted(selected.select("season", "player_id").rows()) == sorted(map(tuple, check["source_keys"]))
            assert not set(selected["player_id"]) & set(te["player_id"])
            w = .5 ** (y - selected["season"].to_numpy())
            num = float(w @ selected["opportunities"].to_numpy())
            den = float(w @ selected["official_exposure"].to_numpy())
            assert np.isclose(num / den, conv["rate"], atol=1e-12, rtol=1e-12)
            assert np.isclose(den, conv["official_outs"], atol=1e-8, rtol=1e-12)
            assert conv["people"] == selected["player_id"].n_unique()
            assert conv["expanded_history_fallback"] == expand
            scope_positions = (2,) if channel in ("framing", "throwing", "blocking") else (7, 8, 9) if channel == "arm" else (3,)
            all_den = sum(sum(r[f"out_{p}"] for p in scope_positions) * .5**(y-r["season"])
                          for r in official.to_dicts() if r["season"] in conv["seasons"] and fold(r["player_id"]) != k)
            assert np.isclose(all_den, conv["all_corresponding_official_outs"], atol=1e-8, rtol=0)
            assert np.isclose(den / all_den, conv["measured_out_coverage_fraction"], atol=1e-12, rtol=0)
            native_cells += 1
        # A range warning is based only on actually available training outcomes.
        maxima = np.max(T, axis=0)
        total_max = float(T[:, :8].sum(axis=1).max())
        for r in te.to_dicts():
            v = shares[r["row_id"]]
            expected_vectors = {"pooled": vector(rebuilt, r, v, False), "context": vector(rebuilt, r, v, True),
                                "carry": np.array([r[f"carry_{p}"] for p in ROLES])}
            expected_vectors["ratio"] = expected_vectors["carry"] * r["preseason_pa"] / r["pa_0"] if r["pa_0"] > 0 else expected_vectors["pooled"]
            for arm, values in expected_vectors.items():
                assert np.allclose(values, [r[f"{arm}_{p}"] for p in ROLES], atol=1e-8, rtol=1e-12)
                assert np.isclose(values[:8].sum(), r[f"{arm}_total_outs"], atol=1e-8, rtol=0)
                assert np.all(values >= 0) and np.all(np.isfinite(values))
                high = [p for j, p in enumerate(ROLES) if values[j] > maxima[j]]
                if high or values[:8].sum() > total_max:
                    extrapolation.append(dict(player_id=r["player_id"], player_name=r["player_name"], origin=y, fold=k,
                        arm=arm, positions_beyond_training_max=high, total_beyond_training_max=bool(values[:8].sum() > total_max)))
                for channel in CHANNELS:
                    actual_record = native_map.get((channel, y + 1, r["player_id"]))
                    obs = official_map.get((y + 1, r["player_id"]), {})
                    pos = (2,) if channel in ("framing", "throwing", "blocking") else (7, 8, 9) if channel == "arm" else (3,)
                    exposure = sum(obs.get(f"out_{p}", 0) for p in pos)
                    if actual_record and actual_record["valid"]:
                        assert r[f"actual_native_{channel}"] == actual_record["opportunities"]
                    elif exposure == 0 and not (actual_record and actual_record["opportunities"] and actual_record["opportunities"] > 0):
                        assert r[f"actual_native_{channel}"] == 0
                    else:
                        assert r[f"actual_native_{channel}"] is None
                    if arm != "carry":
                        predicted = sum(values[ROLES.index(p)] for p in pos) * m["conversions"][channel]["rate"]
                        assert np.isclose(predicted, r[f"{arm}_native_{channel}"], atol=1e-8, rtol=1e-12)
            forecast_count += 1
    metrics = []
    for y in (2022, 2023, 2024):
        q = predictions.filter(pl.col("origin_year") == y)
        for arm in ARMS:
            s = scores(q, arm)
            old = next(c for c in report["overall"] if c["origin"] == y and c["arm"] == arm)
            for key, v in s.items():
                assert np.isclose(v, old[key], atol=1e-8, rtol=1e-12)
            metrics.append(dict(origin=y, arm=arm, **s))
    groups, coverage, contamination = [], [], []
    for y in (2022, 2023, 2024):
        q = predictions.filter(pl.col("origin_year") == y).with_columns(
            pl.when((pl.col("carry_total_outs") > 0) & (pl.col("actual_total_outs") > 0)).then(pl.lit("continuing_defender"))
            .when((pl.col("carry_total_outs") == 0) & (pl.col("actual_total_outs") > 0)).then(pl.lit("new_or_returning_defender"))
            .when((pl.col("carry_total_outs") > 0) & (pl.col("actual_total_outs") == 0)).then(pl.lit("defensive_exit"))
            .otherwise(pl.lit("no_defense_before_or_after")).alias("exposure_cohort"))
        for name in q["exposure_cohort"].unique():
            g = q.filter(pl.col("exposure_cohort") == name)
            for arm in ARMS:
                groups.append(dict(origin=y, cohort=name, arm=arm, **scores(g, arm)))
        full = official.filter(pl.col("season") == y + 1)
        modeled = set(q["player_id"])
        missing = full.filter(~pl.col("player_id").is_in(modeled))
        for p in POSITIONS:
            full_total = int(full[f"out_{p}"].sum())
            matched = int(q[f"actual_{p}"].sum())
            omitted = int(missing[f"out_{p}"].sum())
            assert full_total == matched + omitted
            coverage.append(dict(origin=y, position=p, full_actual=full_total, matched_actual=matched, omitted_actual=omitted,
                                 **{arm:float(q[f"{arm}_{p}"].sum()) for arm in ARMS}))
        for arm in ("pooled", "context", "ratio"):
            # C allocation to noncatchers is not intrinsically impossible, but
            # a systematic spread into unrelated roles needs a baseball judgment.
            noncatcher = q.filter(pl.col("bridge_role_shares").list.get(0) == 0)
            contaminated = noncatcher.filter(pl.col(f"{arm}_2") >= 27)
            contamination.append(dict(origin=y, arm=arm, zero_origin_C_share_rows=noncatcher.height,
                forecast_C_outs=float(noncatcher[f"{arm}_2"].sum()), actual_C_outs=int(noncatcher["actual_2"].sum()),
                at_least_nine_C_innings_rows=contaminated.height,
                examples=contaminated.sort(f"{arm}_2", descending=True).select("player_id", "player_name", f"{arm}_2", "actual_2").head(10).to_dicts()))
    # Recompute paired uncertainty from grouped player sums in batches. This
    # does not call the experiment's score/interval implementation.
    persons = predictions["player_id"].unique().sort().to_list()
    pi = {p:i for i,p in enumerate(persons)}
    loss = np.zeros((len(persons), 3, 2))
    has = np.zeros((len(persons), 3))
    for r in predictions.to_dicts():
        i,j = pi[r["player_id"]], r["origin_year"]-2022
        has[i,j] = 1
        for a,arm in enumerate(("context", "pooled")):
            loss[i,j,a] = sum((r[f"{arm}_{p}"]-r[f"actual_{p}"])**2 for p in POSITIONS)/8
    rng = np.random.default_rng(708006)
    changes = []
    for _ in range(40):
        counts = rng.multinomial(len(persons), np.full(len(persons),1/len(persons)), size=50)
        denominator = counts @ has
        estimates = np.sqrt(np.einsum("bi,ija->bja",counts,loss)/denominator[:,:,None])
        changes.extend((estimates[:,:,0]-estimates[:,:,1]).mean(axis=1))
    interval = np.quantile(changes,[.025,.975]).tolist()
    assert np.allclose(interval,report["paired_interval"]["interval_95"],atol=1e-8,rtol=0)
    result = dict(integrity_pass=True, empirical_tables_replayed=table_count, all_forecasts_replayed=forecast_count,
        native_cells_replayed=native_cells, native_source_records_replayed=native.height, conditional_target_not_quality=True,
        paired_interval_95=interval, scores=metrics, exposure_cohorts=groups, full_MLB_and_matched_totals=coverage,
        extrapolation_warnings=extrapolation, catcher_role_contamination=contamination,
        extrapolation_not_a_physical_cap=True, forecast_and_model_changes=False, player_walkthrough_status="mechanics_only_not_baseball_judgment",
        protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__), OUT/"preflight.json",OUT/"fit-report.json",OUT/"player-walkthrough.json",OUT/"predictions.parquet"]})
    save(OUT/"independent-verification.json",result)
    save(PUBLIC/"independent-verification.json",result)
    protections()
    print(json.dumps({k:result[k] for k in ["integrity_pass","empirical_tables_replayed","all_forecasts_replayed","native_cells_replayed","paired_interval_95"]}))


if __name__ == "__main__":
    main()
