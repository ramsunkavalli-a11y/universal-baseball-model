import csv

import duckdb

from scripts.audit_hitter_v2_matchup_context_source import (
    _materialize_group,
    _write_results,
)


FIELDS = (
    "game_pk",
    "at_bat_number",
    "pitch_number",
    "game_date",
    "batter",
    "pitcher",
    "stand",
    "p_throws",
    "game_type",
)


def test_matchup_audit_fails_closed_and_excludes_same_day_prior(tmp_path) -> None:
    source = tmp_path / "pbp.csv"
    rows = [
        (1, 1, 1, "2024-04-01", 10, 100, "R", "L", "R"),
        (1, 2, 1, "2024-04-01", 12, 100, "L", "L", "R"),
        (2, 1, 1, "2024-04-02", 13, 100, "R", "L", "R"),
        (3, 1, 1, "2024-04-03", 14, 100, "R", "R", "R"),
        (3, 1, 2, "2024-04-03", 15, 101, "L", "L", "R"),
    ]
    with source.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(FIELDS)
        writer.writerows(rows)

    connection = duckdb.connect()
    report_root = tmp_path / "report"
    pa_root = report_root / "pa"
    pa_root.mkdir(parents=True)
    _materialize_group(
        connection,
        {
            "season": 2024,
            "level_group": "AAA",
            "source_system": "TEST_PBP",
            "files": [source],
            "retained_raw_source": True,
        },
        pa_root / "2024_AAA.parquet",
    )
    by_level, total = _write_results(connection, pa_root, report_root)

    assert len(by_level) == 1
    assert total["canonical_pa"] == 4
    assert total["complete_matchup_pa"] == 4
    assert total["conflict_free_matchup_pa"] == 3
    assert total["conflicting_batter_pa"] == 1
    assert total["conflicting_pitcher_pa"] == 1
    assert total["conflicting_batter_side_pa"] == 1
    assert total["conflicting_pitcher_hand_pa"] == 1
    # The second PA on April 1 cannot use the first PA from that same date.
    # Only the April 2 PA has strictly prior-date evidence for pitcher 100.
    assert total["prior_1_pa"] == 1
    assert total["prior_50_pa"] == 0
