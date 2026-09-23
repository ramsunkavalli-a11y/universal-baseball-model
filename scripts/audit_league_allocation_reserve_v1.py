"""Post-score reserve composition diagnosis; never rescore or fit a candidate."""
import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file

BASE = Path("reports/generated/multiyear-hitter-v1")
OUT = Path("model_artifacts/hitter-league-allocation-v1-2026-09-22")
PITCH = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/"
             "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet")


def verify():
    report = json.loads((OUT/"reserve-composition-audit.json").read_text())
    for name, digest in report["sources"].items():
        assert sha256_file(Path(name)) == digest, name
    for row in report["rows"]:
        assert row["outside_pa"] == row["outside_pa_players_with_100_bf"]+row["outside_other_pa"]
    assert not report["forecast_changed"] and not report["protected_outcomes_used"]
    print(json.dumps({"status": "reserve_composition_verified", "cohorts": len(report["rows"])}))


def main():
    sources = [Path(__file__).relative_to(Path.cwd()), BASE/"panel.parquet", BASE/"targets.parquet",
               PITCH, OUT/"manifest.json", OUT/"report.json", OUT/"predictions.parquet"]
    hashes = {str(p): sha256_file(p) for p in sources}
    panel = pl.read_parquet(BASE/"panel.parquet")
    targets = pl.read_parquet(BASE/"targets.parquet")
    pitchers = pl.read_parquet(PITCH)
    assert pitchers["season"].max() <= 2025 and targets["season"].max() <= 2025
    # Descriptive same-season classification, not a cutoff-known forecast input.
    pitchers = pitchers.filter(pl.col("pitching_bf") >= 100).select("season", "player_id").unique()
    rows = []
    for y in [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023]:
        outside = targets.filter(pl.col("season") == y+2).join(
            panel.filter(pl.col("origin_year") == y).select("player_id"), on="player_id", how="anti")
        pitching = outside.join(pitchers, on=["season", "player_id"], how="inner", validate="1:1")
        other = outside.join(pitchers, on=["season", "player_id"], how="anti")
        assert outside["mlb_pa"].sum() == pitching["mlb_pa"].sum()+other["mlb_pa"].sum()
        rows.append({"origin": y, "target": y+2, "outside_pa": outside["mlb_pa"].sum(),
                     "outside_pa_players_with_100_bf": pitching["mlb_pa"].sum(),
                     "outside_other_pa": other["mlb_pa"].sum()})
    result = {"status": "post_score_descriptive_diagnosis", "sources": hashes, "rows": rows,
              "pitcher_definition": "At least 100 batters faced in the SAME target season; descriptive only",
              "interpretation": "Old outside-cohort PA includes substantial pitcher batting; not a stationary hitter-entrant reserve",
              "limits": ["Not a definitive pitcher/position-player classifier",
                         "Universal-DH regime requires cutoff-known treatment; do not retroactively assume it in 2021",
                         "No refit, rescoring, or claim that subtracting pitcher PA fixes individual predictions"],
              "rule_source": "https://www.mlb.com/news/mlb-rule-changes-for-2022",
              "forecast_changed": False, "protected_outcomes_used": False}
    assert all(sha256_file(Path(p)) == digest for p, digest in hashes.items())
    (OUT/"reserve-composition-audit.json").write_text(
        json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "rows": rows}, indent=2))
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    if parser.parse_args().verify:
        verify()
    else:
        main()
