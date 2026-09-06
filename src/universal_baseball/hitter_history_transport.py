"""Competition normalization from same-player, same-season level contrasts."""

from itertools import combinations
import numpy as np
import polars as pl
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import normalize_level

OUTCOMES = list(HITTER_TALENT_OUTCOMES)
LEVELS = ("RK", "A", "A+", "AA", "AAA", "MLB")


def canonical_level(value):
    return dict(
        zip(("ROOKIE_COMPLEX", "SINGLE_A", "HIGH_A", "AA", "AAA", "MLB"), LEVELS)
    )[normalize_level(value)]


NODES = {
    "plate_appearance": (["K"], [o for o in OUTCOMES if o != "K"]),
    "non_k": (["UBB"], [o for o in OUTCOMES if o not in ("K", "UBB")]),
    "contact": (["HR"], [o for o in OUTCOMES if o not in ("K", "UBB", "HBP", "HR")]),
    "non_hr_contact": (
        ["1B", "2B", "3B", "ROE", "FC_REACH"],
        ["SF", "MULTI_OUT", "OTHER_OUT"],
    ),
}
MASKS = [
    ([OUTCOMES.index(o) for o in a], [OUTCOMES.index(o) for o in b])
    for a, b in NODES.values()
]


def transform(p, shifts):
    """Move only four common branch odds, preserving all conditional rare ratios."""
    q = np.asarray(p, dtype=float).copy()
    shifts = np.broadcast_to(shifts, (len(q), 4))
    if (
        not np.isfinite(q).all()
        or (q < 0).any()
        or not np.allclose(q.sum(axis=1), 1, atol=1e-10, rtol=0)
    ):
        raise ValueError("Invalid terminal distribution")
    if not np.isfinite(shifts).all():
        raise ValueError("Invalid level effects")
    for j, (left, right) in enumerate(MASKS):
        a = q[:, left].sum(axis=1)
        b = q[:, right].sum(axis=1)
        denominator = a * np.exp(shifts[:, j]) + b
        new_a = np.divide(
            (a + b) * a * np.exp(shifts[:, j]),
            denominator,
            out=np.zeros_like(a),
            where=denominator > 0,
        )
        new_b = a + b - new_a
        q[:, left] *= np.divide(new_a, a, out=np.ones_like(a), where=a > 0)[:, None]
        q[:, right] *= np.divide(new_b, b, out=np.ones_like(b), where=b > 0)[:, None]
    return q


def aggregate(history, cutoff):
    if history["season"].max() > cutoff:
        raise ValueError("History crosses forecast cutoff")
    if history.filter(
        (pl.col("season") == 2020) & (pl.col("level_group").str.to_uppercase() != "MLB")
    ).height:
        raise ValueError("2020 MiLB cannot be constructed")
    return (
        history.with_columns(
            pl.col("level_group").map_elements(canonical_level, return_dtype=pl.String)
        )
        .group_by("player_id", "season", "level_group")
        .agg(pl.col(o).sum() for o in OUTCOMES)
        .with_columns(pl.sum_horizontal(OUTCOMES).alias("pa"))
        .sort("player_id", "season", "level_group")
    )


def fit_effects(history, cutoff):
    grouped = aggregate(history, cutoff).filter(pl.col("pa") >= 50)
    x = []
    y = []
    w = []
    for _, frame in grouped.group_by("player_id", "season"):
        rows = frame.to_dicts()
        pairs = list(combinations(rows, 2))
        for a, b in pairs:
            design = np.zeros(6)
            design[LEVELS.index(b["level_group"])] += 1
            design[LEVELS.index(a["level_group"])] -= 1
            ac = np.array([a[o] + 0.5 for o in OUTCOMES])
            bc = np.array([b[o] + 0.5 for o in OUTCOMES])
            al = np.array(
                [np.log(ac[left].sum() / ac[right].sum()) for left, right in MASKS]
            )
            bl = np.array(
                [np.log(bc[left].sum() / bc[right].sum()) for left, right in MASKS]
            )
            x.append(design[:5])
            y.append(bl - al)
            w.append(1 / (1 / a["pa"] + 1 / b["pa"]) / len(pairs))
    if not x:
        raise ValueError("No supported same-season level contrasts")
    x = np.array(x)
    y = np.array(y)
    w = np.array(w)
    effects = np.zeros((6, 4))
    effects[:5] = np.clip(
        np.linalg.solve(
            x.T @ (w[:, None] * x) + 5000 * np.eye(5), x.T @ (w[:, None] * y)
        ),
        -1,
        1,
    )
    return effects, {
        "pairs": len(x),
        "harmonic_pa": float(w.sum()),
        "effects": effects.tolist(),
        "levels": list(LEVELS),
        "nodes": list(NODES),
    }


def normalize_history(history, effects):
    counts = history.select(OUTCOMES).to_numpy().astype(float)
    pa = counts.sum(axis=1)
    if (pa < 0).any():
        raise ValueError("History has negative evidence")
    idx = np.array([LEVELS.index(canonical_level(s)) for s in history["level_group"]])
    rates = np.divide(
        counts, pa[:, None], out=np.full_like(counts, 1 / 12), where=pa[:, None] > 0
    )
    adjusted = transform(rates, -effects[idx]) * pa[:, None]
    return history.with_columns(
        [pl.Series(o, adjusted[:, j]) for j, o in enumerate(OUTCOMES)]
    )


def transition_matrix(history, cutoff):
    rows = aggregate(history, cutoff)
    totals = 100 * np.eye(6)
    support = np.zeros(6, dtype=int)
    seasons = {year: f for (year,), f in rows.group_by("season")}
    for year, current in seasons.items():
        if year + 1 not in seasons:
            continue
        primary = (
            current.sort(
                ["player_id", "pa", "level_group"], descending=[False, True, False]
            )
            .unique("player_id", keep="first")
            .select("player_id", pl.col("level_group").alias("origin"))
        )
        future = (
            seasons[year + 1]
            .join(primary, on="player_id")
            .with_columns(pl.col("pa").sum().over("player_id").alias("total"))
        )
        for row in future.to_dicts():
            a, b = LEVELS.index(row["origin"]), LEVELS.index(row["level_group"])
            totals[a, b] += row["pa"] / row["total"]
        for (origin,), frame in future.group_by("origin"):
            support[LEVELS.index(origin)] += frame["player_id"].n_unique()
    return totals / totals.sum(axis=1, keepdims=True), support.tolist()
