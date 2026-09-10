#!/usr/bin/env python3
"""Compare a frozen model prospect top 50 with an outside audit list."""

from __future__ import annotations

import argparse
from datetime import date
from html import escape
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_ranking_audit import add_explanations
from universal_baseball.storage import write_canonical_parquet


def _display(value: object, *, percent: bool = False, money: bool = False) -> str:
    if value is None:
        return "—"
    if percent:
        return f"{100.0 * float(value):.0f}%"
    if money:
        return f"${float(value) / 1_000_000.0:.1f}M"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _table(rows: list[dict[str, object]], columns: list[tuple[str, str, str]]) -> str:
    head = "".join(f"<th>{escape(label)}</th>" for _, label, _ in columns)
    body = []
    for row in rows:
        cells = []
        for key, _, style in columns:
            value = row.get(key)
            text = _display(value, percent=style == "percent", money=style == "money")
            cells.append(f"<td>{escape(text)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _write_html(
    path: Path,
    *,
    dated: str,
    summary: dict[str, object],
    source_top: pl.DataFrame,
    model_top: pl.DataFrame,
) -> None:
    source_columns = [
        ("source_rank", "FG", ""), ("player_name", "Player", ""),
        ("prospect_type", "Type", ""), ("comparison_status", "Status", ""),
        ("model_rank", "Model", ""), ("model_fv_display", "Model FV", ""),
        ("age_years", "Age", ""), ("level_tier", "Level", ""),
        ("model_arrival_probability", "MLB chance", "percent"),
        ("model_meaningful_role_probability", "Role chance", "percent"),
        ("expected_six_year_war", "Expected WAR", ""),
        ("baseball_explanation", "Model explanation", ""),
    ]
    model_columns = [
        ("model_rank", "Model", ""), ("player_name", "Player", ""),
        ("model_player_type", "Type", ""), ("source_rank", "FG", ""),
        ("model_fv_display", "Model FV", ""), ("age_years", "Age", ""),
        ("level_tier", "Level", ""),
        ("model_arrival_probability", "MLB chance", "percent"),
        ("model_meaningful_role_probability", "Role chance", "percent"),
        ("conditional_skill_war_rate", "WAR rate", ""),
        ("expected_six_year_war", "Expected WAR", ""),
        ("transferable_value_dollars", "Value", "money"),
        ("baseball_explanation", "Model explanation", ""),
    ]
    cards = "".join(
        f"<div><b>{escape(str(value))}</b><span>{escape(key.replace('_', ' '))}</span></div>"
        for key, value in summary.items()
        if not isinstance(value, list)
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Prospect ranking sanity audit</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;color:#17212b;background:#faf9f5}}
h1,h2{{color:#063852}} p{{max-width:1000px;line-height:1.45}} .cards{{display:flex;gap:12px;flex-wrap:wrap}}
.cards div{{background:white;border:1px solid #ddd6c8;border-radius:8px;padding:12px 16px;min-width:150px}}
.cards b,.cards span{{display:block}} .cards b{{font-size:22px}} .cards span{{font-size:12px;color:#59636e}}
.table-wrap{{overflow:auto;border:1px solid #d8d3c8;border-radius:8px;background:white}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th{{position:sticky;top:0;background:#ebe8df;text-align:left}}
th,td{{padding:8px;border-bottom:1px solid #ece8df;vertical-align:top;white-space:nowrap}}
td:last-child{{white-space:normal;min-width:520px}} .note{{background:#fff4d6;padding:12px;border-left:4px solid #d59b18}}
</style></head><body><h1>Prospect ranking sanity audit</h1>
<p>Checkpoint {escape(dated)}. FanGraphs is an outside diagnostic only. The model is not rewarded for agreement and no public rank or FV enters a projection.</p>
<div class="note">A disagreement is acceptable only when the model can trace it to age, level, performance, opportunity, WAR and value using one consistent rule.</div>
<div class="cards">{cards}</div>
<h2>FanGraphs top 50 through the model</h2><div class="table-wrap">{_table(source_top.to_dicts(), source_columns)}</div>
<h2>Model top 50 through the FanGraphs check</h2><div class="table-wrap">{_table(model_top.to_dicts(), model_columns)}</div>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-top50-ranking-audit"),
    )
    return parser.parse_args()


def _rates(root: Path, dated: str) -> pl.DataFrame:
    tables = root / "phase2-conditional-war-paths" / dated / "tables"
    hitter = pl.read_parquet(tables / "hitter_expected_war_paths.parquet").group_by(
        "player_id"
    ).agg(
        pl.lit("hitter").alias("rate_player_type"),
        pl.col("conditional_war_per_600_pa").mean().alias(
            "conditional_skill_war_rate"
        ),
        pl.lit("600 PA").alias("skill_rate_unit"),
        pl.col("batting_runs_per_600").mean(),
        pl.col("baserunning_runs_per_600").mean(),
        pl.col("defense_runs_per_600").mean(),
        pl.col("positional_runs_per_600").mean(),
        pl.col("weighted_history_pa").max().alias("weighted_skill_workload"),
        pl.col("reliability").mean().alias("skill_reliability"),
        pl.col("evidence_tier").first().alias("skill_evidence_tier"),
    )
    pitcher = pl.read_parquet(tables / "pitcher_expected_war_paths.parquet").group_by(
        "player_id"
    ).agg(
        pl.lit("pitcher").alias("rate_player_type"),
        pl.col("conditional_war_per_800_bf").mean().alias(
            "conditional_skill_war_rate"
        ),
        pl.lit("800 BF").alias("skill_rate_unit"),
        pl.col("pitching_runs_above_average_per_800").mean(),
        pl.col("predicted_so_rate").mean(),
        pl.col("predicted_ubb_rate").mean(),
        pl.col("predicted_hbp_rate").mean(),
        pl.col("predicted_hr_rate").mean(),
        pl.col("weighted_history_bf").max().alias("weighted_skill_workload"),
        pl.col("reliability").mean().alias("skill_reliability"),
        pl.col("evidence_tier").first().alias("skill_evidence_tier"),
    )
    return pl.concat([hitter, pitcher], how="diagonal_relaxed")


def _arrivals(root: Path, dated: str) -> pl.DataFrame:
    source = root / "phase2-prospect-arrival" / dated
    frames = []
    for player_type in ("hitter", "pitcher"):
        frames.append(
            pl.read_parquet(source / f"{player_type}-arrival-probabilities.parquet")
            .select(
                "player_id",
                pl.lit(player_type).alias("arrival_player_type"),
                "age_years",
                "age_evidence_source",
                "level_tier",
                "current_milb_workload",
                "primary_level_tier",
                "primary_level_workload_share",
                "level_progression",
                "development_history_workload",
                "development_history_seasons",
                "role_tier",
                "on_40man",
                "height_inches",
                "weight_pounds",
                "bat_side",
                "pitch_hand",
                "birth_country",
                "rule4_drafted",
                "draft_pick_quality",
                "signing_bonus_percentile",
            )
        )
    return pl.concat(frames, how="vertical_relaxed")


def _model_ranking(root: Path, dated: str) -> pl.DataFrame:
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    ).filter(
        pl.col("player_name").is_not_null()
        & pl.col("ordered_arrival_probability").is_not_null()
    )
    values = pl.read_parquet(
        root / "phase2-current-value" / dated / "value-records.parquet"
    ).select(
        "player_id",
        "transferable_value_dollars",
        "expected_remaining_cost_dollars",
        "calculation_status",
        "coverage_tier",
    )
    model = (
        nested.join(values, on="player_id", how="inner", validate="1:1")
        .join(_arrivals(root, dated), on="player_id", how="left", validate="1:m")
        .filter(pl.col("model_player_type") == pl.col("arrival_player_type"))
        .join(
            _rates(root, dated),
            left_on=["player_id", "model_player_type"],
            right_on=["player_id", "rate_player_type"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("three_tier_expected_workload").alias("expected_workload"),
            pl.col("three_tier_expected_six_year_war").alias(
                "expected_six_year_war"
            ),
            pl.col("three_tier_model_fv_granular").alias("model_fv_granular"),
            pl.col("three_tier_model_fv_display").alias("model_fv_display"),
        )
        .sort(
            ["transferable_value_dollars", "expected_six_year_war", "player_id"],
            descending=[True, True, False],
        )
        .with_row_index("model_rank", offset=1)
    )
    return model


def _comparison(model: pl.DataFrame, source: pl.DataFrame) -> pl.DataFrame:
    source_join = source.filter(pl.col("player_id").is_not_null()).select(
        "player_id",
        pl.col("rank").alias("source_rank"),
        pl.col("player_name").alias("source_player_name"),
        pl.col("future_value").cast(pl.String).alias("source_fv"),
        pl.col("position").alias("source_position"),
        pl.col("age").alias("source_age"),
        pl.col("eta_year").alias("source_eta_year"),
    )
    return model.join(source_join, on="player_id", how="left", validate="1:1")


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    source = pl.read_parquet(
        root / "phase2-prospect-source" / dated / "fangraphs-top-100.parquet"
    )
    model = _model_ranking(root, dated)
    comparison = _comparison(model, source)
    model_top = add_explanations(
        comparison.head(50).with_columns(
            pl.when(pl.col("source_rank") <= 50)
            .then(pl.lit("same_top_50"))
            .otherwise(pl.lit("model_top_50_only"))
            .alias("comparison_status")
        )
    )

    public_top = source.filter(pl.col("rank") <= 50).rename(
        {"rank": "source_rank", "future_value": "source_fv"}
    )
    control = pl.read_parquet(
        root / "league-control" / dated / "league-control-snapshot.parquet"
    ).select("player_id", "mlb_debut_date", "organization_status")
    public_top = public_top.join(control, on="player_id", how="left", validate="m:1")
    public_matched = public_top.filter(pl.col("player_id").is_not_null()).join(
        model, on="player_id", how="left", validate="1:1", suffix="_model"
    )
    public_unmatched = public_top.filter(pl.col("player_id").is_null()).with_columns(
        pl.lit(None, dtype=pl.UInt32).alias("model_rank")
    )
    public_view_columns = list(public_matched.columns)
    public_unmatched = public_unmatched.select(
        [
            pl.col(column)
            if column in public_unmatched.columns
            else pl.lit(None).alias(column)
            for column in public_view_columns
        ]
    )
    source_top = pl.concat(
        [public_matched, public_unmatched], how="vertical_relaxed"
    ).sort("source_rank").with_columns(
        pl.when(pl.col("model_rank") <= 50)
        .then(pl.lit("same_top_50"))
        .when(pl.col("model_rank").is_not_null())
        .then(pl.lit("source_top_50_model_lower"))
        .when(pl.col("mlb_debut_date").is_not_null())
        .then(pl.lit("graduated_to_mlb"))
        .when(pl.col("player_id").is_null())
        .then(pl.lit("source_identity_unresolved"))
        .otherwise(pl.lit("unresolved_missing_from_model"))
        .alias("comparison_status")
    )
    source_top = add_explanations(source_top)

    overlap = source_top.filter(pl.col("model_rank") <= 50).height
    source_graduated = source_top.filter(
        pl.col("comparison_status") == "graduated_to_mlb"
    ).height
    source_unresolved = source_top.filter(
        pl.col("comparison_status").is_in(
            ["source_identity_unresolved", "unresolved_missing_from_model"]
        )
    ).height
    model_type_counts = model_top.group_by("model_player_type").len().sort(
        "model_player_type"
    )
    outside_source_top = model_top.filter(
        pl.col("source_rank").is_null() | (pl.col("source_rank") > 50)
    ).height
    flagged_source = source_top.filter(pl.col("review_flags").list.len() > 0).height
    flagged_model = model_top.filter(pl.col("review_flags").list.len() > 0).height
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "diagnostic_only_no_ranking_tuning",
        "ranking_metric": "pre-MLB transferable value, then expected six-year WAR",
        "policy": {
            "outside_rank_used_as_model_input": False,
            "agreement_is_required": False,
            "every_large_difference_requires_model_input_explanation": True,
            "fix_general_rules_not_named_players": True,
        },
        "summary": {
            "source_top_50_rows": source_top.height,
            "source_top_50_still_pre_mlb": source_top.height - source_graduated,
            "source_top_50_graduated_to_mlb": source_graduated,
            "source_top_50_unresolved_model_match": source_unresolved,
            "top_50_membership_overlap": overlap,
            "model_top_50_outside_source_top_50": outside_source_top,
            "source_top_50_with_review_flags": flagged_source,
            "model_top_50_with_review_flags": flagged_model,
            "model_top_50_by_player_type": model_type_counts.to_dicts(),
        },
        "structural_checks": {
            "model_prospect_pool": model.height,
            "duplicate_model_players": model.group_by("player_id").len().filter(
                pl.col("len") > 1
            ).height,
            "missing_basic_explanation_inputs_in_model_top_50": model_top.filter(
                pl.col("review_flags").list.contains(
                    "missing_basic_explanation_input"
                )
            ).height,
            "extreme_skill_rates_in_model_top_50": model_top.filter(
                pl.col("review_flags").list.contains(
                    "extreme_conditional_skill_rate"
                )
            ).height,
        },
    }
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "source_top_50": write_canonical_parquet(
            source_top,
            output / "source-top-50-comparison.parquet",
            table_name="prospect_source_top_50_comparison",
        ).as_record(),
        "model_top_50": write_canonical_parquet(
            model_top,
            output / "model-top-50-comparison.parquet",
            table_name="prospect_model_top_50_comparison",
        ).as_record(),
    }
    report["storage"] = storage
    source_top.with_columns(pl.col("review_flags").list.join("|")).write_csv(
        output / "source-top-50-comparison.csv"
    )
    model_top.with_columns(pl.col("review_flags").list.join("|")).write_csv(
        output / "model-top-50-comparison.csv"
    )
    _write_html(
        output / "index.html",
        dated=dated,
        summary=report["summary"],
        source_top=source_top,
        model_top=model_top,
    )
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
