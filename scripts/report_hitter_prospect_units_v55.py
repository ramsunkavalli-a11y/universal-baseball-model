"""Finish fixed-unit review, retaining exact source/fit traces and both controls."""
from pathlib import Path
import shutil
import polars as pl
import evaluate_hitter_prospect_pooling_v54 as io
import evaluate_hitter_prospect_units_v55 as e
from universal_baseball.storage import sha256_file


def main():
    io.OUT = e.OUT
    cases = io.read(e.OUT / "cases.json")
    notes_path = e.ROOT / "config/practical_hitter_prospect_units_v55_case_notes.json"
    notes = io.read(notes_path)
    assert set(notes) == {f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    pre = io.read(e.OUT / "preflight.json")
    assert all(sha256_file(Path(p)) == h for p, h in pre["input_hashes"].items())
    standardized = {
        r["row_id"]: r for r in pl.read_parquet(e.PRIOR / "predictions.parquet").to_dicts()
    }
    lines = [
        "# Fixed baseball-unit prospect model: actual player review", "",
        "Nine complete source-to-fit reviews. The full candidate is not adopted. "
        "Fixed references remove extreme rare-column standardization but the fitted "
        "workload model materially deteriorates. All established forecasts are bit-exact.", "",
        "The same features, sources, temporal/player folds, targets, numeric C=.01 and "
        "alpha=100 are retained. Important qualification: changing predictor units "
        "changes effective regularization even with numeric penalties held constant. "
        "This is a representation-and-shrinkage comparison, not isolated causal proof "
        "about StandardScaler or a rejection of smooth prospect models.", "",
        "| Scope | Rows | Baseline PA RMSE | Standardized PA RMSE | Fixed PA RMSE | Baseline offense RMSE | Standardized offense RMSE | Fixed offense RMSE |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in io.read(e.OUT / "standardized-comparison.json"):
        a, b, c = [s["scores"][x] for x in ["repaired", "standardized", "shared"]]
        lines.append(
            f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.3f} | {b['pa_rmse']:.3f} | "
            f"{c['pa_rmse']:.3f} | {a['value_rmse']:.6f} | {b['value_rmse']:.6f} | {c['value_rmse']:.6f} |"
        )
    lines += [
        "", "Future-participant rate scoring uses actual PA within each target year "
        "and equal years. Contribution retains non-arrivals. The rate is custom "
        "fixed-event, origin-centered batting wins/600, not official wOBA or latent "
        "park-neutral skill. Offense includes replacement, not fielding/full WAR. "
        "No new park/opponent correction is introduced. Four peers per case are "
        "selected using origin information, not future outcomes.", "",
    ]
    for c in cases:
        o = c["origin"]
        key = f"{o['player_id']}|{o['origin_year']}"
        old = standardized[o["row_id"]]
        lines += [
            f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}", "",
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; "
            f"age {o['age']}, highest observed current level {c['known_highest_current']}. "
            f"Selection: {', '.join(c['selection'])}.", "",
            "| Year | League | PA | HR | K | UBB |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for h in c["source_history"]:
            lines.append(
                f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | "
                f"{h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |"
            )
        lines += [
            "", f"Draft {o['draft_year']}, pick {o['pick_number']}, class "
            f"{o['draft_school_class'] or 'unknown'}. Source pooling retains the "
            "inherited neutral 100-opportunity prior.", "",
            "| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row, prefix, label in [
            (o, "repaired", "Corrected baseline"),
            (old, "shared", "Standardized prospect"),
            (o, "shared", "Fixed-unit prospect"),
        ]:
            lines.append(
                f"| {label} | {row[prefix+'_p']:.6f} | {row[prefix+'_conditional_pa']:.6f} | "
                f"{row[prefix+'_pa']:.6f} | {row[prefix+'_rate']:.6f} | {row[prefix+'_value']:.6f} |"
            )
        actual_rate = format(o["next_batting_rate"], ".6f") if o["next_pa"] else "unobserved"
        lines += [
            f"| Actual | {int(o['next_pa'] > 0)} | Not a forecast | {o['next_pa']} | "
            f"{actual_rate} | {o['next_value']:.6f} |", "",
            f"Fixed expected PA = {o['shared_p']:.9f} × {o['shared_conditional_pa']:.9f}. "
            f"Offense = expected PA × (rate/600 + origin replacement "
            f"{o['origin_replacement_rate']:.9f}/PA). PA-only offense "
            f"{o['prospect_pa_only_value']:.6f}; rate-only {o['prospect_rate_only_value']:.6f}.", "",
        ]
        for head, t in c["heads"].items():
            lines += [
                f"{head}: intercept {t['reference']:.9f}, exact linear sum "
                f"{t['raw_prediction']:.9f}, linked output {t['linked_prediction']:.9f}. "
                "Contribution = coefficient × (input minus fixed reference)/fixed scale.", "",
                "| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |",
                "|---|---:|---:|---:|---:|",
            ]
            for z in t["feature_effects"][:5]:
                lines.append(
                    f"| {z['feature']} | {z['input']:.7f} | {z['fixed_reference']:.7f} | "
                    f"{z['fixed_scale']:.7f} | {z['effect']:.7f} |"
                )
            lines.append("")
        lines += [
            "Broad actual training-profile support: " + ", ".join(
                f"{p['head']} {p['profile_players']} distinct people"
                for p in c["training_profile"]
            ) + ".", "", notes[key], "",
            "| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for p in c["peers"]:
            pr = format(p["next_batting_rate"], ".4f") if p["next_pa"] else "unobserved"
            lines.append(
                f"| {p['player_name']} | {p['repaired_pa']:.2f} | {p['shared_pa']:.2f} | "
                f"{p['next_pa']} | {p['shared_rate']:.4f} | {pr} |"
            )
        lines.append("")
    lines += [
        "## Decision", "",
        "Do not adopt the full fixed-unit model. Never-debut PA MSE worsens +107.718 "
        "(nominal interval +67.114 to +153.027), offense MSE +.000999 "
        "(+.000286 to +.001784). Conditional rate MSE changes +.021800 "
        "(-.167961 to +.216508), statistically uncertain and much less bad than "
        "the standardized +1.226. Public established-player forecasts do not change.", "",
        "Upper-never PA falls from 73,593 to 64,274 versus 92,891 actual. Lower-never "
        "PA rises from 7,652 to 11,915 versus 5,194. Holliday improves, but Alonso and "
        "Julio Rodriguez lose useful opportunity signal. Neither closeness of a "
        "product for Azocar nor fixing one extreme validates the joint forecast.", "",
        "The head-specific results justify one bounded, explicitly post-result "
        "assembly check: standardized prospect opportunity with fixed-unit prospect "
        "hitting, against both complete models and standardized-PA/baseline-rate. "
        "No new fits or weight search. Review that combined forecast before any "
        "selection; none of these development comparisons can certify long-term "
        "prospect value or resolve the established-player availability deficit.", "",
    ]
    path = e.OUT / "player-walkthrough.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf8")
    ver = io.read(e.OUT / "verification.json")
    ver.update(
        player_walkthrough_status="complete", notes_sha256=sha256_file(notes_path),
        walkthrough_sha256=sha256_file(path),
    )
    io.write("verification.json", ver)
    io.write("report.json", dict(
        player_walkthrough_status="complete", cases=len(cases), full_candidate_adopted=False,
        effective_regularization_changes_with_units=True,
        established_forecasts_unchanged=True, protected_outcomes_used=False,
        frozen_forecast_changed=False,
        evidence_hashes={str(p.relative_to(e.ROOT)): sha256_file(p) for p in [
            notes_path, path, e.OUT/"predictions.parquet", e.OUT/"scores.json",
            e.OUT/"intervals.json", e.OUT/"standardized-comparison.json",
        ]},
    ))
    io.write("preflight-summary.json", dict(
        cells=35, heads=105, features=pre["features"],
        checks=[dict(year=c["year"], fold=c["fold"], heads=c["preflight"]) for c in pre["cells"]],
        input_hashes=pre["input_hashes"],
        fixed_unit_scaling=pre.get("fixed_unit_scaling"),
    ))
    dest = e.ROOT / "reports/model-evidence/practical-hitter-prospect-units-v55"
    dest.mkdir(parents=True, exist_ok=True)
    for name in [
        "report.json", "scores.json", "intervals.json", "standardized-comparison.json",
        "verification.json", "preflight-summary.json", "cases.json",
        "player-walkthrough.md", "fit-report.json",
    ]:
        shutil.copy2(e.OUT/name, dest/name)
    print("Nine actual reviews complete; fixed-unit full prospect model not adopted.", flush=True)


if __name__ == "__main__":
    main()
