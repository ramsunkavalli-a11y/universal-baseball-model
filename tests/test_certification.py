from __future__ import annotations

import polars as pl
import pytest

import universal_baseball.certification as certification
from universal_baseball.certification import ReleaseSpec, build_release_report, download_file


def _spec() -> ReleaseSpec:
    return ReleaseSpec(
        source_name="test",
        asset_name="2025_3_aaa_pbp.csv",
        url="https://example.invalid/test.csv",
        expected_year=2025,
        expected_month=3,
        expected_level="aaa",
    )


def _minimal_scope_frame(level_name: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["1"],
            "pitch_number": ["1"],
            "game_date": ["2025-03-28"],
            "game_year": ["2025"],
            "game_month": ["3"],
            "league_level_name": [level_name],
            "batter": ["10"],
            "pitcher": ["20"],
        }
    )


def test_report_separates_exact_duplicates_from_conflicting_pitch_keys() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1", "1"],
            "at_bat_number": ["1", "1", "2", "2"],
            "pitch_number": ["1", "1", "1", "1"],
            "game_date": ["2025-03-28"] * 4,
            "game_year": ["2025"] * 4,
            "game_month": ["3"] * 4,
            "batter": ["10", "10", "11", "11"],
            "pitcher": ["20", "20", "20", "20"],
            "events": [None, None, "single", "single"],
            "type": ["S", "S", "X", "B"],
            "bb_type": [None, None, "line_drive", "line_drive"],
            "release_speed": ["95.0", "95.0", "91.0", "91.0"],
        }
    )

    report = build_release_report(frame, _spec(), {"sha256": "test"})

    grain = report["grain"]
    assert grain["exact_duplicate_extra_rows"] == 1
    assert grain["duplicate_key_extra_rows"] == 2
    assert grain["conflicting_key_extra_rows"] == 1
    assert grain["duplicate_key_groups"] == 2
    assert grain["key_blank_counts"] == {
        "game_pk": 0,
        "at_bat_number": 0,
        "pitch_number": 0,
    }

    assert report["shape"]["unique_games"] == 1
    assert report["tracking"]["release_speed"]["row_nonblank_fraction"] == 1.0
    assert any("exact duplicate" in warning for warning in report["assessment"]["warnings"])
    assert any("sharing a pitch key" in warning for warning in report["assessment"]["warnings"])


def test_scope_mismatch_is_reported_without_repairing_data() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "2"],
            "at_bat_number": ["1", "1"],
            "pitch_number": ["1", "1"],
            "game_date": ["2025-03-30", "2025-04-01"],
            "game_year": ["2025", "2025"],
            "game_month": ["3", "4"],
            "batter": ["10", "11"],
            "pitcher": ["20", "21"],
        }
    )

    report = build_release_report(frame, _spec(), {"sha256": "test"})

    assert report["grain"]["exact_duplicate_extra_rows"] == 0
    assert report["grain"]["conflicting_key_extra_rows"] == 0
    assert any("expected game_month 3" in warning for warning in report["assessment"]["warnings"])


def test_expected_aaa_accepts_triple_a_level_name() -> None:
    report = build_release_report(
        _minimal_scope_frame("Triple-A"),
        _spec(),
        {"sha256": "test"},
    )

    warnings = report["assessment"]["warnings"]
    assert not any("league_level_name" in warning for warning in warnings)


def test_level_taxonomy_mismatch_is_reported() -> None:
    report = build_release_report(
        _minimal_scope_frame("Double-A"),
        _spec(),
        {"sha256": "test"},
    )

    assert any(
        "expected league_level_name" in warning
        and "double-a" in warning
        for warning in report["assessment"]["warnings"]
    )


def test_unknown_expected_level_is_reported_as_missing_taxonomy_rule() -> None:
    spec = ReleaseSpec(
        source_name="test",
        asset_name="unknown.csv",
        url="https://example.invalid/test.csv",
        expected_year=2025,
        expected_month=3,
        expected_level="mystery",
    )

    report = build_release_report(
        _minimal_scope_frame("Rookie"),
        spec,
        {"sha256": "test"},
    )

    assert any(
        "no level-taxonomy rule defined" in warning
        for warning in report["assessment"]["warnings"]
    )


@pytest.mark.parametrize(
    ("url", "attempts", "timeout", "message"),
    [
        ("file:///private/source.csv", 1, 60, "http or https"),
        ("https://example.invalid/source.csv", 0, 60, "attempts"),
        ("https://example.invalid/source.csv", 1, 0, "timeout_seconds"),
    ],
)
def test_download_rejects_unsafe_or_invalid_transport_settings(
    tmp_path, url: str, attempts: int, timeout: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        download_file(
            url,
            tmp_path / "source.csv",
            attempts=attempts,
            timeout_seconds=timeout,
        )


def test_download_rejects_a_non_http_resolved_url_without_writing(
    tmp_path, monkeypatch
) -> None:
    class RedirectedResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        @staticmethod
        def geturl() -> str:
            return "file:///private/source.csv"

    monkeypatch.setattr(
        certification,
        "urlopen",
        lambda *_args, **_kwargs: RedirectedResponse(),
    )
    destination = tmp_path / "source.csv"
    with pytest.raises(RuntimeError, match="resolved to a non-http URL"):
        download_file("https://example.invalid/source.csv", destination)
    assert not destination.exists()
    assert not destination.with_suffix(".csv.part").exists()
