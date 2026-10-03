"""Separate research explorer; never overwrite frozen or existing candidates."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import evaluate_hitter_numeric_repair_v53 as base

ROOT=base.ROOT
OUT=ROOT/"reports/generated/practical-hitter-repaired-research-v58"


def main():
    old=ROOT/"reports/generated/practical-hitter-candidate-v52/explorer"
    ready=ROOT/"reports/generated/practical-hitter-prospect-pooling-v54"
    compact=ROOT/"reports/generated/practical-hitter-compact-readiness-v57"
    for folder in [base.OUT,ready,compact]:
        assert base.read(folder/"report.json")["player_walkthrough_status"]=="complete"
    rows=base.read(old/"data.json")
    sources=[base.OUT/"scored-predictions.parquet",ready/"predictions.parquet",compact/"predictions.parquet"]
    maps=[{r["row_id"]:r for r in pl.read_parquet(p).iter_rows(named=True)} for p in sources]
    assert len(rows)==len(maps[0])==30506 and set(r["row_id"] for r in rows)==set(maps[0])
    comparisons=[
        ("binary_corrected",0,"repaired","repaired"),
        ("binary_sharedpa",1,"shared","repaired"),
        ("binary_compact",2,"shared","repaired"),
    ]
    for r in rows:
        rid=r["row_id"];o=maps[0][rid]
        for key,idx,pa,rate in comparisons:
            p=maps[idx][rid];a=dict(p=p[pa+"_p"],conditional_pa=p[pa+"_conditional_pa"],
                pa=p[pa+"_pa"],rate=p[rate+"_rate"])
            a["value"]=a["pa"]*(a["rate"]/600+o["origin_replacement_rate"])
            assert np.isclose(a["pa"],a["p"]*a["conditional_pa"],atol=1e-10)
            r[key]=a
        assert r["target_year"]==o["target_year"]<=2025 and r["next_pa"]==o["next_pa"]
        assert np.isclose(r["next_value"],o["next_value"],atol=1e-10)
    # Use the exact established explorer conversion constant, not an assumed unit.
    import audit_hitter_public_units_v51 as public
    for r in rows:
        for key,_,_,_ in comparisons:
            r[key]["index"]=r[key]["rate"]/public.UNIT+r["origin_index"]
    html=(old/"index.html").read_text(encoding="utf8")
    marker="const names={";start=html.index(marker);end=html.index("};",start)+2
    html=html[:start]+(
        "const names={binary_corrected:'Corrected baseline — retained research anchor',"
        "binary_sharedpa:'Shared prospect PA + baseline hitting — uncertain alternative',"
        "binary_compact:'Compact prospect PA + baseline hitting — not adopted',"
        "binary_scout:'Earlier candidate — unchanged reference'};"
    )+html[end:]
    assert "$('model').value='binary_scout'" in html
    html=html.replace("$('model').value='binary_scout'","$('model').value='binary_corrected'")
    html=html.replace("Practical hitter candidate and honest comparisons","Corrected hitter research and reviewed alternatives")
    html=html.replace("Practical hitter candidate</h1>","Corrected hitter research</h1>")
    start=html.index('<div class="notice">');end=html.index("</div>",start)+6
    html=html[:start]+(
        '<div class="notice"><strong>Retained research baseline:</strong> repaired '
        'numeric history + existing hitting estimate + binary MLB readiness. '
        'Alternatives were reviewed but did not earn a replacement. '
        'Historical next-year forecasts only, through 2025. '
        'No 2026 forecast or old explorer changed.</div>'
    )+html[end:]
    # Replace old benchmark figures with the actually corrected matched results.
    html=html.replace("1.745","1.744").replace("138.28","138.49").replace("106.79","106.87")
    html=html.replace("broader sample 16.0%","broader sample 16.1%")
    html=html.replace("original 1,789 matches is still 19.1%","original 1,789 matches is still about 19%")
    html=html.replace("The two binary models condition workload on participation;",
        "The readiness models condition workload on participation;")
    marker="const review=reviews[r.player_id+'|'+r.origin_year];"
    assert marker in html
    html=html.replace(marker,
        "html+='<p class=\"warn\">Alternative readiness means are development comparisons, "
        "not approved upgrades. The corrected baseline retains large fast-entry misses; "
        "near-exact offense can hide offsetting hitting and PA errors. "
        "The support count above is the original candidate\\'s coarse profile, "
        "not certification of either prospect-specific head.</p>';\n"+marker)
    reviews={k:"Earlier candidate notes, before numeric repair (numbers may differ "
        "from the selected forecast): "+v for k,v in base.read(old/"reviews.json").items()}
    for filename,label in [
        ("practical_hitter_numeric_repair_v53_case_notes.json","Numeric source repair"),
        ("practical_hitter_prospect_pooling_v54_case_notes.json","Shared prospect model"),
        ("practical_hitter_prospect_units_v55_case_notes.json","Fixed-unit prospect model"),
        ("practical_hitter_head_assembly_v56_case_notes.json","Separate-head assembly"),
        ("practical_hitter_compact_readiness_v57_case_notes.json","Compact readiness"),
    ]:
        p=ROOT/"config"/filename
        for k,v in base.read(p).items():reviews[k]=reviews.get(k,"")+"\n"+label+": "+v
    dest=OUT/"explorer";dest.mkdir(parents=True,exist_ok=True)
    for name,value in [
        ("data.json",rows),("history.json",base.read(old/"history.json")),
        ("scores.json",{}),("reviews.json",reviews),
    ]:
        (dest/name).write_text(json.dumps(value,allow_nan=False,separators=(",",":")),encoding="utf8")
    (dest/"index.html").write_text(html,encoding="utf8")
    manifest=dict(rows=len(rows),people=len({r["player_id"] for r in rows}),
        team_filter=True,historical_only=True,maximum_target_year=2025,
        default_model="binary_corrected",alternative_models_not_promoted=True,
        products_and_actual_common_units_verified=True,required_reviews_complete=True,
        old_explorers_and_frozen_2026_unchanged=True,protected_outcomes_used=False,
        practical_goal_complete=False,browser_visual_verification="pending",
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in dest.iterdir() if p.is_file()},
        source_hashes={str(p):sha256_file(p) for p in [*sources,old/"index.html",old/"data.json",Path(__file__)]})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"candidate-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    print(dest,flush=True)


if __name__=="__main__":main()
