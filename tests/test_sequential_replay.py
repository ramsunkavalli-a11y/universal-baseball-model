from datetime import UTC, date, datetime

import polars as pl
import pytest

from universal_baseball.sequential_replay import replay_value_checkpoints


def _records(*, vintage: bool = False, unexplained: bool = False) -> pl.DataFrame:
    rows = []
    for index, (checkpoint, day, value, game, projection) in enumerate(
        [
            ("c1", 1, 10_000_000.0, date(2024, 4, 1), "projection-a"),
            (
                "c2",
                2,
                11_000_000.0,
                date(2024, 4, 2) if not unexplained else date(2024, 4, 1),
                "projection-b" if not unexplained else "projection-a",
            ),
        ]
    ):
        cutoff = datetime(2024, 4, day, 23, tzinfo=UTC)
        rows.extend(
            [
                {
                    "checkpoint_id": checkpoint,
                    "as_of_at_utc": cutoff,
                    "evidence_cutoff_at_utc": cutoff,
                    "replay_mode": (
                        "vintage_information_set" if vintage else "retrospective_event_cutoff"
                    ),
                    "player_id": 1,
                    "organization_id": 100,
                    "rights_state": "controlled",
                    "last_completed_game_date": game,
                    "model_version": "model-a",
                    "evidence_bundle_id": f"bundle-{index}",
                    "projection_source_id": projection,
                    "contract_source_id": "contract-a",
                    "coverage_tier": "primary",
                    "calculation_status": "available",
                    "expected_remaining_war": 2.0 + index,
                    "expected_remaining_war_lower": 1.0,
                    "expected_remaining_war_upper": 4.0,
                    "expected_remaining_cost_dollars": 5_000_000.0,
                    "transferable_value_dollars": value,
                    "transferable_value_lower_dollars": value - 2_000_000,
                    "transferable_value_upper_dollars": value + 2_000_000,
                    "declared_change_reasons": "",
                },
                {
                    "checkpoint_id": checkpoint,
                    "as_of_at_utc": cutoff,
                    "evidence_cutoff_at_utc": cutoff,
                    "replay_mode": (
                        "vintage_information_set" if vintage else "retrospective_event_cutoff"
                    ),
                    "player_id": 2,
                    "organization_id": None,
                    "rights_state": "no_incumbent_rights",
                    "last_completed_game_date": None,
                    "model_version": "model-a",
                    "evidence_bundle_id": f"bundle-{index}",
                    "projection_source_id": "population-prior",
                    "contract_source_id": "no-rights",
                    "coverage_tier": "prior",
                    "calculation_status": "available",
                    "expected_remaining_war": 0.5,
                    "expected_remaining_war_lower": -0.5,
                    "expected_remaining_war_upper": 1.5,
                    "expected_remaining_cost_dollars": 0.0,
                    "transferable_value_dollars": 0.0,
                    "transferable_value_lower_dollars": 0.0,
                    "transferable_value_upper_dollars": 0.0,
                    "declared_change_reasons": "",
                },
            ]
        )
    return pl.DataFrame(rows)


def _universes() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "checkpoint_id": checkpoint,
                "player_id": player,
                "organization_id": organization,
                "rights_state": rights,
            }
            for checkpoint in ("c1", "c2")
            for player, organization, rights in (
                (1, 100, "controlled"),
                (2, None, "no_incumbent_rights"),
            )
        ]
    )


def _evidence(*, knowledge: bool = False, future_event: bool = False) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "checkpoint_id": checkpoint,
                "source_snapshot_id": f"source-{checkpoint}",
                "maximum_predictor_event_date": date(
                    2024, 4, day + (1 if future_event else 0)
                ),
                "knowledge_available_at_utc": (
                    datetime(2024, 4, day, 20, tzinfo=UTC) if knowledge else None
                ),
            }
            for checkpoint, day in (("c1", 1), ("c2", 2))
        ]
    )


def test_replay_accepts_complete_event_cutoff_checkpoints() -> None:
    result = replay_value_checkpoints(_records(), _universes(), _evidence())

    assert result.checkpoints.height == 2
    assert result.checkpoints.get_column("players").to_list() == [2, 2]
    player = result.deltas.filter(pl.col("player_id") == 1).row(0, named=True)
    assert player["transferable_value_change_dollars"] == 1_000_000.0
    assert player["change_reasons"] == "completed_games_added,projection_evidence_change"


def test_replay_accepts_vintage_only_with_known_source_timing() -> None:
    result = replay_value_checkpoints(
        _records(vintage=True), _universes(), _evidence(knowledge=True)
    )
    assert result.checkpoints.get_column("replay_mode").unique().to_list() == [
        "vintage_information_set"
    ]


def test_replay_rejects_false_vintage_claim() -> None:
    with pytest.raises(ValueError, match="vintage source timing"):
        replay_value_checkpoints(_records(vintage=True), _universes(), _evidence())


def test_replay_rejects_future_source_event() -> None:
    with pytest.raises(ValueError, match="source evidence crosses"):
        replay_value_checkpoints(_records(), _universes(), _evidence(future_event=True))


def test_replay_rejects_dropped_player() -> None:
    records = _records().filter(
        ~((pl.col("checkpoint_id") == "c2") & (pl.col("player_id") == 2))
    )
    with pytest.raises(ValueError, match="frozen rights universe"):
        replay_value_checkpoints(records, _universes(), _evidence())


def test_replay_rejects_value_for_no_incumbent_rights() -> None:
    records = _records().with_columns(
        [
            pl.when(pl.col("player_id") == 2)
            .then(pl.lit(value))
            .otherwise(pl.col(column))
            .alias(column)
            for column, value in (
                ("transferable_value_lower_dollars", 0.0),
                ("transferable_value_dollars", 1.0),
                ("transferable_value_upper_dollars", 1.0),
            )
        ]
    )
    with pytest.raises(ValueError, match="rights that are not transferable"):
        replay_value_checkpoints(records, _universes(), _evidence())


def test_replay_rejects_unexplained_material_change() -> None:
    with pytest.raises(ValueError, match="unexplained material"):
        replay_value_checkpoints(
            _records(unexplained=True), _universes(), _evidence()
        )
