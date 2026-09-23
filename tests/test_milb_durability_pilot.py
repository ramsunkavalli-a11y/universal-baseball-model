import importlib
import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


def test_pilot_eligibility_is_not_selected_by_future_mlb_success(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root/"scripts"))
    build = importlib.import_module("test_milb_durability_pilot_v1").build_cohort
    stats = pl.DataFrame([{ "season": y, "player_id": i, "level_group": "AA", "plate_appearances": 200,
        "at_bats": 170, "hits": 50, "doubles": 10, "triples": 1, "home_runs": 5,
        "base_on_balls": 25, "hit_by_pitch": 3, "sac_flies": 2} for y in (2021, 2022) for i in (1, 2, 3)])
    field = stats.select("season", "player_id", "level_group").with_columns(pl.lit("SS").alias("position_abbreviation"),
        pl.lit(50).alias("games_played"), pl.lit(1000).alias("fielding_outs"))
    panel = pl.DataFrame({"origin_year": [2022]*3, "player_id": [1, 2, 3]})
    targets = pl.DataFrame({"season": [2021, 2023], "player_id": [1, 2], "mlb_pa": [10, 10]})
    a = build(stats, field, panel, targets)
    b = build(stats.reverse(), field.reverse(), panel.reverse(), targets.filter(pl.col("season") <= 2022))
    assert a.equals(b) and a["player_id"].to_list() == [2, 3]
    # Moving a player to a different level for one of the seasons excludes them.
    moved = stats.with_columns(pl.when((pl.col("player_id") == 3) & (pl.col("season") == 2021))
        .then(pl.lit("AAA")).otherwise(pl.col("level_group")).alias("level_group"))
    assert build(moved, field, panel, targets)["player_id"].to_list() == [2]


def test_saved_pilot_is_small_chronological_and_not_delivered():
    root = Path(__file__).resolve().parents[1]
    out = root/"model_artifacts/milb-durability-pilot-v1-2026-09-22"
    manifest = json.loads((out/"manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha256_file(out/name) == digest
    for name, digest in manifest["sources"].items():
        assert sha256_file(root/name) == digest
    r = json.loads((out/"report.json").read_text())
    assert not r["forecast_changed"] and not r["protected_outcomes_used"]
    assert all(x["latest_training_label"] <= x["origin"] for x in r["support"])
    assert r["results"]["arrival"]["productive"]["rows"] == 37
    assert r["results"]["arrival"]["productive"]["events"] == 6
    assert r["results"]["mlb_200pa"] == {}
