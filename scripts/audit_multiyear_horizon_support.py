"""Inventory available annual/cumulative forecast horizons without fitting a model.

Reads only origin IDs, target season IDs, and existing artifact manifests. Presence
of a season is not certification of completeness or proof of a valid player universe.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


def horizon_support(
    origins: list[int], target_seasons: list[int], *, last_outcome: int = 2025
) -> list[dict]:
    """Use the conservative full-outcome-year < forecast-origin-year embargo."""
    if last_outcome > 2025:
        raise ValueError("Protected outcomes after 2025 are outside this audit")
    if any(year > last_outcome for year in target_seasons):
        raise ValueError("Target table extends beyond the declared outcome boundary")
    seasons = set(target_seasons)
    result = []
    for horizon in range(1, 7):
        annual = [o for o in sorted(set(origins)) if o + horizon in seasons]
        cumulative = [
            o for o in annual
            if set(range(o + 1, o + horizon + 1)) <= seasons
        ]
        folds = []
        for origin in cumulative:
            training = [s for s in cumulative if s + horizon < origin]
            inner = [
                v for v in training
                if any(s + horizon < v for s in training)
            ]
            folds.append({
                "origin": origin,
                "outcome_end": origin + horizon,
                "training_origins": training,
                "inner_validation_origins": inner,
                "touches_2020": origin < 2020 <= origin + horizon,
            })
        result.append({
            "horizon": horizon,
            "annual_label_origins": annual,
            "cumulative_label_origins": cumulative,
            "outer_origins_with_prior_training": [
                f["origin"] for f in folds if f["training_origins"]
            ],
            "outer_origins_with_nested_support": [
                f["origin"] for f in folds if f["inner_validation_origins"]
            ],
            "folds": folds,
        })
    return result


def audit(root: Path) -> dict:
    report = {
        "status": "availability_audit_only_no_model_fit_or_score",
        "last_outcome_season": 2025,
        "embargo": "training_origin + horizon < scoring_origin",
        "limitations": [
            "Season presence is not source completeness certification.",
            "Current panel membership is not a certified historical rights universe.",
            "Potential folds are dependent when players/outcome years overlap.",
            "Nested support means at least one inner split, not adequate sample size.",
            "Excluded one-year origins may be recoverable from original features.",
        ],
        "populations": {},
    }
    for kind in ("hitter", "pitcher"):
        folder = root / f"{kind}-value-panel-v2"
        panel_path = folder / "tables/modeling-panel.parquet"
        target_path = folder / f"tables/{kind}-value-targets.parquet"
        manifest_path = folder / "report.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        hashes = {}
        for key, path in (("modeling_panel", panel_path), ("value_targets", target_path)):
            actual = sha256_file(path)
            if actual != manifest["artifacts"][key]["file_sha256"]:
                raise ValueError(f"Source hash differs from existing manifest: {path}")
            hashes[key] = {"path": path.as_posix(), "sha256": actual}
        panel = pl.read_parquet(panel_path, columns=["origin_year", "player_id"])
        targets = pl.read_parquet(target_path, columns=["season", "player_id"])
        if panel.unique().height != panel.height or targets.unique().height != targets.height:
            raise ValueError(f"Duplicate player-year keys in {kind} sources")
        if panel.null_count().row(0) != (0, 0) or targets.null_count().row(0) != (0, 0):
            raise ValueError(f"Null player-year keys in {kind} sources")
        origins = panel["origin_year"].unique().sort().to_list()
        seasons = targets["season"].unique().sort().to_list()
        report["populations"][kind] = {
            "source_artifacts": hashes,
            "origin_rows": panel.height,
            "origin_players": panel["player_id"].n_unique(),
            "origin_counts": panel.group_by("origin_year").len().sort("origin_year").to_dicts(),
            "target_seasons": seasons,
            "horizons": horizon_support(origins, seasons),
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output", type=Path,
        default=Path("docs/multiyear-horizon-support-2026-09-22.json"),
    )
    args = parser.parse_args()
    report = audit(args.generated_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for kind, population in report["populations"].items():
        for row in population["horizons"]:
            print(kind, row["horizon"], "year(s):", len(row["cumulative_label_origins"]),
                  "mature origins;", len(row["outer_origins_with_prior_training"]),
                  "with prior training;", len(row["outer_origins_with_nested_support"]),
                  "with nested support")


if __name__ == "__main__":
    main()
