"""Reconstruct position histories and inspect opportunity support before fits."""

from collections import defaultdict
from datetime import date
import gzip
import json
import math
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import polars as pl

from universal_baseball.defense_position_history import (
    POSITIONS, ROLE_POSITIONS, SPORT_LEVEL, annual_usage, index_usage, normalize,
    origin_summary, support_tags,
)
from universal_baseball.position_role_source import project_fielding_usage_splits
from universal_baseball.storage import sha256_file
from build_defense_native_range_v3 import identity
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defense-position-opportunity-v7"
PUBLIC = ROOT / "reports/model-evidence/defense-position-opportunity-v7"
LEGACY = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated")
KEY = ["season", "league_id", "team_id", "player_id", "position_code"]
MEASURES = ["games_played", "games_started", "source_innings", "fielding_outs"]
FIXED = [(683146, 2019), (682626, 2019), (605141, 2023), (662139, 2022),
         (656941, 2023), (682829, 2022), (805811, 2024)]


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def receipt(name, obj):
    save(OUT / name, obj)
    save(PUBLIC / name, obj)


def exact(actual, rebuilt):
    metadata = ["team_name", "player_name", "position_abbreviation", "position_name", "position_type"]
    a, b = [f.select(KEY + MEASURES + metadata).sort(KEY) for f in (actual, rebuilt)]
    assert a.equals(b), "Saved fielding does not replay from captured values"


def replay_early(frame, paths):
    manifest_path = ROOT / "model_artifacts/prospect-role-usage-v3/manifest.json"
    manifest = read(manifest_path)
    assert len(manifest["sources"]) == 66
    paths.append(manifest_path)
    rebuilt, evidence = [], []
    for c in manifest["sources"]:
        path = Path(c["path"])
        assert path.exists() and sha256_file(path) == c["sha256"]
        paths.append(path)
        with gzip.open(path, "rt", encoding="utf8") as stream:
            payload = json.load(stream)
        y, sport = int(payload["year"]), int(payload["sport"])
        assert (y, sport) == (c["year"], c["sport"])
        assert len(payload["splits"]) == payload["expected"] == c["rows"]
        for url in payload["urls"]:
            q = parse_qs(urlparse(url).query)
            assert q["season"] == [str(y)] and q["sportId"] == [str(sport)]
            assert q["group"] == ["fielding"] and q["gameType"] == ["R"] and q["playerPool"] == ["ALL"]
        leagues = defaultdict(list)
        for r in payload["splits"]:
            assert int(r["season"]) == y and int(r["sport"]["id"]) == sport
            leagues[int(r["league"]["id"])].append(r)
        rebuilt.extend(project_fielding_usage_splits(rows, season=y, league_id=lg,
                       level_group=SPORT_LEVEL[sport]) for lg, rows in leagues.items())
        evidence.append(dict(season=y, sport=sport, rows=len(payload["splits"]),
                             pages=len(payload["urls"]), capture_sha256=sha256_file(path)))
    exact(frame, pl.concat(rebuilt))
    return evidence


def replay_repair(frame, paths):
    path = ROOT / "model_artifacts/advanced-rookie-repair-v3/raw/2019/fielding.json.gz"
    manifest_path = ROOT / "model_artifacts/advanced-rookie-repair-v3/manifest.json"
    manifest = read(manifest_path)
    raw = next(s for y in manifest["years"] if y["year"] == 2019 for s in y["sources"]
               if str(s["path"]).replace("\\", "/").endswith("/fielding.json.gz"))
    assert sha256_file(path) == raw["sha256"]
    artifact = next(a for a in manifest["artifacts"]
                    if str(a["path"]).replace("\\", "/").endswith("/2019/fielding_supplement.parquet"))
    assert sha256_file(ROOT / artifact["path"]) == artifact["sha256"]
    paths.extend([path, manifest_path])
    with gzip.open(path, "rt", encoding="utf8") as stream:
        payload = json.load(stream)
    splits = payload["stats"][0]["splits"]
    assert len(splits) == int(payload["stats"][0]["totalSplits"]) == frame.height
    assert all(int(s["sport"]["id"]) == 5442 and int(s["season"]) == 2019 for s in splits)
    rebuilt = pl.concat([project_fielding_usage_splits([s for s in splits if s["league"]["id"] == lg],
                        season=2019, league_id=lg, level_group="RK") for lg in (120, 128)])
    exact(frame, rebuilt)
    return dict(rows=frame.height, raw_sport_ids=[5442], leagues=[120, 128],
                only_2019_added=True, older_advanced_rookie_subsets_added=False)


def replay_modern(frame, base, result_path, paths):
    old_result = read(result_path)
    paths.append(result_path)
    result_path = base / Path(old_result["storage"]["fielding_usage"]["path"]).parent.parent / "report.json"
    result = read(result_path)
    assert not result["source_errors"]
    stored_path = base / result["storage"]["fielding_usage"]["path"]
    original_hash = result["storage"]["fielding_usage"]["file_sha256"]
    actual_hash = sha256_file(stored_path)
    assert actual_hash == original_hash
    paths.append(result_path)
    grouped = defaultdict(list)
    pages = []
    for c in result["capture_records"]:
        if c["group"] != "fielding":
            continue
        path = base / c["capture_path"]
        assert path.exists() and sha256_file(path) == c["response_sha256"] and c["status_code"] == 200
        paths.append(path)
        q = parse_qs(urlparse(c["requested_url"]).query)
        assert q["season"] == [str(c["season"])] and q["leagueId"] == [str(c["league_id"])]
        assert q["gameType"] == ["R"] and q["playerPool"] == ["ALL"]
        payload = read(path)
        block = payload["stats"][0]
        assert len(block["splits"]) == c["returned_split_count"]
        assert int(block["totalSplits"]) == c["reported_total_splits"]
        grouped[c["season"], c["league_id"]].append((c["offset"], block, c))
        pages.append(dict(season=c["season"], league=c["league_id"], offset=c["offset"],
                          rows=len(block["splits"]), capture_sha256=sha256_file(path)))
    rebuilt = []
    for (y, lg), entries in sorted(grouped.items()):
        splits, expected = [], entries[0][1]["totalSplits"]
        for offset, block, capture in sorted(entries):
            assert offset == len(splits) and block["totalSplits"] == expected
            assert all(int(s["season"]) == y and int(s["league"]["id"]) == lg for s in block["splits"])
            splits.extend(block["splits"])
        assert len(splits) == expected
        rebuilt.append(project_fielding_usage_splits(splits, season=y, league_id=lg, level_group="replayed"))
    exact(frame, pl.concat(rebuilt))
    return dict(rows=frame.height, scope_count=len(grouped), pages=len(pages), captures=pages,
                original_receipt_file_sha256=original_hash, current_file_sha256=actual_hash,
                original_file_hash_matches=original_hash == actual_hash,
                older_docs_receipt_file_sha256=old_result["storage"]["fielding_usage"]["file_sha256"],
                older_receipt_applies_to_current_artifact=False,
                exact_values_and_identity_metadata_replayed=True,
                current_table_acceptance="Matching artifact-local receipt and complete content replay from matching raw captures.")


def conservation(frame, groups):
    table = frame.group_by(groups + ["position_code"]).agg(pl.col("fielding_outs").sum().alias("outs"))
    wide = table.pivot(on="position_code", index=groups, values="outs").fill_null(0)
    wide = wide.with_columns((pl.max_horizontal([str(p) for p in POSITIONS]) -
                             pl.min_horizontal([str(p) for p in POSITIONS])).alias("spread"))
    return dict(groups=wide.height, exact_groups=wide.filter(pl.col("spread") == 0).height,
                unequal_groups=wide.filter(pl.col("spread") > 0).height,
                discrepancies=wide.filter(pl.col("spread") > 0).sort("spread", descending=True).to_dicts())


def prepare():
    protections()
    assert not (OUT / "source-review.json").exists(), "Do not overwrite completed source evidence"
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    paths = [Path(__file__), ROOT / "src/universal_baseball/defense_position_history.py",
             ROOT / "tests/test_defense_position_history.py", ROOT / "docs/defense-position-opportunity-v7-source-contract.md"]
    audit_path = ROOT / "reports/generated/multiyear-hitter-components-v1/source-audit.json"
    audit = read(audit_path)["mlb_fielding"]
    files = dict(mlb=Path(audit["path"]), early=ROOT / "model_artifacts/prospect-role-usage-v3/fielding.parquet",
                 repair2019=ROOT / "model_artifacts/advanced-rookie-repair-v3/2019/fielding_supplement.parquet",
                 modern=LEGACY / "position-capacity-source/historical/reports/generated/position-role-historical-source/tables/historical_fielding_usage.parquet",
                 modern2025=LEGACY / "position-capacity-source/2025/reports/generated/position-role-2025-confirmation-source/tables/position_role_2025_fielding_usage.parquet")
    assert sha256_file(files["mlb"]) == audit["sha256"]
    assert sha256_file(files["modern"]) == "fa84a74402390c62de06e174083810cfe668010d696a2c71a312347e95ef71f4"
    assert sha256_file(files["modern2025"]) == "372cd75d0f67217c7def51351e938a16b2584d30de374d9f5097a5d739f8f8d4"
    frames = {n: pl.read_parquet(p) for n, p in files.items()}
    paths += list(files.values()) + [audit_path]
    replays = dict(early=replay_early(frames["early"], paths), repair2019=replay_repair(frames["repair2019"], paths))
    for name, folder, result in [("modern", "historical", "position-role-historical-source-result.json"),
                                 ("modern2025", "2025", "position-role-2025-confirmation-source-result.json")]:
        replays[name] = replay_modern(frames[name], LEGACY / f"position-capacity-source/{folder}", ROOT / f"docs/{result}", paths)
    overlapping = pl.concat([frames[n].filter(pl.col("level_group") == "MLB") for n in ("modern", "modern2025")])
    exact(overlapping, frames["mlb"].filter(pl.col("season") >= 2021))
    normalized = [normalize(f if n in ("mlb", "early", "repair2019") else f.filter(pl.col("level_group") != "MLB"), n)
                  for n, f in frames.items()]
    source = pl.concat(normalized, how="diagonal_relaxed").sort(["season", "source_id", "usage_scope", "player_id", "position_code"])
    assert source.filter(pl.col("source_id").is_in(["modern", "modern2025"]) & pl.col("is_mlb")).height == 0
    assert source.unique(["season", "usage_scope", "player_id", "position_code"]).height == source.height
    source.write_parquet(OUT / "source.parquet")
    annual = annual_usage(source).sort(["season", "player_id", "is_mlb", "normalized_level"])
    annual.write_parquet(OUT / "annual-usage.parquet")
    index = index_usage(annual)
    panel_path = ROOT / "reports/generated/hitter-preseason-readiness-v68/predictions.parquet"
    paths.append(panel_path)
    base_cols = ["row_id", "player_id", "player_name", "origin_year", "target_year", "age", "age_unknown", "stage", "outer_fold",
                 "source_position", "preseason_pa", "next_pa"]
    base = pl.read_parquet(panel_path, columns=base_cols)
    assert base.height == 30506 and base["target_year"].max() <= 2025 and not (base["target_year"] == 2020).any()
    assert (base["target_year"] == base["origin_year"] + 1).all() and base.unique("row_id").height == base.height
    contexts = []
    for r in base.iter_rows(named=True):
        h = origin_summary(index.get(r["player_id"], []), r["origin_year"])
        if r["age_unknown"]:
            r["age"] = None
        contexts.append({**r, **h})
    context = support_tags(pl.DataFrame(contexts, infer_schema_length=None))
    context.write_parquet(OUT / "origin-context.parquet")
    official = defaultdict(lambda: defaultdict(int))
    for r in frames["mlb"].iter_rows(named=True):
        official[r["season"], r["player_id"]][int(r["position_code"])] += r["fielding_outs"]
    labels = [dict(row_id=r["row_id"], **{f"actual_outs_{p}": official[r["target_year"], r["player_id"]][p] for p in POSITIONS})
              for r in base.iter_rows(named=True)]
    label_frame = pl.DataFrame(labels).with_columns(pl.sum_horizontal([f"actual_outs_{p}" for p in POSITIONS]).alias("actual_defensive_outs"))
    label_frame.write_parquet(OUT / "exposure-labels.parquet")
    support_rows, cells = [], []
    profiles = [["stage", "primary_start_position"],
                ["stage", "age_band", "primary_start_position", "defensive_sample_band"],
                ["stage", "age_band", "primary_start_position", "role_evidence_source"]]
    for y in (2022, 2023, 2024):
        for k in range(5):
            train = context.filter((pl.col("target_year") <= y) & (pl.col("outer_fold") != k) & (pl.col("next_pa") > 0))
            test = context.filter((pl.col("origin_year") == y) & (pl.col("outer_fold") == k))
            assert not set(train["player_id"]) & set(test["player_id"])
            assert train["target_year"].max() <= y and not train.is_empty() and not test.is_empty()
            for kind, keys in enumerate(profiles):
                counts = train.group_by(keys).agg(pl.col("player_id").n_unique().alias("training_people"))
                view = test.select("row_id", *keys).join(counts, on=keys, how="left", nulls_equal=True, validate="m:1")
                view = view.with_columns(pl.col("training_people").fill_null(0), pl.lit(y).alias("origin"), pl.lit(k).alias("fold"), pl.lit(kind).alias("profile_kind"))
                support_rows.append(view)
                cells.append(dict(origin=y, fold=k, profile_kind=kind, training_rows=train.height,
                                  training_people=train["player_id"].n_unique(), test_rows=test.height,
                                  sparse_rows=view.filter(pl.col("training_people") < 20).height,
                                  unsupported_rows=view.filter(pl.col("training_people") == 0).height))
    supports = pl.concat(support_rows, how="diagonal_relaxed")
    supports.write_parquet(OUT / "profile-support.parquet")
    scopes = conservation(source, ["source_id", "season", "usage_scope"])
    teams = conservation(source, ["source_id", "season", "team_id"])
    mlb = conservation(source.filter(pl.col("is_mlb")), ["season"])
    assert mlb["unequal_groups"] == 0
    for name, obj in [("scope-conservation.json", scopes), ("team-scope-diagnostic.json", teams)]:
        receipt(name, obj)
    receipt("support-review.json", dict(cells=cells, profile_definitions=profiles,
        all_players_retained=True, opportunity_fits_run=0, support_is_not_predictive_validation=True,
        training_target_is_conditional_exposure_not_talent=True, test_origins=[2022, 2023, 2024],
        target_ceiling=2025, fixed_playing_time_input="preseason_pa", player_separation_checked=True))
    receipt("source-review.json", dict(source_rows=source.height, annual_rows=annual.height,
        source_rows_by_id=source.group_by("source_id").len().sort("source_id").to_dicts(),
        reconstructed_captures=replays, independent_mlb_overlap_rows=overlapping.height,
        exact_mlb_overlap=True, mlb_all_position_out_totals_conserve=True,
        requested_scope_discrepancies=scopes["unequal_groups"], team_scope_discrepancies=teams["unequal_groups"],
        team_scope_certified=False, older_rookie_subtypes_certified=False,
        dsl_normalized_from_explicit_league130=True, minor2020_absent_not_zero=True,
        origin_rows=context.height, label_rows=label_frame.height, forecasts_changed=False,
        protected_outcomes_used=False, new_fits=0, player_walkthrough_status="pending",
        raw_2004_2025_mlb_replay_claim=False,
        qualification="MLB inventory hash/conservation checked and 2021–2025 independently replayed. Older MLB raw captures not replayed here.",
        input_hashes={str(p): sha256_file(p) for p in sorted(set(paths))},
        output_hashes={str(p): sha256_file(p) for p in sorted(OUT.glob("*.parquet"))}))
    protections()
    print(json.dumps(dict(source_rows=source.height, origins=context.height,
                          requested_scope_discrepancies=scopes["unequal_groups"], team_scope_discrepancies=teams["unequal_groups"])))


def review():
    protections()
    source_review = read(OUT / "source-review.json")
    assert not (OUT / "source-final-review.json").exists()
    for p, h in {**source_review["input_hashes"], **source_review["output_hashes"]}.items():
        assert sha256_file(Path(p)) == h
    annual = pl.read_parquet(OUT / "annual-usage.parquet")
    source = pl.read_parquet(OUT / "source.parquet")
    index = index_usage(annual)
    bios, ages, age_paths = identity()
    names = dict(annual.select("player_id", "player_name").unique("player_id").iter_rows())
    def age(pid, y):
        dob = bios.get(pid)
        return (date(y, 7, 1) - dob).days / 365.25 if dob else ages.get((y, pid))
    cases = []
    for pid, y in FIXED:
        h = origin_summary(index.get(pid, []), y)
        assert h["mlb_history_observed"] or h["minor_history_observed"], (pid, y)
        focal_age = age(pid, y)
        peers = []
        eligible_ids = set(annual.filter(pl.col("season") == y)["player_id"])
        for peer in eligible_ids - {pid}:
            other = origin_summary(index.get(peer, []), y)
            if (other["role_evidence_source"], other["primary_start_position"]) != (h["role_evidence_source"], h["primary_start_position"]):
                continue
            peer_age = age(peer, y)
            if focal_age is not None and (peer_age is None or abs(focal_age - peer_age) > 3):
                continue
            distance = abs(math.log1p(h["role_defensive_sample"]) - math.log1p(other["role_defensive_sample"]))
            if focal_age is not None:
                distance += abs(focal_age - peer_age) / 3
            peers.append((distance, peer, other, peer_age))
        selected = sorted(peers, key=lambda p: (p[0], p[1]))[:3]
        assert len(selected) == 3
        records = []
        for who, summary, player_age in [(pid, h, focal_age)] + [(p[1], p[2], p[3]) for p in selected]:
            raw = source.filter((pl.col("player_id") == who) & pl.col("season").is_between(y - 2, y))
            recompute = {}
            for label, mlb_flag in [("mlb", True), ("minor", False)]:
                for measure, positions in [("outs", POSITIONS), ("starts", ROLE_POSITIONS)]:
                    col = "fielding_outs" if measure == "outs" else "games_started"
                    for p in positions:
                        total = sum((0.5 ** (y - r["season"])) * r[col] for r in raw.iter_rows(named=True)
                                    if r["is_mlb"] == mlb_flag and int(r["position_code"]) == p)
                        recompute[f"{label}_weighted_{measure}_{p}"] = total
                        assert total == summary[f"{label}_weighted_{measure}_{p}"]
            records.append(dict(player_id=who, player_name=names[who], age=player_age,
                                source_rows=raw.select(["season", "source_id", "usage_scope", "normalized_level", "league_id", "team_id", "team_name", "position_code", "games_started", "games_played", "source_innings", "fielding_outs", "level_subtype_certified", "team_usage_certified"]).to_dicts(),
                                history=summary, independent_weighted_sums=recompute,
                                benchmark_forecast=None, candidate_forecast=None,
                                reason="Source preparation only; no opportunity prediction fitted."))
        cases.append(dict(focal_player_id=pid, origin=y, player_name=names[pid],
                          selection="Fixed source/role contrast before opportunity fitting", records=records))
    receipt("source-player-walkthrough.json", dict(status="complete", focal_count=len(cases), peer_count=3 * len(cases),
        peer_rule="Same MLB/minor evidence and primary starting position; origin age within 3 years where known; closest log exposure plus age distance, ID tie break. No future results.", cases=cases))
    receipt("source-final-review.json", dict(player_walkthrough_status="complete", source_review_complete=True,
        focal_count=len(cases), peer_count=3 * len(cases), weighted_inputs_independently_recomputed=True,
        disposition="Usable player/scope position history with explicit historical conservation and subtype limits; not team-level allocation or predictive improvement.",
        opportunity_model_fitted=False, defensive_talent_model_changed=False, total_value_validated=False,
        protected_outcomes_used=False, forecast_or_explorer_changed=False,
        next_step="Predeclare one position/opportunity comparison against legacy persistence using fixed playing time, with sparse role fallback and full-cohort value diagnostics.",
        hashes={str(p): sha256_file(p) for p in [OUT / "source-review.json", OUT / "source-player-walkthrough.json", *age_paths]}))
    protections()
    print(json.dumps(dict(source_walks=len(cases), peers=3 * len(cases), status="complete")))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "review"])
    args = parser.parse_args()
    {"prepare": prepare, "review": review}[args.action]()
