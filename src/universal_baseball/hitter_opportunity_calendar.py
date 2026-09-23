"""Saved-head diagnostics only; no fitting or deployable forecast selection."""
from __future__ import annotations

import numpy as np
import polars as pl

KEYS = ["origin_year", "player_id"]


def regime(origin: int) -> str:
    if origin == 2018:
        return "shortened_target_2020"
    if origin == 2019:
        return "pandemic_bridge_to_2021"
    if origin in (2016, 2017):
        return "ordinary_pre"
    if origin in (2021, 2022, 2023):
        return "ordinary_post"
    raise ValueError("Unsupported diagnostic origin")


def _finite(frame, columns):
    for col in columns:
        if frame[col].null_count() or not np.isfinite(frame[col].to_numpy()).all():
            raise ValueError(f"Missing or nonfinite {col}")


def prepare_rows(history, base, updates):
    """Match exact saved cohorts; allow no silent row loss or label replacement."""
    for frame in (history, base, updates):
        if frame.unique(KEYS).height != frame.height:
            raise ValueError("Duplicate player/origin")
    if history["origin_year"].max() + 2 > 2025:
        raise ValueError("Protected outcomes cannot enter this diagnostic")
    if history.join(base, on=KEYS, how="anti").height or base.join(history, on=KEYS, how="anti").height:
        raise ValueError("Mismatched historical cohorts")
    if updates.join(base, on=KEYS, how="anti").height:
        raise ValueError("Opportunity update outside the matched cohort")
    _finite(updates, ["p1", "pa1", "actual_pa", "p0", "pa0"])
    old = base.select(*KEYS, pl.col("activity_h2").alias("base_p"),
                      pl.col("expected_pa_h2").alias("base_pa"),
                      pl.col("pa_h2").alias("base_label"))
    new = updates.select(*KEYS, pl.col("p1").alias("update_p"),
        pl.col("pa1").alias("update_pa"), pl.col("actual_pa").alias("update_label"),
        pl.col("p0").alias("update_original_p"), pl.col("pa0").alias("update_original_pa"))
    result = history.join(old, on=KEYS, validate="1:1").join(new, on=KEYS, how="left", validate="1:1").sort(KEYS)
    _finite(result, ["base_p", "base_pa", "base_label", "pa_h2", "war_h2", "performance_anchor",
                     "activity_h2_challenger", "conditional_pa_h2_challenger"])
    np.testing.assert_array_equal(result["pa_h2"], result["base_label"])
    changed = result.filter(pl.col("update_p").is_not_null())
    _finite(changed, ["update_p", "update_pa", "update_label", "update_original_p", "update_original_pa"])
    for a, b in (("update_label", "base_label"), ("update_original_p", "base_p"), ("update_original_pa", "base_pa")):
        np.testing.assert_allclose(changed[a], changed[b], rtol=1e-12, atol=1e-12)
    result = result.with_columns(
        pl.coalesce("update_p", "base_p").alias("old_p"),
        (pl.col("base_pa") / pl.col("base_p")).alias("old_q"),
        pl.col("activity_h2_challenger").alias("new_p"),
        pl.col("conditional_pa_h2_challenger").alias("new_q"),
        pl.Series("regime", [regime(y) for y in result["origin_year"]]))
    if changed.height:
        np.testing.assert_allclose(changed["update_pa"], changed["update_p"] * changed["base_pa"] / changed["base_p"], rtol=1e-12, atol=1e-12)
    validate_heads(result)
    if result.filter(pl.col("pa_h2") < 0).height:
        raise ValueError("Negative actual PA")
    if result.filter((pl.col("pa_h2") == 0) & (pl.col("war_h2") != 0)).height:
        raise ValueError("Nonzero production without play")
    return result


def validate_heads(frame):
    _finite(frame, ["old_p", "old_q", "new_p", "new_q"])
    for prefix in ("old", "new"):
        p, q = frame[f"{prefix}_p"].to_numpy(), frame[f"{prefix}_q"].to_numpy()
        if np.any((p <= 0) | (p > 1)) or np.any(q < 0):
            raise ValueError("Invalid opportunity head")


def exact_contributions(loss00, loss10, loss01, loss11):
    """Symmetric head-swap attribution, not causal effect estimation."""
    activity = ((loss10 - loss00) + (loss11 - loss01)) / 2
    conditional = ((loss01 - loss00) + (loss11 - loss10)) / 2
    np.testing.assert_allclose(activity + conditional, loss11 - loss00, rtol=1e-10, atol=1e-8)
    return activity, conditional


def score_rows(frame, exposure=1.0):
    validate_heads(frame)
    if not np.isfinite(exposure) or not 0 < exposure <= 1:
        raise ValueError("Invalid hindsight exposure fraction")
    if exposure != 1 and set(frame["origin_year"]) != {2018}:
        raise ValueError("Hindsight exposure sensitivity is limited to target 2020")
    pa, war = frame["pa_h2"].to_numpy(), frame["war_h2"].to_numpy()
    active = pa > 0
    rate = frame["performance_anchor"].to_numpy()
    p0, p1 = frame["old_p"].to_numpy(), frame["new_p"].to_numpy()
    q0, q1 = frame["old_q"].to_numpy() * exposure, frame["new_q"].to_numpy() * exposure
    series = []
    for prefix, p, q in (("old", p0, q0), ("new", p1, q1)):
        safe = np.clip(p, 1e-8, 1 - 1e-8)
        values = {"brier": (p-active)**2, "log_loss": -(active*np.log(safe)+(~active)*np.log1p(-safe)),
                  "conditional_pa": q, "conditional_error": q-pa, "conditional_mse": (q-pa)**2,
                  "conditional_mae": abs(q-pa), "pa_error": p*q-pa, "pa_mae": abs(p*q-pa)}
        series.extend(pl.Series(f"{prefix}_{name}", value) for name, value in values.items())
    pa_losses, value_losses = {}, {}
    for name, p, q in (("00", p0, q0), ("10", p1, q0), ("01", p0, q1), ("11", p1, q1)):
        expected_pa = p*q
        pa_losses[name] = (expected_pa-pa)**2
        value_losses[name] = (expected_pa*rate/600-war)**2
        series.extend([pl.Series(f"pa_{name}", expected_pa), pl.Series(f"pa_loss_{name}", pa_losses[name]),
                       pl.Series(f"value_loss_{name}", value_losses[name])])
    for name, losses in (("pa", pa_losses), ("value", value_losses)):
        a, q = exact_contributions(*(losses[k] for k in ("00", "10", "01", "11")))
        series.extend([pl.Series(f"{name}_activity_contribution", a), pl.Series(f"{name}_conditional_contribution", q)])
    return frame.with_columns(series)


def mean_origin(frame, column):
    if frame.is_empty():
        return None
    ordered = frame.sort(KEYS)
    return float(np.mean([g[column].to_numpy().mean() for g in ordered.partition_by("origin_year", maintain_order=True)]))


def summarize(frame):
    active = frame.filter(pl.col("pa_h2") > 0)
    result = {"rows": frame.height, "players": frame["player_id"].n_unique(),
              "origins": sorted(frame["origin_year"].unique().to_list()), "active_rows": active.height,
              "active_origins": active["origin_year"].n_unique(), "actual_pa": mean_origin(frame, "pa_h2"),
              "actual_activity": mean_origin(frame.with_columns((pl.col("pa_h2") > 0).cast(pl.Float64).alias("active")), "active"),
              "actual_pa_if_active": mean_origin(active, "pa_h2")}
    for prefix, combo in (("old", "00"), ("new", "11")):
        record = {k: mean_origin(frame, f"{prefix}_{k}") for k in ("brier", "log_loss", "pa_error", "pa_mae")}
        record.update({"predicted_activity": mean_origin(frame, f"{prefix}_p"), "expected_pa": mean_origin(frame, f"pa_{combo}"),
                       "pa_mse": mean_origin(frame, f"pa_loss_{combo}"), "value_mse_fixed_anchor": mean_origin(frame, f"value_loss_{combo}")})
        record["pa_rmse"] = float(np.sqrt(record["pa_mse"]))
        record["conditional_pa"] = mean_origin(active, f"{prefix}_conditional_pa")
        record["conditional_bias"] = mean_origin(active, f"{prefix}_conditional_error")
        record["conditional_mae"] = mean_origin(active, f"{prefix}_conditional_mae")
        mse = mean_origin(active, f"{prefix}_conditional_mse")
        record["conditional_rmse"] = float(np.sqrt(mse)) if mse is not None else None
        result[prefix] = record
    for target in ("pa", "value"):
        result[f"{target}_head_swap"] = {"activity": mean_origin(frame, f"{target}_activity_contribution"),
            "conditional_pa": mean_origin(frame, f"{target}_conditional_contribution"),
            "mse_by_combination": {k: mean_origin(frame, f"{target}_loss_{k}") for k in ("00", "10", "01", "11")}}
    return result
