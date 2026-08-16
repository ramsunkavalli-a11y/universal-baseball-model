#!/usr/bin/env python
"""Run the generic level POC with the certified production control/authority rules.

The generic builder predates two cross-level findings:

1. player-game contact controls need the production component-wise resolver; and
2. official participant authority belongs at play-sequence grain, not current
   official ``isInPlay`` pitch grain.

Keep this launcher thin while the 2024 multilevel gate is active. It monkeypatches
only those two already-certified boundaries into the reviewed generic builder.
After the gate is accepted, the indirection can be folded into the production
builder in one cleanup commit.
"""

from __future__ import annotations

import polars as pl

import build_batting_performance_level_poc as base
from universal_baseball.contact_identity_overlay import (
    OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA,
    apply_contact_identity_authority_by_sequence,
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_sequence_authority,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.player_game_controls import resolve_player_game_contact_controls


base.resolve_player_game_batting = resolve_player_game_contact_controls


def _participant_authority_and_false_negative_gate(
    contacts: pl.DataFrame,
    player_games: pl.DataFrame,
    *,
    unflagged_sample_games: int,
):
    residuals = contact_identity_residuals(contacts, player_games)
    exception_games = exception_games_from_residuals(residuals)
    if exception_games:
        pa, _pitch = fetch_official_game_evidence(exception_games)
        official_sequences = project_official_sequence_authority(pa)
    else:
        official_sequences = pl.DataFrame(schema=OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA)

    authorized, authority_metrics = apply_contact_identity_authority_by_sequence(
        contacts,
        player_games,
        official_sequences,
    )

    all_games = sorted(
        int(value) for value in contacts.get_column("game_pk").unique().to_list()
    )
    exception_set = set(exception_games)
    unflagged = [game for game in all_games if game not in exception_set]
    sample = base._evenly_spaced(unflagged, unflagged_sample_games)

    if sample:
        sample_pa, _sample_pitch = fetch_official_game_evidence(sample)
        sample_authority = project_official_sequence_authority(sample_pa)
        sample_source = contacts.filter(pl.col("game_pk").is_in(sample))
        joined = sample_source.join(
            sample_authority,
            on=["game_pk", "at_bat_index"],
            how="left",
        )
        missing = joined.filter(pl.col("official_batter_id").is_null())
        mismatch = joined.filter(
            pl.col("official_batter_id").is_not_null()
            & (
                pl.col("source_batter_id").cast(pl.Int64)
                != pl.col("official_batter_id").cast(pl.Int64)
            )
        )
        if not missing.is_empty():
            raise RuntimeError(
                "unflagged identity sample contains source contact sequences without "
                "official matchup authority"
            )
        if not mismatch.is_empty():
            raise RuntimeError(
                "unflagged identity sample found hidden source batter attribution errors"
            )
        source_sequence_count = sample_source.select(
            "game_pk", "at_bat_index"
        ).unique().height
        covered_sequence_count = joined.select(
            "game_pk", "at_bat_index"
        ).unique().height
        comparison = {
            "authority_grain": "play_sequence",
            "source_contact_count": sample_source.height,
            "official_contact_count": 0,
            # Compatibility field for the generic report line; this means source
            # contact rows covered by official sequence authority, not pitch-key
            # equality against current official isInPlay rows.
            "matched_physical_key_count": joined.height,
            "source_only_physical_key_count": missing.height,
            "official_only_physical_key_count": 0,
            "batter_mismatch_count": mismatch.height,
            "batter_mismatch_game_count": mismatch.get_column("game_pk").n_unique(),
            "source_contact_sequence_count": source_sequence_count,
            "covered_source_sequence_count": covered_sequence_count,
            "official_allplay_sequence_count": sample_authority.height,
        }
    else:
        comparison = {
            "authority_grain": "play_sequence",
            "source_contact_count": 0,
            "official_contact_count": 0,
            "matched_physical_key_count": 0,
            "source_only_physical_key_count": 0,
            "official_only_physical_key_count": 0,
            "batter_mismatch_count": 0,
            "batter_mismatch_game_count": 0,
            "source_contact_sequence_count": 0,
            "covered_source_sequence_count": 0,
            "official_allplay_sequence_count": 0,
        }

    false_negative = {
        "design": "deterministic evenly spaced unflagged contact games",
        "authority_grain": "play_sequence",
        "unflagged_game_count": len(unflagged),
        "sample_game_count": len(sample),
        "sample_game_ids": sample,
        **comparison,
    }
    return authorized, authority_metrics, false_negative


base._participant_authority_and_false_negative_gate = (
    _participant_authority_and_false_negative_gate
)


if __name__ == "__main__":
    raise SystemExit(base.main())
