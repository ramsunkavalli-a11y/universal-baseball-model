#!/usr/bin/env python3
"""Persist a complete selected playing-time refit outside temporary CI storage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_baseball.durable_model_package import (
    persist_playing_time_refit_package,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refit-root", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    args = parser.parse_args()

    manifest = persist_playing_time_refit_package(
        args.refit_root, args.destination_root
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
