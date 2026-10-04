"""Independent arithmetic checks and full player interpretation of the audit."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.hitter_compatible_value import UNIT
import audit_hitter_season_value_ledger as a

NOTES = {
 ('Aaron Judge',2018): 'The 2017 breakout (678 MLB PA/52 HR) and 2018 (498/27) reach the MLB branch through pooled quality and separate histories, with 646 recent measured contacts. Quality and workload terms are positive; forecast hitting 3.415 exceeds observed 3.107 and forecast PA 516 exceeds 447. The higher-scoring 2019 league adds .433 to the old common-reference outcome, concealing part of that overforecast. The signed season-relative miss is -.836, not just -.402. Bryant reaches 634 PA while Polanco and Nimmo receive 167/254: differing health/use remains possible without a bad origin forecast.',
 ('Aaron Judge',2024): 'The origin records 696/458/704 MLB PA and 62/37/58 HR across three seasons. Pooled MLB quality contributes +2.408, recent quality +1.211 and age -.518 to the exact linear sum, with 1025 measured contacts. The main 4.935 hitting estimate improves on 4.534 but remains below actual 6.287. 531 expected versus 679 PA contributes +1.682 to the shortfall; hitting contributes another +1.530. League conditions add only .158 to the older label. This superstar miss is substantive, not explained by recentering. Ozuna, Harper, Schwarber and Profar have 592/580/724/371 actual PA, retaining ordinary downside alongside extreme upside.',
 ('Nick Kurtz',2024): 'Only 35 A PA/four HR and fifteen AA PA are present. Fourth-overall draft pedigree and dated rank are known, but the translated branch has no matching active hitting people and the workload profile has zero. Translated other-outcomes +.807 and age +.607 are partly offset by translated strikeouts -.334 and era -.230. Arrival .06056 times 168.16 active PA yields only 10.18 PA against 489. Main hitting 1.024 exceeds old -.063 but is far below 5.150. The value miss has +2.313 opportunity and +3.362 hitting terms; .113 league reference cannot explain it. Origin-selected peers mostly remain minors; this coarse nearest-profile rule does not make them equivalent fourth-overall college prospects. No post-result boost is adopted.',
 ('Bo Bichette',2024): 'The input history has MLB 697 PA/24 HR, 601/20, then 336/four, with six and fourteen AAA PA in the last two seasons. MLB Statcast, not the minor overlay, is the selected main branch. It receives 1192 MLB measurements; past workload +.573, current workload +.324 and pooled quality +.237 partly offset era -.300. Main hitting -.019 is barely above old -.090; actual 2.424 shows a real rebound miss. Opportunity contributes +.503 and hitting +2.556 to the 3.059 season-relative shortfall. The prior precision repair keeps eighteen minor contacts from dominating, but does not repair this MLB estimate. The broad peer rule selects Rortvedt/Benson/Brujan/Brennan with much less established MLB success; those are exposure/profile diagnostics, not convincing healthy-Bichette talent analogues.',
 ('Junior Caminero',2024): 'The origin has 236 AAA PA/13 HR and 177 MLB PA/six HR after 2023 AA 351/20 and High-A 159/eleven. The main head uses 152 MLB measurements, age +.748 and current workload +.193, partly offset by era -.269. Its .588 hitting improves on .280 but misses observed 2.175. Arrival .8989 times 466.60 gives 419 PA against 653. The season-relative shortfall is +.958 opportunity and +1.728 hitting, versus just .151 for league reference. Holliday, Dominguez, Wood and Angel Martinez receive 649/429/689/484 PA, consistent with the risk of underallocating advancing players. The negative unadopted minor adjustment remains a separate contrary finding; this audit does not validate it.',
 ('Steven Kwan',2021): 'The cancelled 2020 minor season provides no sample. Actual source history is 2019 High-A 542 PA/three HR/51 K and 2021 AA 221/seven/23 plus AAA 120/five/eight. Translated strikeouts contribute +.331 and age +.428, but translated other-outcomes -.534 and older unavailable rank score -.160 offset that advantage. The translated .253 below-average point is worse than the prior +.106 against actual +1.618. .6957 arrival times 166.69 active PA gives 116 versus 638. The miss remains +1.416 opportunity and +1.990 hitting after removing the -.367 league shift. Carpio, Rodriguez and McKenna never arrive and Jung gets 102 PA, but their broad age/stage/exposure similarity is not equivalent low-strikeout AAA evidence. This is not a solved profile.',
 ('Brandon Belt',2023): 'The prior MLB samples are 381 PA/29 HR, 298/eight and 404/nineteen. The exact main rate sum uses positive pooled quality +.653 and current workload +.428 against age -.854. .6463 arrival times 377.77 active PA produces 244 PA and .979 contribution; actual MLB PA is zero. Both actual value definitions equal zero, with no observed hitting rate and no league term. The whole signed miss is opportunity -.979. Solano/Martinez/Pham/Blackmon receive 309/495/478/499 PA. This unexpected employment failure is not evidence to tune an ordinary older productive hitter to zero.',
 ('Eric Thames',2016): 'There is no own recent source history in the panel. The main branch is exact current fallback, with age/draft/position terms but no recent Korean production or MLB launch sample. .2067 arrival times 100.49 active PA produces 20.78 PA and .039 contribution; actual is 551 PA and 2.423 hitting per 600. The season-relative shortfall is +1.007 opportunity and +2.878 hitting, versus .209 for league reference. Blanks/Danks/Exposito/Tosoni all have zero actual PA, but absent foreign production means they are not appropriate evidence against this known return. Source incompleteness remains, not an inherently unforecastable breakout.',
 ('Juneiker Caceres',2024): 'The raw source has 167 PA, zero HR, eighteen K and seventeen unintentional walks at league 130; its broad stored label is ROOKIE_COMPLEX. Age contributes +1.179 but translated other-outcomes -.468 and era -.151 offset it. There is no draft/ranking or tracking evidence, no matching hitting/workload people, and no observed next-year MLB rate. .001074 arrival times 62.09 gives .0667 expected PA and .000193 value. All four origin-selected young peers have zero MLB PA. This explains immediate non-arrival expectations, not eventual DSL talent or career value; missing pedigree is not proof of poor ability.',
 ('Aaron Judge',2023): 'The largest gain still has a major false low. Source MLB samples are 633 PA/39 HR, 696/62 and 458/37. Pooled quality +1.879, older quality +.558 and recent quality +.543 enter the exact MLB head, with 1031 measured contacts. Main hitting 3.899 improves on 3.360 but actual is 7.558; .9851 arrival times 544.11 gives 536 PA against 704. Value 5.142 versus 11.047 has +1.612 opportunity and +4.293 hitting residual. The old league reference subtracts .554 and understates the miss. Flores has 242 PA and negative value while Harper reaches 631; comparison outcomes retain both successes and failures. The gain supports useful measurements, not a solved superstar forecast.',
 ('Ronald Acuña Jr.',2023): 'The largest harm and false high has known 2021/22/23 MLB PA 360/533/735, HR 24/15/41 and K 85/126/84, plus a brief AAA rehab. Pooled quality +1.463, latest quality +.854 and work +.778 enter; recent EV95 adds +.274. .9921 arrival times 592.95 gives 588 PA. Main hitting rises 3.414 to 3.826, reasonable after the demonstrated season, but actual is only 222 PA/.723 rate. The shortfall reverses: opportunity -3.470 and hitting -1.148, with -.175 league term. Soto/Steer reach 713/656 PA, Riley/Tucker 469/339. Later absence is part of actual risk, not justification to use that future absence as an origin input or discard useful contact quality.',
 ('Aaron Judge',2016): 'The largest false low has 410 AAA PA/nineteen HR/98 K and just 95 MLB PA/four HR/42 K after earlier AA/AAA exposure. There are only 43 measured MLB contacts. Age/draft/position add value but negative pooled MLB quality subtracts .117; main hitting .264 beats old -.040 yet falls far below actual 5.330. .9250 arrival times 335.05 gives 310 PA against 678. Season-relative value 8.115 versus 1.093 has +1.298 opportunity and +5.724 hitting residual; league reference adds just .257. Moya has zero PA, Austin 46, Cowart 117 and Difo 365. These outcomes show breakout risk but do not make the model capable of identifying extreme upper tails.',
 ('Brian Anderson',2022): 'The ordinary near-exact value example has MLB 229 PA/eleven HR in short 2020, 264/seven in 2021 and 383/eight in 2022; rehab stays separate. Actual skill counts are not annualized, but historical workload 2020 is separately schedule normalized. Current/older workload contribute +.407/+.390, launch-angle variability -.242 and age -.208. Main hitting -.260 versus actual -.874 is too high. .6861 arrival times 327.27 gives 225 PA versus 361. Contribution .6058 nearly equals .6045 actual only because +.368 opportunity and -.369 hitting cancel. The old league reference adds .327. Trevino/Story have 168 PA, Tim Anderson 524 and Franco zero. This near-perfect total is not proof of correct talent or workload.'
}


def main():
    assert not (a.OUT/'final-review.json').exists(), 'Preserve completed review'
    audit = a.b.prep.read(a.OUT/'audit.json')
    a.b.prep.old.verify_hashes(audit['source_hashes'])
    for p,h in audit['output_hashes'].items(): assert sha256_file(a.OUT/p)==h
    q = pl.read_parquet(a.OUT/'ledger.parquet')
    saved = pl.read_parquet(a.SOURCE).sort('row_id')
    assert q['row_id'].equals(saved['row_id'])
    for col in ['preseason_pa','next_pa','next_value',*[x+s for x in a.ARMS for s in ['_rate','_value']]]:
        assert q[col].equals(saved[col]), col
    assert np.allclose(q['next_value']-q['audit_relative_value'], q['audit_environment'], atol=1e-10, rtol=0)
    assert np.allclose(q['audit_relative_value']-q['combined_value'], q['audit_opportunity']+q['audit_hitting'], atol=1e-10, rtol=0)
    # Recalculate endpoints from group means, independently of the scoring helper.
    scores = a.b.prep.read(a.OUT/'scores.json'); checked=0
    for s in scores['scopes']:
        if s['scope'].startswith('origin_'): g=saved.filter(pl.col('origin_year')==int(s['scope'].split('_')[1]))
        elif s['scope'].startswith('stage_'): g=saved.filter(pl.col('stage')==s['scope'][6:])
        elif s['scope']=='all': g=saved
        elif s['scope']=='never_debut': g=saved.filter(pl.col('prior_debut')==0)
        elif s['scope']=='upper_never_debut': g=saved.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))
        elif s['scope']=='lower_never_debut': g=saved.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))
        elif s['scope']=='tracked': g=saved.filter(pl.col('sc_tracked'))
        elif s['scope']=='untracked': g=saved.filter(~pl.col('sc_tracked'))
        elif s['scope']=='minor_eligible': g=saved.filter(pl.col('msc_eligible'))
        elif s['scope']=='public': g=saved.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
        else: raise ValueError(s['scope'])
        rows=q.filter(pl.col('row_id').is_in(g['row_id'].to_list())).sort('row_id')
        assert len(rows)==s['rows'] and rows['player_id'].n_unique()==s['people']
        for response,arms in s['losses'].items():
            actual='next_value' if response=='common_origin' else 'audit_relative_value'
            for arm,record in arms.items():
                vals=[]
                for (year,), group in rows.group_by('origin_year'):
                    pred=g.filter(pl.col('origin_year')==year).sort('row_id')[arm+'_value'].to_numpy()
                    err=pred-group.sort('row_id')[actual].to_numpy()
                    vals.append([np.mean(err**2),np.mean(np.abs(err)),np.mean(err)])
                mse,mae,bias=np.mean(vals,axis=0)
                assert np.allclose([mse,mae,bias],[record['mse'],record['mae'],record['bias']],atol=1e-12,rtol=0)
                checked+=1
    stints=pl.read_parquet(a.DATED); omitted=[]
    for year in sorted(saved['target_year'].unique()):
        g=saved.filter(pl.col('target_year')==year)
        missing=stints.filter((pl.col('sport_id')==1)&(pl.col('season')==year)&~pl.col('player_id').is_in(g['player_id'].to_list()))
        annual=missing.group_by('player_id','player_name','position').agg(pl.col(a.COUNT_COLS).sum())
        env=np.array([g['target_env_'+e][0] for e in EVENTS]);rep=g['origin_replacement_rate'][0]
        annual=annual.with_columns((pl.col('plate_appearances')-pl.sum_horizontal(a.COUNT_COLS[1:])).alias('other'))
        n=annual['plate_appearances'].to_numpy(); counts=annual.select(['other',*a.COUNT_COLS[1:]]).to_numpy()
        annual=annual.with_columns(pl.Series('season_relative_value',((counts-n[:,None]*env)@VALUES)*UNIT/600+n*rep))
        positions=annual.group_by('position').agg(pl.col('plate_appearances','season_relative_value').sum()).sort('plate_appearances',descending=True).to_dicts()
        item=next(x for x in scores['league'] if x['target_year']==year)
        assert annual['plate_appearances'].sum()==item['missing_pa']
        assert np.isclose(annual['season_relative_value'].sum(),item['missing_relative_value'],atol=1e-9,rtol=0)
        omitted.append(dict(target_year=year,positions=positions,largest_source_cases=annual.sort('plate_appearances','player_id',descending=[True,False]).head(8).to_dicts(),
            interpretation='Source position 1 denotes pitcher; diagnostic source metadata, not origin forecasting input. Zero-PA source people do not represent missing future jobs.'))
    casefile=a.b.prep.read(a.OUT/'cases.json'); cases=casefile['cases']; lines=['# Player walks for the season value audit','',
        'All forecasts are unchanged. Values are fixed-event custom batting-plus-replacement wins, not full WAR. Actual minus predicted is split into opportunity, hitting and (for the old label) league environment. Exact saved inputs and full source histories accompany these calculations.','']
    for c in cases:
        o=c['origin'];d=c['displayed_forecast'];key=(o['player_name'],o['origin_year'])
        assert key in NOTES
        assert all(o['origin_year']-2<=r['season']<=o['origin_year'] for r in c['source_history'])
        h=c['selected_head'];x=np.array(c['fitted_inputs']['rate_inputs']);coef=np.array(h['coefficients'])
        assert np.isclose(h['intercept']+x@coef,o['combined_rate'],atol=1e-10,rtol=0)
        assert np.isclose(d['p']*d['conditional_pa'],o['preseason_pa'],atol=1e-10,rtol=0)
        assert np.isclose(o['audit_relative_value']-o['combined_value'],o['audit_opportunity']+o['audit_hitting'],atol=1e-10,rtol=0)
        c['baseball_review']=NOTES[key]
        c['linear_terms']=[dict(feature=n,input=float(v),coefficient=float(b),signed_term=float(v*b)) for n,v,b in zip(h['features'],x,coef)]
        c['linear_intercept']=h['intercept'];c['linear_sum_terms']=float(x@coef)
        lines += [f"## {o['player_name']} predicting {o['target_year']}",'',
            'Selection: '+', '.join(c['selection'])+'.','',NOTES[key],'',
            f"The selected {d['branch']} head has intercept {h['intercept']:.6f} plus input terms {float(x@coef):.6f} = {o['combined_rate']:.6f} batting wins per 600. Appearance {d['p']:.6f} × active PA {d['conditional_pa']:.6f} = {o['preseason_pa']:.6f} expected PA.",'',
            '| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |',
            '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
            '| '+' | '.join(f'{o[k]:.6f}' for k in ['preseason_value','combined_value','audit_relative_value','next_value','audit_opportunity','audit_hitting','audit_environment'])+' |','',
            f"Observed eight-event vector ({', '.join(EVENTS)}): {', '.join(str(int(c['actual_events'][e])) for e in EVENTS)}. Origin/target indexes {c['origin_index']:.9f}/{c['target_index']:.9f}; replacement reference {c['replacement_reference']:.9f} per PA. No future reference enters the forecast.",'',
            'Origin source production (season, level, PA, HR, K, unintentional walks):','']
        if not c['source_history']: lines+=['No own recent source production; unknown is not zero talent.','']
        else:
            for r in sorted(c['source_history'],key=lambda z:(z['season'],z['level_group'])):
                lines += [f"- {r['season']} {r['level_group']}: {r['plate_appearances']} PA, {r['home_runs']} HR, {r['strike_outs']} K, {r['unintentional_walks']} UBB."]
            lines+=['']
        lines+=['Origin-selected peers (expected/actual PA): '+ '; '.join(f"{p['player_name']} {p['preseason_pa']:.1f}/{p['next_pa']}" for p in c['peers'])+'.','',
            'These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.','']
    a.write('reviewed-cases.json',dict(cases=cases,player_walkthrough_status='complete',peer_rule=casefile['peer_rule'],new_predictions=False))
    a.write('omitted-cohort-review.json',dict(years=omitted,source_review_status='complete_for_accounting_only',new_forecast_inputs=False))
    (a.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    freeze=subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=a.ROOT,check=True,capture_output=True,text=True)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider','tests/test_hitter_value_ledger.py','tests/test_hitter_research_export.py','-q'],cwd=a.ROOT,check=True,capture_output=True,text=True)
    outputs={str(p.relative_to(a.OUT)):sha256_file(p) for p in a.OUT.iterdir() if p.is_file()}
    a.write('final-review.json',dict(execution_verification_status='complete',player_walkthrough_status='complete',player_origins=len(cases),
        forecast_rows=30506,endpoint_components_checked=checked,all_forecasts_unchanged=True,new_models_fitted=0,
        protected_freeze=json.loads(freeze.stdout),tests=tests.stdout,artifact_hashes=outputs,
        reviewer_sha256=sha256_file(Path(__file__)),deployment_approved=False,full_goal_complete=False,
        decision='Use explicit season-relative custom batting contribution for WAR-like development interpretation; retain prior common-reference records. Main improvement survives, minor incremental uncertainty and workload gaps remain.'))
    dest=a.ROOT/'reports/model-evidence/hitter-season-value-ledger';dest.mkdir(parents=True,exist_ok=True)
    for path in sorted(a.OUT.iterdir()):
        if path.is_file():
            target=dest/path.name
            assert not target.exists(),'Preserve compact evidence'
            shutil.copyfile(path,target)
    print('Reviewed',len(cases),'player origins;',checked,'independent endpoint components; protected freeze and tests verified.',flush=True)


if __name__=='__main__':main()
