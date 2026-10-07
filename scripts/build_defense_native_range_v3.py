"""Recover native components and qualify broad MLB range support before fitting."""
from collections import defaultdict
from datetime import date
import json
import math
from pathlib import Path

import polars as pl

from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.defense_native_range import history
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defense-native-range-v3"
PUBLIC = ROOT / "reports/model-evidence/defense-native-range-v3"
SOURCE = ROOT / "reports/generated/defensive-talent-position-v2"
COMPONENTS = ("range_runs", "arm_runs", "dp_runs", "fielding_runs_prevented_on_rec1b",
              "framing_runs", "throwing_runs", "blocking_runs")
FIXED_NAMES = ("Kiermaier", "Castellanos", "Arenado", "Semien", "Witt", "Tovar")


def write(name, data):
    save(OUT / name, data)
    save(PUBLIC / name, data)


def identity():
    sources = [SOURCE / "identity.parquet",
               ROOT / "reports/generated/hitter-2020-cohort/birthdates.parquet"]
    bios = {}
    for p in sources:
        for r in pl.read_parquet(p, columns=["player_id", "birth_date"]).iter_rows(named=True):
            if not r["birth_date"]:
                continue
            dob = date.fromisoformat(str(r["birth_date"]))
            if r["player_id"] in bios:
                assert bios[r["player_id"]] == dob, "Conflicting immutable birth date"
            bios[r["player_id"]] = dob
    panel_path = ROOT / "reports/generated/multiyear-hitter-components-v1/component-panel.parquet"
    ages = {(r["origin_year"], r["player_id"]): r["age"]
            for r in pl.read_parquet(panel_path, columns=["origin_year", "player_id", "age"]).iter_rows(named=True)}
    return bios, ages, sources + [panel_path]


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "source-review.json").exists()
    protected = protections()
    cert_path = SOURCE / "qualified/annual.parquet"
    cert = {(r["season"], r["player_id"], r["position"]): r
            for r in pl.read_parquet(cert_path).iter_rows(named=True)}
    audit_path = ROOT / "reports/generated/multiyear-hitter-components-v1/source-audit.json"
    source = json.loads(audit_path.read_text(encoding="utf8"))["mlb_fielding"]
    official_path = Path(source["path"])
    assert sha256_file(official_path) == source["sha256"]
    official = defaultdict(int)
    for r in pl.read_parquet(official_path).iter_rows(named=True):
        if str(r["position_code"]).isdigit():
            official[r["season"], r["player_id"], int(r["position_code"])] += r["fielding_outs"]
    ledger, coverage, source_paths = [], [], [cert_path, official_path, audit_path,
                                           ROOT / "docs/defense-native-range-v3-contract.md"]
    for year in range(2016, 2026):
        paths = [SOURCE / f"position-{year}.response", SOURCE / f"aggregate-{year}.response"]
        source_paths.extend(paths)
        split, agg = [embedded(p.read_text(encoding="utf8"), "data") for p in paths]
        for p in paths:
            params = embedded(p.read_text(encoding="utf8"), "serverParams")
            assert int(params["seasonStart"]) == int(params["seasonEnd"]) == year
        sums = defaultdict(lambda: defaultdict(float))
        max_additive, max_recompose = 0., 0.
        aggregate_outs_gaps = []
        for r in split:
            key = year, r["id"], r["pos_id"]
            total = sum(float(r[c]) for c in COMPONENTS if r[c] is not None)
            max_additive = max(max_additive, abs(total - r["total_runs"]))
            assert math.isclose(total, r["total_runs"], abs_tol=1e-9)
            for c in (*COMPONENTS, "total_runs", "outs_total"):
                sums[r["id"]][c] += float(r[c] or 0)
            if not 2 <= r["pos_id"] <= 9:
                continue
            n, independent = int(r["outs_total"]), official[key]
            exposure_valid = n > 0 and independent > 0 and abs(n - independent) <= 5 and abs(n - independent) <= .01 * max(n, independent)
            valid = exposure_valid and r["range_runs"] is not None
            assert key in cert and valid == cert[key]["measurement_valid"]
            ledger.append(dict(season=year, player_id=r["id"], player_name=r["name"],
                               position=r["pos_id"], native_outs=n, official_outs=independent,
                               exposure_valid=exposure_valid, range_valid=valid,
                               total_runs=r["total_runs"], **{c:r[c] for c in COMPONENTS}))
        for r in agg:
            for c in (*COMPONENTS, "total_runs", "outs_total"):
                diff = abs(sums[r["id"]][c] - float(r[c] or 0))
                if c == "outs_total" and diff:
                    # Aggregate outs include tiny positions omitted from splits;
                    # do not certify aggregate exposure by component additivity.
                    # Each used position remains independently qualified.
                    aggregate_outs_gaps.append(dict(player_id=r["id"], difference=diff))
                else:
                    max_recompose = max(max_recompose, diff)
                    assert diff < 1e-8, (year, r["id"], c, diff)
        coverage.append(dict(season=year, rows=len(split), max_additive_error=max_additive,
                             max_aggregate_recomposition_error=max_recompose,
                             aggregate_outs_gaps=aggregate_outs_gaps,
                             components_present={c:sum(r[c] is not None for r in split) for c in COMPONENTS}))
    frame = pl.DataFrame(ledger, infer_schema_length=None)
    assert frame.select("season", "player_id", "position").unique().height == frame.height
    frame.write_parquet(OUT / "component-ledger.parquet")
    bios, ages, identity_paths = identity()
    source_paths.extend(identity_paths)
    native = defaultdict(list)
    names = {}
    for r in ledger:
        native[r["player_id"]].append(r)
        names[r["player_id"]] = r["player_name"]
    origins, labels = [], []
    for year in range(2016, 2025):
        if year == 2020:
            continue
        for pid, rows in sorted(native.items()):
            for pos in range(3, 10):
                h, past = history(rows, year, pos)
                if sum(r["native_outs"] for r in past) < 25:
                    continue
                dob = bios.get(pid)
                age = year - dob.year - ((7, 1) < (dob.month, dob.day)) if dob else ages.get((year, pid))
                if age is not None and (not math.isfinite(age) or not 15 <= age <= 55):
                    age = None
                row = dict(origin_year=year, player_id=pid, player_name=names[pid], position=pos,
                           age=float(age) if age is not None else None,
                           age_basis="birthdate_july1" if dob else "dated_panel" if age is not None else "unknown",
                           history_left_truncated=year - 2 < 2016, **h)
                origins.append(row)
                window_end = year + 3
                path = [r for r in rows if year < r["season"] <= min(window_end, 2025) and r["position"] == pos]
                measured = [r for r in path if r["range_valid"]]
                missing_outs = sum(official.get((s, pid, pos), 0)
                                   for s in range(year + 1, min(window_end, 2025) + 1)
                                   if not any(r["season"] == s and r["range_valid"] for r in measured))
                n = sum(r["native_outs"] for r in measured)
                runs = sum(r["range_runs"] for r in measured)
                complete = window_end <= 2025
                valid = complete and n >= 1500 and len(measured) >= 2 and missing_outs == 0
                other_n = sum(official.get((s, pid, p), 0)
                              for s in range(year + 1, min(window_end, 2025) + 1)
                              for p in range(2, 10) if p != pos)
                labels.append({**row, "window_end":window_end, "window_mature":complete,
                               "window_has_2020":year < 2020 <= window_end,
                               "quality_rate":1500 * runs / n if valid else None,
                               "quality_status":"measured" if valid else "window_incomplete" if not complete else "unknown",
                               "future_outs":n, "future_runs":runs, "future_seasons":len(measured),
                               "future_other_position_outs":other_n, "unmeasured_official_outs":missing_outs})
    pl.DataFrame(origins).write_parquet(OUT / "origins.parquet")
    pl.DataFrame(labels).write_parquet(OUT / "labels.parquet")
    # Source audit walkthrough, outcome-blind identities and peers. Not a fitted forecast.
    cases = []
    for token in FIXED_NAMES:
        pids = [pid for pid, name in names.items() if token.lower() in name.lower()]
        for pid in pids:
            candidates = [r for r in labels if r["player_id"] == pid and r["origin_year"] == 2022]
            if not candidates:
                candidates = [r for r in labels if r["player_id"] == pid][-1:]
            if not candidates:
                continue
            r = max(candidates, key=lambda x:x["history_outs"])
            peers = [p for p in labels if p["origin_year"] == r["origin_year"] and p["position"] == r["position"] and p["player_id"] != pid]
            peers.sort(key=lambda p:(abs((p["age"] or 27) - (r["age"] or 27)),
                                     abs(p["history_outs"] - r["history_outs"]), p["player_id"]))
            cases.append(dict(token=token, origin=r, dated_source=[x for x in native[pid] if r["origin_year"] - 2 <= x["season"] <= r["origin_year"]],
                              future_path=[x for x in native[pid] if r["origin_year"] < x["season"] <= r["window_end"]],
                              peers=peers[:3], scope="native range; no fitted forecast yet"))
    write("source-player-walkthrough.json", dict(selection="fixed names, 2022 or latest eligible origin, largest origin-known position exposure; peers by same origin/position then age/exposure/ID, no future selection", cases=cases))
    counts = []
    for year in sorted(set(r["origin_year"] for r in labels)):
        pool = [r for r in labels if r["origin_year"] == year]
        q = [r for r in pool if r["quality_rate"] is not None]
        counts.append(dict(origin=year, people=len({r["player_id"] for r in pool}), position_rows=len(pool),
                           measured_people=len({r["player_id"] for r in q}), measured_rows=len(q),
                           missing_age_rows=sum(r["age"] is None for r in pool),
                           unknown_quality_with_other_position=sum(r["quality_rate"] is None and r["future_other_position_outs"] > 0 for r in pool)))
    files = source_paths + [OUT / n for n in ("component-ledger.parquet", "origins.parquet", "labels.parquet", "source-player-walkthrough.json")]
    write("source-review.json", dict(player_walkthrough_status="complete", coverage=coverage,
                                     cohort=counts, hashes={str(p):sha256_file(p) for p in files}, protections=protected,
                                     retrospective_vintage=True, catcher_pitch_denominators_certified=False,
                                     rare_nonoutfield_arm_rows_retained=True,
                                     claim="Component additivity and exposures; range support only. No ability/value improvement yet."))
    print(json.dumps(dict(rows=frame.height, origins=len(origins), coverage=counts), indent=2))


if __name__ == "__main__":
    prepare()
