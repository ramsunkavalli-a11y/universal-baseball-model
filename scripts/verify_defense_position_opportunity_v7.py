"""Independent sums and more comparable level-matched source walkthroughs."""

from collections import defaultdict
from datetime import date
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from universal_baseball.defense_position_history import POSITIONS, ROLE_POSITIONS, index_usage, origin_summary
from build_defense_native_range_v3 import identity
from prepare_defense_position_opportunity_v7 import ROOT, OUT, PUBLIC, read, receipt
from run_hitter_finite_return_baseline import protections

LEVEL_RANK = {"MLB": 8, "AAA": 7, "AA": 6, "Aplus": 5, "A": 4, "Aminus": 3,
              "ADVANCED_ROOKIE": 2, "ROOKIE_COMBINED": 1, "COMPLEX": 1, "DSL": 1}


def main():
    protections()
    assert not (OUT / "independent-source-verification.json").exists()
    final = read(OUT / "source-final-review.json")
    assert final["player_walkthrough_status"] == "complete"
    source_review = read(OUT / "source-review.json")
    for p, h in {**source_review["input_hashes"], **source_review["output_hashes"], **final["hashes"]}.items():
        assert sha256_file(Path(p)) == h
    source = pl.read_parquet(OUT / "source.parquet")
    contexts = pl.read_parquet(OUT / "origin-context.parquet")
    annual = pl.read_parquet(OUT / "annual-usage.parquet")
    origins = contexts["origin_year"].unique().to_list()
    weighted = pl.concat([source.with_columns((pl.col("season") + j).alias("origin_year"), pl.lit(0.5 ** j).alias("weight"))
                          for j in range(3)]).filter(pl.col("origin_year").is_in(origins))
    sums = weighted.group_by(["origin_year", "player_id", "is_mlb"]).agg(
        *[(pl.col("weight") * pl.col("fielding_outs")).filter(pl.col("position_code") == str(p)).sum().alias(f"outs_{p}") for p in POSITIONS],
        *[(pl.col("weight") * pl.col("games_started")).filter(pl.col("position_code") == str(p)).sum().alias(f"starts_{p}") for p in ROLE_POSITIONS],
        pl.len().alias("source_rows"), pl.col("season").max().alias("latest"),
        pl.col("level_subtype_certified").all().alias("subtype"),
    )
    checked_values = 0
    for label, is_mlb in [("mlb", True), ("minor", False)]:
        f = sums.filter(pl.col("is_mlb") == is_mlb).drop("is_mlb")
        joined = contexts.join(f, on=["origin_year", "player_id"], how="left", validate="m:1")
        for measure, positions in [("outs", POSITIONS), ("starts", ROLE_POSITIONS)]:
            for p in positions:
                assert np.allclose(joined[f"{label}_weighted_{measure}_{p}"], joined[f"{measure}_{p}"].fill_null(0), atol=0, rtol=0)
                checked_values += joined.height
        assert joined[f"{label}_history_observed"].equals(joined["source_rows"].is_not_null())
        assert joined[f"{label}_source_rows"].equals(joined["source_rows"].fill_null(0).cast(pl.Int64))
        assert joined[f"{label}_latest_season"].cast(pl.Int64).equals(joined["latest"].cast(pl.Int64))
    # These are independently reconstructed exposure outcomes, not talent labels.
    actual = source.filter(pl.col("is_mlb")).group_by(["season", "player_id"]).agg(
        *[pl.col("fielding_outs").filter(pl.col("position_code") == str(p)).sum().alias(f"out_{p}") for p in POSITIONS])
    paired = contexts.select("row_id", "player_id", "target_year").join(actual, left_on=["target_year", "player_id"],
                      right_on=["season", "player_id"], how="left", validate="m:1")
    labels = pl.read_parquet(OUT / "exposure-labels.parquet")
    paired = paired.join(labels, on="row_id", validate="1:1")
    for p in POSITIONS:
        assert paired[f"out_{p}"].fill_null(0).equals(paired[f"actual_outs_{p}"])
    assert contexts.group_by("player_id").agg(pl.col("outer_fold").n_unique()).filter(pl.col("outer_fold") != 1).is_empty()
    assert contexts.filter(pl.col("age_unknown") != 0)["age"].null_count() == contexts.filter(pl.col("age_unknown") != 0).height
    # The original source walkthrough matched broad MLB/minor role evidence.
    # Append stricter stage matches; never erase those original comparisons.
    old_walk = read(OUT / "source-player-walkthrough.json")
    usage = index_usage(annual)
    bios, ages, age_paths = identity()
    names = dict(annual.select("player_id", "player_name").unique("player_id").iter_rows())
    def age(pid, y):
        dob = bios.get(pid)
        return (date(y, 7, 1) - dob).days / 365.25 if dob else ages.get((y, pid))
    def stage(pid, y):
        levels = [r["normalized_level"] for r in usage[pid] if r["season"] == y]
        top = max(levels, key=LEVEL_RANK.get) if levels else None
        return "MLB" if top == "MLB" else "Upper minors" if top in ("AAA", "AA") else "Lower minors" if top else "unknown"
    refined = []
    for c in old_walk["cases"]:
        pid, y = c["focal_player_id"], c["origin"]
        focal = c["records"][0]
        h, focal_age, focal_stage = focal["history"], focal["age"], stage(pid, y)
        pool = []
        for peer in set(annual.filter(pl.col("season") == y)["player_id"]) - {pid}:
            if stage(peer, y) != focal_stage:
                continue
            other = origin_summary(usage[peer], y)
            if (other["role_evidence_source"], other["primary_start_position"]) != (h["role_evidence_source"], h["primary_start_position"]):
                continue
            peer_age = age(peer, y)
            if focal_age is not None and (peer_age is None or abs(focal_age - peer_age) > 3):
                continue
            distance = abs(math.log1p(h["role_defensive_sample"]) - math.log1p(other["role_defensive_sample"]))
            if focal_age is not None:
                distance += abs(focal_age - peer_age) / 3
            pool.append((distance, peer, other, peer_age))
        selected = sorted(pool, key=lambda r: (r[0], r[1]))[:3]
        records = []
        for distance, who, history, player_age in selected:
            raw = source.filter((pl.col("player_id") == who) & pl.col("season").is_between(y - 2, y))
            for label, flag in [("mlb", True), ("minor", False)]:
                for measure, positions in [("outs", POSITIONS), ("starts", ROLE_POSITIONS)]:
                    col = "fielding_outs" if measure == "outs" else "games_started"
                    for p in positions:
                        v = sum(0.5 ** (y - r["season"]) * r[col] for r in raw.iter_rows(named=True)
                                if r["is_mlb"] == flag and int(r["position_code"]) == p)
                        assert v == history[f"{label}_weighted_{measure}_{p}"]
            records.append(dict(player_id=who, player_name=names[who], age=player_age,
                                stage=focal_stage, age_source="immutable birth date" if who in bios else "origin panel reported age",
                                distance=distance, history=history,
                                source_rows=raw.select("season", "normalized_level", "usage_scope", "position_code", "games_started", "fielding_outs").to_dicts()))
        refined.append(dict(player_name=c["player_name"], player_id=pid, origin=y, focal=focal,
                            focal_stage=focal_stage, focal_age_source="immutable birth date" if pid in bios else "origin panel reported age",
                            eligible_peer_count=len(pool), peers=records, fewer_than_three=len(records) < 3,
                            interpretation="Stage-matched source comparison, not proof of a MLB defensive-skill forecast."))
    receipt("stage-matched-source-walkthrough.json", dict(status="complete", focal_count=len(refined),
        peer_count=sum(len(r["peers"]) for r in refined),
        peer_rule="Same current MLB/upper-minors/lower-minors stage, primary starting role, MLB/minor history evidence; age within 3 years when known, then log exposure plus age distance. Fewer than three retained where genuine support is sparse.",
        correction="Original broader peers are preserved. These add current stage separation, particularly for De La Cruz and Eldridge.", cases=refined))
    receipt("independent-source-verification.json", dict(all_origin_rows=contexts.height,
        weighted_position_values_reconstructed_from_source=checked_values,
        independent_eight_position_outcome_labels=labels.height,
        no_held_player_fold_movement=True, unknown_age_not_imputed_as_known=True,
        player_walkthrough_status="complete", refined_peer_count=sum(len(r["peers"]) for r in refined),
        source_preparation_complete=True, opportunity_fits_run=0, defensive_talent_validated=False,
        forecasts_or_explorer_changed=False, protected_outcomes_used=False,
        qualification="Quality and exposure remain separate; later acquired fielding history is not a vintage preseason roster/depth chart.",
        hashes={str(p): sha256_file(p) for p in [Path(__file__), OUT / "source-final-review.json", OUT / "stage-matched-source-walkthrough.json", *age_paths]}))
    protections()
    print(json.dumps(dict(origins=contexts.height, independent_weighted_values=checked_values,
                          stage_matched_peers=sum(len(r["peers"]) for r in refined))))


if __name__ == "__main__":
    main()
