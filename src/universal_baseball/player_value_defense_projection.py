"""Frozen Defense v1 historical projection helpers for Player Value.

The functions in this module reproduce the already-selected T1/U1/C2/F1
prediction semantics.  They do not fit parameters, select candidates, convert
skills to runs, or inspect target-season defensive outcomes.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import math
from pathlib import Path
from typing import Any

import polars as pl


SEASONS = {2021, 2022, 2023, 2024}
LEVEL_BY_LEAGUE = {
    103: "MLB",
    104: "MLB",
    112: "AAA",
    117: "AAA",
    109: "AA",
    111: "AA",
    113: "AA",
    116: "HIGH_A",
    118: "HIGH_A",
    126: "HIGH_A",
    110: "SINGLE_A",
    122: "SINGLE_A",
    123: "SINGLE_A",
    121: "ROOKIE_COMPLEX",
    124: "ROOKIE_COMPLEX",
    130: "ROOKIE_COMPLEX",
}
LEVEL_RANK = {
    "ROOKIE_COMPLEX": 1,
    "SINGLE_A": 2,
    "HIGH_A": 3,
    "AA": 4,
    "AAA": 5,
    "MLB": 6,
}
POSITION_ORDER = {"C": 2, "1B": 3, "2B": 4, "3B": 5, "SS": 6, "LF": 7, "CF": 8, "RF": 9}
GENERAL_POSITIONS = frozenset({"1B", "2B", "3B", "SS", "LF", "CF", "RF"})
GENERAL_FEATURES = (
    "fielding_pct",
    "range_factor_per_9",
    "errors_per_9",
    "throwing_errors_per_9",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _infer_context(path: Path) -> tuple[int, int]:
    parts = list(path.parts)
    for index, part in enumerate(parts[:-1]):
        try:
            season = int(part)
        except ValueError:
            continue
        if season not in SEASONS or index + 1 >= len(parts):
            continue
        try:
            league_id = int(parts[index + 1])
        except ValueError:
            continue
        if league_id in LEVEL_BY_LEAGUE:
            return season, league_id
    raise RuntimeError(f"cannot infer season/league from {path}")


def _integer(value: Any, *, field: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {field}")
    numeric = float(str(value).strip())
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid nonnegative integer {field}: {value!r}")
    return int(numeric)


def _innings_to_outs(value: Any) -> int:
    text = str(value if value is not None else "").strip()
    if not text:
        raise ValueError("missing innings")
    whole, separator, fraction = text.partition(".")
    if not separator:
        fraction = "0"
    if not whole.isdigit() or fraction not in {"0", "1", "2"}:
        raise ValueError(f"invalid baseball innings: {text!r}")
    return int(whole) * 3 + int(fraction)


def load_frozen_fielding_profiles(source_root: Path) -> tuple[pl.DataFrame, dict[str, int]]:
    """Load the certified fielding capture with the frozen Defense parser semantics."""

    paths = sorted(source_root.rglob("fielding_offset_*.json"))
    if not paths:
        raise RuntimeError("no certified fielding capture pages found")

    rows: list[dict[str, Any]] = []
    observed_pairs: set[tuple[int, int]] = set()
    for path in paths:
        season, league_id = _infer_context(path)
        observed_pairs.add((season, league_id))
        level_group = LEVEL_BY_LEAGUE[league_id]
        payload = json.loads(path.read_text(encoding="utf-8"))
        groups = payload.get("stats") or []
        if len(groups) != 1:
            raise RuntimeError(f"expected one stats group in {path}")
        for raw_split in groups[0].get("splits") or []:
            split = _mapping(raw_split)
            player = _mapping(split.get("player") or split.get("person"))
            position = str(_mapping(split.get("position")).get("abbreviation") or "").strip()
            if position not in POSITION_ORDER:
                continue
            stat = _mapping(split.get("stat"))
            is_catcher = position == "C"
            rows.append(
                {
                    "season": season,
                    "league_id": league_id,
                    "level_group": level_group,
                    "level_rank": LEVEL_RANK[level_group],
                    "player_id": _integer(player.get("id"), field="player.id"),
                    "position": position,
                    "position_order": POSITION_ORDER[position],
                    "fielding_outs": _innings_to_outs(stat.get("innings")),
                    "put_outs": _integer(stat.get("putOuts"), field="putOuts"),
                    "assists": _integer(stat.get("assists"), field="assists"),
                    "chances": _integer(stat.get("chances"), field="chances"),
                    "errors": _integer(stat.get("errors"), field="errors"),
                    "throwing_errors": _integer(stat.get("throwingErrors"), field="throwingErrors"),
                    "caught_stealing": _integer(stat.get("caughtStealing"), field="caughtStealing") if is_catcher else 0,
                    "stolen_bases": _integer(stat.get("stolenBases"), field="stolenBases") if is_catcher else 0,
                    "passed_balls": _integer(stat.get("passedBall"), field="passedBall") if is_catcher else 0,
                }
            )

    expected_pairs = {(season, league_id) for season in SEASONS for league_id in LEVEL_BY_LEAGUE}
    if observed_pairs != expected_pairs:
        raise RuntimeError(
            "certified source pair mismatch "
            f"missing={sorted(expected_pairs - observed_pairs)} "
            f"unexpected={sorted(observed_pairs - expected_pairs)}"
        )

    raw = pl.DataFrame(rows)
    highest_level = (
        raw.filter(pl.col("fielding_outs") > 0)
        .group_by(["season", "player_id"])
        .agg(pl.col("level_rank").max().alias("current_level_rank"))
        .with_columns(
            pl.col("current_level_rank")
            .replace_strict(
                {rank: level for level, rank in LEVEL_RANK.items()},
                return_dtype=pl.Utf8,
            )
            .alias("current_level_group")
        )
        .select("season", "player_id", "current_level_group")
    )
    position = (
        raw.group_by(["season", "player_id", "position", "position_order"])
        .agg(
            pl.col("fielding_outs").sum(),
            pl.col("put_outs").sum(),
            pl.col("assists").sum(),
            pl.col("chances").sum(),
            pl.col("errors").sum(),
            pl.col("throwing_errors").sum(),
            pl.col("caught_stealing").sum(),
            pl.col("stolen_bases").sum(),
            pl.col("passed_balls").sum(),
        )
        .join(highest_level, on=["season", "player_id"], how="left")
        .with_columns(
            pl.when(pl.col("chances") > 0)
            .then((pl.col("put_outs") + pl.col("assists")) / pl.col("chances"))
            .otherwise(None)
            .alias("fielding_pct"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * (pl.col("put_outs") + pl.col("assists")) / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("range_factor_per_9"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("errors") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("errors_per_9"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("throwing_errors") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("throwing_errors_per_9"),
            (pl.col("caught_stealing") + pl.col("stolen_bases")).alias("steal_attempts"),
            pl.when((pl.col("caught_stealing") + pl.col("stolen_bases")) > 0)
            .then(pl.col("caught_stealing") / (pl.col("caught_stealing") + pl.col("stolen_bases")))
            .otherwise(None)
            .alias("caught_stealing_pct"),
            pl.when(pl.col("fielding_outs") > 0)
            .then(27.0 * pl.col("passed_balls") / pl.col("fielding_outs"))
            .otherwise(None)
            .alias("passed_balls_per_9"),
        )
        .sort(["season", "player_id", "position"])
    )
    return position, {
        "capture_page_count": len(paths),
        "raw_position_split_count": raw.height,
        "player_season_position_count": position.height,
    }


def tracked_range_z_lookup(frame: pl.DataFrame) -> dict[tuple[int, str, int, str], float]:
    eligible = frame.filter(
        pl.col("position_abbreviation").is_in(sorted(GENERAL_POSITIONS))
        & (pl.col("opportunities") >= 100)
        & pl.col("tracked_oaa_per_100").is_not_null()
    )
    moments = eligible.group_by(["season", "level_group", "position_abbreviation"]).agg(
        pl.col("tracked_oaa_per_100").mean().alias("mean"),
        pl.col("tracked_oaa_per_100").std(ddof=0).alias("sd"),
        pl.len().alias("n"),
    )
    scored = (
        eligible.join(moments, on=["season", "level_group", "position_abbreviation"], how="left")
        .filter((pl.col("n") >= 20) & pl.col("sd").is_not_null() & (pl.col("sd") > 1e-12))
        .with_columns(((pl.col("tracked_oaa_per_100") - pl.col("mean")) / pl.col("sd")).alias("tracked_z"))
    )
    return {
        (int(row["season"]), str(row["level_group"]), int(row["player_id"]), str(row["position_abbreviation"])): float(row["tracked_z"])
        for row in scored.select("season", "level_group", "player_id", "position_abbreviation", "tracked_z").iter_rows(named=True)
    }


def tracked_framing_z_lookup(frame: pl.DataFrame) -> dict[tuple[int, str, int], float]:
    eligible = frame.filter(
        (pl.col("takes") >= 500)
        & pl.col("tracked_framing_per_1000_takes").is_not_null()
    )
    moments = eligible.group_by(["season", "level_group"]).agg(
        pl.col("tracked_framing_per_1000_takes").mean().alias("mean"),
        pl.col("tracked_framing_per_1000_takes").std(ddof=0).alias("sd"),
        pl.len().alias("n"),
    )
    scored = (
        eligible.join(moments, on=["season", "level_group"], how="left")
        .filter((pl.col("n") >= 15) & pl.col("sd").is_not_null() & (pl.col("sd") > 1e-12))
        .with_columns(((pl.col("tracked_framing_per_1000_takes") - pl.col("mean")) / pl.col("sd")).alias("tracked_z"))
    )
    return {
        (int(row["season"]), str(row["level_group"]), int(row["player_id"])): float(row["tracked_z"])
        for row in scored.select("season", "level_group", "player_id", "tracked_z").iter_rows(named=True)
    }


def _normalization_moment(
    normalization: Mapping[str, Any],
    *,
    feature: str,
    position: str,
    level_group: str,
) -> tuple[float, float]:
    for row in normalization["cell"]:
        if row["feature"] == feature and row["position"] == position and row["level_group"] == level_group:
            return float(row["mean"]), float(row["sd"])
    for row in normalization["position"]:
        if row["feature"] == feature and row["position"] == position:
            return float(row["mean"]), float(row["sd"])
    for row in normalization["global"]:
        if row["feature"] == feature:
            return float(row["mean"]), float(row["sd"])
    raise ValueError(f"missing frozen normalization for {feature}/{position}/{level_group}")


def predict_general_range_skill(
    profile: Mapping[str, Any] | None,
    *,
    tracked_z: float | None,
    parameters: Mapping[str, Any],
) -> tuple[float, str]:
    """Apply the frozen T1 -> U1 -> B0 hierarchy to one player-position row."""

    if profile is None:
        return 0.0, "B0"
    position = str(profile["position"])
    if (
        position not in GENERAL_POSITIONS
        or int(profile["fielding_outs"]) < 300
        or int(profile["chances"]) < 100
        or profile.get("current_level_group") is None
        or any(profile.get(feature) is None for feature in GENERAL_FEATURES)
    ):
        return 0.0, "B0"

    level_group = str(profile["current_level_group"])
    normalization = parameters["normalization"]
    features: list[float] = []
    for feature in GENERAL_FEATURES:
        mean, sd = _normalization_moment(
            normalization,
            feature=feature,
            position=position,
            level_group=level_group,
        )
        features.append((float(profile[feature]) - mean) / sd)

    if level_group == "MLB" and tracked_z is not None and math.isfinite(float(tracked_z)):
        coefficients = [float(value) for value in parameters["tracked_mlb"]["coefficients"]]
        values = [1.0, *features, float(tracked_z)]
        return sum(left * right for left, right in zip(coefficients, values, strict=True)), "T1"

    coefficients = [float(value) for value in parameters["universal"]["coefficients"]]
    values = [1.0, *features]
    return sum(left * right for left, right in zip(coefficients, values, strict=True)), "U1"


def predict_catcher_c2_skill(
    current: Mapping[str, Any] | None,
    prior: Mapping[str, Any] | None,
    *,
    parameters: Mapping[str, Any],
    component: str,
) -> tuple[float, str]:
    """Apply repaired C2 with its frozen eligibility and exposure weighting."""

    if component not in {"throwing", "blocking"}:
        raise ValueError(f"unsupported catcher component: {component}")
    if current is None or int(current["fielding_outs"]) < 300:
        return 0.0, "B0"

    feature = str(parameters["feature"])
    if current.get(feature) is None:
        return 0.0, "B0"
    if component == "throwing" and int(current["steal_attempts"]) < 10:
        return 0.0, "B0"

    normalization = parameters["normalization"]
    mean = float(normalization["mean"])
    sd = float(normalization["sd"])
    current_z = (float(current[feature]) - mean) / sd
    current_exposure = float(current["steal_attempts"] if component == "throwing" else current["fielding_outs"])
    feature_value = current_z

    prior_eligible = (
        prior is not None
        and int(prior["fielding_outs"]) >= 300
        and prior.get(feature) is not None
        and (component != "throwing" or int(prior["steal_attempts"]) >= 10)
    )
    if prior_eligible:
        assert prior is not None
        prior_z = (float(prior[feature]) - mean) / sd
        prior_exposure = float(prior["steal_attempts"] if component == "throwing" else prior["fielding_outs"])
        prior_weight = float(parameters["prior_season_recency_weight"])
        feature_value = (
            current_exposure * current_z + prior_weight * prior_exposure * prior_z
        ) / (current_exposure + prior_weight * prior_exposure)

    coefficients = [float(value) for value in parameters["coefficients"]]
    return coefficients[0] + coefficients[1] * feature_value, "C2"


def predict_framing_skill(
    current: Mapping[str, Any] | None,
    *,
    tracked_z: float | None,
    parameters: Mapping[str, Any],
) -> tuple[float, str]:
    if (
        current is None
        or int(current["fielding_outs"]) < 300
        or str(current.get("current_level_group")) != "MLB"
        or tracked_z is None
        or not math.isfinite(float(tracked_z))
    ):
        return 0.0, "F0"
    coefficients = [float(value) for value in parameters["coefficients"]]
    return coefficients[0] + coefficients[1] * float(tracked_z), "F1"
