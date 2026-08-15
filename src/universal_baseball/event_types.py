"""Versioned MLB Stats API event-type semantics used for reconciliation.

This is a small reproducibility snapshot of the public
``https://statsapi.mlb.com/api/v1/eventTypes`` endpoint retrieved on 2026-08-15.
It is intentionally explicit rather than inferred from event names. A future
unseen code is treated as unknown and must be investigated before certification
rather than silently assumed to be or not be a plate appearance.

Only the two flags needed at this foundation stage are retained: whether MLB
marks the event as a plate appearance and whether it is a hit.
"""

from __future__ import annotations


# code: (plate_appearance, hit)
MLB_EVENT_TYPE_FLAGS: dict[str, tuple[bool, bool]] = {
    "pickoff_1b": (False, False),
    "pickoff_2b": (False, False),
    "pickoff_3b": (False, False),
    "pitcher_step_off": (False, False),
    "pickoff_error_1b": (False, False),
    "pickoff_error_2b": (False, False),
    "pickoff_error_3b": (False, False),
    "batter_timeout": (False, False),
    "mound_visit": (False, False),
    "no_pitch": (False, False),
    "single": (True, True),
    "double": (True, True),
    "triple": (True, True),
    "home_run": (True, True),
    "double_play": (True, False),
    "field_error": (True, False),
    "error": (False, False),
    "field_out": (True, False),
    "fielders_choice": (True, False),
    "fielders_choice_out": (True, False),
    "force_out": (True, False),
    "grounded_into_double_play": (True, False),
    # The endpoint currently marks this false. Preserve source semantics rather
    # than silently 'correcting' it; reconciliation will expose any problem.
    "grounded_into_triple_play": (False, False),
    "strikeout": (True, False),
    "strike_out": (True, False),
    "strikeout_double_play": (True, False),
    "strikeout_triple_play": (True, False),
    "triple_play": (True, False),
    "sac_fly": (True, False),
    "catcher_interf": (True, False),
    "batter_interference": (True, False),
    "fielder_interference": (False, False),
    "runner_interference": (False, False),
    "fan_interference": (True, False),
    "batter_turn": (False, False),
    "ejection": (False, False),
    "cs_double_play": (False, False),
    "defensive_indiff": (False, False),
    "sac_fly_double_play": (True, False),
    "sac_bunt": (True, False),
    "sac_bunt_double_play": (True, False),
    "walk": (True, False),
    "intent_walk": (True, False),
    "hit_by_pitch": (True, False),
    "injury": (False, False),
    "os_ruling_pending_prior": (False, False),
    "os_ruling_pending_primary": (True, False),
    "at_bat_start": (False, False),
    "passed_ball": (False, False),
    "other_advance": (False, False),
    "runner_double_play": (False, False),
    "runner_placed": (False, False),
    "pitching_substitution": (False, False),
    "offensive_substitution": (False, False),
    "defensive_switch": (False, False),
    "umpire_substitution": (False, False),
    "pitcher_switch": (False, False),
    "game_advisory": (False, False),
    "stolen_base": (False, False),
    "stolen_base_2b": (False, False),
    "stolen_base_3b": (False, False),
    "stolen_base_home": (False, False),
    "caught_stealing": (False, False),
    "caught_stealing_2b": (False, False),
    "caught_stealing_3b": (False, False),
    "caught_stealing_home": (False, False),
    "defensive_substitution": (False, False),
    "pickoff_caught_stealing_2b": (False, False),
    "pickoff_caught_stealing_3b": (False, False),
    "pickoff_caught_stealing_home": (False, False),
    "balk": (False, False),
    "forced_balk": (False, False),
    "wild_pitch": (False, False),
    "other_out": (False, False),
}

KNOWN_EVENT_TYPES = frozenset(MLB_EVENT_TYPE_FLAGS)
PLATE_APPEARANCE_EVENT_TYPES = frozenset(
    code for code, (is_pa, _) in MLB_EVENT_TYPE_FLAGS.items() if is_pa
)
HIT_EVENT_TYPES_FROM_MLB = frozenset(
    code for code, (_, is_hit) in MLB_EVENT_TYPE_FLAGS.items() if is_hit
)
