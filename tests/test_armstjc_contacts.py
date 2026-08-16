from __future__ import annotations

import json

import polars as pl

from universal_baseball.armstjc_contacts import (
    contact_resolution_metrics,
    project_armstjc_contact_observations,
    resolve_armstjc_contact_observations,
)


def _raw() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1, 1],
            "at_bat_number": [0, 1, 2],
            "pitch_number": [1, 1, 1],
            "batter": [101, 102, 103],
            "pitcher": [201, 201, 201],
            "batter_side": ["R", "L", "R"],
            "game_date": ["2024-06-01", "2024-06-01", "2024-06-01"],
            "game_type": ["R", "R", "R"],
            "league_id": [112, 112, 112],
            # The first two contacts exercise non-X evidence.
            "type": ["D", "S", "B"],
            "bb_type": [None, "ground_ball", None],
            "hc_x": [None, 125.42, None],
            "hc_y": [None, 100.0, None],
            "description": ["Batter singles.", "Batter grounds out.", None],
            "hit_location": [None, None, None],
            "hit_distance_sc": [None, None, None],
            "launch_speed": [None, None, None],
            "launch_angle": [None, None, None],
        },
        schema_overrides={
            "bb_type": pl.String,
            "hc_x": pl.Float64,
            "hc_y": pl.Float64,
            "description": pl.String,
            "hit_location": pl.String,
            "hit_distance_sc": pl.Float64,
            "launch_speed": pl.Float64,
            "launch_angle": pl.Float64,
        },
    )


def test_projection_accepts_d_e_x_or_hitdata_contact_evidence() -> None:
    projected = project_armstjc_contact_observations(
        _raw(), source_asset="2024_6_aaa_pbp.csv", season=2024
    )
    assert projected.get_column("source_is_in_play").to_list() == [True, True, False]
    assert projected.get_column("source_batter_id").to_list() == [101, 102, 103]


def test_resolution_uses_non_null_consensus_and_preserves_conflicts() -> None:
    projected = project_armstjc_contact_observations(
        _raw().head(1), source_asset="a.csv", season=2024
    )
    null_variant = projected.with_columns(
        pl.lit(None, dtype=pl.String).alias("bb_type"),
        pl.lit(None, dtype=pl.Float64).alias("hc_x"),
        pl.lit("b.csv").alias("source_asset"),
    )
    value_variant = projected.with_columns(
        pl.lit("fly_ball").alias("bb_type"),
        pl.lit(80.0).alias("hc_x"),
        pl.lit("c.csv").alias("source_asset"),
    )
    conflicting_variant = projected.with_columns(
        pl.lit("line_drive").alias("bb_type"),
        pl.lit(80.0).alias("hc_x"),
        pl.lit("d.csv").alias("source_asset"),
    )

    resolved = resolve_armstjc_contact_observations(
        pl.concat([null_variant, value_variant, conflicting_variant]),
        contacts_only=False,
    ).to_dicts()[0]

    assert resolved["hc_x"] == 80.0
    assert resolved["bb_type"] is None
    assert resolved["source_snapshot_count"] == 3
    assert "bb_type" in json.loads(resolved["conflict_fields_json"])
    assert "hc_x" not in json.loads(resolved["conflict_fields_json"])


def test_exact_duplicate_rows_do_not_create_variants_but_raw_count_is_retained() -> None:
    projected = project_armstjc_contact_observations(
        _raw().head(1), source_asset="a.csv", season=2024
    )
    resolved = resolve_armstjc_contact_observations(
        pl.concat([projected, projected]), contacts_only=False
    ).to_dicts()[0]
    assert resolved["observation_variant_count"] == 1
    assert resolved["raw_source_row_count"] == 2
    assert resolved["conflict_field_count"] == 0


def test_contact_status_conflict_never_enters_contacts_only_view() -> None:
    projected = project_armstjc_contact_observations(
        _raw().head(1), source_asset="a.csv", season=2024
    )
    conflict = projected.with_columns(
        pl.lit(False).alias("source_is_in_play"),
        pl.lit("b.csv").alias("source_asset"),
    )
    observations = pl.concat([projected, conflict])
    all_resolved = resolve_armstjc_contact_observations(observations, contacts_only=False)
    contacts = resolve_armstjc_contact_observations(observations, contacts_only=True)
    assert contacts.is_empty()
    metrics = contact_resolution_metrics(observations, all_resolved)
    assert metrics["contact_status_conflict_key_count"] == 1
    assert metrics["resolved_contact_count"] == 0


def test_description_conflict_is_explicit_profile_conflict() -> None:
    projected = project_armstjc_contact_observations(
        _raw().head(1), source_asset="a.csv", season=2024
    )
    conflict = projected.with_columns(
        pl.lit("Different result narrative.").alias("result_description"),
        pl.lit("b.csv").alias("source_asset"),
    )
    observations = pl.concat([projected, conflict])
    resolved = resolve_armstjc_contact_observations(observations, contacts_only=False)
    row = resolved.to_dicts()[0]
    assert row["result_description"] is None
    assert "result_description" in json.loads(row["conflict_fields_json"])
    metrics = contact_resolution_metrics(observations, resolved)
    assert metrics["profile_field_conflict_contact_count"] == 1
