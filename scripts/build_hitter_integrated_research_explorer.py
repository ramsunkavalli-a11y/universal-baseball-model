"""Export reviewed historical branches and replay every displayed fitted head."""
import json
from pathlib import Path
import shutil

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_research_export import ARMS, branch, export_row
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_minor_precision as prep
import build_hitter_risk_research_explorer as previous

ROOT = prep.ROOT
OUT = ROOT/'reports/generated/hitter-integrated-research-explorer'
DIST = OUT/'dist'
TEMPLATE = ROOT/'src/universal_baseball/templates/hitter_integrated_research'
HISTORY = ['season','level_group','plate_appearances','home_runs','strike_outs',
           'unintentional_walks','doubles','triples','hits','at_bats','team_id','league_id']


def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(',', ':'), default=str)+'\n'
    if path.exists():
        assert path.read_text(encoding='utf8') == data, f'Preserve prior export: {path}'
    else:
        path.write_text(data, encoding='utf8', newline='\n')


def linear_head(path, cols, frame, hashes):
    hashes[str(path)] = sha256_file(path)
    model = joblib.load(path); x = safe_matrix(frame, cols)
    predicted = model.predict(x)
    assert np.allclose(predicted, model.intercept_ + x @ model.coef_, atol=1e-10, rtol=0)
    return dict(features=cols, coefficients=model.coef_.tolist(), intercept=float(model.intercept_),
                path=str(path), sha256=hashes[str(path)]), x, predicted


def main():
    assert not (OUT/'build-report.json').exists(), 'Completed exports are immutable; inspect or create a new revision.'
    hashes = {}
    def record(p):
        p = Path(p); hashes[str(p)] = sha256_file(p); return p
    finals = [prep.OUT/'final-review.json', prep.old.mlb.OUT/'final-review.json',
              prep.old.BRIDGE/'report.json', previous.e.old.current.OUT/'report.json']
    for path in finals:
        final = prep.read(record(path)); assert final['player_walkthrough_status'] == 'complete'
        for group in ['artifact_hashes','input_hashes','output_hashes']:
            prep.old.verify_hashes(final.get(group, {}))
    pre = prep.read(record(prep.OUT/'preflight.json'))
    prep.old.verify_hashes(pre['input_hashes'])
    q = pl.read_parquet(record(prep.OUT/'scored-predictions.parquet')).sort('row_id')
    assert len(q) == q['row_id'].n_unique() == 30506 and q['target_year'].max() == 2025
    assert q['target_year'].unique().sort().to_list() == [2017,2018,2019,2022,2023,2024,2025]
    team = previous.TEAM
    affiliation_review = prep.read(record(team/'source-review.json'))
    assert affiliation_review['player_walkthrough_status'] == 'complete_for_source_only'
    assert affiliation_review['source_review_status'] == 'complete_with_ownership_coverage_qualification'
    prep.old.verify_hashes(affiliation_review['review_hashes'])
    assert sha256_file(record(team/'features.parquet')) == affiliation_review['features_sha256']
    cf = pl.read_parquet(team/'features.parquet').select('row_id',*[c for c in pl.read_parquet(team/'features.parquet').columns if c.startswith('context_')])
    contexts = {r['row_id']:r for r in cf.iter_rows(named=True)}
    pf = pl.read_parquet(record(previous.e.old.current.OUT/'profile-support.parquet')).filter(
        (pl.col('arm') == 'preseason') & (pl.col('kind') == 'refined'))
    support = {}
    for r in pf.iter_rows(named=True): support.setdefault(r['row_id'], {})[r['head']] = r['profile_people']
    opportunity_pre = prep.read(record(previous.e.old.current.OUT/'preflight.json'))
    pnames = opportunity_pre['pa_features']
    opportunity_source = previous.e.old.context()
    record(previous.e.old.current.OUT/'features.parquet')
    record(previous.e.old.VALUE/'features.parquet')
    dates = {str(c['year']+1):c['information_date'] for c in opportunity_pre['cells']}
    # Preserve the different actual fitted frames for PA and translated batting.
    reviews = {}
    for label, path in [('Prospect translation', prep.old.BRIDGE/'reviewed-cases.json'),
                        ('Minor precision comparison', prep.OUT/'reviewed-cases.json')]:
        source = prep.read(record(path)); cases = source if isinstance(source,list) else source['cases']
        for c in cases:
            rid = c['origin']['row_id']
            reviews.setdefault(rid, []).append(dict(component=label, note=c['baseball_review'],
                selection=c['selection'], peers=c['peers'], source_path=str(path)))
    mlb_path = prep.old.mlb.OUT/'reviewed-cases.json'
    mlb_cases = prep.read(record(mlb_path))['cases']
    # Existing full MLB narrative is carried intact, not invented from error ranks.
    narrative = (ROOT/'docs/hitter-statcast-next-year-result.md').read_text(encoding='utf8')
    record(ROOT/'docs/hitter-statcast-next-year-result.md')
    for c in mlb_cases:
        rid = c['origin']['row_id']
        reviews.setdefault(rid, []).append(dict(component='MLB Statcast', selection=c['selection'],
            note='The completed source-to-fit review is included below. This case belongs to the MLB-only comparison, not a new joint validation.',
            peers=c['peers'], source_path=str(mlb_path)))
    for rid, cases in reviews.items(): write(DIST/f'reviews/{rid}.json', cases)
    write(DIST/'mlb-review.json', dict(text=narrative))
    bridge_profiles = pl.read_parquet(record(prep.old.BRIDGE/'profile-support.parquet')).filter(
        (pl.col('arm')=='translated_ridge') & (pl.col('kind')=='active') & (pl.col('profile_kind')=='refined'))
    rate_profiles = {r['row_id']:r['profile_people'] for r in bridge_profiles.iter_rows(named=True)}
    mlb_profiles = {r['row_id']:r['tracked_profile_people'] for r in
        pl.read_parquet(record(prep.old.mlb.OUT/'tracked-profile-support.parquet')).iter_rows(named=True)}
    exported = []
    for r in q.iter_rows(named=True):
        o = export_row(r, contexts[r['row_id']], support[r['row_id']], dates[str(r['target_year'])], reviews)
        o['rate_profile_people'] = rate_profiles.get(r['row_id']) if not r['prior_debut'] else (mlb_profiles.get(r['row_id']) if r['sc_tracked'] else None)
        if o['rate_profile_people'] is None or o['rate_profile_people'] < 20:
            o['flags'].append('Sparse or undocumented matching hitting profile; the ability estimate is not certified for this exact player type.')
        exported.append(o)
    stints = pl.read_parquet(record(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')).filter(pl.col('season')<=2024)
    histories = {}
    for r in stints.iter_rows(named=True): histories.setdefault(r['player_id'], []).append([r[k] for k in HISTORY])
    sources = {}
    for label, path in [('MLB',ROOT/'reports/generated/hitter-statcast-full-history/annual-launch-features.parquet'),
                        ('Minor',prep.OUT/'annual-contact-noise.parquet')]:
        for r in pl.read_parquet(record(path)).filter(pl.col('season')<=2024).iter_rows(named=True):
            fields = ['season','measured_ev_contacts','measured_pair_contacts','terminal_nonbunt_contacts',
                      'mean_ev','ev95','mean_la','hard_air_fraction','pair_coverage']
            fields += [k for k in ['league_id','level_group','best_half_ev'] if k in r]
            sources.setdefault(r['player_id'], []).append(dict(source=label,**{k:r[k] for k in fields}))
    for year in q['target_year'].unique().sort():
        rows = [r for r in exported if r['target_year']==year]; ids = {r['player_id'] for r in rows}
        history = {str(pid): sorted([h for h in histories.get(pid,[]) if year-3<=h[0]<year],key=lambda h:(h[0],h[1])) for pid in ids}
        launch = {str(pid): [h for h in sources.get(pid,[]) if year-3<=h['season']<year] for pid in ids}
        write(DIST/f'years/{year}.json',dict(rows=rows, history=history, launch=launch))
    replays = []; all_heads = {}
    with threadpool_limits(limits=2):
        for fold in range(5):
            f = pl.read_parquet(record(prep.OUT/f'features-{fold}.parquet'))
            for c in [c for c in pre['cells'] if c['fold']==fold]:
                year = c['year']; key=f'{year}-{fold}'
                _, te, _ = prep.routed(f,c)
                got=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert got['row_id'].equals(te['row_id'])
                pt=opportunity_source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert pt['row_id'].equals(te['row_id'])
                px=pt.select(pnames).to_numpy(); assert np.isfinite(px).all()
                heads={}; x_by_branch={}; pred=np.zeros(len(te))
                labels=['Translated prospect Ridge','MLB Statcast Ridge','Current rate fallback']
                masks=[te['prior_debut'].to_numpy()==0,
                       (te['prior_debut'].to_numpy()==1)&te['sc_tracked'].to_numpy(),
                       (te['prior_debut'].to_numpy()==1)&~te['sc_tracked'].to_numpy()]
                assert np.all(sum(m.astype(int) for m in masks)==1)
                for label, h, mask in zip(labels,c['baseline_heads'],masks):
                    assert sha256_file(Path(h['path']))==h['sha256']
                    head,x,raw=linear_head(Path(h['path']),h['features'],te,hashes)
                    heads[label]=head;x_by_branch[label]=x;pred[mask]=raw[mask]
                assert np.allclose(pred,got['combined_rate'],atol=1e-10,rtol=0)
                ph=prep.read(record(previous.e.old.current.OUT/f'fit-{year}-{fold}.json'))
                for h in ph['heads']:
                    assert sha256_file(Path(h['path']))==h['sha256'];record(h['path'])
                    m=joblib.load(h['path'])
                    raw=m.predict_proba(px)[:,1] if h['head']=='participation' else m.predict(px)
                    col='preseason_raw_p' if h['head']=='participation' else 'preseason_raw_conditional_pa'
                    assert np.allclose(raw,got[col],atol=1e-10,rtol=0)
                adjustment={}; ax={}
                for h in prep.read(record(prep.OUT/f'fit-{year}-{fold}.json'))['heads']:
                    assert sha256_file(Path(h['path']))==h['sha256']
                    head,x,raw=linear_head(Path(h['path']),h['features'],te,hashes)
                    assert np.allclose(raw,got[h['arm']+'_raw_update'],atol=1e-12,rtol=0)
                    applied=np.where(got['msc_eligible'],raw,0.)
                    assert np.allclose(pred+applied,got[h['arm']+'_rate'],atol=1e-10,rtol=0)
                    adjustment[h['arm']]=head;ax[h['arm']]=x
                rows={}
                for i,r in enumerate(got.iter_rows(named=True)):
                    label=branch(r)
                    rows[str(r['row_id'])]=dict(branch=label,rate_inputs=x_by_branch[label][i].tolist(),
                        opportunity_inputs=px[i].tolist(),
                        adjustment_inputs={a:x[i].tolist() for a,x in ax.items()})
                write(DIST/f'cells/{key}.json',dict(rows=rows))
                all_heads[key]=dict(rate=heads,adjustments=adjustment,opportunity_heads=ph['heads'])
                replays.append(dict(origin=year,fold=fold,rows=len(te),rate_replayed=True,opportunity_heads_replayed=2,adjustment_heads_replayed=len(adjustment)))
                print('Exported and replayed',key,len(te),'forecasts',flush=True)
    write(DIST/'heads.json',all_heads)
    scores=prep.read(record(prep.OUT/'scores.json'))
    point_scores=prep.read(record(previous.e.old.current.OUT/'scores.json'))
    public=next(s for s in point_scores if s['scope']=='public_broad')
    public_value=next(s for s in scores['scopes'] if s['scope']=='public')
    metadata=dict(title='Historical hitter projection candidate',target_years=q['target_year'].unique().sort().to_list(),
        forecasts=len(q),people=q['player_id'].n_unique(),arms=ARMS,default_arm='combined',
        information_dates=dates,history_fields=HISTORY,opportunity_features=pnames,
        public_benchmark=public,public_value=public_value,scores=scores['scopes'],
        model_card=[
            'Before MLB debut: a regularized model learns next-year MLB hitting from production at separate minor levels, age, position, draft and dated prospect-ranking evidence. Cross-level translations are learned from earlier movers; they are not fully park- or opponent-neutral minor league equivalents.',
            'After MLB debut: players with their own recent MLB launch measurements use the reviewed Statcast Ridge branch. It combines three seasons of production with exit velocity, launch angle, contact-quality summaries and measurement counts. Others retain the current hitting forecast exactly.',
            'Playing time is unchanged: two histogram gradient-tree models predict any MLB PA and PA if active. Their product is expected PA. Production, level, age, listed position, draft, observed games/roles, roster/status and dated rankings enter; no complete diagnosed-injury or future-job model is claimed.',
            'The main assembly was already scored and replayed in the minor-tracking comparisons. It is a research candidate, not an independently confirmed joint model. The uncertain minor tracking updates are visible comparisons and are not adopted.',
            'All rows are historical held-player chronological forecasts. Labels have already been used for development. Historical feeds and affiliations are retrospective reconstructions, not guaranteed archived preseason snapshots. No protected 2026 outcomes are used.'
        ],limits=[
            'PA absolute error remains outside the declared public benchmark allowance; elite thin entrants and some advancing players still have severe opportunity misses.',
            'Hitting profile counts are warning diagnostics, not certification of comparable superstars or DSL long-term talent. Non-arrivals have no observed MLB hitting rate.',
            'Statcast means here are not fully adjusted for park, opponent or sensor changes. Minor measurements cover selected AAA/FSL leagues and limited mature years, not all levels.',
            'No calibrated uncertainty distribution is attached to the changed hitting mean. Older ranges were fitted around a different forecast and cannot be silently reused.',
            'Defense, catcher value, running, position value, contracts, new entrants, multi-year control and trade value are not included. Cohort totals are not complete team or league budgets.'
        ])
    write(DIST/'metadata.json',metadata)
    for name in ['index.html','app.js','app.css']:
        source=record(TEMPLATE/name);target=DIST/name
        if target.exists():assert sha256_file(target)==sha256_file(source)
        else:shutil.copyfile(source,target)
    for path in [Path(__file__),ROOT/'src/universal_baseball/hitter_research_export.py',
                 ROOT/'docs/hitter-integrated-research-explorer-contract.md']:record(path)
    write(OUT/'build-report.json',dict(forecasts=len(q),people=q['player_id'].n_unique(),source_hashes=hashes,
        output_hashes={str(p.relative_to(DIST)):sha256_file(p) for p in sorted(DIST.rglob('*')) if p.is_file()},
        selected_branch_and_opportunity_replays=replays,reviewed_origins=len(reviews),new_models_fitted=0,
        source_history_cutoff=2024,means_unchanged_from_existing_combined=True,
        protected_outcomes_used=False,frozen_forecast_changed=False,existing_explorers_changed=False,
        browser_verification_status='pending',export_verification_status='pending',deployment_approved=False,
        full_goal_complete=False,output_directory=str(DIST)))
    print('Historical integrated research explorer built:',DIST,flush=True)


if __name__=='__main__':main()
