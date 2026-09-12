#!/usr/bin/env python3
"""Test an active-prior-equivalent BIP bridge on untouched 2024 outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_full_bip_pitcher_challenger import _affiliated_components
from audit_full_bip_pitcher_rate_replay import _rate_rows, _score, _source


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pitching-source", type=Path, action="append", required=True)
    parser.add_argument(
        "--hitting-translation-source", type=Path, action="append", required=True
    )
    parser.add_argument("--bip-2021", type=Path, required=True)
    parser.add_argument("--bip-2022", type=Path, required=True)
    parser.add_argument("--bip-2023", type=Path, required=True)
    parser.add_argument("--bip-2024", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _fit_weight(frames: list[pl.DataFrame]) -> float:
    joined = pl.concat(frames, how="vertical_relaxed")
    baseline = joined.get_column("baseline_runs_per_800").to_numpy()
    full_bip = joined.get_column("candidate_runs_per_800").to_numpy()
    target = joined.get_column("target_runs_per_800").to_numpy()
    bf = joined.get_column("target_bf").to_numpy()
    residual_estimate = full_bip - baseline
    residual_target = target - baseline
    denominator = float(np.sum(bf * residual_estimate**2))
    unconstrained = (
        float(np.sum(bf * residual_estimate * residual_target)) / denominator
        if denominator > 0
        else 0.0
    )
    return min(1.0, max(0.0, unconstrained))


def _fold(
    source: pl.DataFrame,
    contact_source: pl.DataFrame,
    origin: Path,
    target: Path,
    *,
    weight: float,
) -> pl.DataFrame:
    return _rate_rows(
        source,
        contact_source,
        origin_root=origin,
        target_root=target,
        contact_weight=weight,
        bip_prior_contacts=None,
    )


def main() -> int:
    args = _args()
    source = _source(args.pitching_source)
    contact_source = pl.concat(
        [
            _affiliated_components(path, "hitter")
            for path in args.hitting_translation_source
        ],
        how="vertical_relaxed",
    )
    development_full = [
        _fold(source, contact_source, args.bip_2021, args.bip_2022, weight=1.0),
        _fold(source, contact_source, args.bip_2022, args.bip_2023, weight=1.0),
    ]
    frozen_weight = _fit_weight(development_full)
    development = [
        _fold(
            source,
            contact_source,
            args.bip_2021,
            args.bip_2022,
            weight=frozen_weight,
        ),
        _fold(
            source,
            contact_source,
            args.bip_2022,
            args.bip_2023,
            weight=frozen_weight,
        ),
    ]
    confirmation = _fold(
        source,
        contact_source,
        args.bip_2023,
        args.bip_2024,
        weight=frozen_weight,
    )
    confirmation_score = _score(confirmation)
    baseline = confirmation_score["baseline"]
    candidate = confirmation_score["candidate"]
    promotion_pass = bool(
        candidate["player_mae"] < baseline["player_mae"]
        and candidate["player_rmse"] < baseline["player_rmse"]
        and candidate["bf_weighted_mae"] < baseline["bf_weighted_mae"]
        and candidate["bf_weighted_rmse"] < baseline["bf_weighted_rmse"]
        and not confirmation_score["supported_level_reversals"]
    )
    report = {
        "status": "reliability_bridge_2024_confirmation_scored",
        "method": {
            "bip_prior": "800 BF times origin MLB BIP rate",
            "weight_fit": "bounded BF-weighted squared-error residual blend",
            "development_transitions": ["2021_to_2022", "2022_to_2023"],
            "confirmation_transition": "2023_to_2024",
        },
        "frozen_weight": frozen_weight,
        "development": {
            "2021_to_2022": _score(development[0]),
            "2022_to_2023": _score(development[1]),
        },
        "confirmation": confirmation_score,
        "promotion_pass": promotion_pass,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
