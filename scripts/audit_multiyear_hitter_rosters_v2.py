"""Audit retained 2025 roster membership and bounded historical API responses.

No model input is repaired from this diagnostic. No 2026 endpoints are requested.
"""
from datetime import date
import gzip
import json
from pathlib import Path

import polars as pl

from universal_baseball.playing_time_roster_source import (
    project_team_40man_membership_payload, fetch_team_40man_membership_as_of,
    fetch_team_transactions_around,
)
from universal_baseball.storage import sha256_file
from evaluate_multiyear_hitter_followup_v2 import OUT, V1, save_json

SOURCE = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/opportunity-40man-history")


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    captures = OUT/"roster-captures"
    captures.mkdir(exist_ok=True)
    rows, hashes = [], {}
    for path in sorted((SOURCE/"captures/2025").glob("team-*.json.gz")):
        team = int(path.name.split("-")[1].split(".")[0])
        with gzip.open(path,"rt",encoding="utf-8") as source:
            capture = json.load(source)
        rows.append(project_team_40man_membership_payload(capture["payload"],team_id=team,season=2025,as_of_date=date(2025,10,15)))
        hashes[str(path)] = sha256_file(path)
    saved = pl.concat(rows)
    source_path = SOURCE/"tables/historical_40man_membership.parquet"
    hashes[str(source_path)] = sha256_file(source_path)
    membership = pl.scan_parquet(source_path).filter(pl.col("season")==2025).collect()
    keys = ["team_id","player_id"]
    discrepancies = saved.select(keys).join(membership.select(keys),on=keys,how="anti").height + membership.select(keys).join(saved.select(keys),on=keys,how="anti").height
    if len(rows)!=30 or discrepancies:
        raise ValueError("Saved 30-team roster projection does not reconcile")
    cohort = pl.read_parquet(V1/"player-forecast-2026-2028.parquet")
    ids = saved["player_id"].unique().to_list()
    absent = cohort.filter((pl.col("mlb_pa_lag0")>0)&~pl.col("player_id").is_in(ids))
    absence_rows = absent.select("player_id","player_name","mlb_pa_lag0","on_40man").to_dicts()
    checks = []
    for day in (date(2025,9,30),date(2025,10,15),date(2025,12,31)):
        path = captures/f"mets-40man-{day}.json"
        try:
            if path.exists():
                capture = json.loads(path.read_text(encoding="utf-8"))
                frame = project_team_40man_membership_payload(capture["payload"],team_id=121,season=2025,as_of_date=day)
            else:
                frame,capture = fetch_team_40man_membership_as_of(121,season=2025,as_of_date=day)
                save_json(path,capture)
            checks.append({"as_of_date":str(day),"rows":frame.height,"alonso_present":624413 in frame["player_id"],
                           "capture":str(path),"sha256":sha256_file(path)})
        except Exception as exc:
            checks.append({"as_of_date":str(day),"error":str(exc)})
    path = captures/"mets-transactions-2025-10-02-to-2025-12-01.json"
    try:
        if path.exists():
            capture = json.loads(path.read_text(encoding="utf-8")); transactions = capture["payload"]["transactions"]
        else:
            transactions,capture = fetch_team_transactions_around(121,as_of_date=date(2025,11,1),days_each_side=30)
            save_json(path,capture)
        transaction_result = {"capture":str(path),"sha256":sha256_file(path),"total_rows":len(transactions),
            "alonso":[r for r in transactions if (r.get("person") or {}).get("id")==624413]}
    except Exception as exc:
        transaction_result = {"error":str(exc)}
    report = {"saved_teams":len(rows),"saved_memberships":saved.height,"unique_players":len(ids),
        "projection_discrepancies":discrepancies,"source_hashes":hashes,"absent_current_mlb":absence_rows,
        "absent_500plus_PA":[r for r in absence_rows if r["mlb_pa_lag0"]>=500],
        "fresh_historical_checks":checks,"transactions":transaction_result,
        "conclusion":"Endpoint membership is a reconstructive proxy, not certified historical reserve rights. The saved source and projection agree. Do not hand-add Alonso or change frozen inputs.",
        "model_inputs_changed":False,"protected_2026_used":False}
    save_json(OUT/"roster-audit.json",report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("source_hashes","absent_current_mlb")},indent=2),flush=True)


if __name__=="__main__":
    main()
