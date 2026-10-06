"""Audit saved forecasts by origin-known groups; no models or outcomes refitted."""

from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_miss_groups import FIELDS, groups, account, summary
from universal_baseball.storage import sha256_file
from run_hitter_employment_comparison import ROOT, read, verify
from run_hitter_finite_return_baseline import save, protections

BASE = ROOT / "reports/generated/hitter-nonmedical-opportunity"
SOURCE = ROOT / "reports/generated/hitter-medical-timeline-repair"
PUBLIC = ROOT / "reports/model-evidence/hitter-big-miss-group-repair"
OUT = ROOT / "reports/generated/hitter-big-miss-group-repair"


def main():
    assert not PUBLIC.exists() and not OUT.exists()
    protections()
    verify(read(BASE / "final-review.json")["hashes"])
    verify(read(BASE / "preflight.json")["hashes"])
    verify(read(ROOT / "reports/model-evidence/hitter-medical-opportunity-comparison/completion.json")["hashes"])
    paths = [Path(__file__), ROOT / "src/universal_baseball/hitter_miss_groups.py", ROOT / "tests/test_hitter_miss_groups.py",
             ROOT / "docs/hitter-big-miss-group-repair-plan.md", BASE / "predictions.parquet", SOURCE / "model-observations.parquet",
             *[BASE / f"features-{k}.parquet" for k in range(5)]]
    PUBLIC.mkdir(parents=True)
    OUT.mkdir(parents=True)
    save(PUBLIC / "audit-seal.json", dict(new_fits=0, hashes={str(p): sha256_file(p) for p in paths}))
    q = pl.read_parquet(BASE / "predictions.parquet").sort("row_id")
    assert q.height == 30519 and q["target_year"].max() == 2025
    fs = [pl.read_parquet(BASE / f"features-{k}.parquet").sort("row_id") for k in range(5)]
    for f in fs[1:]:
        assert f.select(FIELDS).equals(fs[0].select(FIELDS))
    medical = pl.read_parquet(SOURCE / "model-observations.parquet")
    g = account(groups(q, fs[0], medical))
    g.write_parquet(OUT / "audit-rows.parquet")
    selections = []
    for label, column in [("PA", "pa_error"), ("value", "value_error")]:
        chosen = g.with_columns(pl.col(column).abs().alias("size")).sort(["size", "row_id"], descending=[True, False]).head(50)
        selections.extend(dict(row_id=r["row_id"], reason="top50_absolute_" + label) for r in chosen.iter_rows(named=True))
    save(PUBLIC / "case-selection.json", dict(rules="top50 absolute PA and value, ascending row ID ties", selected=selections))
    ids = {r["row_id"] for r in selections}
    cols = ["row_id", "player_id", "player_name", "origin_year", "ctx_information_date", "age", "stage", "pa_0", "career_group", "opportunity_group",
            "observation_state", "best_recent_MLB_PA", "last_MLB_quality", "observation_p", "observation_conditional_pa", "observation_pa", "observation_rate",
            "observation_value", "next_pa", "actual_relative_value", "pa_error", "value_error", "value_PA_term", "value_rate_term"]
    save(PUBLIC / "large-misses.json", dict(rows=g.filter(pl.col("row_id").is_in(ids)).select(cols).sort("row_id").to_dicts()))
    scores = []
    scopes = [("all", g), ("past_MLB", g.filter(pl.col("prior_debut") > 0))]
    for key in ["career_group", "opportunity_group", "observation_state", "age_group", "high_prior_MLB_quality", "origin_year"]:
        scopes += [(key + "=" + str(v), g.filter(pl.col(key) == v)) for v in sorted(g[key].unique().to_list())]
    for key, part in scopes:
        scores.append(dict(group=key, **summary(part), earlier_selected_architecture=summary(part, "repaired_domestic"),
                           top50_PA=sum(r["row_id"] in set(part["row_id"]) for r in selections if r["reason"] == "top50_absolute_PA"),
                           top50_value=sum(r["row_id"] in set(part["row_id"]) for r in selections if r["reason"] == "top50_absolute_value"),
                           mean_signed_value_PA_term=float(part["value_PA_term"].mean()),
                           mean_signed_value_rate_term=float(part["value_rate_term"].mean())))
    active = g.filter(pl.col("next_pa") > 0)
    assert np.allclose(g["observation_pa"], g["observation_p"] * g["observation_conditional_pa"], atol=1e-10, rtol=0)
    save(PUBLIC / "group-audit.json", dict(scores=scores, rows=g.height,
        active_only_scores_not_full_population=True, actual_active=active.height, selected_miss_rows=len(ids),
        signed_accounting_not_additive_MSE_shares=True, player_walkthrough_status="pending", new_fits=0,
        hashes={str(p): sha256_file(p) for p in [OUT / "audit-rows.parquet", PUBLIC / "audit-seal.json", PUBLIC / "case-selection.json", PUBLIC / "large-misses.json"]}))
    print(f"Grouped {g.height} forecasts; {len(ids)} distinct large-miss rows; no new fits")


if __name__ == "__main__":
    main()
