"""Expose a single reviewed historical candidate; no new fitting or deployment."""
import json
from pathlib import Path
import polars as pl
import numpy as np
import audit_hitter_public_units_v51 as audit
from universal_baseball.mlb_event_logit import EVENTS,VALUES
from universal_baseball.storage import sha256_file

ROOT=audit.ROOT;OUT=ROOT/'reports/generated/practical-hitter-candidate-v52'


def main():
    read=audit.previous.prior.old.r.read
    assert read(audit.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert read(audit.previous.OUT/'report.json')['player_walkthrough_status']=='complete'
    old=ROOT/'reports/generated/practical-hitter-readiness-v49/explorer';rows=read(old/'data.json')
    source=pl.read_parquet(audit.previous.OUT/'features.parquet').select('row_id',*[stem+'_'+ev for stem in ['origin_env','target_env','count'] for ev in EVENTS])
    features={o['row_id']:o for o in source.iter_rows(named=True)}
    fits={o['row_id']:o for o in pl.read_parquet(audit.previous.OUT/'scored-predictions.parquet').iter_rows(named=True)}
    public={o['row_id']:o for o in pl.read_parquet(audit.OUT/'predictions.parquet').iter_rows(named=True)}
    for r in rows:
        x=features[r['row_id']];o=fits[r['row_id']];env=np.array([x['origin_env_'+ev] for ev in EVENTS])@VALUES
        r['origin_index']=float(env);r['old_actual_value']=r['next_value']
        for a in ['fixed_reliability','learned_reliability']:
            r[a]=dict(rate=o[a+'_rate'],pa=o[a+'_pa'],value=o[a+'_value'],p=o['binary_scout_p'],conditional_pa=o['binary_scout_conditional_pa'])
        for a in ['safe_ridge','games','fallback','binary_count','binary_scout','fixed_reliability','learned_reliability']:
            r[a]['index']=r[a]['rate']/audit.UNIT+float(env)
        if r['next_pa']>0:
            counts=np.array([x['count_'+ev] for ev in EVENTS]);assert counts.sum()==r['next_pa']
            r['actual_index']=float(counts@VALUES/r['next_pa']);r['next_batting_rate']=(r['actual_index']-float(env))*audit.UNIT
            r['next_value']=r['next_pa']*(r['next_batting_rate']/600+r['origin_replacement_rate'])
        else:r['actual_index']=None;r['next_batting_rate']=None;r['next_value']=0.
        q=public.get(r['row_id']);r['public']=None if q is None or q['steamer_index'] is None or q['zips_index'] is None else dict(
            steamer_index=q['steamer_index'],zips_index=q['zips_index'],steamer_pa=q['steamer_pa'])
    assert len(rows)==30506 and max(r['target_year'] for r in rows)==2025
    scores=read(audit.OUT/'scores.json');b=next(s for s in scores if s['scope']=='all_current_common_public')
    w=read(audit.OUT/'workload-information-diagnostic.json')['groups'][0]['scores']
    bench='<table><thead><tr><th>2,627 identical current-MLB forecasts</th><th>Hitting-rate RMSE*</th><th>PA RMSE</th><th>PA MAE</th></tr></thead><tbody>'
    for a,label in [('binary','Practical candidate'),('steamer','Steamer archive'),('zips','ZiPS archive')]:
        bench+=f"<tr><td>{label}</td><td>{b['rates'][a]['rmse']:.3f}</td><td>{w[a]['pa_rmse']:.2f}</td><td>{w[a]['pa_mae']:.2f}</td></tr>" if a in w else f"<tr><td>{label}</td><td>{b['rates'][a]['rmse']:.3f}</td><td>Not scored</td><td>Not scored</td></tr>"
    bench+='</tbody></table><p>*Common fixed-event index, expressed as origin-centered batting wins/600. 2,088 actual participants enter rate scoring; all 2,627 remain in PA scoring. This is not official wOBA or park-neutral talent. Public exact dates are unknown. Target 2023 loses to both public systems. Near-equal pooled scores do not establish superiority.</p><p>Prospects remain in the 30,506-player-season explorer but not this current-MLB public subset. Historical team totals are a fixed cohort, not future team rosters or a complete league budget.</p>'
    html=(old/'index.html').read_text(encoding='utf8')
    html=html.replace('Hitter readiness and actual MLB results','Practical hitter candidate and honest comparisons').replace('Hitting forecasts, MLB readiness and actual results','Practical hitter candidate')
    start=html.index('<div class="notice">');end=html.index('</div>',start)+6
    html=html[:start]+'<div class="notice"><strong>Selected historical candidate:</strong> the existing count-and-draft batting estimate plus separate MLB-appearance chance and playing time if active. This is a reviewed development assembly, not a change to the working or frozen 2026 forecast. Ability is reasonably close to public systems on the common event measure; opportunity, fast entrants and uncertainty remain weaker.</div>'+html[end:]
    html=html.replace("binary_scout:'MLB chance × PA if active — scouting research'","binary_scout:'Practical candidate: existing hitting + binary readiness',fixed_reliability:'Fixed skill shrinkage — not adopted',learned_reliability:'Learned skill shrinkage — not adopted'")
    html=html.replace("'');\nfor(let id", "'');$('model').value='binary_scout';\nfor(let id")
    assert "$('model').value='binary_scout'" in html
    html=html.replace('<th class="n">Batting / 600*</th>','<th class="n">Batting / 600*</th><th class="n">Hitting index*</th>')
    html=html.replace('n(r[m].rate,2),n(r.next_batting_rate,2)','n(r[m].rate,2),n(r[m].index,3),n(r.next_batting_rate,2)')
    html=html.replace('<th class="n">Actual batting / 600</th>','<th class="n">Actual batting / 600*</th>')
    html=html.replace('<p class="muted">*MLB chance','<p class="muted">*Hitting index is a fixed-weight event numerator divided by total PA, not official wOBA or a current MLB-equivalent prospect grade. Forecast and actual batting wins/600 share the origin league environment; actual values differ from older target-centered explorers for this reason. MLB chance')
    start=html.index('<details><summary>How close');end=html.index('</details>',start)+10
    html=html[:start]+'<details open><summary>How close is this to public projections?</summary><div class="scroll">'+bench+'</div><p>MAE on the original 1,789 matches is still 19.1% above Steamer; broader sample 16.0%. A one-PA public-availability diagnostic explains part of this gap, but no players are dropped or silently treated as predictable injuries.</p></details>'+html[end:]
    start=html.index("$('benchmarks').innerHTML=");end=html.index("update();}).catch",start)
    html=html[:start]+html[end:]
    html=html.replace('</style>','body{padding:18px}.notice,.filters{padding:12px;margin:12px 0}.card{padding:12px}.filters{gap:10px}th{white-space:normal;line-height:1.25}th,td{padding:9px;font-size:13px}.n{font-variant-numeric:tabular-nums}</style>')
    start=html.index('<div class="notice">');end=html.index('</div>',start)+6
    html=html[:start]+'<div class="notice"><strong>Selected candidate:</strong> existing hitting estimate + MLB chance × PA if active. Hitting is close to public systems on our event measure; playing time and fast prospects need work. Historical research only: the working and frozen 2026 forecasts are unchanged.</div>'+html[end:]
    start=html.index('<p class="warn">These values');end=html.index('</p>',start)+4
    html=html[:start]+'<p class="warn">Offense only—not full WAR or trade value. Low next-year MLB value does not mean low career value.</p>'+html[end:]
    start=html.index('<p class="muted">*Hitting index');end=html.index('</p>',start)+4
    html=html[:start]+'<p class="muted">*Hitting index uses fixed event weights, not official wOBA. Actual and forecast rates share the same origin environment. Prospect rates are conditional forecasts, not present-day MLB grades.</p>'+html[end:]
    marker="const review=reviews[r.player_id+'|'+r.origin_year];"
    detail="""html+='<p><strong>Common event comparison:</strong> implied hitting index '+n(a.index,4)+' = origin league '+n(r.origin_index,4)+' + relative batting rate converted to events.'+(r.public?' Steamer '+n(r.public.steamer_index,4)+', ZiPS '+n(r.public.zips_index,4)+'. Steamer expected PA '+n(r.public.steamer_pa,1)+'.':' No common historical public forecast available.')+'</p>';
"""
    assert marker in html;html=html.replace(marker,detail+marker)
    reviews=read(old/'reviews.json')
    for path in [ROOT/'config/practical_hitter_reliability_v50_case_notes.json',ROOT/'config/practical_hitter_public_units_v51_case_notes.json']:
        for k,v in read(path).items():reviews[k]=reviews.get(k,'')+' '+v
    dest=OUT/'explorer';dest.mkdir(parents=True,exist_ok=True)
    for name,value in [('data.json',rows),('history.json',read(old/'history.json')),('scores.json',{}),('reviews.json',reviews)]:
        (dest/name).write_text(json.dumps(value,allow_nan=False,separators=(',',':')),encoding='utf8')
    (dest/'index.html').write_text(html,encoding='utf8')
    manifest=dict(candidate='existing V34 cohort batting rate + V49 binary scouting readiness',rows=len(rows),people=len({r['player_id'] for r in rows}),
        no_new_fits=True,historical_only=True,maximum_target_year=2025,default_model='binary_scout',team_filter=True,actual_same_origin_units=True,
        old_working_and_frozen_unchanged=True,protected_outcomes_used=False,practical_goal_complete=False,required_reviews_complete=True,
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in dest.iterdir() if p.is_file()},
        source_hashes={str(p):sha256_file(p) for p in [old/'index.html',old/'data.json',audit.OUT/'report.json',audit.previous.OUT/'report.json',Path(__file__)]})
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(dest,flush=True)


if __name__=='__main__':main()
