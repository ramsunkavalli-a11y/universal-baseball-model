from __future__ import annotations

import pytest

from universal_baseball.player_value_baserunning_sources import (
    audit_mlb_baserunning_splits,
    audit_savant_baserunning_rows,
    parse_savant_baserunning_csv,
    savant_baserunning_query_params,
)


def _split(**stat):
    return {"player": {"id": 1, "fullName": "Example"}, "stat": stat}


def test_mlb_baserunning_source_audit_accepts_complete_counts() -> None:
    result = audit_mlb_baserunning_splits(
        [
            _split(
                hits=20,
                doubles=5,
                triples=1,
                homeRuns=4,
                stolenBases=8,
                caughtStealing=2,
                groundIntoDoublePlay=4,
                gidpOpp=23,
            ),
            _split(
                hits="0",
                doubles="0",
                triples="0",
                homeRuns="0",
                stolenBases="0",
                caughtStealing="0",
                groundIntoDoublePlay="0",
                gidpOpp="0",
            ),
        ]
    )

    assert result["row_count"] == 2
    assert result["fields"]["stolenBases"]["complete"] is True
    assert result["fields"]["hits"]["complete"] is True
    assert result["fields"]["gidpOpp"]["complete"] is True
    assert result["gidp_opportunity_identity"] == {
        "checked_rows": 2,
        "violation_rows": 0,
    }
    assert result["singles_identity"] == {
        "checked_rows": 2,
        "violation_rows": 0,
    }


def test_mlb_baserunning_source_audit_reports_missing_gidp_opportunity() -> None:
    result = audit_mlb_baserunning_splits(
        [
            _split(stolenBases=8, caughtStealing=2, groundIntoDoublePlay=4),
            _split(stolenBases=1, caughtStealing=0, groundIntoDoublePlay=1),
        ]
    )

    assert result["fields"]["gidpOpp"] == {
        "present_rows": 0,
        "nonnull_rows": 0,
        "missing_rows": 2,
        "complete": False,
    }
    assert result["gidp_opportunity_identity"]["checked_rows"] == 0
    assert result["singles_identity"]["checked_rows"] == 0


def test_mlb_baserunning_source_audit_rejects_gidp_above_opportunities() -> None:
    with pytest.raises(ValueError, match="groundIntoDoublePlay <= gidpOpp"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    stolenBases=2,
                    caughtStealing=1,
                    groundIntoDoublePlay=5,
                    gidpOpp=4,
                )
            ]
        )


def test_mlb_baserunning_source_audit_rejects_negative_singles_identity() -> None:
    with pytest.raises(ValueError, match="negative singles"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    hits=5,
                    doubles=3,
                    triples=1,
                    homeRuns=2,
                    stolenBases=0,
                    caughtStealing=0,
                    groundIntoDoublePlay=0,
                )
            ]
        )


def test_mlb_baserunning_source_audit_rejects_negative_or_fractional_counts() -> None:
    with pytest.raises(ValueError, match="invalid stolenBases"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    stolenBases=-1,
                    caughtStealing=0,
                    groundIntoDoublePlay=0,
                    gidpOpp=0,
                )
            ]
        )

    with pytest.raises(ValueError, match="invalid caughtStealing"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    stolenBases=1,
                    caughtStealing=0.5,
                    groundIntoDoublePlay=0,
                    gidpOpp=0,
                )
            ]
        )


def test_savant_baserunning_csv_parser_normalizes_public_headers() -> None:
    rows = parse_savant_baserunning_csv(
        "player_id,runner_runs_tot,runner_runs_XB,runner_runs_SBX,"
        "N_runner_moved,N_runner_moved_XB,N_runner_moved_SBX\n"
        "123,1.6,1.2,0.4,12,9,3\n"
        "456,-0.5,-0.2,-0.3,7,5,2\n"
    )

    assert rows[0]["runner_runs_xb"] == "1.2"
    assert rows[0]["n_runner_moved_xb"] == "9"

    audit = audit_savant_baserunning_rows(rows)
    assert audit["row_count"] == 2
    assert audit["duplicate_player_id_rows"] == 0
    assert audit["fields"]["runner_runs_xb"]["complete"] is True
    assert audit["run_decomposition"]["max_abs_delta"] == pytest.approx(0.0)
    assert audit["opportunity_identity"]["violation_rows"] == 0
    assert audit["advancement_source_usable"] is True


def test_savant_baserunning_source_audit_reports_missing_required_field() -> None:
    rows = parse_savant_baserunning_csv(
        "player_id,runner_runs_tot,runner_runs_XB,runner_runs_SBX,"
        "N_runner_moved,N_runner_moved_XB\n"
        "123,1.6,1.2,0.4,12,9\n"
    )

    audit = audit_savant_baserunning_rows(rows)
    assert audit["fields"]["n_runner_moved_sbx"] == {
        "present_rows": 0,
        "nonnull_rows": 0,
        "missing_rows": 1,
        "complete": False,
    }
    assert audit["advancement_source_usable"] is False


def test_savant_baserunning_source_audit_rejects_bad_counts_and_duplicate_headers() -> None:
    with pytest.raises(ValueError, match="invalid n_runner_moved_xb"):
        audit_savant_baserunning_rows(
            [
                {
                    "player_id": "123",
                    "runner_runs_tot": "1",
                    "runner_runs_xb": "1",
                    "runner_runs_sbx": "0",
                    "n_runner_moved": "4",
                    "n_runner_moved_xb": "-1",
                    "n_runner_moved_sbx": "5",
                }
            ]
        )

    with pytest.raises(ValueError, match="duplicate normalized headers"):
        parse_savant_baserunning_csv(
            "player_id,runner_runs_XB,runner_runs_xb\n123,1,1\n"
        )


def test_savant_baserunning_csv_parser_rejects_html_or_empty_payload() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_savant_baserunning_csv("")

    with pytest.raises(ValueError, match="HTML"):
        parse_savant_baserunning_csv("<!doctype html><html></html>")


def test_savant_baserunning_query_params_are_runner_level_and_unqualified() -> None:
    params = savant_baserunning_query_params(2024)
    assert params == {
        "game_type": "Regular",
        "n": "1",
        "season_start": "2024",
        "season_end": "2024",
        "split": "no",
        "team": "",
        "type": "Run",
        "with_team_only": "0",
        "csv": "true",
    }

    with pytest.raises(ValueError, match="2016"):
        savant_baserunning_query_params(2015)
