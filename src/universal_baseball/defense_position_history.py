"""Cutoff-safe position history; source scope is not a team allocation model."""

from collections import defaultdict
import math

import polars as pl

from universal_baseball.position_role_source import baseball_innings_to_outs

POSITIONS = tuple(range(2, 10))
ROLE_POSITIONS = (*POSITIONS, 10)
SPORT_LEVEL = {11: "AAA", 12: "AA", 13: "Aplus", 14: "A", 15: "Aminus", 16: "ROOKIE_COMBINED"}
LEAGUE_LEVEL = {103: "MLB", 104: "MLB", 112: "AAA", 117: "AAA",
                109: "AA", 111: "AA", 113: "AA", 116: "Aplus", 118: "Aplus",
                126: "Aplus", 110: "A", 122: "A", 123: "A", 121: "COMPLEX",
                124: "COMPLEX", 130: "DSL", 120: "ADVANCED_ROOKIE", 128: "ADVANCED_ROOKIE"}


def normalize(frame, source):
    """Validate measures and annotate only the scope the original request proves."""
    if source not in {"mlb", "early", "repair2019", "modern", "modern2025"}:
        raise ValueError("Unknown source scope")
    out = []
    for r in frame.iter_rows(named=True):
        y, p, league = int(r["season"]), int(r["position_code"]), int(r["league_id"])
        if y > 2025 or y < 2004 or p not in range(1, 11):
            raise ValueError("Unsupported year or position")
        if r["fielding_outs"] != baseball_innings_to_outs(r["source_innings"]):
            raise ValueError("Outs do not reproduce source innings")
        if r["games_started"] < 0 or r["games_played"] < r["games_started"]:
            raise ValueError("Invalid start/game counts")
        if p == 10 and r["fielding_outs"] != 0:
            raise ValueError("DH cannot receive defensive outs")
        if source == "early":
            sport = int(r["sport_id"])
            if sport not in SPORT_LEVEL or not 2009 <= y <= 2019:
                raise ValueError("Wrong early source season/sport")
            level, scope, exact = SPORT_LEVEL[sport], f"sport:{sport}", sport != 16
        elif source == "repair2019":
            if y != 2019 or int(r["sport_id"]) != 5442 or league not in (120, 128):
                raise ValueError("Only disjoint 2019 advanced rookie repair may be added")
            level, scope, exact = "ADVANCED_ROOKIE", f"league:{league}", True
        else:
            if league not in LEAGUE_LEVEL:
                raise ValueError("Unknown league scope")
            level, scope, exact = LEAGUE_LEVEL[league], f"league:{league}", True
            if source == "mlb" and level != "MLB":
                raise ValueError("Non-MLB row in MLB inventory")
            if source == "modern" and not 2021 <= y <= 2024:
                raise ValueError("Wrong modern season")
            if source == "modern2025" and y != 2025:
                raise ValueError("Wrong confirmation season")
        out.append({**r, "source_id": source, "usage_scope": scope,
                    "normalized_level": level, "level_subtype_certified": exact,
                    "team_usage_certified": False, "is_mlb": level == "MLB"})
    result = pl.DataFrame(out, infer_schema_length=None)
    key = ["source_id", "season", "usage_scope", "player_id", "position_code"]
    if result.unique(key).height != result.height:
        raise ValueError("Duplicate player position in a requested source scope")
    return result


def annual_usage(frame):
    """Aggregate mutually disjoint source scopes, without using attached club IDs."""
    group = ["season", "player_id", "is_mlb", "normalized_level"]
    return frame.group_by(group).agg(
        pl.col("player_name").sort().first(),
        pl.col("usage_scope").unique().sort().alias("usage_scopes"),
        pl.col("source_id").unique().sort().alias("source_ids"),
        pl.col("level_subtype_certified").all(),
        pl.len().alias("source_rows"),
        *[pl.col("fielding_outs").filter(pl.col("position_code") == str(p)).sum().alias(f"outs_{p}")
          for p in range(1, 11)],
        *[pl.col("games_started").filter(pl.col("position_code") == str(p)).sum().alias(f"starts_{p}")
          for p in ROLE_POSITIONS],
    ).with_columns(pl.sum_horizontal([f"outs_{p}" for p in POSITIONS]).alias("defensive_outs"))


def index_usage(annual):
    index = defaultdict(list)
    for r in annual.iter_rows(named=True):
        index[int(r["player_id"])].append(r)
    return index


def origin_summary(rows, origin):
    """Describe observed history only; absent evidence has an explicit flag."""
    past = [r for r in rows if origin - 2 <= int(r["season"]) <= origin]
    out = {"minor_2020_canceled_in_window": origin - 2 <= 2020 <= origin}
    for label, is_mlb in [("mlb", True), ("minor", False)]:
        selected = [r for r in past if r["is_mlb"] == is_mlb]
        out[f"{label}_history_observed"] = bool(selected)
        out[f"{label}_latest_season"] = max((r["season"] for r in selected), default=None)
        out[f"{label}_source_rows"] = sum(r["source_rows"] for r in selected)
        out[f"{label}_level_subtype_certified"] = all(r["level_subtype_certified"] for r in selected) if selected else None
        for measure, positions in [("outs", POSITIONS), ("starts", ROLE_POSITIONS)]:
            for p in positions:
                # Zero is a sum within an explicitly marked missing/observed view,
                # never a measurement of zero talent or verified inactivity.
                out[f"{label}_weighted_{measure}_{p}"] = sum(
                    0.5 ** (origin - r["season"]) * r[f"{measure}_{p}"] for r in selected)
        out[f"{label}_weighted_defensive_outs"] = sum(out[f"{label}_weighted_outs_{p}"] for p in POSITIONS)
        out[f"{label}_current_defensive_outs"] = sum(r["defensive_outs"] for r in selected if r["season"] == origin)
    role_source = "mlb" if out["mlb_history_observed"] else "minor" if out["minor_history_observed"] else "unknown"
    out["role_evidence_source"] = role_source
    if role_source == "unknown":
        out["primary_start_position"] = "unknown"
        out["primary_defensive_position"] = "unknown"
        out["role_defensive_sample"] = 0.
    else:
        starts = {p: out[f"{role_source}_weighted_starts_{p}"] for p in ROLE_POSITIONS}
        outs = {p: out[f"{role_source}_weighted_outs_{p}"] for p in POSITIONS}
        out["primary_start_position"] = str(max(starts, key=starts.get)) if max(starts.values()) > 0 else "unknown"
        out["primary_defensive_position"] = str(max(outs, key=outs.get)) if max(outs.values()) > 0 else "unknown"
        out["role_defensive_sample"] = sum(outs.values())
    if not all(math.isfinite(v) for k, v in out.items() if "weighted" in k):
        raise ValueError("Nonfinite historical exposure")
    return out


def support_tags(frame):
    return frame.with_columns(
        pl.when(pl.col("age").is_null()).then(pl.lit("unknown"))
        .otherwise((pl.col("age") // 5).cast(pl.Int64).cast(pl.String)).alias("age_band"),
        pl.when(pl.col("role_defensive_sample") == 0).then(pl.lit("none"))
        .when(pl.col("role_defensive_sample") < 150).then(pl.lit("under150"))
        .when(pl.col("role_defensive_sample") < 1500).then(pl.lit("150to1499"))
        .otherwise(pl.lit("1500plus")).alias("defensive_sample_band"),
    )
