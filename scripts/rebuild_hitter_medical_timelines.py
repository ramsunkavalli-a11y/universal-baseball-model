"""Source-only reconstruction, exact row joins, fold support and retained cases."""

import argparse
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.medical_observation_timeline import rebuild, union_days
from universal_baseball.storage import sha256_file
from prepare_hitter_status_evidence import sources
from repair_hitter_nonmedical_observation import verified_windows
from run_hitter_employment_comparison import ROOT, read, verify
from run_hitter_finite_return_baseline import protections, save

GEN = ROOT / "reports/generated"
OUT = GEN / "hitter-medical-timeline-repair"
PUBLIC = ROOT / "reports/model-evidence/hitter-medical-timeline-repair"
BASE = GEN / "hitter-nonmedical-opportunity"
TRACK = GEN / "hitter-statcast-full-history"
LEDGER = GEN / "hitter-status-evidence-v2/status-ledger.json"
FIXED = [
    (581527, 2016),
    (665487, 2022),
    (656555, 2023),
    (453056, 2018),
    (670541, 2022),
    (596748, 2016),
    (607680, 2022),
    (519390, 2016),
    (592192, 2016),
    (592450, 2024),
]
FIELDS = [
    "observation_state",
    "recent_history_coverage_complete",
    "recent_episode_count",
    "recent_placement_reports",
    "recent_surgery_report_count",
    "recent_followup_calendar_upper_days",
    "recent_censored_followup_upper_days",
    "pending_observation",
    "true_injury_days",
    "medical_recovery_certified",
]


def load_sources():
    population, _, records, _, _, paths, _ = sources()
    seal = read(GEN / "hitter-status-evidence-v2/source-seal.json")
    verify({str(ROOT / p): h for p, h in seal["source_hashes"].items()})
    approval = read(TRACK / "final-source-review.json")
    assert approval["source_walkthrough_status"] == "complete"
    report = read(TRACK / "source-report.json")
    assert sha256_file(TRACK / "source-report.json") == approval["source_report_sha256"]
    oldcomplete = read(
        ROOT / "reports/model-evidence/hitter-role-health-separation/completion.json"
    )
    verify(oldcomplete["hashes"])
    assert oldcomplete["player_walkthrough_status"] == "complete"
    overrides = TRACK / "split-game-venue-overrides.json"
    assert sha256_file(overrides) == report["output_hashes"][str(overrides)]
    excluded = {r["game_pk"] for r in read(overrides)["overrides"]}
    appearances = {}
    sourcecounts = []
    for y in range(2015, 2025):
        path = TRACK / f"launch-events-{y}.parquet"
        assert sha256_file(path) == report["output_hashes"][str(path)]
        paths.append(path)
        q = pl.read_parquet(
            path, columns=["season", "game_date", "game_pk", "player_id"]
        )
        assert set(q["season"]) == {y} and q["game_date"].null_count() == 0
        assert q["game_date"].dt.year().eq(y).all()
        conflicts = q.group_by("game_pk").agg(
            pl.col("game_date").n_unique().alias("dates")
        )
        omitted = excluded | set(conflicts.filter(pl.col("dates") > 1)["game_pk"])
        unique = q.filter(~pl.col("game_pk").is_in(omitted)).unique()
        sourcecounts.append(
            dict(
                year=y,
                positive_player_games=len(unique),
                source_people=unique["player_id"].n_unique(),
                excluded_contact_rows=q["game_pk"].is_in(omitted).sum(),
            )
        )
        for r in unique.select("player_id", "game_date", "game_pk").iter_rows(
            named=True
        ):
            appearances.setdefault(r["player_id"], []).append(r)
    winpath = GEN / "practical-hitter-late-role-v46/source-manifest.json"
    winmanifest = read(winpath)
    windows, checks = verified_windows(winmanifest)
    paths.extend(
        [
            winpath,
            GEN / "practical-hitter-late-role-v46/windows.parquet",
            LEDGER,
            TRACK / "source-report.json",
            TRACK / "final-source-review.json",
            overrides,
            GEN / "hitter-status-evidence-v2/source-seal.json",
            GEN / "practical-hitter-opportunity-status-v59/open-spell-report.json",
            BASE / "features-0.parquet",
            BASE / "predictions.parquet",
            BASE / "preflight.json",
            ROOT / "src/universal_baseball/medical_observation_timeline.py",
            ROOT / "tests/test_medical_observation_timeline.py",
            ROOT / "docs/hitter-medical-timeline-repair-contract.md",
            Path(__file__),
            ROOT
            / "reports/model-evidence/hitter-role-health-separation/travis-2016-official-gamelog.json",
        ]
    )
    paths.extend(Path(c["path"]) for c in winmanifest["sources"])
    for pid in appearances:
        appearances[pid].sort(key=lambda r: (r["game_date"], r["game_pk"]))
    return population, records, appearances, windows, paths, sourcecounts, checks


def summarize(old, new, row_id=None):
    origin = old["origin_year"]
    intervals = [
        (s["start"], s["end"] or old["information_date"])
        for s in old["clinical_spells"]
    ]
    olddays = union_days(intervals, date(origin - 1, 1, 1), date(origin + 1, 1, 1))
    oldspells = [
        s
        for s in old["clinical_spells"]
        if date.fromisoformat(s["end"] or old["information_date"])
        >= date(origin - 1, 1, 1)
    ]
    return dict(
        candidate_key=old["candidate_key"],
        row_id=row_id,
        player_id=old["player_id"],
        origin_year=origin,
        information_date=old["information_date"],
        **{k: new[k] for k in FIELDS},
        old_medical_open=old["status_medical_evidence_open"],
        old_medical_scope_interrupted=old["status_medical_scope_interrupted"],
        old_followup_union_days=olddays,
        old_overlapping_episode_count=len(oldspells),
        followup_days_removed=olddays - new["recent_followup_calendar_upper_days"]
        if new["recent_history_coverage_complete"]
        else None,
        episode_count_added=new["recent_episode_count"] - len(oldspells)
        if new["recent_history_coverage_complete"]
        else None,
    )


def build():
    assert not OUT.exists(), "Preserve completed or partial reconstruction"
    protections()
    population, records, apps, windows, paths, counts, checks = load_sources()
    ledger = {r["candidate_key"]: r for r in read(LEDGER)["rows"]}
    assert len(ledger) == len(population) == 83300
    OUT.mkdir()
    save(
        OUT / "source-seal.json",
        dict(
            before_reconstruction=True,
            new_fits=0,
            hashes={str(p): sha256_file(p) for p in set(paths)},
        ),
    )
    frame = pl.read_parquet(BASE / "features-0.parquet")
    rowids = {
        (r["origin_year"], r["player_id"]): r["row_id"]
        for r in frame.select("origin_year", "player_id", "row_id").to_dicts()
    }
    summaries, reconstructed = [], {}
    for i, p in enumerate(population):
        pid, y, key = p["player_id"], p["origin_year"], p["candidate_key"]
        old = ledger[key]
        assert old["information_date"] == p["information_date"]
        new = rebuild(
            pid,
            records.get(pid, []),
            apps.get(pid, []),
            windows.get(pid, []),
            p["information_date"],
            y,
        )
        summaries.append(summarize(old, new, rowids.get((y, pid))))
        if new["spells"]:
            reconstructed[key] = new
        if (i + 1) % 15000 == 0:
            print(f"Reconstructed {i + 1} of 83,300 source origins", flush=True)
    summary = pl.DataFrame(
        summaries,
        infer_schema_length=None,
        schema_overrides={"row_id": pl.Int64, "true_injury_days": pl.Int64},
    )
    assert summary.height == summary["candidate_key"].n_unique() == 83300
    summary.write_parquet(OUT / "source-observations.parquet")
    model = frame.select(
        "row_id",
        "player_id",
        "origin_year",
        "age",
        "stage",
        "pa_0",
        "ctx_information_date",
    )
    model = model.join(
        summary.filter(pl.col("row_id").is_not_null()).drop("player_id", "origin_year"),
        on="row_id",
        how="left",
        validate="1:1",
    )
    assert model.height == 63314 and model["candidate_key"].null_count() == 0
    assert model["information_date"].eq(model["ctx_information_date"]).all()
    model.write_parquet(OUT / "model-observations.parquet")
    save(OUT / "reconstructed-spells.json", dict(origins=reconstructed))
    profiles, support = [], []
    pre = read(BASE / "preflight.json")
    # Source support in actual existing subsets. No fitting or outcome exclusion beyond
    # the existing active-head subset; missing clinical coverage stays a separate profile.
    for c in pre["cells"]:
        f = pl.read_parquet(
            BASE / f"features-{c['fold']}.parquet",
            columns=["row_id", "next_pa", "outer_fold", "target_year"],
        )
        for head, ids in [
            ("participation", c["training_row_ids"]),
            ("conditional_pa", c["training_row_ids"]),
        ]:
            sub = f.filter(pl.col("row_id").is_in(ids))
            if head == "conditional_pa":
                sub = sub.filter(pl.col("next_pa") > 0)
            assert sub["target_year"].max() <= c["year"]
            assert not sub["outer_fold"].eq(c["fold"]).any()
            tr = model.join(
                sub.select("row_id"), on="row_id", how="inner", validate="1:1"
            )
            te = model.filter(pl.col("row_id").is_in(c["test_row_ids"]))

            def tag(g):
                return g.with_columns(
                    (pl.col("age") // 5).alias("age_band"),
                    pl.when(pl.col("pa_0") == 0)
                    .then(pl.lit("no_current_MLB_PA"))
                    .when(pl.col("pa_0") < 300)
                    .then(pl.lit("brief_or_part_time"))
                    .otherwise(pl.lit("established_workload"))
                    .alias("workload"),
                )

            keys = [
                "observation_state",
                "recent_history_coverage_complete",
                "age_band",
                "workload",
            ]
            people = (
                tag(tr)
                .group_by(keys)
                .agg(pl.col("player_id").n_unique().alias("source_profile_people"))
            )
            flags = (
                tag(te)
                .select("row_id", *keys)
                .join(people, on=keys, how="left", validate="m:1")
            )
            flags = flags.with_columns(
                pl.col("source_profile_people").fill_null(0),
                pl.lit(c["year"]).alias("origin"),
                pl.lit(c["fold"]).alias("fold"),
                pl.lit(head).alias("head"),
            )
            profiles.append(flags)
            support.append(
                dict(
                    origin=c["year"],
                    fold=c["fold"],
                    head=head,
                    training_rows=len(tr),
                    training_people=tr["player_id"].n_unique(),
                    complete_history_training_people=tr.filter(
                        pl.col("recent_history_coverage_complete")
                    )["player_id"].n_unique(),
                    missing_profile_rows=int(
                        (flags["source_profile_people"] == 0).sum()
                    ),
                )
            )
    pl.concat(profiles).write_parquet(OUT / "profile-support.parquet")
    fixed = list(FIXED)
    comparable = model.filter(pl.col("followup_days_removed").is_not_null())
    for col in ["followup_days_removed", "episode_count_added"]:
        row = comparable.sort([col, "row_id"], descending=[True, False]).row(
            0, named=True
        )
        pair = row["player_id"], row["origin_year"]
        if pair not in fixed:
            fixed.append(pair)
    save(
        OUT / "case-selection.json",
        dict(
            cases=fixed,
            fixed_cases=FIXED,
            added_rule="largest removed union follow-up days and added episodes; no future outcomes",
        ),
    )
    save(
        OUT / "build-receipt.json",
        dict(
            population_rows=len(summary),
            model_rows=len(model),
            source_counts=counts,
            verified_positive_window_cells=checks,
            support=support,
            states=summary.group_by("observation_state")
            .len()
            .sort("observation_state")
            .to_dicts(),
            changed_open_rows=summary.filter(
                pl.col("old_medical_open") & ~pl.col("pending_observation")
            ).height,
            observed_use_after_old_open_rows=summary.filter(
                pl.col("old_medical_open")
                & (pl.col("observation_state") == "observed_MLB_use")
            ).height,
            removed_span_rows=comparable.filter(
                pl.col("followup_days_removed") > 0
            ).height,
            added_episode_rows=comparable.filter(
                pl.col("episode_count_added") > 0
            ).height,
            new_fits=0,
            forecasts_changed=False,
            protected_2026_outcomes_used=False,
            hashes={str(p): sha256_file(p) for p in OUT.glob("*") if p.is_file()},
        ),
    )
    protections()
    print("Source and all 70 source-support subsets rebuilt; no fits", flush=True)


def review():
    assert not PUBLIC.exists()
    receipt = read(OUT / "build-receipt.json")
    verify(receipt["hashes"])
    verify(read(OUT / "source-seal.json")["hashes"])
    population, records, apps, windows, _, _, _ = load_sources()
    population = {p["candidate_key"]: p for p in population}
    ledger = {r["candidate_key"]: r for r in read(LEDGER)["rows"]}
    rebuilt = read(OUT / "reconstructed-spells.json")["origins"]
    observations = pl.read_parquet(OUT / "model-observations.parquet")
    q = pl.read_parquet(BASE / "predictions.parquet")
    stats = pl.read_parquet(GEN / "practical-hitter-v31/dated-stints.parquet")
    profiles = pl.read_parquet(OUT / "profile-support.parquet")
    walks, checked = [], 0
    for pid, y in read(OUT / "case-selection.json")["cases"]:
        key = f"{y}:{pid}"
        p, old = population[key], ledger[key]
        new = rebuild(
            pid,
            records.get(pid, []),
            apps.get(pid, []),
            windows.get(pid, []),
            p["information_date"],
            y,
        )
        # Compare decoded serialized dates with fresh reconstruction.
        from json import dumps, loads

        assert loads(dumps(new, default=str)) == rebuilt.get(
            key, loads(dumps(new, default=str))
        )
        future = dict(
            player_id=pid,
            transaction_id=-999999,
            event_date=date(y, 1, 1),
            available_date=date(y + 1, 12, 31),
            kind="other",
            il_kind="placement",
            category="upper",
            surgery=True,
        )
        assert new == rebuild(
            pid,
            records.get(pid, []) + [future],
            apps.get(pid, []),
            windows.get(pid, []),
            p["information_date"],
            y,
        )
        row = observations.filter(
            (pl.col("player_id") == pid) & (pl.col("origin_year") == y)
        ).row(0, named=True)
        assert all(row[k] == new[k] for k in FIELDS)
        saved = q.filter(pl.col("row_id") == row["row_id"]).to_dicts()
        pool = observations.filter(
            (pl.col("origin_year") == y)
            & (pl.col("player_id") != pid)
            & (pl.col("old_medical_open") == row["old_medical_open"])
            & (
                pl.col("old_medical_scope_interrupted")
                == row["old_medical_scope_interrupted"]
            )
        )
        pool = (
            pool.with_columns(
                (
                    (pl.col("age") - row["age"]) ** 2 / 25
                    + ((pl.col("pa_0") - row["pa_0"]) / 300) ** 2
                ).alias("distance")
            )
            .sort(["distance", "player_id"])
            .head(3)
        )
        peers = pool.join(
            q.select("row_id", "player_name", "observation_pa", "next_pa"),
            on="row_id",
            how="left",
            validate="1:1",
        )
        walks.append(
            dict(
                player_id=pid,
                origin=y,
                name=p["player_name"],
                row_id=row["row_id"],
                information_date=p["information_date"],
                old_clinical_spells=old["clinical_spells"],
                supplied_source_summary=row,
                rebuilt_medical_observation=new,
                dated_relevant_transactions=[
                    r
                    for r in records.get(pid, [])
                    if r["available_date"] <= date.fromisoformat(p["information_date"])
                    and r["event_date"] >= date(y - 2, 1, 1)
                ],
                appearance_evidence=[
                    r
                    for r in apps.get(pid, [])
                    if date(y - 1, 1, 1)
                    <= r["game_date"]
                    <= date.fromisoformat(p["information_date"])
                ],
                origin_known_stats=stats.filter(
                    (pl.col("player_id") == pid) & pl.col("season").is_between(y - 2, y)
                )
                .select(
                    "season",
                    "bucket",
                    "plate_appearances",
                    "home_runs",
                    "strike_outs",
                    "base_on_balls",
                )
                .to_dicts(),
                unchanged_forecast=[
                    {
                        k: r[k]
                        for k in [
                            "player_name",
                            "observation_p",
                            "observation_conditional_pa",
                            "observation_pa",
                            "observation_rate",
                            "observation_value",
                            "next_pa",
                            "actual_relative_value",
                        ]
                    }
                    for r in saved
                ],
                source_support=profiles.filter(
                    pl.col("row_id") == row["row_id"]
                ).to_dicts(),
                peer_rule="Same origin and old open/censored flags, nearest age/5 and MLB PA/300, no future outcomes",
                peers=peers.to_dicts(),
                future_mutation_invariant=True,
                new_forecast=None,
            )
        )
        checked += 1
    # Independent official positive dates, already saved before this repair.
    logpath = (
        ROOT
        / "reports/model-evidence/hitter-role-health-separation/travis-2016-official-gamelog.json"
    )
    log = read(logpath)["stats"][0]["splits"]
    direct = [
        dict(
            player_id=581527,
            game_pk=s["game"]["gamePk"],
            game_date=date.fromisoformat(s["date"]),
        )
        for s in log
        if s["stat"]["plateAppearances"] > 0
    ]
    key = "2016:581527"
    o = rebuilt[key]
    official = rebuild(
        581527, records[581527], direct, windows[581527], o["information_date"], 2016
    )
    first = next(s for s in o["spells"] if s["start"] == "2016-03-25")
    matched = next(s for s in official["spells"] if s["start"] == date(2016, 3, 25))
    assert (
        first["observation_end_upper"]
        == str(matched["observation_end_upper"])
        == "2016-05-25"
    )
    assert first["closure_kind"] == matched["closure_kind"] == "observed_MLB_use"
    PUBLIC.mkdir(parents=True)
    save(
        PUBLIC / "player-walks.json",
        dict(cases=walks, player_walkthrough_status="pending_judgment"),
    )
    save(
        PUBLIC / "report.json",
        dict(
            **{k: v for k, v in receipt.items() if k != "hashes"},
            fixed_cases_reconstructed_independently=checked,
            travis_official_log_return_upper="2016-05-25",
            true_injury_days_certified=False,
            predictive_improvement_established=False,
            source_correction_implemented=True,
            player_walkthrough_status="pending_judgment",
            hashes={
                str(p): sha256_file(p)
                for p in [
                    OUT / "build-receipt.json",
                    PUBLIC / "player-walks.json",
                    logpath,
                ]
            },
        ),
    )
    protections()
    print(
        f"{checked} source walks reconstructed; Travis agrees with official log",
        flush=True,
    )


def finalize():
    report = read(PUBLIC / "report.json")
    verify(report["hashes"])
    verify(read(OUT / "source-seal.json")["hashes"])
    verify(read(OUT / "build-receipt.json")["hashes"])
    f = pl.read_parquet(OUT / "source-observations.parquet")
    assert f.height == 83300 and not f["medical_recovery_certified"].any()
    assert f["true_injury_days"].null_count() == len(f)
    assert (
        f.filter(~pl.col("recent_history_coverage_complete"))[
            "recent_followup_calendar_upper_days"
        ].null_count()
        == f.filter(~pl.col("recent_history_coverage_complete")).height
    )
    w = read(PUBLIC / "player-walks.json")["cases"]
    assert all(
        c["future_mutation_invariant"]
        and c["origin_known_stats"]
        and c["peer_rule"]
        and c["new_forecast"] is None
        for c in w
    )
    doc = ROOT / "docs/hitter-medical-timeline-repair-result.md"
    assert "Walkthrough status: complete" in doc.read_text(encoding="utf8")
    protections()
    save(
        PUBLIC / "completion.json",
        dict(
            player_walkthrough_status="complete",
            source_table_approved_for_separately_contracted_experiment=True,
            clinical_recovery_model_validated=False,
            source_repair_complete=True,
            new_fits=0,
            forecasts_changed=False,
            protected_2026_outcomes_used=False,
            hashes={
                str(p): sha256_file(p)
                for p in [
                    doc,
                    PUBLIC / "report.json",
                    PUBLIC / "player-walks.json",
                    Path(__file__),
                ]
            },
        ),
    )
    print("Source repair complete; no forecast/clinical prediction claim", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["build", "review", "finalize"])
    {"build": build, "review": review, "finalize": finalize}[
        parser.parse_args().phase
    ]()
