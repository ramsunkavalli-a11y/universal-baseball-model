#!/usr/bin/env python3
"""Time-separated test of pitcher contact shape beyond aggregate components."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


LEVEL_ORDER = {
    "ROOKIE_COMPLEX": 0.0,
    "SINGLE_A": 1.0,
    "HIGH_A": 2.0,
    "AA": 3.0,
    "AAA": 4.0,
    "MLB": 5.0,
}
LEVEL_LABEL = {value: key for key, value in LEVEL_ORDER.items()}
BASE_FEATURES = (
    "prior_component_rate",
    "prior_k_rate",
    "prior_ubb_rate",
    "prior_hbp_rate",
    "prior_hr_rate",
    "log_prior_bf",
    "starter_share",
    "highest_level",
)
CONTACT_FEATURES = {
    "ground": ("ground_rate",),
    "popup": ("ground_rate", "popup_rate"),
    "pulled_air": ("ground_rate", "popup_rate", "pulled_air_rate"),
    "pulled_ground": (
        "ground_rate",
        "popup_rate",
        "pulled_air_rate",
        "pulled_ground_rate",
    ),
}
ALPHAS = (1.0, 10.0, 100.0, 1000.0)


def _season_stats(path: Path) -> pl.DataFrame:
    raw = (
        pl.read_parquet(path)
        .filter(pl.col("batters_faced") > 0)
        .with_columns(
            pl.col("level_group").replace_strict(LEVEL_ORDER).alias("level_number"),
            (pl.col("base_on_balls") - pl.col("intentional_walks"))
            .clip(lower_bound=0)
            .alias("ubb"),
        )
    )
    environment = raw.group_by(["season", "level_group"]).agg(
        (pl.col("strike_outs").sum() / pl.col("batters_faced").sum()).alias(
            "environment_k_rate"
        ),
        (pl.col("ubb").sum() / pl.col("batters_faced").sum()).alias(
            "environment_ubb_rate"
        ),
        (pl.col("hit_batters").sum() / pl.col("batters_faced").sum()).alias(
            "environment_hbp_rate"
        ),
        (pl.col("home_runs").sum() / pl.col("batters_faced").sum()).alias(
            "environment_hr_rate"
        ),
    )
    return (
        raw.join(environment, on=["season", "level_group"], validate="m:1")
        .with_columns(
            (
                pl.col("strike_outs")
                - pl.col("batters_faced") * pl.col("environment_k_rate")
            ).alias("so_above_environment"),
            (
                pl.col("ubb") - pl.col("batters_faced") * pl.col("environment_ubb_rate")
            ).alias("ubb_above_environment"),
            (
                pl.col("hit_batters")
                - pl.col("batters_faced") * pl.col("environment_hbp_rate")
            ).alias("hbp_above_environment"),
            (
                pl.col("home_runs")
                - pl.col("batters_faced") * pl.col("environment_hr_rate")
            ).alias("hr_above_environment"),
        )
        .group_by(["season", "player_id"])
        .agg(
            pl.col("batters_faced").sum().alias("bf"),
            pl.col("strike_outs").sum().alias("so"),
            pl.col("ubb").sum(),
            pl.col("hit_batters").sum().alias("hbp"),
            pl.col("home_runs").sum().alias("hr"),
            pl.col("so_above_environment").sum(),
            pl.col("ubb_above_environment").sum(),
            pl.col("hbp_above_environment").sum(),
            pl.col("hr_above_environment").sum(),
            pl.col("games").sum(),
            pl.col("starts").sum(),
            pl.col("level_number").max().alias("highest_level"),
        )
    )


def _contact_rates(frame: pl.DataFrame) -> pl.DataFrame:
    grouped = frame.group_by(["season", "player_id"]).agg(
        pl.col("contact_count").sum(),
        pl.col("trajectory_known_count").sum(),
        pl.col("ground_count").sum(),
        pl.col("airborne_count").sum(),
        pl.col("popup_count").sum(),
        pl.col("direction_known_count").sum(),
        pl.col("pulled_air_count").sum(),
        pl.col("pulled_ground_count").sum(),
    )
    totals = grouped.group_by("season").agg(
        (pl.col("ground_count").sum() / pl.col("trajectory_known_count").sum()).alias(
            "mean_ground"
        ),
        (pl.col("popup_count").sum() / pl.col("airborne_count").sum()).alias(
            "mean_popup"
        ),
        (pl.col("pulled_air_count").sum() / pl.col("airborne_count").sum()).alias(
            "mean_pull_air"
        ),
        (pl.col("pulled_ground_count").sum() / pl.col("ground_count").sum()).alias(
            "mean_pull_ground"
        ),
    )
    return grouped.join(totals, on="season").with_columns(
        (
            (pl.col("ground_count") + 200 * pl.col("mean_ground"))
            / (pl.col("trajectory_known_count") + 200)
        ).alias("ground_rate"),
        (
            (pl.col("popup_count") + 400 * pl.col("mean_popup"))
            / (pl.col("airborne_count") + 400)
        ).alias("popup_rate"),
        (
            (pl.col("pulled_air_count") + 400 * pl.col("mean_pull_air"))
            / (pl.col("airborne_count") + 400)
        ).alias("pulled_air_rate"),
        (
            (pl.col("pulled_ground_count") + 400 * pl.col("mean_pull_ground"))
            / (pl.col("ground_count") + 400)
        ).alias("pulled_ground_rate"),
    )


def _cohort(stats: pl.DataFrame, contacts: pl.DataFrame, year: int) -> pl.DataFrame:
    prior = stats.filter(
        (pl.col("season") == year) & (pl.col("highest_level") < LEVEL_ORDER["MLB"])
    )
    prior = prior.with_columns(
        (pl.col("so_above_environment") / (pl.col("bf") + 100)).alias("prior_k_rate"),
        (pl.col("ubb_above_environment") / (pl.col("bf") + 100)).alias(
            "prior_ubb_rate"
        ),
        (pl.col("hbp_above_environment") / (pl.col("bf") + 100)).alias(
            "prior_hbp_rate"
        ),
        (pl.col("hr_above_environment") / (pl.col("bf") + 100)).alias("prior_hr_rate"),
        pl.col("bf").log1p().alias("log_prior_bf"),
        (pl.col("starts") / pl.col("games").clip(lower_bound=1)).alias("starter_share"),
    ).with_columns(
        (
            13 * pl.col("prior_hr_rate")
            + 3 * (pl.col("prior_ubb_rate") + pl.col("prior_hbp_rate"))
            - 2 * pl.col("prior_k_rate")
        ).alias("prior_component_rate")
    )
    future = (
        stats.filter(pl.col("season") == year + 1)
        .filter(pl.col("bf") >= 100)
        .select(
            "player_id",
            pl.col("bf").alias("future_bf"),
            (
                (
                    13 * pl.col("hr_above_environment")
                    + 3
                    * (
                        pl.col("ubb_above_environment")
                        + pl.col("hbp_above_environment")
                    )
                    - 2 * pl.col("so_above_environment")
                )
                / pl.col("bf")
            ).alias("future_component_rate"),
        )
    )
    return (
        prior.join(
            _contact_rates(contacts).filter(pl.col("season") == year),
            on=["season", "player_id"],
            how="inner",
        )
        .join(future, on="player_id", how="inner", validate="1:1")
        .filter((pl.col("bf") >= 100) & (pl.col("trajectory_known_count") >= 50))
        .sort("player_id")
    )


def _design(frame: pl.DataFrame, extra: tuple[str, ...]) -> np.ndarray:
    return frame.select([*BASE_FEATURES, *extra]).to_numpy()


def _metric(y: np.ndarray, prediction: np.ndarray) -> dict[str, float | int]:
    error = prediction - y
    return {
        "players": len(y),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mae": float(np.abs(error).mean()),
        "bias": float(error.mean()),
    }


def _bootstrap(
    y: np.ndarray, base: np.ndarray, candidate: np.ndarray
) -> dict[str, float]:
    difference = (candidate - y) ** 2 - (base - y) ** 2
    rng = np.random.default_rng(20260910)
    draws = np.array(
        [difference[rng.integers(0, len(y), len(y))].mean() for _ in range(2000)]
    )
    return {
        "candidate_minus_baseline_mse": float(difference.mean()),
        "p025": float(np.quantile(draws, 0.025)),
        "p975": float(np.quantile(draws, 0.975)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contact-2021",
        type=Path,
        default=Path(
            "reports/generated/pitcher-contact-panel/tables/pitcher_contact_panel.parquet"
        ),
    )
    parser.add_argument(
        "--contact-2022",
        type=Path,
        default=Path(
            "reports/generated/pitcher-contact-panel-2022/tables/pitcher_contact_panel.parquet"
        ),
    )
    parser.add_argument(
        "--contact-2023",
        type=Path,
        default=Path(
            "reports/generated/pitcher-contact-panel-2023/tables/"
            "pitcher_contact_panel.parquet"
        ),
    )
    parser.add_argument(
        "--stats",
        type=Path,
        default=Path(
            "reports/generated/phase2-arrival-skill-source/tables/affiliated_pitching_components.parquet"
        ),
    )
    parser.add_argument(
        "--source-reports",
        nargs=3,
        type=Path,
        default=(
            Path("reports/generated/pitcher-contact-panel/report.json"),
            Path("reports/generated/pitcher-contact-panel-2022/report.json"),
            Path("reports/generated/pitcher-contact-panel-2023/report.json"),
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/pitcher-contact-increment-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/pitcher-contact-increment-result.md"),
    )
    args = parser.parse_args()
    stats = _season_stats(args.stats)
    contacts = pl.concat(
        [
            pl.read_parquet(args.contact_2021),
            pl.read_parquet(args.contact_2022),
            pl.read_parquet(args.contact_2023),
        ]
    )
    development = _cohort(stats, contacts, 2021)
    outer = _cohort(stats, contacts, 2022)
    confirmation = _cohort(stats, contacts, 2023)
    folds = KFold(n_splits=5, shuffle=True, random_state=20260910)
    y_dev = development["future_component_rate"].to_numpy()
    candidates = []
    for name, extra in {"baseline": (), **CONTACT_FEATURES}.items():
        x = _design(development, extra)
        for alpha in ALPHAS:
            predictions = np.empty(len(y_dev))
            for fit, score in folds.split(x):
                model = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
                    x[fit], y_dev[fit]
                )
                predictions[score] = model.predict(x[score])
            candidates.append(
                {
                    "name": name,
                    "alpha": alpha,
                    "cv_rmse": float(np.sqrt(np.mean((predictions - y_dev) ** 2))),
                }
            )
    selected_by_name = {
        name: min(
            (r for r in candidates if r["name"] == name), key=lambda r: r["cv_rmse"]
        )
        for name in ("baseline", *CONTACT_FEATURES)
    }
    y_outer = outer["future_component_rate"].to_numpy()
    y_confirmation = confirmation["future_component_rate"].to_numpy()
    outer_predictions = {}
    confirmation_predictions = {}
    results = {}
    for name, selection in selected_by_name.items():
        extra = () if name == "baseline" else CONTACT_FEATURES[name]
        model = make_pipeline(
            StandardScaler(), Ridge(alpha=float(selection["alpha"]))
        ).fit(_design(development, extra), y_dev)
        prediction = model.predict(_design(outer, extra))
        confirmation_prediction = model.predict(_design(confirmation, extra))
        outer_predictions[name] = prediction
        confirmation_predictions[name] = confirmation_prediction
        results[name] = {
            "development": selection,
            "outer": _metric(y_outer, prediction),
            "confirmation": _metric(y_confirmation, confirmation_prediction),
        }
    for name in CONTACT_FEATURES:
        results[name]["paired_outer"] = _bootstrap(
            y_outer, outer_predictions["baseline"], outer_predictions[name]
        )
        results[name]["paired_confirmation"] = _bootstrap(
            y_confirmation,
            confirmation_predictions["baseline"],
            confirmation_predictions[name],
        )
    best = min(CONTACT_FEATURES, key=lambda name: selected_by_name[name]["cv_rmse"])
    promoted = (
        results[best]["paired_outer"]["p975"] < 0
        and results[best]["paired_confirmation"]["p975"] < 0
    )
    source_manifests = []
    for path in args.source_reports:
        source = json.loads(path.read_text(encoding="utf-8"))
        source_manifests.append(
            {
                "years": source["years"],
                "asset_count": source["asset_count"],
                "raw_download_bytes": source["raw_download_bytes"],
                "resolved_contacts": source["resolved_contacts"],
                "assets": source["assets"],
            }
        )
    subgroup_results = {}
    for label, frame, y, baseline_prediction, candidate_prediction in (
        (
            "outer",
            outer,
            y_outer,
            outer_predictions["baseline"],
            outer_predictions[best],
        ),
        (
            "confirmation",
            confirmation,
            y_confirmation,
            confirmation_predictions["baseline"],
            confirmation_predictions[best],
        ),
    ):
        rows = []
        levels = frame["highest_level"].to_numpy()
        for level in sorted(set(levels)):
            selected = levels == level
            if int(selected.sum()) < 100:
                continue
            rows.append(
                {
                    "highest_prior_level": LEVEL_LABEL[float(level)],
                    "players": int(selected.sum()),
                    **_bootstrap(
                        y[selected],
                        baseline_prediction[selected],
                        candidate_prediction[selected],
                    ),
                }
            )
        subgroup_results[label] = rows
    payload = {
        "report_schema_version": 1,
        "status": "confirmed_research_signal" if promoted else "rejected",
        "development": "2021 inputs predict 2022",
        "outer": "2022 inputs predict 2023",
        "confirmation": "2023 inputs predict 2024; model remains fit on 2021 only",
        "eligibility": "pre-MLB input; same-player next-year BF >=100; prior BF >=100; known trajectory >=50",
        "target": (
            "next-season component rate above the applicable season-level environment"
        ),
        "development_players": development.height,
        "outer_players": outer.height,
        "confirmation_players": confirmation.height,
        "shrinkage_contacts": {"ground": 200, "popup": 400, "direction": 400},
        "selected_contact_path": best,
        "promoted": promoted,
        "results": results,
        "selected_path_subgroups": subgroup_results,
        "source_manifests": source_manifests,
        "model_effect": (
            "research signal only; production requires an incremental test against "
            "the incumbent translated pitcher projection"
        ),
    }
    args.output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Pitcher contact increment audit",
        "",
        f"Status: **{payload['status']}**; production model unchanged.",
        "",
        f"- Development: {payload['development']} ({development.height} pitchers).",
        f"- Frozen outer test: {payload['outer']} ({outer.height} pitchers).",
        f"- Untouched confirmation: {payload['confirmation']} "
        f"({confirmation.height} pitchers).",
        f"- Development-selected contact path: `{best}`.",
        "",
        "| Model | Outer RMSE | Outer MSE change [95% interval] | Confirm RMSE | Confirm MSE change [95% interval] |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in results.items():
        pair = result.get("paired_outer")
        confirm_pair = result.get("paired_confirmation")
        lines.append(
            f"| {name} | {result['outer']['rmse']:.5f} | "
            + (
                "— | "
                if pair is None
                else f"{pair['candidate_minus_baseline_mse']:+.6f} "
                f"[{pair['p025']:+.6f}, {pair['p975']:+.6f}] | "
            )
            + f"{result['confirmation']['rmse']:.5f} | "
            + (
                "— |"
                if confirm_pair is None
                else f"{confirm_pair['candidate_minus_baseline_mse']:+.6f} "
                f"[{confirm_pair['p025']:+.6f}, {confirm_pair['p975']:+.6f}] |"
            )
        )
    lines += [
        "",
        "Features were fixed in baseball order: ground rate, popup rate, pulled-air rate, then pulled-ground rate. Rates were exposure-shrunk; missing or sparse evidence did not receive favorable values. Selection used only the development transition. A research signal required negative full confidence intervals in both later transitions. It still must beat the existing level-translated projection before production use.",
        "",
        "This is a level-and-season-adjusted conditional-quality test among pre-MLB pitchers with at least 100 BF in the next season. It does not estimate arrival or workload; those outcomes remain in the separate hurdle model.",
        "",
        "## Selected ground-rate path by prior level",
        "",
        "| Period | Prior level | Pitchers | MSE change [95% interval] |",
        "|---|---|---:|---:|",
    ]
    for period, rows in subgroup_results.items():
        for row in rows:
            lines.append(
                f"| {period} | {row['highest_prior_level']} | {row['players']} | "
                f"{row['candidate_minus_baseline_mse']:+.6f} "
                f"[{row['p025']:+.6f}, {row['p975']:+.6f}] |"
            )
    lines.append("")
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
