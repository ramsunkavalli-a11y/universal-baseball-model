"""Cutoff-safe DH reserve decomposition and contract source admissibility."""
from datetime import date

import numpy as np
import polars as pl

from universal_baseball.hitter_league_allocation import budget_at_cutoff


def contract_source_usable(available_date, cutoff, *, event_known_date=None, event_history_certified=False):
    """Payroll year alone never establishes an earlier information date."""
    boundary = date(cutoff, 12, 31)
    snapshot_known = bool(available_date and date.fromisoformat(available_date[:10]) <= boundary)
    event_known = bool(event_history_certified and event_known_date
                       and date.fromisoformat(event_known_date[:10]) <= boundary)
    return snapshot_known or event_known


def dh_budget(panel, targets, schedules, pitching, cutoff):
    if not 2022 <= cutoff <= 2025:
        raise ValueError("Universal-DH correction requires a rule-known 2022-2025 cutoff")
    old = budget_at_cutoff(panel, targets, schedules, cutoff)
    known = targets.filter(pl.col("season") <= cutoff)
    pitchers = pitching.filter((pl.col("season") <= cutoff) & (pl.col("pitching_bf") >= 100))
    pitchers = pitchers.select("season", "player_id").unique()
    support = []
    for row in old["reserve_support"]:
        y, season = row["origin"], row["target"]
        annual = known.filter(pl.col("season") == season)
        outside = annual.join(panel.filter(pl.col("origin_year") == y).select("player_id"), on="player_id", how="anti")
        proxy = outside.filter(pl.col("mlb_pa") < 200).join(pitchers, on=["season", "player_id"], how="inner", validate="1:1")
        pitcher_pa = float(proxy["mlb_pa"].sum())
        other = float(outside["mlb_pa"].sum()) - pitcher_pa
        support.append({**row, "pitcher_proxy_pa": pitcher_pa, "other_pa": other,
                        "other_fraction": other/float(annual["mlb_pa"].sum())})
    reserve = old["pool"]*float(np.median([r["other_fraction"] for r in support]))
    return {**old, "old_reserve_pa": old["reserve_pa"], "old_named_budget": old["named_budget"],
            "reserve_pa": reserve, "reserve_fraction": reserve/old["pool"],
            "named_budget": old["pool"]-reserve, "reserve_support": support,
            "structural_pitcher_slot_reserve": 0.,
            "rule_known_origin": cutoff, "classifier": ">=100 BF and <200 batting PA in a completed historical season"}
