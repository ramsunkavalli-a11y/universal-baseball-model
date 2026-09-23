"""Conservative reported IL state and explicit unallocated league budgets."""
from datetime import date, timedelta
import numpy as np
import polars as pl

from universal_baseball.historical_injury_features import parse_injury_event

HEALTH = ["health_mlb_scope", "health_log_days730", "health_open", "health_log_elapsed",
          "health_offseason_activation", "health_late_season_activation"]


def available_date(raw):
    dates = []
    for key in ("date", "effectiveDate", "resolutionDate"):
        value = raw.get(key)
        if value:
            try:
                dates.append(date.fromisoformat(str(value)[:10]))
            except ValueError:
                raise ValueError(f"Unparseable transaction {key}")
    if not dates:
        raise ValueError("Undated transaction")
    return max(dates)


def normalize_records(captures, team_ids, maximum=date(2023, 12, 31)):
    records = {}
    audit = {"raw_rows": 0, "date_disagreements": 0, "cross_year_dates": 0,
             "beyond_maximum": 0, "non_mlb_or_missing_team": 0, "injury_events": 0}
    for _, payload in captures:
        for raw in payload["transactions"]:
            audit["raw_rows"] += 1
            when = available_date(raw)
            dates = [str(raw[k])[:10] for k in ("date", "effectiveDate", "resolutionDate") if raw.get(k)]
            audit["date_disagreements"] += len(set(dates)) > 1
            audit["cross_year_dates"] += len({d[:4] for d in dates}) > 1
            if when > maximum:
                audit["beyond_maximum"] += 1
                continue  # Do not inspect future descriptions.
            team = raw.get("toTeam") or raw.get("fromTeam") or raw.get("team") or {}
            if team.get("id") not in team_ids:
                audit["non_mlb_or_missing_team"] += 1
                continue
            event = parse_injury_event(raw.get("description"))
            if event is None or not (raw.get("person") or {}).get("id"):
                continue
            key = (int(raw["id"]), int(raw["person"]["id"]))
            record = {"transaction_id": key[0], "player_id": key[1], "available_date": when,
                      "kind": event[0], "list_days": event[1]}
            if key not in records or when > records[key]["available_date"]:
                records[key] = record
    audit["injury_events"] = len(records)
    schema = {"transaction_id": pl.Int64, "player_id": pl.Int64, "available_date": pl.Date,
              "kind": pl.String, "list_days": pl.Int64}
    return pl.DataFrame(list(records.values()), schema=schema).sort(["player_id", "available_date", "transaction_id"]), audit


def health_state(events, cutoff, season_end, observed):
    eligible = sorted((r for r in events if r["available_date"] <= cutoff),
                      key=lambda r: (r["available_date"], r["transaction_id"]))
    start = None
    intervals, activations = [], []
    orphan = 0
    for row in eligible:
        day = row["available_date"]
        if row["kind"] in ("placement", "transfer") and start is None:
            start = day
        elif row["kind"] == "activation":
            activations.append(day)
            if start is None:
                orphan += 1
            else:
                intervals.append((start, day))
                start = None
    if start is not None:
        intervals.append((start, cutoff))
    window = cutoff - timedelta(days=729)
    days = sum(max(0, (min(end, cutoff)-max(begin, window)).days+1) for begin, end in intervals)
    values = [int(observed), np.log1p(days), int(start is not None),
              np.log1p((cutoff-start).days+1) if start else 0.,
              int(any(season_end < d <= cutoff for d in activations)),
              int(any(season_end-timedelta(days=89) <= d <= season_end for d in activations))]
    if not observed:
        values = [0.] * len(HEALTH)
    return {**dict(zip(HEALTH, values)), "recorded_il_days730": days if observed else None,
            "health_status": "recorded_il_history" if observed and days else "no_recorded_il_evidence" if observed else "unknown_scope",
            "orphan_activations": orphan, "latest_health_evidence": max((r["available_date"] for r in eligible), default=None)}


def exposure_training(panel, cutoff, fractions):
    if cutoff > 2025:
        raise ValueError("Protected cutoff")
    train = panel.filter((pl.col("origin_year") >= 2016) & (pl.col("origin_year")+2 <= cutoff)
        & (pl.col("pa_h2") > 0) & pl.col("war_h2").is_not_null()).sort(["origin_year", "player_id"])
    if train["origin_year"].n_unique() < 2:
        raise ValueError("Insufficient mature training origins")
    fraction = np.array([fractions[int(y)+2] for y in train["origin_year"]])
    if not np.isfinite(fraction).all() or np.any(fraction <= 0):
        raise ValueError("Invalid exposure")
    return train, fraction


def budget_ledger(predicted_pa, predicted_value, pool, value_budget):
    if not np.isfinite([predicted_pa, predicted_value, pool, value_budget]).all() or predicted_pa < 0 or pool <= 0:
        raise ValueError("Invalid budget input")
    return {"named_player_pa": float(predicted_pa), "league_pa_budget": float(pool),
            "unallocated_pa": float(max(0, pool-predicted_pa)), "pa_excess": float(max(0, predicted_pa-pool)),
            "named_player_partial_value": float(predicted_value), "partial_value_budget": float(value_budget),
            "signed_value_gap_not_pure_outsider_value": float(value_budget-predicted_value)}
