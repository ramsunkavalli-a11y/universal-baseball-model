from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_translation import (
    build_training_environment_transition_evidence,
    fit_level_clr_translation,
)
from universal_baseball.performance_season import ALL_CORE_BINS


def _game_row(
    *,
    game_date: str,
    game_pk: int,
    league_id: int,
    player_id: int,
    level_group: str,
    season: int = 2024,
    plate_appearances: int = 10,
    core_events: int = 10,
) -> dict[str, object]:
    # Profile helper below uses 1 BB/HBP + 2 K + remaining contact events.
    expected_contacts = core_events - 3
    return {
        "season": season,
        "game_date": game_date,
        "game_pk": game_pk,
        "league_id": league_id,
        "player_id": player_id,
        "level_group": level_group,
        "batting_plate_appearances": plate_appearances,
        "expected_contact_count": expected_contacts,
        "observed_contact_count": expected_contacts,
        "contact_count_residual": 0,
        "core_profile_event_count": core_events,
        "bunt_contact_count": 0,
        "foul_air_excluded_count": 0,
        "unknown_contact_count": 0,
        "special_noncontact_count": 0,
        "pa_accounting_residual": plate_appearances - expected_contacts - 3,
        "participant_authority_status": "source",
        "source_capability_tier": "result",
    }


def _profile_for_summary(summary: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    contact_bins = [
        "PULL_GB",
        "CENTER_GB",
        "OPPO_GB",
        "PULL_LD",
        "CENTER_LD",
        "OPPO_LD",
        "PULL_OFFB",
    ]
    for row in summary.iter_rows(named=True):
        core_events = int(row["core_profile_event_count"])
        contact_count = core_events - 3
        base = {
            "season": row["season"],
            "game_date": row["game_date"],
            "game_pk": row["game_pk"],
            "league_id": row["league_id"],
            "player_id": row["player_id"],
            "level_group": row["level_group"],
        }
        rows.append({**base, "core_bin": "BB_HBP", "occurrence_count": 1})
        rows.append({**base, "core_bin": "K", "occurrence_count": 2})
        if contact_count:
            rows.append(
                {
                    **base,
                    "core_bin": contact_bins[int(row["game_pk"]) % len(contact_bins)],
                    "occurrence_count": contact_count,
                }
            )
    return pl.DataFrame(rows)


def _stint_fixture() -> tuple[pl.DataFrame, pl.DataFrame]:
    rows = [
        # Player 10 has clean adjacent AA -> AAA -> MLB stints.
        _game_row(game_date="2024-04-01", game_pk=1, league_id=111, player_id=10, level_group="AA"),
        _game_row(game_date="2024-04-10", game_pk=2, league_id=111, player_id=10, level_group="AA"),
        _game_row(game_date="2024-05-01", game_pk=3, league_id=117, player_id=10, level_group="AAA"),
        _game_row(game_date="2024-05-10", game_pk=4, league_id=117, player_id=10, level_group="AAA"),
        _game_row(game_date="2024-06-01", game_pk=5, league_id=1, player_id=10, level_group="MLB"),
        _game_row(game_date="2024-06-10", game_pk=6, league_id=1, player_id=10, level_group="MLB"),
        # Future row must never enter training evidence.
        _game_row(game_date="2024-08-01", game_pk=7, league_id=1, player_id=10, level_group="MLB"),
        # Player 20 has two environments on one date. That date breaks continuity,
        # so the later MLB stint must not be paired across it.
        _game_row(game_date="2024-04-01", game_pk=8, league_id=111, player_id=20, level_group="AA"),
        _game_row(game_date="2024-04-20", game_pk=9, league_id=111, player_id=20, level_group="AA"),
        _game_row(game_date="2024-04-20", game_pk=10, league_id=117, player_id=20, level_group="AAA"),
        _game_row(game_date="2024-05-15", game_pk=11, league_id=1, player_id=20, level_group="MLB"),
        # Player 30 changes actual league while remaining at AA.
        _game_row(game_date="2024-04-01", game_pk=12, league_id=111, player_id=30, level_group="AA"),
        _game_row(game_date="2024-04-10", game_pk=13, league_id=111, player_id=30, level_group="AA"),
        _game_row(game_date="2024-05-01", game_pk=14, league_id=112, player_id=30, level_group="AA"),
        _game_row(game_date="2024-05-10", game_pk=15, league_id=112, player_id=30, level_group="AA"),
    ]
    summary = pl.DataFrame(rows)
    return summary, _profile_for_summary(summary)


def test_training_transition_evidence_is_cutoff_safe_and_adjacent_only() -> None:
    summary, profile = _stint_fixture()
    evidence = build_training_environment_transition_evidence(
        summary,
        profile,
        training_end=date(2024, 7, 1),
        min_core_events_per_stint=10,
    )

    player10 = evidence.stint_summary.filter(pl.col("player_id") == 10)
    assert player10.height == 3
    assert player10.get_column("level_group").to_list() == ["AA", "AAA", "MLB"]
    assert player10.get_column("last_game_date").max() == date(2024, 6, 10)

    player10_pairs = evidence.pair_summary.filter(pl.col("player_id") == 10)
    assert player10_pairs.height == 2
    assert player10_pairs.get_column("transition").to_list() == ["PROMOTION", "PROMOTION"]
    assert player10_pairs.get_column("translation_pair_eligible").to_list() == [True, True]

    # Same-day ambiguity breaks the chain; there is no AA -> MLB pair for player 20.
    assert evidence.metrics["ambiguous_player_date_count"] == 1
    assert evidence.pair_summary.filter(pl.col("player_id") == 20).is_empty()

    same_level = evidence.pair_summary.filter(pl.col("player_id") == 30).row(0, named=True)
    assert same_level["from_league_id"] == 111
    assert same_level["to_league_id"] == 112
    assert same_level["transition"] == "SAME_LEVEL_ENVIRONMENT_CHANGE"

    # Every eligible pair receives all 12 CLR components and each side is centered.
    for pair_id in evidence.pair_summary.filter(pl.col("translation_pair_eligible")).get_column(
        "pair_id"
    ):
        pair_profile = evidence.pair_profile.filter(pl.col("pair_id") == pair_id)
        assert pair_profile.height == len(ALL_CORE_BINS)
        assert abs(float(pair_profile.get_column("from_clr").sum())) < 1e-12
        assert abs(float(pair_profile.get_column("to_clr").sum())) < 1e-12


def test_low_evidence_intermediate_stint_is_not_silently_bridged() -> None:
    rows = [
        _game_row(game_date="2024-04-01", game_pk=101, league_id=111, player_id=50, level_group="AA"),
        _game_row(game_date="2024-04-10", game_pk=102, league_id=111, player_id=50, level_group="AA"),
        # Four-event AAA stop: below the ten-event pair threshold.
        _game_row(
            game_date="2024-05-01",
            game_pk=103,
            league_id=117,
            player_id=50,
            level_group="AAA",
            plate_appearances=4,
            core_events=4,
        ),
        _game_row(game_date="2024-06-01", game_pk=104, league_id=1, player_id=50, level_group="MLB"),
        _game_row(game_date="2024-06-10", game_pk=105, league_id=1, player_id=50, level_group="MLB"),
    ]
    summary = pl.DataFrame(rows)
    evidence = build_training_environment_transition_evidence(
        summary,
        _profile_for_summary(summary),
        training_end=date(2024, 7, 1),
        min_core_events_per_stint=10,
    )

    assert evidence.pair_summary.height == 2
    assert evidence.pair_summary.filter(pl.col("translation_pair_eligible")).is_empty()
    pairs = evidence.pair_summary.select("from_level_group", "to_level_group").rows()
    assert pairs == [("AA", "AAA"), ("AAA", "MLB")]
    assert ("AA", "MLB") not in pairs


def _synthetic_translation_pairs() -> tuple[pl.DataFrame, pl.DataFrame, dict[str, dict[str, float]]]:
    bin_index = {core_bin: index for index, core_bin in enumerate(ALL_CORE_BINS)}
    mean_index = sum(bin_index.values()) / len(bin_index)
    effects = {
        "MLB": {core_bin: 0.0 for core_bin in ALL_CORE_BINS},
        "AAA": {
            core_bin: 0.01 * (bin_index[core_bin] - mean_index) for core_bin in ALL_CORE_BINS
        },
        "AA": {
            core_bin: -0.02 * (bin_index[core_bin] - mean_index) for core_bin in ALL_CORE_BINS
        },
    }
    pair_specs = [
        ("p1", 1, "AA", "AAA", 30.0),
        ("p2", 2, "AA", "AAA", 45.0),
        ("p3", 3, "AAA", "MLB", 40.0),
        ("p4", 4, "AAA", "MLB", 60.0),
    ]
    pair_summary = pl.DataFrame(
        {
            "pair_id": [row[0] for row in pair_specs],
            "player_id": [row[1] for row in pair_specs],
            "from_level_group": [row[2] for row in pair_specs],
            "to_level_group": [row[3] for row in pair_specs],
            "pair_precision_weight": [row[4] for row in pair_specs],
            "translation_pair_eligible": [True] * len(pair_specs),
        }
    )
    profile_rows: list[dict[str, object]] = []
    for pair_id, _, from_level, to_level, _ in pair_specs:
        for core_bin in ALL_CORE_BINS:
            profile_rows.append(
                {
                    "pair_id": pair_id,
                    "core_bin": core_bin,
                    "clr_delta": effects[to_level][core_bin] - effects[from_level][core_bin],
                }
            )
    return pair_summary, pl.DataFrame(profile_rows), effects


def test_level_clr_fit_recovers_connected_anchor_relative_offsets() -> None:
    pair_summary, pair_profile, expected = _synthetic_translation_pairs()
    fit = fit_level_clr_translation(pair_summary, pair_profile, anchor_level="MLB")

    assert fit.metrics["all_levels_connected_to_anchor"] is True
    assert fit.metrics["fitted_level_count"] == 3
    for level, component_effects in expected.items():
        for core_bin, expected_effect in component_effects.items():
            actual = fit.offsets.filter(
                (pl.col("level_group") == level) & (pl.col("core_bin") == core_bin)
            ).row(0, named=True)["clr_environment_effect"]
            assert float(actual) == pytest.approx(expected_effect, abs=1e-10)

    centered = fit.offsets.group_by("level_group").agg(
        pl.col("clr_environment_effect").sum().alias("effect_sum")
    )
    assert centered.filter(pl.col("effect_sum").abs() > 1e-10).is_empty()


def test_level_clr_fit_fails_closed_without_mlb_anchor_support() -> None:
    pair_summary, pair_profile, _ = _synthetic_translation_pairs()
    milb_only = pair_summary.filter(pl.col("to_level_group") != "MLB")
    milb_pair_ids = milb_only.get_column("pair_id").to_list()
    with pytest.raises(ValueError, match="anchor level 'MLB'"):
        fit_level_clr_translation(
            milb_only,
            pair_profile.filter(pl.col("pair_id").is_in(milb_pair_ids)),
            anchor_level="MLB",
        )


def test_level_clr_fit_fails_when_a_level_is_disconnected_from_anchor() -> None:
    pair_summary, pair_profile, _ = _synthetic_translation_pairs()
    extra_summary = pl.DataFrame(
        {
            "pair_id": ["p5"],
            "player_id": [5],
            "from_level_group": ["SINGLE_A"],
            "to_level_group": ["HIGH_A"],
            "pair_precision_weight": [25.0],
            "translation_pair_eligible": [True],
        }
    )
    extra_profile = pl.DataFrame(
        {
            "pair_id": ["p5"] * len(ALL_CORE_BINS),
            "core_bin": list(ALL_CORE_BINS),
            "clr_delta": [0.0] * len(ALL_CORE_BINS),
        }
    )
    with pytest.raises(ValueError, match="not connected to anchor MLB"):
        fit_level_clr_translation(
            pl.concat([pair_summary, extra_summary], how="vertical_relaxed"),
            pl.concat([pair_profile, extra_profile], how="vertical_relaxed"),
            anchor_level="MLB",
        )
