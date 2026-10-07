"""Close the player review without promoting a numerically passing flawed allocator."""

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defense-opportunity-v8"
PUBLIC = ROOT / "reports/model-evidence/defense-opportunity-v8"

JUDGMENTS = {
    (543807, 2022): ("missing_available_assignment_and_PA_shortfall", "Springer: December 2022 RF assignment omitted; broad role change helps slightly but remains far short and adds unrelated C innings."),
    (605141, 2023): ("missing_available_assignment_and_diffuse_roles", "Betts: December 2B plan is origin-known; March SS revision belongs to a later update. Fair PA does not excuse diffuse/unrelated roles."),
    (656555, 2022): ("post_cutoff_injury_and_unrelated_role_allocation", "Hoskins: March ACL injury explains zero opportunity after cutoff; predicted catcher innings remain a separate allocation defect."),
    (656941, 2023): ("later_assignment_update_and_diffuse_roles", "Schwarber: February 2024 primary-DH report is later than the January information date. History-only allocations miss DH and add unrelated positions."),
    (662139, 2022): ("missing_available_assignment_and_older_role_overhang", "Varsho: dated December LF plan omitted; older C/RF roles persist. OF peers receive C innings without personal C role evidence."),
    (664761, 2022): ("reasonable_main_role_but_missing_split_and_diffusion", "Bohm: main 3B role identified, increased 1B exposure missed; 2B/SS/C spread recurs among his established 3B peers."),
    (665487, 2022): ("known_cached_upstream_return_defect", "Tatis: 40 expected PA fails to distinguish a known finite suspension return. Inactivity-matched minor peers are not equivalent established-MLB returns."),
    (665489, 2022): ("age_group_role_borrowing_inappropriate", "Guerrero: reasonable PA and concentrated 1B history become broad LF/RF/C predictions. Ratio anchor better preserves his established role."),
    (671655, 2022): ("nonarrival_opportunity_not_quality", "Valera: OF record supplies expected opportunities but no next-season arrival; peers also do not arrive. Do not label their skill zero."),
    (680574, 2023): ("post_cutoff_injury_and_peer_opportunity_misses", "McLain: March shoulder injury is later information; peers have independently large role/PA shortfalls, not evidence of bad defensive quality."),
    (682626, 2022): ("tiny_MLB_ratio_and_minor_DH_role_overhang", "Alvarez: fuller minor C record beats scaling tiny MLB history, but minor DH share and broad-role spreading still underallocate MLB catching."),
    (682829, 2022): ("upstream_PA_shortfall_plus_wrong_position_split", "De La Cruz: most total-out shortfall comes from fixed PA; 2B spread dilutes the actual known SS/3B repertoire. Winn peer arrives while other peers do not."),
    (805811, 2024): ("older_repertoire_and_unrelated_role_allocation", "Eldridge: current 2024 fielding is all 1B, older RF persists, and C comes solely from group borrowing. Low next-season exposure does not settle eventual value."),
}


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def main():
    protections()
    assert not (OUT / "final-review.json").exists()
    verification = read(OUT / "independent-verification.json")
    assert verification["integrity_pass"] and verification["all_forecasts_replayed"] == 12432
    for path, digest in verification["hashes"].items():
        assert sha256_file(Path(path)) == digest
    report, walk = read(OUT / "fit-report.json"), read(OUT / "player-walkthrough.json")
    assert walk["status"] == "mechanical_trace_complete_baseball_judgment_pending"
    observed = {(c["player_id"],c["origin"]) for c in walk["cases"]}
    assert observed == set(JUDGMENTS), (observed - set(JUDGMENTS), set(JUDGMENTS) - observed)
    assert all(c["peers_selected"] == 3 and len(c["records"]) == 4 for c in walk["cases"])
    cohorts = verification["exposure_cohorts"]
    totals = [s for s in report["overall"] if s["origin"] in (2022,2023) and s["arm"] == "context"]
    tolerant_total_pass = all(abs(s["predicted_total_outs"]/s["actual_total_outs"]-1) <= .2 for s in totals)
    group_ratios = []
    for s in report["groups"]:
        if s["origin"] not in (2022,2023) or s["arm"] != "context" or s["rows"] < 100:
            continue
        reference = next(b for b in report["groups"] if (b["origin"],b["field"],b["value"],b["arm"]) == (s["origin"],s["field"],s["value"],"pooled"))
        group_ratios.append(dict(origin=s["origin"],field=s["field"],value=s["value"],rows=s["rows"],rmse_ratio=s["cell_rmse"]/reference["cell_rmse"]))
    primary_pass = report["paired_interval"]["equal_origin_rmse_change"] < 0
    group_pass = all(g["rmse_ratio"] <= 1.1 for g in group_ratios)
    stronger_anchor_loss = all(next(s["cell_rmse"] for s in report["overall"] if s["origin"] == y and s["arm"] == "ratio") <
                               next(s["cell_rmse"] for s in report["overall"] if s["origin"] == y and s["arm"] == "context") for y in (2022,2023,2024))
    # Trace where an unrelated target position enters the largest deterioration's
    # empirical means. This is a saved-fit explanation, not a new candidate.
    features = pl.read_parquet(OUT/"features.parquet")
    case = next(c for c in walk["cases"] if c["player_id"] == 665489)
    focal = case["records"][0]
    donations = []
    for cell in focal["chosen_support_and_rate"]:
        scope = cell["scope"]
        tr = features.filter((pl.col("target_year") <= focal["origin"]) & (pl.col("outer_fold") != focal["fold"]) & (pl.col("next_pa") > 0))
        if scope[0] in ("role_stage", "role_stage_age"):
            tr = tr.filter(pl.col("stage") == scope[2])
        if scope[0] == "role_stage_age":
            tr = tr.filter(pl.col("age_band") == scope[3])
        if scope[0] == "all":
            weights = np.ones(tr.height)
        else:
            weights = np.array([r[int(scope[1])-2] for r in tr["bridge_role_shares"].to_list()])
        for target_pos in (2,7):
            donor = tr.select("player_id","player_name","origin_year","target_year",f"actual_{target_pos}").with_columns(
                pl.Series("weighted_target_outs",weights*tr[f"actual_{target_pos}"].to_numpy()))
            top = donor.filter(pl.col("weighted_target_outs") > 0).sort("weighted_target_outs",descending=True).head(5).to_dicts()
            total = float((weights*tr[f"actual_{target_pos}"].to_numpy()).sum())
            assert np.isclose(total,cell["numerator"][target_pos-2],atol=1e-8,rtol=0)
            donations.append(dict(scope=scope,focal_role_share=cell["share"],target_position=target_pos,
                borrowed_weighted_target_outs=total,top_training_donors=top,
                focal_predicted_outs_from_group=cell["share"]*cell["rates"][target_pos-2]*focal["fixed_expected_PA"]))
    result = dict(date="2026-10-07",integrity_pass=True,player_walkthrough_status="complete",
        focal_players=len(walk["cases"]),origin_selected_peer_walks=39,
        statistical_tolerance_checks=dict(primary_improves_pooled=primary_pass,large_groups_within_tolerance=group_pass,
            dev_total_within_tolerance=tolerant_total_pass,group_checks=group_ratios),
        numerical_conditions_pass=primary_pass and group_pass and tolerant_total_pass,
        beats_stronger_ratio_anchor=False,ratio_beats_context_all_origins=stronger_anchor_loss,
        baseball_reasonability_pass=False,
        disposition="repair_allocation_before_value_integration_no_role_average_promotion",
        retained="Audited sources, separate skill baselines, native conversions and stronger prior-usage/PA ratio reference.",
        next="One bounded repertoire/exposure repair with tiny-MLB fallback and explicit dated role-input limits; then matched delivered-runs/value integration.",
        allocator_defect="Nonexclusive origin-role weights borrow entire future position vectors, then mix those again; unrelated role exposure is not individualized evidence.",
        design_defect_not_rejection_of_age_or_position_information=True,cohort_diagnostics=cohorts,
        explanation_donor_trace=donations,
        case_judgments=[dict(player_id=p,origin=y,classification=c,judgment=j,three_peer_outcomes_reviewed=True)
                        for (p,y),(c,j) in JUDGMENTS.items()],
        source_dates=[dict(date="2022-12-24",known_by_year_end=True,subject="Toronto LF/CF/RF plans",url="https://www.mlb.com/bluejays/news/daulton-varsho-traded-to-blue-jays"),
                      dict(date="2023-12-04",known_by_year_end=True,subject="Betts everyday 2B",url="https://www.mlb.com/dodgers/news/mookie-betts-second-base-dodgers-2024"),
                      dict(date="2024-03-08",known_by_year_end=False,subject="Betts SS revision",url="https://www.mlb.com/news/mookie-betts-dodgers-shortstop"),
                      dict(date="2024-02-21",known_by_year_end=False,subject="Schwarber primary DH",url="https://www.mlb.com/news/kyle-schwarber-ready-for-2024-after-injury"),
                      dict(date="2023-03-23",known_by_year_end=False,subject="Hoskins ACL injury",url="https://www.mlb.com/news/rhys-hoskins-suffers-left-knee-injury"),
                      dict(date="2024-03-18",known_by_year_end=False,subject="McLain shoulder injury",url="https://www.mlb.com/news/matt-mclain-shoulder-surgery"),
                      dict(date="2022-10-25",known_by_year_end=True,subject="Tatis finite suspension return",url="https://www.mlb.com/news/fernando-tatis-jr-return-date-from-suspension-in-2023")],
        protected_outcomes_used=False,forecast_or_explorer_changed=False,upstream_PA_repaired_here=False,
        eventual_minor_talent_validated=False,value_integration_complete=False,deployment_approved=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/"independent-verification.json",OUT/"player-walkthrough.json",OUT/"fit-report.json",
            ROOT/"docs/defense-opportunity-v8-player-review.md",ROOT/"docs/defense-opportunity-v8-result.md"]})
    save(OUT/"final-review.json",result)
    save(PUBLIC/"final-review.json",result)
    protections()
    print(json.dumps({k:result[k] for k in ["player_walkthrough_status","numerical_conditions_pass","baseball_reasonability_pass","disposition"]}))


if __name__ == "__main__":
    main()
