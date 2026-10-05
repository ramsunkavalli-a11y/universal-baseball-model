"""Append missing named controls and verify the original fold-source support."""

import json
from datetime import date

import polars as pl

import rebuild_hitter_medical_timelines as repair
from universal_baseball.medical_observation_timeline import rebuild
from universal_baseball.storage import sha256_file


def main():
    target = repair.PUBLIC / "identity-review.json"
    assert not target.exists(), "Preserve the supplementary source review"
    receipt = repair.read(repair.OUT / "build-receipt.json")
    repair.verify(receipt["hashes"])
    repair.verify(repair.read(repair.OUT / "source-seal.json")["hashes"])
    pre = repair.read(repair.BASE / "preflight.json")
    repair.verify({str(repair.ROOT / p): h for p, h in pre["hashes"].items()})
    population, records, apps, windows, _, _, _ = repair.load_sources()
    population = {r["candidate_key"]: r for r in population}
    ledger = {r["candidate_key"]: r for r in repair.read(repair.LEDGER)["rows"]}
    observations = pl.read_parquet(repair.OUT / "model-observations.parquet")
    saved_spells = repair.read(repair.OUT / "reconstructed-spells.json")["origins"]
    predictions = pl.read_parquet(repair.BASE / "predictions.parquet")
    statpath = repair.GEN / "practical-hitter-v31/dated-stints.parquet"
    stats = pl.read_parquet(statpath)
    profiles = pl.read_parquet(repair.OUT / "profile-support.parquet")
    walks = []
    for pid, y, name in [
        (664247, 2022, "Kyle Garlick"),
        (592620, 2016, "Jarrett Parker"),
    ]:
        key = f"{y}:{pid}"
        p, old = population[key], ledger[key]
        assert p["player_name"] == name
        new = rebuild(
            pid,
            records[pid],
            apps.get(pid, []),
            windows.get(pid, []),
            p["information_date"],
            y,
        )
        assert json.loads(json.dumps(new, default=str)) == saved_spells[key]
        row = observations.filter(pl.col("candidate_key") == key).row(0, named=True)
        assert all(row[k] == new[k] for k in repair.FIELDS)
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
            records[pid] + [future],
            apps.get(pid, []),
            windows.get(pid, []),
            p["information_date"],
            y,
        )
        pool = observations.filter(
            (pl.col("origin_year") == y)
            & (pl.col("player_id") != pid)
            & (pl.col("old_medical_open") == row["old_medical_open"])
            & (
                pl.col("old_medical_scope_interrupted")
                == row["old_medical_scope_interrupted"]
            )
        ).with_columns(
            (
                (pl.col("age") - row["age"]) ** 2 / 25
                + ((pl.col("pa_0") - row["pa_0"]) / 300) ** 2
            ).alias("distance")
        )
        peers = (
            pool.sort(["distance", "player_id"])
            .head(3)
            .join(
                predictions.select(
                    "row_id", "player_name", "observation_pa", "next_pa"
                ),
                on="row_id",
                how="left",
                validate="1:1",
            )
        )
        walks.append(
            dict(
                name=name,
                player_id=pid,
                origin=y,
                row_id=row["row_id"],
                information_date=p["information_date"],
                old_clinical_spells=old["clinical_spells"],
                supplied_source_summary=row,
                rebuilt_medical_observation=new,
                dated_relevant_transactions=[
                    r
                    for r in records[pid]
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
                unchanged_forecast=predictions.filter(pl.col("row_id") == row["row_id"])
                .select(
                    "player_name",
                    "observation_p",
                    "observation_conditional_pa",
                    "observation_pa",
                    "observation_rate",
                    "observation_value",
                    "next_pa",
                    "actual_relative_value",
                )
                .to_dicts(),
                source_support=profiles.filter(
                    pl.col("row_id") == row["row_id"]
                ).to_dicts(),
                peers=peers.to_dicts(),
                peer_rule="Same origin and old open/censored flags; nearest age/5 and MLB PA/300; no future outcomes",
                future_mutation_invariant=True,
                new_forecast=None,
            )
        )
    # Independently recount, rather than trusting the exported support numbers.
    actual_checks = 0
    for c in pre["cells"]:
        features = pl.read_parquet(
            repair.BASE / f"features-{c['fold']}.parquet",
            columns=["row_id", "next_pa", "outer_fold", "target_year"],
        )
        train = features.filter(pl.col("row_id").is_in(c["training_row_ids"]))
        assert train["target_year"].max() <= c["year"]
        assert not train["outer_fold"].eq(c["fold"]).any()
        for head in ["participation", "conditional_pa"]:
            ids = (
                train
                if head == "participation"
                else train.filter(pl.col("next_pa") > 0)
            )
            t = observations.join(
                ids.select("row_id"), on="row_id", how="inner", validate="1:1"
            )
            flags = profiles.filter(
                (pl.col("origin") == c["year"])
                & (pl.col("fold") == c["fold"])
                & (pl.col("head") == head)
            )
            assert set(flags["row_id"]) == set(c["test_row_ids"])
            for g in flags.partition_by(
                [
                    "observation_state",
                    "recent_history_coverage_complete",
                    "age_band",
                    "workload",
                ],
                maintain_order=True,
            ):
                state, complete, age, workload = g.select(
                    "observation_state",
                    "recent_history_coverage_complete",
                    "age_band",
                    "workload",
                ).row(0)
                p = t.filter(
                    (pl.col("observation_state") == state)
                    & (pl.col("recent_history_coverage_complete") == complete)
                    & ((pl.col("age") // 5) == age)
                )
                if workload == "no_current_MLB_PA":
                    p = p.filter(pl.col("pa_0") == 0)
                elif workload == "brief_or_part_time":
                    p = p.filter(pl.col("pa_0").is_between(1, 299))
                else:
                    p = p.filter(pl.col("pa_0") >= 300)
                assert g["source_profile_people"].eq(p["player_id"].n_unique()).all()
            actual_checks += 1
    repair.protections()
    repair.save(
        target,
        dict(
            amended_identity_pairs_verified=True,
            additional_cases=walks,
            original_case_count=12,
            total_reviewed_player_origins=14,
            unique_reviewed_people=13,
            all_actual_source_support_subsets_recounted=actual_checks,
            fixed_contract_names_complete=True,
            new_fits=0,
            forecasts_changed=False,
            hashes={
                str(p): sha256_file(p)
                for p in [
                    *[repair.BASE / f"features-{i}.parquet" for i in range(5)],
                    statpath,
                    repair.ROOT / "docs/hitter-medical-timeline-review-amendment.md",
                    repair.ROOT / "scripts/complete_hitter_medical_source_review.py",
                    repair.PUBLIC / "report.json",
                    repair.PUBLIC / "player-walks.json",
                ]
            },
        ),
    )
    print(
        f"Intended Garlick/Parker controls replayed; all {actual_checks} support subsets agree"
    )


if __name__ == "__main__":
    main()
