"""Preserved capture recipe with an explicit manager-row parsing correction."""
from pathlib import Path
import capture_npb_hitter_snapshot_2026 as old
from universal_baseball.npb_hitter_2026_identity_v2 import names
from universal_baseball.storage import sha256_file

original_seals = old.c.seals


def seals():
    result = original_seals()
    for p in [Path(__file__), old.c.ROOT / 'src/universal_baseball/npb_hitter_2026_identity_v2.py',
              old.c.ROOT / 'docs/hitter-npb-2026-staff-row-clarification.md']:
        result[str(p)] = sha256_file(p)
    return result


if __name__ == '__main__':
    old.names = names
    old.c.seals = seals
    old.main()
