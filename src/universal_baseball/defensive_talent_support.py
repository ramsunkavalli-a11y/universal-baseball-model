"""Measurement and chronological support only; no fitted talent forecasts."""

from collections import defaultdict
import math

POSITIONS = (4, 5, 6)
WINDOWS = (3, 5, 7)
LAST_OUTCOME = 2025


def age_band(age):
    if age is None or not math.isfinite(age):
        return "unknown"
    return "<=20" if age <= 20 else "21-24" if age <= 24 else "25-29" if age <= 29 else "30+"


def profile(row):
    return (row.get("level") or "unknown", age_band(row.get("age")),
            row["position"], row["prior_mlb_defense"])


def measurable(raw, official, positions):
    """Aggregate runs are attributable only when both usage sources isolate the group."""
    if not raw or not official:
        return False
    total = raw.get("outs_total")
    value = raw.get("range_runs")
    if total is None or total <= 0 or value is None or not math.isfinite(value):
        return False
    # Null native exposure is not an observed zero.
    if any(raw.get(f"outs_{p}") is None for p in range(2, 10)):
        return False
    if sum(raw[f"outs_{p}"] for p in positions) != total:
        return False
    if any(raw[f"outs_{p}"] != 0 for p in range(2, 10) if p not in positions):
        return False
    if any(official.get(f"outs_{p}") is None for p in range(2, 10)):
        return False
    return (sum(official[f"outs_{p}"] for p in positions) > 0
            and all(official[f"outs_{p}"] == 0 for p in range(2, 10) if p not in positions))


def window_label(row, horizon, native_by_player, official_by_player):
    origin, pid, pos = row["origin_year"], row["player_id"], row["position"]
    years = range(origin + 1, min(origin + horizon, LAST_OUTCOME) + 1)
    native = native_by_player.get(pid, {})
    official = official_by_player.get(pid, {})
    paths = []
    for year in years:
        r, o = native.get(year), official.get(year)
        paths.append({
            "season": year,
            "native_present": r is not None,
            "official_present": o is not None,
            "native_outs": r.get("outs_total") if r else None,
            "same_position_outs": r.get(f"outs_{pos}") if r else None,
            "range_runs": r.get("range_runs") if r else None,
            "native_position_outs": {str(p): r.get(f"outs_{p}") for p in range(2, 10)} if r else None,
            "official_position_outs": {str(p): o.get(f"outs_{p}") for p in range(2, 10)} if o else None,
            "official_outs": o.get("official_outs") if o else None,
            "same_position_measurable": measurable(r, o, (pos,)),
            "infield_group_measurable": measurable(r, o, POSITIONS),
        })
    mature = origin + horizon <= LAST_OUTCOME
    same = [r for r in paths if r["same_position_measurable"]]
    group = [r for r in paths if r["infield_group_measurable"]]
    same_outs = sum(r["native_outs"] for r in same)
    group_outs = sum(r["native_outs"] for r in group)
    sufficient = same_outs >= 1500 and len(same) >= 2
    group_sufficient = group_outs >= 1500 and len(group) >= 2
    future_official = sum(r["official_outs"] or 0 for r in paths)
    future_native = sum(r["native_outs"] or 0 for r in paths)
    any_same = any((r["same_position_outs"] or 0) > 0 for r in paths)
    if not mature:
        status = "window_incomplete"
    elif sufficient:
        status = "measured_quality"
    elif future_official == 0 and future_native == 0:
        status = "no_recorded_mlb_fielding"
    elif not any_same:
        status = "no_native_same_position_exposure"
    elif not same:
        status = "no_isolated_same_position_measurement"
    else:
        status = "insufficient_isolated_measurement"
    mean_elapsed = sum((r["season"] - origin) * r["native_outs"] for r in same) / same_outs if same_outs else None
    return {
        **row, "horizon": horizon, "window_end": origin + horizon,
        "window_mature": mature, "quality_status": status,
        "future_official_outs": future_official, "future_native_outs": future_native,
        "same_position_seasons": len(same), "same_position_outs": same_outs,
        "same_position_range_runs": sum(r["range_runs"] for r in same),
        "observed_same_position_rate": 1500 * sum(r["range_runs"] for r in same) / same_outs if same_outs else None,
        "quality_rate": 1500 * sum(r["range_runs"] for r in same) / same_outs if mature and sufficient else None,
        "measurement_mean_elapsed": mean_elapsed,
        "measurement_mean_age": row["age"] + mean_elapsed if row.get("age") is not None and mean_elapsed is not None else None,
        "infield_group_seasons": len(group), "infield_group_outs": group_outs,
        "infield_group_quality_available": mature and group_sufficient,
        "infield_group_observed_rate": 1500 * sum(r["range_runs"] for r in group) / group_outs if group_outs else None,
        "infield_group_outs_4": sum(r["native_position_outs"]["4"] for r in group),
        "infield_group_outs_5": sum(r["native_position_outs"]["5"] for r in group),
        "infield_group_outs_6": sum(r["native_position_outs"]["6"] for r in group),
    }, paths


def training_snapshot(labels, origin, fold, horizon, group=False):
    """Only mature historical labels for other players are available at this cutoff."""
    available = (lambda r: r["infield_group_quality_available"]) if group else (lambda r: r["quality_rate"] is not None)
    train = [r for r in labels if r["horizon"] == horizon and r["origin_year"] < origin
             and r["window_end"] <= origin and r["player_id"] % 5 != fold and available(r)]
    counts = defaultdict(set)
    for row in train:
        counts[profile(row)].add(row["player_id"])
    people = {r["player_id"] for r in train}
    origins = {r["origin_year"] for r in train}
    assert all(r["window_mature"] for r in train)
    assert not any(r["player_id"] % 5 == fold for r in train)
    return {"origin": origin, "fold": fold, "horizon": horizon,
            "target": "infield_group" if group else "same_position",
            "training_rows": len(train), "training_people": len(people),
            "training_origins": sorted(origins),
            "small_comparison_count_screen": len(people) >= 30 and len(origins) >= 2}, counts
