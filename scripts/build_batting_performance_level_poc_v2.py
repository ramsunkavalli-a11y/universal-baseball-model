#!/usr/bin/env python
"""Run the generic level POC with the production contact-control resolver.

Kept as a thin launcher while the multi-level gate is active so the already
reviewed POC script does not need a large mechanical rewrite just to swap one
resolver dependency. Once the gate is accepted, this indirection can be folded
into the generic builder in a contained cleanup.
"""

from __future__ import annotations

import build_batting_performance_level_poc as base

from universal_baseball.player_game_controls import resolve_player_game_contact_controls


base.resolve_player_game_batting = resolve_player_game_contact_controls


if __name__ == "__main__":
    raise SystemExit(base.main())
