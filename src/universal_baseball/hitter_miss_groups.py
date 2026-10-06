"""Origin-only diagnostic groups and exact signed value-error accounting."""

import numpy as np
import polars as pl

FIELDS = [
    "row_id", "career_mlb_observed_pa", "work_0", "work_1", "work_2",
    "last_MLB_quality", "AAA_0_pa", "AA_0_pa", "ctx_foreign_history_known",
    "status_major_link", "status_minor_agreement", "status_released",
    "obs_status_finite_nonmedical", "obs_status_unresolved_nonmedical",
    "status_medical_evidence_open", "employment_evidence_unknown",
]


def groups(q, inputs, medical):
    extra = [n for n in FIELDS if n not in q.columns]
    g = q.join(inputs.select("row_id", *extra), on="row_id", validate="1:1")
    assert g.height == q.height
    g = g.join(medical.select("row_id", "observation_state", "recent_history_coverage_complete"), on="row_id", validate="1:1")
    g = g.with_columns(pl.max_horizontal("work_0", "work_1", "work_2").alias("best_recent_MLB_PA"))
    regular = pl.col("best_recent_MLB_PA") >= 300
    g = g.with_columns(
        pl.when(pl.col("prior_debut") == 0)
        .then(pl.when((pl.col("AAA_0_pa") + pl.col("AA_0_pa")) > 0)
              .then(pl.lit("no_debut_upper_minors")).otherwise(pl.lit("no_debut_lower_or_other")))
        .when(pl.col("pa_0") == 0)
        .then(pl.when(regular).then(pl.lit("established_MLB_gap"))
              .otherwise(pl.lit("former_MLB_no_recent_regular")))
        .when(pl.col("pa_0") < 200)
        .then(pl.when(regular).then(pl.lit("established_brief_current_MLB"))
              .otherwise(pl.lit("brief_current_MLB_no_recent_regular")))
        .when(pl.col("pa_0") < 400).then(pl.lit("current_MLB_200_399"))
        .otherwise(pl.lit("current_MLB_400_plus")).alias("career_group"),
        pl.when(pl.col("age") <= 25).then(pl.lit("through25"))
        .when(pl.col("age") <= 33).then(pl.lit("26to33"))
        .otherwise(pl.lit("34plus")).alias("age_group"),
        pl.when(pl.col("status_retired") > 0).then(pl.lit("captured_retirement"))
        .when(pl.col("status_hard_unavailable") > 0).then(pl.lit("known_hard_unavailable"))
        .when(pl.col("obs_status_unresolved_nonmedical") > 0).then(pl.lit("unresolved_nonmedical"))
        .when(pl.col("obs_status_finite_nonmedical") > 0).then(pl.lit("finite_nonmedical"))
        .when(pl.col("status_released") > 0).then(pl.lit("reported_release"))
        .when(pl.col("status_major_link") > 0).then(pl.lit("major_link"))
        .when(pl.col("status_minor_agreement") > 0).then(pl.lit("minor_agreement"))
        .otherwise(pl.lit("other_or_unknown")).alias("opportunity_group"),
        (pl.col("last_MLB_quality") > 1).alias("high_prior_MLB_quality"),
    )
    return g


def account(g, arm="observation"):
    rate = pl.col(arm + "_rate") / 600 + pl.col("origin_replacement_rate")
    g = g.with_columns(
        (pl.col(arm + "_pa") - pl.col("next_pa")).alias("pa_error"),
        (pl.col(arm + "_value") - pl.col("actual_relative_value")).alias("value_error"),
        ((pl.col(arm + "_pa") - pl.col("next_pa")) * rate).alias("value_PA_term"),
        (pl.col("next_pa") * rate - pl.col("actual_relative_value")).alias("value_rate_term"),
    )
    if not np.allclose(g["value_PA_term"] + g["value_rate_term"], g["value_error"], atol=1e-10, rtol=0):
        raise ValueError("Value accounting disagrees with saved forecast")
    return g


def summary(g, arm="observation"):
    if not g.height:
        return {"rows": 0}
    active = g.filter(pl.col("next_pa") > 0)
    return dict(
        rows=g.height, people=g["player_id"].n_unique(),
        predicted_pa=float(g[arm + "_pa"].sum()), actual_pa=int(g["next_pa"].sum()),
        predicted_value=float(g[arm + "_value"].sum()), actual_value=float(g["actual_relative_value"].sum()),
        pa_rmse=float(((g[arm + "_pa"] - g["next_pa"]) ** 2).mean() ** .5),
        value_rmse=float(((g[arm + "_value"] - g["actual_relative_value"]) ** 2).mean() ** .5),
        predicted_active=float(g[arm + "_p"].sum()), actual_active=active.height,
        conditional_pa_rmse=float(((active[arm + "_conditional_pa"] - active["next_pa"]) ** 2).mean() ** .5) if active.height else None,
        mean_predicted_conditional_pa=float(g[arm + "_conditional_pa"].mean()),
        mean_actual_pa_if_active=float(active["next_pa"].mean()) if active.height else None,
    )
