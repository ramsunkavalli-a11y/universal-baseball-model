"""Finish actual player review and close the prospect representation batch."""
from pathlib import Path
import shutil
import evaluate_hitter_compact_readiness_v57 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.read(e.OUT/"cases.json")
    notes_path=e.ROOT/"config/practical_hitter_compact_readiness_v57_case_notes.json"
    notes=e.read(notes_path)
    assert set(notes)=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    pre=e.read(e.OUT/"preflight.json")
    assert all(sha256_file(Path(p))==h for p,h in pre["input_hashes"].items())
    fit=e.read(e.OUT/"fit-report.json")
    lines=["# Compact readiness: eight actual player reviews","",
        "The compact model removes 92 sparse production-rate inputs and fits two "
        "readiness heads, not a new hitting head. All 70 saved heads replay. "
        "All original columns, established forecasts and hitting rates are exact. "
        "Do not adopt this forecast: better totals and clearer terms do not offset "
        "slightly worse individual errors.","",
        "| Scope | Rows | Baseline PA RMSE | Prior detailed PA RMSE | Compact PA RMSE | Baseline offense RMSE | Compact offense RMSE |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for s in e.read(e.OUT/"prior-readiness-comparison.json"):
        a,b,c=[s["scores"][x] for x in ["repaired","prospect_pa_only","shared"]]
        lines.append(f"| {s['scope']} | {s['rows']} | {a['pa_rmse']:.4f} | {b['pa_rmse']:.4f} | "
            f"{c['pa_rmse']:.4f} | {a['value_rmse']:.6f} | {c['value_rmse']:.6f} |")
    lines += ["",
        f"Conditional PA is clipped on {fit['conditional_clipped']:,} of 24,199 never-debut "
        "forecasts (9.6%). This active-only linear model extrapolates negative "
        "conditional workload to some non-ready profiles. Those rows remain in "
        "all scores. A [1,800] bound ensures physical output, not calibrated "
        "conditional use; it is another reason not to certify this architecture.","",
        "Source pooling retains three-year 1/.8/.6 recency and the inherited neutral "
        "100-opportunity prior. Only AA/AAA K, UBB and HR production rates enter "
        "readiness; all levels retain exposure. No new park/opponent correction "
        "or hitting fit is introduced. Offense uses custom common-origin event "
        "weights plus replacement, not official wOBA, full WAR or career value. "
        "Future-participant rate is unobserved when next PA is zero.",""]
    for c in cases:
        o=c["origin"];key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}","",
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; age {o['age']}, "
            f"highest observed current {c['known_highest_current']}; draft {o['draft_year']}, "
            f"pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}. "
            f"Selection: {', '.join(c['selection'])}.","",
            "| Year | League | PA | HR | K | UBB |","|---|---|---:|---:|---:|---:|"]
        for h in c["source_history"]:
            lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | "
                f"{h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ["","| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |",
            "|---|---:|---:|---:|---:|---:|"]
        for a in ["repaired","shared"]:
            lines.append(f"| {a} | {o[a+'_p']:.6f} | {o[a+'_conditional_pa']:.6f} | "
                f"{o[a+'_pa']:.6f} | {o[a+'_rate']:.6f} | {o[a+'_value']:.6f} |")
        actual=format(o["next_batting_rate"],".6f") if o["next_pa"] else "unobserved"
        lines += [f"| Actual | {int(o['next_pa']>0)} | Not a forecast | {o['next_pa']} | "
            f"{actual} | {o['next_value']:.6f} |","",
            f"Expected PA = {o['shared_p']:.9f} × {o['shared_conditional_pa']:.9f}; "
            f"offense = PA × (unchanged rate/600 + origin replacement {o['origin_replacement_rate']:.9f}/PA).",""]
        for head,t in c["heads"].items():
            lines += [f"{head}: intercept {t['reference']:.9f}, exact linear sum "
                f"{t['raw_prediction']:.9f}, linked output {t['linked_prediction']:.9f}. "
                "Contributions are coefficient × (input minus actual training mean)/training scale; "
                "they describe the fitted model, not causal effects.","",
                "| Feature | Origin input | Training mean | Training scale | Contribution |",
                "|---|---:|---:|---:|---:|"]
            for z in t["feature_effects"][:5]:
                lines.append(f"| {z['feature']} | {z['input']:.7f} | {z['training_mean']:.7f} | "
                    f"{z['training_scale']:.7f} | {z['effect']:.7f} |")
            lines.append("")
        lines += ["Broad actual profile support: "+", ".join(
            f"{p['head']} {p['profile_players']} people" for p in c["training_profile"])+".","",notes[key],"",
            "| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |",
            "|---|---:|---:|---:|---:|"]
        for p in c["peers"]:
            pr=format(p["next_batting_rate"],".4f") if p["next_pa"] else "unobserved"
            lines.append(f"| {p['player_name']} | {p['shared_pa']:.2f} | {p['next_pa']} | "
                f"{p['shared_rate']:.4f} | {pr} |")
        lines.append("")
    lines += ["## Origin and probability checks","",
        "| Information year → MLB target | Actual prospect PA | Baseline PA | Compact PA | Actual arrivals | Baseline expected arrivals | Compact expected arrivals |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for s in e.read(e.OUT/"scores.json"):
        if not s["scope"].startswith("never_origin_"):
            continue
        y=int(s["scope"].split("_")[-1]);a=s["scores"]["repaired"];b=s["scores"]["shared"]
        p=s["probabilities"]
        lines.append(f"| {y} → {y+1} | {s['actual_pa']:.0f} | {a['pa_total']:.0f} | {b['pa_total']:.0f} | "
            f"{p['repaired']['actual_participants']} | {p['repaired']['expected_participants']:.1f} | "
            f"{p['shared']['expected_participants']:.1f} |")
    lines += ["",
        "The 2021-origin return-to-normal cohort worsens from 10,463 to 6,326 "
        "prospect PA versus 18,944 actual, with expected arrivals 80 to 45 versus "
        "158. The 2023-origin cohort rises from 14,758 to 22,091 versus only 11,697 "
        "actual. These are major opposite calibration errors, not a harmless "
        "one-player miss. Canceled-year flags are present, but their presence does "
        "not prove the model handles career interruption/reorganization correctly. "
        "The exact source of the vintage/role associations remains unestablished; "
        "do not call this a uniquely identified COVID effect. Probability losses "
        "also worsen overall: Brier .020003 to .020559 and log loss .071834 to "
        ".074951. A closer seven-year PA total masks these errors.","",
        "## Batch decision","",
        "Never-debut offense MSE worsens +.0001351, nominal interval [-.0003200,+.0005834]; "
        "no meaningful individual gain. Upper-never PA total improves from 73,593 "
        "to 83,447 versus 92,891 actual. Lower-never remains 7,652 versus 5,194. "
        "Never-debut total offense 217.53 is close to 214.80 actual but the model "
        "misallocates individual forecasts. All public current-MLB forecasts remain "
        "unchanged (PA MAE 106.87 versus Steamer 92.08).","",
        "Removing fragile rookie rates makes several model explanations more "
        "baseball-reasonable, but loses useful classifier signal for Julio "
        "Rodriguez and does not resolve stars' starting-role expectations. "
        "This negative does not prove lower-league production is useless; it "
        "tests this reduced next-year readiness construction with fixed penalties.","",
        "Close V54–57 without an automatic forecast promotion. Keep numeric source "
        "repair and corrected baseline talent/readiness as the defensible research "
        "anchor. Preserve the detailed PA-only variant as an uncertain alternative, "
        "not a new winning model. Next material work is timely MLB availability "
        "and role-to-workload uncertainty, with matched public cutoff qualifications. "
        "Do not spend another batch sweeping feature scales or penalties on these "
        "same rare prospect cases.",""]
    path=e.OUT/"player-walkthrough.md";path.write_text("\n".join(lines)+"\n",encoding="utf8")
    ver=e.read(e.OUT/"verification.json")
    assert ver["replayed_heads"]==70
    ver.update(player_walkthrough_status="complete",notes_sha256=sha256_file(notes_path),
        walkthrough_sha256=sha256_file(path),conditional_clipped=fit["conditional_clipped"])
    e.write("verification.json",ver)
    e.write("report.json",dict(player_walkthrough_status="complete",cases=len(cases),
        full_candidate_adopted=False,meaningful_joint_gain=False,prospect_representation_batch_closed=True,
        conditional_clipped=fit["conditional_clipped"],rate_unchanged=True,
        protected_outcomes_used=False,frozen_forecast_changed=False,
        evidence_hashes={str(p.relative_to(e.ROOT)):sha256_file(p) for p in [
            path,notes_path,e.OUT/"predictions.parquet",e.OUT/"scores.json",
            e.OUT/"intervals.json",e.OUT/"prior-readiness-comparison.json"]}))
    e.write("preflight-summary.json",dict(cells=35,heads=70,features=pre["features"],
        removed_features=pre["removed_features"],input_hashes=pre["input_hashes"],
        checks=[dict(year=c["year"],fold=c["fold"],heads=c["preflight"]) for c in pre["cells"]]))
    dest=e.ROOT/"reports/model-evidence/practical-hitter-compact-readiness-v57"
    dest.mkdir(parents=True,exist_ok=True)
    for name in ["report.json","scores.json","intervals.json","prior-readiness-comparison.json",
        "verification.json","preflight-summary.json","cases.json","player-walkthrough.md","fit-report.json"]:
        shutil.copy2(e.OUT/name,dest/name)
    print("Eight actual compact-readiness reviews complete; representation batch closed.",flush=True)


if __name__=="__main__":main()
