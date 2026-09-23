"""Prior-defined regulars and position-aware workload shortfalls, not diagnoses."""
import numpy as np
import polars as pl

POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "unknown"]
CONTEXT = [f"gap_position_{p}" for p in POSITIONS] + [f"gap_{name}_{lag}" for lag in (0, 1)
    for name in ("regular", "measured", "reference")]
GAPS = ["gap_shortfall_0", "gap_shortfall_1", "gap_change"]


def position_lookup(fielding):
    if fielding["season"].max() > 2025:
        raise ValueError("Protected position history")
    frame = fielding.filter(pl.col("position_abbreviation").is_in(POSITIONS[:-1])).group_by(
        "season", "player_id", "position_abbreviation").agg(pl.col("games_played").sum(), pl.col("fielding_outs").sum())
    frame = frame.sort(["season", "player_id", "games_played", "fielding_outs", "position_abbreviation"],
                       descending=[False, False, True, True, False]).unique(["season", "player_id"], keep="first", maintain_order=True)
    return {(r["season"], r["player_id"]): r["position_abbreviation"] for r in frame.iter_rows(named=True)}


def build_gap_features(panel, targets, fielding, fractions):
    if targets["season"].max() > 2025 or panel["origin_year"].max() > 2025:
        raise ValueError("Protected outcomes")
    pos = position_lookup(fielding)
    pa = {(r["season"], r["player_id"]): r["mlb_pa"] for r in targets.iter_rows(named=True)}
    ids_by_year = {y: sorted(i for (s, i) in pa if s == y) for y in fractions}
    years = sorted(set(panel["origin_year"].to_list()) | {y-1 for y in panel["origin_year"]})

    def regular(year, player):
        p = pos.get((year-1, player), "unknown")
        exposure = fractions.get(year-1)
        known = exposure is not None and p != "unknown"
        qualifies = known and pa.get((year-1, player), 0) / exposure >= (300 if p == "C" else 400)
        return p, bool(qualifies)

    references = {}
    notes = []
    for year in years:
        prior_years = sorted(y for y in fractions if y < year and y != 2020)[-3:]
        pool = []
        for prior in prior_years:
            for player in ids_by_year.get(prior-1, []):
                p, eligible = regular(prior, player)
                if eligible:
                    pool.append((p, pa.get((prior, player), 0) / fractions[prior]))
        for p in POSITIONS:
            cell = [v for position, v in pool if position == p]
            fallback = len(cell) < 30
            values = [v for _, v in pool] if fallback else cell
            ref = float(np.quantile(values, .75)) if len(values) >= 30 and p != "unknown" else None
            references[year, p] = ref
            notes.append({"season": year, "position": p, "prior_years": prior_years, "cell_rows": len(cell),
                          "pool_rows": len(pool), "pooled_fallback": fallback, "reference_pa": ref})
    rows = []
    for row in panel.select("origin_year", "player_id").sort(["origin_year", "player_id"]).iter_rows(named=True):
        year, player = row["origin_year"], row["player_id"]
        primary, _ = regular(year, player)
        out = {**row, "gap_prior_position": primary, **{f"gap_position_{p}": float(primary == p) for p in POSITIONS}}
        for lag in (0, 1):
            season = year-lag
            p, eligible = regular(season, player)
            reference = references[season, p]
            measured = bool(eligible and reference is not None and reference > 0 and season in fractions)
            expected = reference * fractions[season] if measured else None
            observed = pa.get((season, player), 0)
            out.update({f"gap_regular_{lag}": float(eligible), f"gap_measured_{lag}": float(measured),
                f"gap_reference_{lag}": float(reference) if measured else 0.,
                f"gap_shortfall_{lag}": max(0., (expected-observed)/expected) if measured else 0.,
                f"gap_expected_pa_{lag}": expected, f"gap_observed_pa_{lag}": observed})
        out["gap_change"] = out["gap_shortfall_0"]-out["gap_shortfall_1"] if out["gap_measured_0"] and out["gap_measured_1"] else 0.
        rows.append(out)
    return pl.DataFrame(rows), notes
