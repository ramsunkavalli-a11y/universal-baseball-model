from datetime import UTC, datetime

import pytest

from universal_baseball.season_stat_assets import (
    ArmstjcSeasonStatAsset,
    parse_season_stat_asset_name,
    season_stat_asset_from_github_payload,
    select_season_stat_asset,
    validate_season_stat_asset_inventory,
)


def _payload(name: str, *, asset_id: int = 1, size: int = 123) -> dict[str, object]:
    return {
        "id": asset_id,
        "name": name,
        "size": size,
        "created_at": "2023-08-09T04:08:43Z",
        "updated_at": "2023-08-09T04:08:44Z",
        "browser_download_url": f"https://example.test/{name}",
    }


def test_parse_season_stat_asset_name_preserves_plus_level() -> None:
    assert parse_season_stat_asset_name("2022_a+_season_batting_stats.csv") == (
        2022,
        "a+",
        "batting",
    )
    assert parse_season_stat_asset_name("2023_rk_season_pitching_stats.csv") == (
        2023,
        "rk",
        "pitching",
    )
    assert parse_season_stat_asset_name("README.md") is None


def test_asset_payload_and_selection_keep_placeholder_explicit() -> None:
    good = season_stat_asset_from_github_payload(
        _payload("2022_aaa_season_batting_stats.csv", asset_id=1, size=265_553),
        expected_kind="batting",
    )
    placeholder = season_stat_asset_from_github_payload(
        _payload("2025_rk_season_batting_stats.csv", asset_id=2, size=1),
        expected_kind="batting",
    )
    assert good is not None and good.is_nonempty is True
    assert placeholder is not None and placeholder.is_nonempty is False

    inventory = validate_season_stat_asset_inventory([good, placeholder])
    assert select_season_stat_asset(
        inventory, year=2022, filename_level="aaa", kind="batting"
    ).name == "2022_aaa_season_batting_stats.csv"
    with pytest.raises(ValueError, match="empty/placeholder"):
        select_season_stat_asset(
            inventory, year=2025, filename_level="rk", kind="batting"
        )


def test_validate_inventory_rejects_duplicate_identity() -> None:
    stamp = datetime(2023, 1, 1, tzinfo=UTC)
    a = ArmstjcSeasonStatAsset(
        asset_id=1,
        name="2022_aaa_season_batting_stats.csv",
        size_bytes=100,
        created_at_utc=stamp,
        updated_at_utc=stamp,
        browser_download_url="https://example.test/a",
        year=2022,
        filename_level="aaa",
        kind="batting",
    )
    b = ArmstjcSeasonStatAsset(
        asset_id=1,
        name="2022_aa_season_batting_stats.csv",
        size_bytes=100,
        created_at_utc=stamp,
        updated_at_utc=stamp,
        browser_download_url="https://example.test/b",
        year=2022,
        filename_level="aa",
        kind="batting",
    )
    with pytest.raises(ValueError, match="duplicate armstjc season-stat asset id"):
        validate_season_stat_asset_inventory([a, b])
