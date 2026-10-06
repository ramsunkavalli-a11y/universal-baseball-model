"""Append transparent support warnings and better minor-player peers; no fits."""
import polars as pl

import audit_hitter_big_miss_groups as a
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file


def main():
    p = a.PUBLIC / "audit-completion.json"
    assert not p.exists()
    walks = a.read(a.PUBLIC / "audit-player-walks.json")
    a.verify(walks["hashes"])
    a.verify(a.read(a.PUBLIC / "audit-seal.json")["hashes"])
    original = pl.read_parquet(a.BASE / "profile-support.parquet")
    profiles = original.with_columns(
        (pl.col("profile_people") == 0).alias("exact_profile_absent"),
        (pl.col("profile_people") < 20).alias("exact_profile_under20_warning"),
        pl.col("sparse_profile").alias("coarse_preflight_sparse_profile"),
    )
    assert profiles.select(original.columns).equals(original)
    profiles.write_parquet(a.OUT / "explicit-profile-warnings.parquet")
    q = pl.read_parquet(a.OUT / "audit-rows.parquet")
    keys = ["AAA_0_pa", "AA_0_pa", "pooled_AAA_K", "pooled_AAA_BB", "pooled_AAA_HR",
            "pooled_AA_K", "pooled_AA_BB", "pooled_AA_HR"]
    f = pl.read_parquet(a.BASE / "features-0.parquet")
    q = q.join(f.select("row_id", *[k for k in keys if k not in q.columns]), on="row_id", validate="1:1")
    peers = []
    for c in walks["cases"]:
        if c["origin"]["player_id"] not in [680757, 668804]:
            continue
        r = q.filter(pl.col("row_id") == c["origin"]["row_id"]).row(0, named=True)
        dist = ((pl.col("age") - r["age"]) / 5) ** 2
        for k in keys:
            scale = 300 if k.endswith("_pa") else .1 if k.endswith("_K") else .05
            dist = dist + ((pl.col(k) - r[k]) / scale) ** 2
        part = q.filter((pl.col("origin_year") == r["origin_year"]) &
                        (pl.col("career_group") == r["career_group"]) &
                        (pl.col("player_id") != r["player_id"])).with_columns(dist.alias("distance")).sort("distance", "row_id").head(3)
        peers.append(dict(row_id=r["row_id"], player_name=r["player_name"],
                          original_peer_rule_retained=True,
                          rule="same origin and career group; age/5, AA+AAA PA/300, K/.1, BB+HR/.05; no outcomes",
                          peers=part.select("row_id", "player_id", "player_name", "age", *keys,
                                            "observation_p", "observation_conditional_pa", "observation_pa", "next_pa").to_dicts()))
    save(a.PUBLIC / "audit-support-and-peer-correction.json", dict(
        profiles=profiles.filter(pl.col("row_id").is_in([c["origin"]["row_id"] for c in walks["cases"]])).to_dicts(),
        all_profile_rows=profiles.height,
        exact_zero_rows=profiles.filter(pl.col("exact_profile_absent")).height,
        exact_under20_rows=profiles.filter(pl.col("exact_profile_under20_warning")).height,
        coarse_warning_false_but_exact_zero_rows=profiles.filter(pl.col("exact_profile_absent") & ~pl.col("sparse_profile")).height,
        minor_peer_correction=peers, forecast_changed=False,
        hashes={str(a.OUT / "explicit-profile-warnings.parquet"): sha256_file(a.OUT / "explicit-profile-warnings.parquet")}))
    protections()
    save(p, dict(player_walkthrough_status="complete", cases=len(walks["cases"]),
        replayed_heads=walks["replayed_heads"], new_fits=0, forecasting_defect_fixed=False,
        disposition="Group diagnosis completed; public career-departure repair next under separate contract",
        hashes={str(x): sha256_file(x) for x in [a.PUBLIC / "audit-player-walks.json", a.PUBLIC / "audit-support-and-peer-correction.json",
            a.ROOT / "docs/hitter-big-miss-group-audit-result.md", a.BASE / "profile-support.parquet", Path(__file__)]}))
    print("Group audit complete; explicit exact-profile warnings and minor-peer supplement saved")


if __name__ == "__main__":
    from pathlib import Path
    main()
