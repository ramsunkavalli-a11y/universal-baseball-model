"""Comparative research UI from reviewed forecasts; no new models."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import build_practical_hitter_handoff_v64 as old
import evaluate_hitter_preseason_readiness_v68 as fresh

ROOT=old.ROOT;OUT=ROOT/'reports/generated/hitter-comparative-handoff-v72'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def main():
    assert not (OUT/'manifest.json').exists(),'Preserve the existing handoff'
    reports=[fresh.OUT/'report.json',ROOT/'reports/generated/hitter-graduation-v69/report.json',ROOT/'reports/generated/hitter-employment-v71/report.json',old.OUT/'handoff-manifest.json']
    for p in reports:
        r=read(p);assert r['player_walkthrough_status']=='complete'
        for key in ['input_hashes','source_hashes','output_hashes','review_code_hashes','handoff_hashes']:
            for path,h in r.get(key,{}).items():assert sha256_file(Path(path))==h,path
    q=pl.read_parquet(fresh.OUT/'scored-predictions.parquet').sort('row_id')
    f=pl.read_parquet(fresh.OUT/'features.parquet').filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
    base=pl.read_parquet(old.OUT/'candidate.parquet').sort('row_id');assert len(q)==len(base)==30506 and q['row_id'].equals(base['row_id'])
    for col in ['baseline_pa','baseline_rate','baseline_value','next_pa','next_value']:
        assert q[col].equals(base[col]),col
    for arm in ['baseline','preseason']:
        assert np.allclose(q[arm+'_pa'],q[arm+'_p']*q[arm+'_conditional_pa'],atol=1e-10,rtol=0)
        assert np.allclose(q[arm+'_value'],q[arm+'_pa']*(q['baseline_rate']/600+q['origin_replacement_rate']),atol=1e-10,rtol=0)
    assert q['target_year'].max()==2025 and q['origin_year'].max()==2024
    support=pl.read_parquet(fresh.OUT/'profile-support.parquet').filter(pl.col('kind')=='refined');sp={}
    for r in support.iter_rows(named=True):sp.setdefault(r['row_id'],{}).setdefault(r['arm'],{})[r['head']]=r['profile_people']
    records={r['row_id']:r for r in read(old.OUT/'explorer/data.json')}
    metadata={r['row_id']:r for r in f.select('row_id',*[s for s in f.columns if s.startswith('scout_')]).iter_rows(named=True)}
    old_meta={r['row_id']:r for r in base.select('row_id',*[s for s in base.columns if s.startswith('scout_')]).iter_rows(named=True)}
    cells=fresh.read(fresh.OUT/'preflight.json')['cells'];dates={c['year']:c['information_date'] for c in cells}
    rows=[]
    for r in q.iter_rows(named=True):
        d=records[r['row_id']];assert d['team_context_year'] is None or d['team_context_year']<=r['origin_year']
        arms={}
        for label,arm,meta in [('original','baseline',old_meta),('candidate','preseason',metadata)]:
            m=meta[r['row_id']]
            arms[label]=dict(p=r[arm+'_p'],conditional_pa=r[arm+'_conditional_pa'],pa=r[arm+'_pa'],value=r[arm+'_value'],
                scout_listed_0=m['scout_listed_0'],scout_rank_score_0=m['scout_rank_score_0'],
                support=dict(sp[r['row_id']][arm],rate=d['support']['rate']))
        d.update(arms=arms,ranking_information_date=dates[r['origin_year']])
        d['flags']=[s for s in d['flags'] if not s.startswith('Current historical ranking')]
        if metadata[r['row_id']]['scout_listed_0']<0:d['flags'].append('Fresher preseason ranking coverage partial or unknown')
        if d['prior_debut']==0 and d['draft_known'] and d['draft_year']==d['origin_year']:d['flags'].append('Elite rapid arrivals remain underpredicted; low chance is not a career grade')
        rows.append(d)
    dest=OUT/'explorer';dest.mkdir(parents=True,exist_ok=True)
    def write(n,o):
        (dest/n).write_text(json.dumps(o,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n',encoding='utf8')
    write('data.json',rows)
    for n in ['history.json','reviews.json']:(dest/n).write_bytes((old.OUT/'explorer'/n).read_bytes())
    notes={}
    for folder in [fresh.OUT,ROOT/'reports/generated/hitter-graduation-v69',ROOT/'reports/generated/hitter-employment-v71']:
        for c in read(folder/'reviewed-case-summary.json'):
            notes.setdefault(f"{c['player_id']}|{c['origin_year']}",[]).append(dict(source=folder.name,note=c['review_note'],saved_terms=c['saved_terms']))
    write('comparison-reviews.json',notes)
    scores=read(fresh.OUT/'scores.json');orig_scores=read(old.OUT/'explorer/scores.json')
    rates=next(s['rates'] for s in orig_scores if s['scope']=='public_broad')
    for s in scores:
        if s['scope']=='public_broad':s['rates']=rates
    write('scores.json',scores)
    scopes=[('all',q),('current_MLB',q.filter(pl.col('pa_0')>0)),('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors')))]
    prob={}
    for label,arm in [('original','baseline'),('candidate','preseason')]:
        prob[label]=dict(scopes=[dict(scope=name,**old.probability(g.with_columns(pl.col(arm+'_p').alias('repaired_p')))) for name,g in scopes])
    write('probability.json',prob)
    template=ROOT/'src/universal_baseball/templates/hitter_comparative_handoff.html';(dest/'index.html').write_bytes(template.read_bytes())
    for d in rows:
        assert d['next_batting_rate'] is None if d['next_pa']==0 else np.isfinite(d['next_batting_rate'])
        for a in d['arms'].values():assert abs(a['p']*a['conditional_pa']-a['pa'])<1e-8
    paths=reports+[fresh.OUT/'scored-predictions.parquet',fresh.OUT/'features.parquet',fresh.OUT/'profile-support.parquet',old.OUT/'candidate.parquet',
        ROOT/'docs/hitter-comparative-handoff-v72-contract.md',Path(__file__),template]
    manifest=dict(candidate='V68 fresher-preseason opportunity with unchanged V53/V63 hitting',rows=len(rows),no_new_models=True,
        all_arithmetic_and_original_forecasts_verified=True,actual_results_hidden_by_default=True,historical_team_filter=True,
        forecast_seasons=sorted(q['target_year'].unique()),ranking_information_dates=dates,
        source_hashes={str(p):sha256_file(p) for p in paths},artifact_hashes={str(p):sha256_file(p) for p in dest.iterdir()},
        browser_verification='pending',player_walkthrough_status='complete',protected_outcomes_used=False,frozen_forecast_changed=False,
        deployed_explorer_changed=False,whole_goal_complete=False)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print('Two reviewed arms exported; all 30,506 arithmetic/source rows verified; browser review pending.',flush=True)


if __name__=='__main__':main()
