"""Leakage-safe diagnostics for partial pooling of Performance-bin values.

This module does not define production weights. It evaluates a simple,
interpretable shrinkage family against split-half estimates produced by the
MiLB bin-value stability audit.

For a target environment/bin, the prior is built only from the *candidate*
halves of other environments. The target environment is excluded from its own
prior, and held-out/reference halves never contribute to the prior. This keeps
the diagnostic from improving merely by feeding the noisy estimate back into
its shrinkage target.
"""

from __future__ import annotations

from math import sqrt
from typing import Any, Literal, Mapping, Sequence


PoolingScope = Literal["group", "all"]

DEFAULT_PRIOR_STRENGTHS: tuple[int, ...] = (
    0,
    5,
    10,
    25,
    50,
    75,
    100,
    150,
    200,
    300,
    400,
)


def shrink_mean(
    observed_mean: float,
    observed_count: int,
    prior_mean: float,
    prior_strength: int,
) -> float:
    """Shrink an observed mean toward a prior using prior-equivalent counts."""

    if observed_count <= 0:
        raise ValueError("observed_count must be positive")
    if prior_strength < 0:
        raise ValueError("prior_strength must be non-negative")
    if prior_strength == 0:
        return float(observed_mean)
    return (
        float(observed_mean) * observed_count
        + float(prior_mean) * prior_strength
    ) / (observed_count + prior_strength)


def _extract_observations(
    environment_reports: Sequence[Mapping[str, Any]],
    *,
    pool_group_by_league: Mapping[int, str],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for report in environment_reports:
        league_id = int(report["league_id"])
        if league_id not in pool_group_by_league:
            raise ValueError(f"pool group missing for league_id={league_id}")
        environment_id = f"{int(report['season'])}:{league_id}"
        comparison = report["split_half"]["comparison"]
        deltas = comparison.get("deltas") or {}
        if not deltas:
            raise ValueError(f"split-half deltas missing for {environment_id}")
        for bin_name, delta in sorted(deltas.items()):
            candidate = delta["candidate"]
            reference = delta["reference"]
            candidate_count = int(candidate["n"])
            reference_count = int(reference["n"])
            if candidate_count <= 0 or reference_count <= 0:
                raise ValueError(
                    f"non-positive split-half count for {environment_id} {bin_name}"
                )
            observations.append(
                {
                    "environment_id": environment_id,
                    "season": int(report["season"]),
                    "league_id": league_id,
                    "league_name": str(report["league_name"]),
                    "pool_group": str(pool_group_by_league[league_id]),
                    "bin": str(bin_name),
                    "candidate_mean": float(candidate["mean"]),
                    "candidate_count": candidate_count,
                    "candidate_standard_error": (
                        None
                        if candidate.get("se") is None
                        else float(candidate["se"])
                    ),
                    "reference_mean": float(reference["mean"]),
                    "reference_count": reference_count,
                }
            )
    return observations


def _leave_one_environment_out_prior(
    observations: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
    *,
    scope: PoolingScope,
) -> tuple[float, int, int]:
    peers = [
        row
        for row in observations
        if row["environment_id"] != target["environment_id"]
        and row["bin"] == target["bin"]
        and (scope == "all" or row["pool_group"] == target["pool_group"])
    ]
    if not peers:
        raise ValueError(
            "no leave-one-environment-out prior support for "
            f"{target['environment_id']} {target['bin']} scope={scope}"
        )
    total_count = sum(int(row["candidate_count"]) for row in peers)
    prior_mean = sum(
        float(row["candidate_mean"]) * int(row["candidate_count"])
        for row in peers
    ) / total_count
    return prior_mean, total_count, len({row["environment_id"] for row in peers})


def _metrics(predictions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not predictions:
        raise ValueError("cannot score an empty prediction set")
    errors = [float(row["prediction"]) - float(row["reference_mean"]) for row in predictions]
    absolute = [abs(value) for value in errors]
    reference_total = sum(int(row["reference_count"]) for row in predictions)
    weighted_mae = sum(
        abs(float(row["prediction"]) - float(row["reference_mean"]))
        * int(row["reference_count"])
        for row in predictions
    ) / reference_total
    return {
        "observation_count": len(predictions),
        "mae": sum(absolute) / len(absolute),
        "rmse": sqrt(sum(value * value for value in errors) / len(errors)),
        "occurrence_weighted_mae": weighted_mae,
        "max_absolute_error": max(absolute),
        "within_0_05_count": sum(value <= 0.05 for value in absolute),
        "within_0_10_count": sum(value <= 0.10 for value in absolute),
    }


def _best_strength(
    evaluations: Sequence[Mapping[str, Any]],
    *,
    group: str,
    metric: str,
) -> dict[str, Any]:
    candidates = [
        row for row in evaluations if row["pool_group"] == group
    ]
    best = min(candidates, key=lambda row: (float(row[metric]), int(row["prior_strength"])))
    return {
        "prior_strength": int(best["prior_strength"]),
        metric: float(best[metric]),
    }


def evaluate_split_half_pooling(
    environment_reports: Sequence[Mapping[str, Any]],
    *,
    pool_group_by_league: Mapping[int, str],
    prior_strengths: Sequence[int] = DEFAULT_PRIOR_STRENGTHS,
    scope: PoolingScope = "group",
) -> dict[str, Any]:
    """Evaluate fixed-strength shrinkage against held-out split-half means.

    ``scope='group'`` builds the prior from other environments in the target's
    pool group (for example AAA or Rookie/complex). ``scope='all'`` uses every
    other environment. Strength zero is the unpooled baseline.
    """

    if scope not in {"group", "all"}:
        raise ValueError(f"unsupported pooling scope: {scope!r}")
    strengths = sorted({int(value) for value in prior_strengths})
    if not strengths or strengths[0] < 0:
        raise ValueError("prior strengths must be a non-empty non-negative set")
    if 0 not in strengths:
        strengths.insert(0, 0)

    observations = _extract_observations(
        environment_reports,
        pool_group_by_league=pool_group_by_league,
    )
    groups = sorted({str(row["pool_group"]) for row in observations})
    environment_counts = {
        group: len(
            {
                row["environment_id"]
                for row in observations
                if row["pool_group"] == group
            }
        )
        for group in groups
    }
    if scope == "group":
        unsupported = [group for group, count in environment_counts.items() if count < 2]
        if unsupported:
            raise ValueError(
                "group pooling requires at least two environments per group: "
                f"{unsupported}"
            )

    prediction_rows: list[dict[str, Any]] = []
    evaluation_rows: list[dict[str, Any]] = []
    overall_rows: list[dict[str, Any]] = []

    for strength in strengths:
        strength_predictions: list[dict[str, Any]] = []
        for row in observations:
            if strength == 0:
                prior_mean = None
                prior_count = 0
                prior_environment_count = 0
                prediction = float(row["candidate_mean"])
            else:
                prior_mean, prior_count, prior_environment_count = (
                    _leave_one_environment_out_prior(
                        observations,
                        row,
                        scope=scope,
                    )
                )
                prediction = shrink_mean(
                    float(row["candidate_mean"]),
                    int(row["candidate_count"]),
                    prior_mean,
                    strength,
                )
            enriched = {
                **dict(row),
                "scope": scope,
                "prior_strength": strength,
                "prior_mean": prior_mean,
                "prior_candidate_count": prior_count,
                "prior_environment_count": prior_environment_count,
                "prediction": prediction,
                "error": prediction - float(row["reference_mean"]),
                "absolute_error": abs(prediction - float(row["reference_mean"])),
            }
            strength_predictions.append(enriched)
            prediction_rows.append(enriched)

        overall_rows.append(
            {
                "scope": scope,
                "prior_strength": strength,
                **_metrics(strength_predictions),
            }
        )
        for group in groups:
            group_predictions = [
                row for row in strength_predictions if row["pool_group"] == group
            ]
            evaluation_rows.append(
                {
                    "scope": scope,
                    "pool_group": group,
                    "prior_strength": strength,
                    **_metrics(group_predictions),
                }
            )

    direct_by_group = {
        row["pool_group"]: row
        for row in evaluation_rows
        if int(row["prior_strength"]) == 0
    }
    for row in evaluation_rows:
        baseline = direct_by_group[row["pool_group"]]
        row["mae_delta_vs_direct"] = float(row["mae"]) - float(baseline["mae"])
        row["rmse_delta_vs_direct"] = float(row["rmse"]) - float(baseline["rmse"])
        row["occurrence_weighted_mae_delta_vs_direct"] = (
            float(row["occurrence_weighted_mae"])
            - float(baseline["occurrence_weighted_mae"])
        )

    best_by_group = {
        group: {
            "mae": _best_strength(evaluation_rows, group=group, metric="mae"),
            "rmse": _best_strength(evaluation_rows, group=group, metric="rmse"),
            "occurrence_weighted_mae": _best_strength(
                evaluation_rows,
                group=group,
                metric="occurrence_weighted_mae",
            ),
        }
        for group in groups
    }

    return {
        "scope": scope,
        "prior_strengths": strengths,
        "environment_count": len({row["environment_id"] for row in observations}),
        "environment_counts_by_group": environment_counts,
        "observation_count": len(observations),
        "pool_groups": groups,
        "overall_evaluations": overall_rows,
        "group_evaluations": evaluation_rows,
        "best_strength_by_group": best_by_group,
        "predictions": prediction_rows,
        "method": (
            "candidate split-half mean shrunk by candidate occurrence count toward "
            "an occurrence-weighted prior built from candidate halves of other "
            "environments; target environment and every reference half are excluded "
            "from the prior"
        ),
    }
