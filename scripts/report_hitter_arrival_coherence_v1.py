"""Deliver only the passing, predeclared repair; retain immutable predecessors."""
from __future__ import annotations
from datetime import date
import json
from pathlib import Path
import shutil

import numpy as np
import polars as pl

from fit_hitter_arrival_coherence_v1 import OUT,SIX,OLD,save
from universal_baseball.multiyear_hitter_components import COMPONENTS
from universal_baseball.storage import sha256_file

PACKAGE=Path('model_artifacts/hitter-arrival-coherence-v1-2026-09-23')
TEMPLATE=Path('templates/six-year-hitter-v1-explorer.html')


def replace_once(text,old,new):
    if text.count(old)!=1: raise ValueError(f'Explorer template anchor is not unique: {old[:70]}')
    return text.replace(old,new,1)


def assemble(base,pred,scope):
    """Canonical delivery schema with explicit baselines; no stale selected aliases."""
    keep=['origin_year','player_id','player_name','age','level','stage','organizations','position_label',
        'opening_service_days'] if 'opening_service_days' in base.columns else ['origin_year','player_id','player_name','age','level','stage','organizations','position_label']
    for h in range(1,7):
        keep += [f'value_{2025+h}',f'expected_pa_h{h}',f'activity_h{h}',f'integrated_h{h}']+[f'{c}_runs_h{h}' for c in COMPONENTS]
    f=base.select(keep)
    original_ids=f['player_id'].to_list()
    for h in range(1,7):
        part=pred.filter(pl.col('horizon')==h).select('player_id',pl.col(scope+'_affected').alias('affected'),
            pl.col(scope+'_pa').alias('new_pa'),pl.col(scope+'_p').alias('new_p'),pl.col(scope+'_value').alias('new_value'))
        f=f.join(part,on='player_id',how='left',validate='1:1',maintain_order='left')
        change=pl.col('affected')&pl.lit(h<=3)
        f=f.with_columns(pl.col(f'value_{2025+h}').alias(f'baseline_value_{2025+h}'),pl.col(f'expected_pa_h{h}').alias(f'baseline_pa_h{h}'),
            pl.col(f'integrated_h{h}').alias(f'baseline_integrated_h{h}'),change.alias(f'arrival_repaired_h{h}'))
        # Zero-PA component rates are not recoverable. Fail rather than invent one.
        bad=f.filter(change&(pl.col(f'expected_pa_h{h}')<=0))
        if bad.height: raise ValueError('Cannot rescale zero-PA inherited component totals')
        ratio=pl.when(change).then(pl.col('new_pa')/pl.col(f'expected_pa_h{h}')).otherwise(1.)
        f=f.with_columns(*[(pl.col(f'{c}_runs_h{h}')*ratio).alias(f'{c}_runs_h{h}') for c in COMPONENTS],
            pl.when(change).then(pl.col('new_value')).otherwise(pl.col(f'value_{2025+h}')).alias(f'value_{2025+h}'),
            pl.when(change).then(pl.col('new_pa')).otherwise(pl.col(f'expected_pa_h{h}')).alias(f'expected_pa_h{h}'),
            pl.when(change).then(pl.col('new_p')).otherwise(pl.col(f'activity_h{h}')).alias(f'activity_h{h}'))
        # Preserve untouched integrated values byte-exactly instead of recomputing their sums.
        f=f.with_columns(pl.when(change).then(pl.col(f'value_{2025+h}')+sum(pl.col(f'{c}_runs_h{h}') for c in COMPONENTS)/10)
            .otherwise(pl.col(f'integrated_h{h}')).alias(f'integrated_h{h}')).drop('affected','new_pa','new_p','new_value')
        check=f.filter(~pl.col(f'arrival_repaired_h{h}'))
        ref=base.filter(pl.col('player_id').is_in(check['player_id'].to_list()))
        for col in [f'value_{2025+h}',f'expected_pa_h{h}',f'activity_h{h}',f'integrated_h{h}']+[f'{c}_runs_h{h}' for c in COMPONENTS]:
            np.testing.assert_array_equal(check[col].to_numpy(),ref[col].to_numpy())
    assert f['player_id'].to_list()==original_ids
    return f.with_columns(sum(pl.col(f'value_{2025+h}') for h in range(1,7)).alias('batting_c6'),
        sum(pl.col(f'integrated_h{h}') for h in range(1,7)).alias('integrated_c6'),
        pl.lit(None,dtype=pl.Float64).alias('full_control_value'),
        pl.lit('joint_service_path_and_tail_not_validated').alias('control_value_status'))


def explorer(current,report):
    source=OLD/'league-control/2026-09-08/league-control-snapshot.parquet'
    control=pl.read_parquet(source,columns=['player_id','baseline_service_days','baseline_status','mlb_debut_date']).with_columns(pl.lit(True).alias('control_present'))
    f=current.join(control,on='player_id',how='left',validate='1:1',maintain_order='left')
    accepted=(pl.col('baseline_status')=='available')&pl.col('baseline_service_days').is_not_null()
    no_debut=pl.col('control_present').fill_null(False)&(pl.col('mlb_debut_date').is_null()|(pl.col('mlb_debut_date')>date(2025,12,31)))
    f=f.with_columns(pl.when(accepted).then(pl.col('baseline_service_days')).when(no_debut).then(0).otherwise(None).alias('opening_service_days'),
        pl.when(accepted).then(pl.lit('Recovered opening-2026 service balance; captured retrospectively.'))
        .when(no_debut).then(pl.lit('Official identity/debut evidence supports no MLB debut by the forecast cutoff.'))
        .otherwise(pl.lit('No accepted opening service balance; not assumed to be zero.')).alias('service_status'))
    f=f.drop('baseline_service_days','baseline_status','mlb_debut_date','control_present')
    text=TEMPLATE.read_text(encoding='utf-8')
    text=replace_once(text,'2026–2031 production for MLB players and prospects. Years 1–3 are unchanged; Years 4–6 are a new research extension.',
        '2026–2031 production for MLB players and prospects. Rookie-ball arrival/value is corrected in Years 1–3; other players and Years 4–6 are unchanged.')
    text=replace_once(text,'<h1>Six-year hitter outlook</h1>','<h1>Six-year hitter outlook</h1><p class="notice"><b>Arrival repair · September 23:</b> rookie-ball players now receive much smaller near-term MLB contributions. The broader minor-league change failed testing and was not applied. Years 4–6 still have unresolved arrival calibration; six-season totals remain provisional.</p>')
    text=replace_once(text,'<section id="detail" hidden></section>',
        '<section><h2 id="totalsHeading">Do the totals add up?</h2><p id="totalsNote"></p><div class="scroll"><table><thead><tr><th>Population / measure</th>'+''.join(f'<th>{y}</th>' for y in range(2026,2032))+'</tr></thead><tbody id="totals"></tbody></table></div><p><small>2025 full-MLB reference: 182,926 PA and 570 batting/replacement target wins. Combined value is not normalized to standard WAR. Later forecasts cover today’s player pool, not future entrants. Organization filters are past affiliations, not future rosters; multi-organization players must not be counted twice across teams.</small></p></section><section id="detail" hidden></section>')
    text=replace_once(text,'<p id="count" role="status" aria-live="polite"></p>',
        '<p><a href="#totalsHeading">Check selected-player and league totals ↓</a></p><p id="count" role="status" aria-live="polite"></p>')
    text=replace_once(text,'Years 1–3 retain the existing batting, playing-time and component forecasts exactly.',
        'Years 1–3 now replace only never-debuted rookie-ball players with the tested linked arrival/PA/value recipe. Other players retain their forecasts exactly. Their old component rates are retained but component amounts shrink with the repaired playing time.')
    text=replace_once(text,'The later-year PA hurdle is refitted separately, not inferred from batting value.',
        'For repaired rookies, expected PA and value share a level/age-based annual participation probability. Conditional PA and a PA-weighted hitting-rate model supply the rest. Other players and later horizons still use separately estimated PA and value.')
    text=replace_once(text,"function render(){",'''function totalsTable(a){const rows=[];for(const [label,pool] of [['Selected players',a],['All unique players',players]])for(const [name,key,whole] of [['Expected PA',h=>'expected_pa_h'+h,true],['Batting + replacement',h=>'value_'+(2025+h),false],['Combined scenario',h=>'integrated_h'+h,false]])rows.push('<tr><td>'+label+' · '+name+'</td>'+H.map(h=>{let x=pool.reduce((s,p)=>s+p[key(h)]-(name==='Combined scenario'&&$('framing').value==='zero'?p['framing_runs_h'+h]/10:0),0);return '<td>'+(whole?Math.round(x).toLocaleString():x.toFixed(1))+'</td>'}).join('')+'</tr>');$('totals').innerHTML=rows.join('');$('totalsNote').textContent='Each player is counted once within each row. The repair is targeted; these totals have not been forced to match a league budget.'}
function render(){''')
    text=replace_once(text,"$('count').textContent=a.length", "totalsTable(a);$('count').textContent=a.length")
    text=replace_once(text,"<p class=\"notice\"><b>Full remaining control value: unavailable—not zero.</b>",
        "<p class=\"notice\">${p.arrival_repaired_h1?'<b>Rookie-ball arrival repair applies in 2026–2028.</b> Probability and playing time now constrain batting value. Years 2029–2031 remain the older, provisional estimates.<br>':''}<b>Full remaining control value: unavailable—not zero.</b>")
    text=replace_once(text,'Research extension · 2026-09-22','Arrival correction · 2026-09-23')
    evidence='The targeted rookie-ball repair passed its predeclared Years 1–3 checks, reducing affected players’ three-year batting/replacement RMSE from 0.237 to 0.206. Only three normal cumulative origins are available. Very few rookies actually arrive this quickly; individual breakout identification remains uncertain. The stronger earlier PA ensemble remains slightly better on pooled PA error. The broader all-minor-league recipe failed and was rejected. Long-horizon forecasts remain unchanged and provisional.'
    return text.replace('__PLAYER_DATA__',json.dumps(f.to_dicts(),allow_nan=False).replace('</','<\\/')).replace('__REPORT_DATA__',json.dumps({'evidence':evidence})),sha256_file(source)


def main():
    report=json.loads((OUT/'score-report.json').read_text())
    scope=report['selected_scope']
    if not scope or not report['combined_update_allowed']: raise ValueError('No approved combined delivery')
    if sha256_file(OUT/'predictions.parquet')!=report['historical_prediction_sha256']: raise ValueError('Score/prediction mismatch')
    pred=pl.read_parquet(OUT/'predictions.parquet').filter((pl.col('origin_year')==2025)&~pl.col('cold'))
    base=pl.read_parquet(SIX/'forecast-2026-2031.parquet')
    current=assemble(base,pred,scope)
    current.write_parquet(OUT/'forecast-2026-2031.parquet')
    html,control_hash=explorer(current,report)
    (OUT/'index.html').write_text(html,encoding='utf-8',newline='\n')
    totals=[]
    for h in range(1,7):
        totals.append({'year':2025+h,'changed_players':int(current[f'arrival_repaired_h{h}'].sum()),
            'old_pa':float(base[f'expected_pa_h{h}'].sum()),'new_pa':float(current[f'expected_pa_h{h}'].sum()),
            'old_value':float(base[f'value_{2025+h}'].sum()),'new_value':float(current[f'value_{2025+h}'].sum()),
            'old_combined':float(base[f'integrated_h{h}'].sum()),'new_combined':float(current[f'integrated_h{h}'].sum())})
    save(OUT/'delivery-report.json',{'status':'targeted_development_repair','scope':scope,'updated_horizons':[1,2,3],
        'later_horizons_unchanged':True,'all_unaffected_fields_checked':True,'players':current.height,'league_totals':totals,
        'control_value_complete':False,'private_control_source_sha256':control_hash,'service_annotations_local_only':True,
        'baseline_forecast_sha256':sha256_file(SIX/'forecast-2026-2031.parquet'),'protected_outcomes_used':False})
    PACKAGE.mkdir(exist_ok=True,parents=True)
    for name in ['predictions.parquet','aggregate-checks.parquet','fit-manifest.json','score-report.json','forecast-2026-2031.parquet','delivery-report.json']:
        shutil.copyfile(OUT/name,PACKAGE/name)
    save(PACKAGE/'manifest.json',{'version':'hitter-arrival-coherence-v1','cutoff':'2025-12-31','status':'targeted_development_repair',
        'files':{p.name:sha256_file(p) for p in PACKAGE.iterdir() if p.name!='manifest.json'},
        'build_code':{str(p):sha256_file(p) for p in [Path(__file__),Path('scripts/score_hitter_arrival_coherence_v1.py'),TEMPLATE]}})
    print(json.dumps(totals,indent=2))


if __name__=='__main__': main()
