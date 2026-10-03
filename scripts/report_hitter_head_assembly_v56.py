"""Close the assembly only after its eight joint player reviews."""
from pathlib import Path
import shutil
import assemble_hitter_heads_v56 as e
from universal_baseball.storage import sha256_file


def main():
    cases=e.e.read(e.OUT/"cases.json")
    notes_path=e.ROOT/"config/practical_hitter_head_assembly_v56_case_notes.json"
    notes=e.e.read(notes_path)
    assert set(notes)=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    pre=e.e.read(e.OUT/"preflight.json")
    assert all(sha256_file(Path(p))==h for p,h in pre["input_hashes"].items())
    lines=["# Separate prospect head assembly: eight actual player reviews","",
        "No new fits or weight search. Assembly uses standardized V54 opportunity "
        "and fixed-unit V55 hitting, with corrected V53 forecasts exact for established "
        "players. This post-result selection is development evidence, not confirmation.","",
        "| Scope | Rows | Baseline offense RMSE | Baseline-rate/new-PA RMSE | Combined RMSE |",
        "|---|---:|---:|---:|---:|"]
    for s in e.e.read(e.OUT/"scores.json")[:5]:
        lines.append(f"| {s['scope']} | {s['rows']} | {s['scores']['repaired']['value_rmse']:.6f} | "
            f"{s['scores']['prospect_pa_only']['value_rmse']:.6f} | {s['scores']['assembled']['value_rmse']:.6f} |")
    lines += ["","Rate is custom fixed-event origin-centered batting wins/600, not official "
        "wOBA or park-neutral latent talent. Future-participant rate errors use actual "
        "PA within each year and equal years. All non-arrivals stay in contribution "
        "scoring. Offense includes replacement, not full WAR. Highest observed level "
        "can be a cameo; it is not a season-ending role. No new environmental adjustment.",""]
    for c in cases:
        o=c["origin"]; key=f"{o['player_id']}|{o['origin_year']}"
        lines += [f"## {o['player_name']}: {o['origin_year']} to {o['target_year']}","",
            f"Player {o['player_id']}, row {o['row_id']}, fold {o['outer_fold']}; "
            f"age {o['age']}, highest current observed {c['known_highest_current']}; "
            f"draft {o['draft_year']}, pick {o['pick_number']}, class {o['draft_school_class'] or 'unknown'}. "
            f"Selection: {', '.join(c['selection'])}.","",
            "| Year | League | PA | HR | K | UBB |","|---|---|---:|---:|---:|---:|"]
        for h in c["source_history"]:
            lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | "
                f"{h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ["","| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |",
            "|---|---:|---:|---:|---:|---:|"]
        for a in ["repaired","standardized","fixed","assembled"]:
            lines.append(f"| {a} | {o[a+'_p']:.6f} | {o[a+'_conditional_pa']:.6f} | "
                f"{o[a+'_pa']:.6f} | {o[a+'_rate']:.6f} | {o[a+'_value']:.6f} |")
        actual=format(o["next_batting_rate"],".6f") if o["next_pa"] else "unobserved"
        lines += [f"| Actual | {int(o['next_pa']>0)} | Not a forecast | {o['next_pa']} | "
            f"{actual} | {o['next_value']:.6f} |","",
            f"Expected PA = {o['assembled_p']:.9f} × {o['assembled_conditional_pa']:.9f}. "
            f"Offense = PA × (rate/600 + origin replacement {o['origin_replacement_rate']:.9f}/PA).",""]
        for head,t in c["heads"].items():
            lines += [f"{head}: {t['transformation']}; intercept {t['reference']:.9f}, "
                f"exact raw sum {t['raw_prediction']:.9f}, linked output {t['linked_prediction']:.9f}. "
                "Contributions are coefficient × transformed origin input, not causal effects.","",
                "| Feature | Origin input | Reference | Scale | Contribution |","|---|---:|---:|---:|---:|"]
            for z in t["feature_effects"][:5]:
                ref=z.get("training_mean",z.get("fixed_reference"))
                scale=z.get("training_scale",z.get("fixed_scale"))
                lines.append(f"| {z['feature']} | {z['input']:.7f} | {ref:.7f} | {scale:.7f} | {z['effect']:.7f} |")
            lines.append("")
        lines += ["Broad actual training support: "+", ".join(
            f"{p['head']} {p['profile_players']} people" for p in c["training_profile"])+".","",
            notes[key],"","| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |",
            "|---|---:|---:|---:|---:|"]
        for p in c["peers"]:
            pr=format(p["next_batting_rate"],".4f") if p["next_pa"] else "unobserved"
            lines.append(f"| {p['player_name']} | {p['assembled_pa']:.2f} | {p['next_pa']} | {p['assembled_rate']:.4f} | {pr} |")
        lines.append("")
    lines += ["## Decision","",
        "Do not replace baseline hitting with the fixed-unit prospect head. Never-debut "
        "offense MSE changes -.0000291 against corrected baseline, nominal interval "
        "[-.0007089,+.0006280]; against new-PA/baseline-rate it changes +.000000061 "
        "[-.0003551,+.0003669]. This is effectively no gain. Upper-minor contribution "
        "improves modestly, lower-minor contribution worsens; sparse profiles remain.","",
        "The simpler PA-only construction remains a research alternative, not an "
        "automatic promotion. Exact player checks reveal rare rookie statistics "
        "still dominating conditional playing time, including Acuna's offsetting "
        "rookie triples/HBP/walk terms. Stop combining and scaling the same "
        "over-detailed readiness representation. A materially different compact "
        "readiness head must focus on role/exposure, pedigree, age and supported "
        "production, retaining talent as its own target. Established-player "
        "availability remains a separate practical shortfall.",""]
    path=e.OUT/"player-walkthrough.md"; path.write_text("\n".join(lines)+"\n",encoding="utf8")
    ver=e.e.read(e.OUT/"verification.json")
    ver.update(player_walkthrough_status="complete",notes_sha256=sha256_file(notes_path),
        walkthrough_sha256=sha256_file(path))
    e.write("verification.json",ver)
    e.write("report.json",dict(player_walkthrough_status="complete",cases=len(cases),
        full_assembly_adopted=False,new_rate_adopted=False,new_pa_remains_research=True,
        post_result_architecture_selection=True,meaningful_joint_gain=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,
        evidence_hashes={str(p.relative_to(e.ROOT)):sha256_file(p) for p in [
            path,notes_path,e.OUT/"scores.json",e.OUT/"intervals.json",e.OUT/"predictions.parquet"]}))
    dest=e.ROOT/"reports/model-evidence/practical-hitter-head-assembly-v56"
    dest.mkdir(parents=True,exist_ok=True)
    for name in ["preflight.json","report.json","scores.json","intervals.json","verification.json","cases.json","player-walkthrough.md"]:
        shutil.copy2(e.OUT/name,dest/name)
    print("Eight joint reviews complete; no meaningful gain from replacing prospect hitting.",flush=True)


if __name__=="__main__":main()
