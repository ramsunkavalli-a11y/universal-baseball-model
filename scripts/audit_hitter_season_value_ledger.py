"""Audit unchanged forecasts under two explicit historical value references."""
import json
from pathlib import Path
import numpy as np
import polars as pl

from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.hitter_value_ledger import miss_terms, equal_origin_loss
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.storage import sha256_file
import build_hitter_integrated_research_explorer as b

ROOT = b.ROOT
OUT = ROOT / 'reports/generated/hitter-season-value-ledger'
CONTRACT = ROOT / 'docs/hitter-season-value-ledger-contract.md'
SOURCE = ROOT / 'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
DATED = ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet'
COUNT_COLS = ['plate_appearances', 'strike_outs', 'unintentional_walks', 'hit_by_pitch',
              'singles', 'doubles', 'triples', 'home_runs']
ARMS = ['preseason', 'combined', 'precision_coverage', 'precision_measurements']
FIXED = [('Aaron Judge', 2018), ('Aaron Judge', 2024), ('Nick Kurtz', 2024),
         ('Bo Bichette', 2024), ('Junior Caminero', 2024), ('Steven Kwan', 2021),
         ('Brandon Belt', 2023), ('Eric Thames', 2016), ('Juneiker Caceres', 2024)]


def write(name, value):
    b.write(OUT / name, value)


def paired(g, candidate, control, label):
    people, pi = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    years, yi = np.unique(g['origin_year'].to_numpy(), return_inverse=True)
    actual = g[label].to_numpy()
    d = (g[candidate+'_value'].to_numpy()-actual)**2 - (g[control+'_value'].to_numpy()-actual)**2
    num = np.zeros((len(people), len(years))); den = np.zeros_like(num)
    np.add.at(num, (pi, yi), d); np.add.at(den, (pi, yi), 1.)
    rng = np.random.default_rng(880104); draws = []
    for _ in range(2000):
        ids = rng.integers(0, len(people), len(people))
        n = num[ids].sum(0); z = den[ids].sum(0)
        assert (z > 0).all()
        draws.append(float(np.mean(n/z)))
    return dict(candidate=candidate, control=control, label=label,
                delta_mse=float(np.mean(num.sum(0)/den.sum(0))),
                nominal_95=np.quantile(draws, [.025, .975]).tolist(),
                resamples=2000, player_clustered=True, multiplicity_adjusted=False,
                shared_year_shocks_covered=False)


def main():
    assert not (OUT / 'audit.json').exists(), 'Preserve completed audit'
    build = b.prep.read(b.OUT / 'build-report.json')
    final = b.prep.read(ROOT / 'reports/model-evidence/hitter-integrated-research-explorer/final-report.json')
    assert final['export_verification_status'] == 'complete'
    b.prep.old.verify_hashes(build['source_hashes'])
    b.prep.old.verify_hashes(final['code_hashes'])
    for name, digest in final['artifact_hashes'].items():
        assert sha256_file(ROOT / 'reports/model-evidence/hitter-integrated-research-explorer' / name) == digest
    q = pl.read_parquet(SOURCE).sort('row_id')
    assert len(q) == q['row_id'].n_unique() == 30506
    assert q['target_year'].unique().sort().to_list() == [2017, 2018, 2019, 2022, 2023, 2024, 2025]
    stints = pl.read_parquet(DATED)
    assert stints['season'].max() == 2025
    counts = stints.filter(pl.col('sport_id') == 1).group_by('player_id', 'season').agg(pl.col(COUNT_COLS).sum())
    counts = counts.with_columns((pl.col('plate_appearances') - pl.sum_horizontal(COUNT_COLS[1:])).alias('other'))
    names = ['other', *COUNT_COLS[1:]]
    assert not counts.filter(pl.col('other') < 0).height
    full = counts.group_by('season').agg(pl.col('plate_appearances', *names).sum()).sort('season')
    environments = {r['season']: np.array([r[k] for k in names], float)/r['plate_appearances']
                    for r in full.iter_rows(named=True)}
    actual = q.select('row_id', 'player_id', 'target_year', 'next_pa').join(
        counts.rename({'season': 'target_year'}), on=['player_id', 'target_year'], how='left', validate='m:1').sort('row_id')
    assert not actual.filter(pl.col('plate_appearances').is_null() & (pl.col('next_pa') > 0)).height
    raw = actual.select(pl.col(names).fill_null(0)).to_numpy()
    assert np.array_equal(raw, q.select(['count_'+e for e in EVENTS]).to_numpy())
    n = raw.sum(1); assert np.array_equal(n, q['next_pa'].to_numpy())
    origin_env = np.array([environments[y] for y in q['origin_year']])
    target_env = np.array([environments[y] for y in q['target_year']])
    assert np.allclose(origin_env, q.select(['origin_env_'+e for e in EVENTS]).to_numpy(), atol=1e-14, rtol=0)
    assert np.allclose(target_env, q.select(['target_env_'+e for e in EVENTS]).to_numpy(), atol=1e-14, rtol=0)
    oi = origin_env @ VALUES; ti = target_env @ VALUES
    ai = np.divide(raw @ VALUES, n, out=np.zeros(len(q)), where=n > 0)
    relative = np.where(n > 0, (ai-ti)*UNIT, 0.)
    common = np.where(n > 0, (ai-oi)*UNIT, 0.)
    assert np.allclose(relative[n > 0], q['actual_future_relative_rate'].to_numpy()[n > 0], atol=1e-10, rtol=0)
    rep = q['origin_replacement_rate'].to_numpy()
    relative_value = n*(relative/600+rep); common_value = n*(common/600+rep)
    assert np.allclose(common_value, q['next_value'], atol=1e-10, rtol=0)
    assert np.allclose(relative_value, q['relative_value_label'], atol=1e-10, rtol=0)
    terms = miss_terms(q['preseason_pa'], q['combined_rate'], n, relative, rep, oi, ti)
    for arm in ARMS:
        assert np.allclose(q[arm+'_value'], q['preseason_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']), atol=1e-10, rtol=0)
    assert np.allclose(terms['common_actual'], common_value, atol=1e-10, rtol=0)
    q = q.with_columns(pl.Series('audit_relative_value', relative_value),
        pl.Series('audit_origin_index', oi), pl.Series('audit_target_index', ti),
        pl.Series('audit_actual_index', ai),
        *[pl.Series('audit_'+k, terms[k]) for k in ['opportunity', 'hitting', 'environment']])
    public = q.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert len(public) == 2627
    scopes = [('all', q), ('never_debut', q.filter(pl.col('prior_debut') == 0)),
        ('upper_never_debut', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
        ('lower_never_debut', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
        ('tracked', q.filter(pl.col('sc_tracked'))), ('untracked', q.filter(~pl.col('sc_tracked'))),
        ('minor_eligible', q.filter(pl.col('msc_eligible'))), ('public', public)]
    scopes += [('origin_'+str(y), q.filter(pl.col('origin_year') == y)) for y in q['origin_year'].unique().sort()]
    scopes += [('stage_'+stage, q.filter(pl.col('stage') == stage)) for stage in q['stage'].unique().sort()]
    scores = []
    for label, g in scopes:
        if not len(g): continue
        arms = ARMS + (['steamer'] if label == 'public' else [])
        losses = {target: {a: equal_origin_loss(g[a+'_value'], g[col], g['origin_year']) for a in arms}
                  for target, col in [('common_origin', 'next_value'), ('season_relative', 'audit_relative_value')]}
        scores.append(dict(scope=label, rows=len(g), people=g['player_id'].n_unique(),
            actual_pa=int(g['next_pa'].sum()), expected_pa=float(g['preseason_pa'].sum()),
            actual_common=float(g['next_value'].sum()), actual_relative=float(g['audit_relative_value'].sum()),
            expected={a:float(g[a+'_value'].sum()) for a in arms},
            residual_terms={k:float(g['audit_'+k].sum()) for k in ['opportunity','hitting','environment']}, losses=losses))
    intervals = []
    for name, g in scopes[:8]:
        if name in ['all','never_debut','tracked','public']:
            for label in ['next_value','audit_relative_value']:
                intervals.append(dict(scope=name, **paired(g, 'combined', 'preseason', label)))
        if name == 'minor_eligible':
            intervals.append(dict(scope=name, **paired(g, 'precision_measurements', 'precision_coverage', 'audit_relative_value')))
    league = []
    for (year,), g in q.group_by('target_year'):
        all_counts = counts.filter(pl.col('season') == year)
        missing = all_counts.filter(~pl.col('player_id').is_in(g['player_id'].to_list()))
        raw_missing = missing.select(names).to_numpy(); mpa=raw_missing.sum(1)
        env = environments[year]; replacement = g['origin_replacement_rate'][0]
        assert g['origin_replacement_rate'].n_unique() == 1
        mvalue = float((((raw_missing-mpa[:,None]*env) @ VALUES)*UNIT/600 + mpa*replacement).sum())
        fullvalue = float(all_counts['plate_appearances'].sum()*replacement)
        assert np.isclose(fullvalue, float(g['audit_relative_value'].sum())+mvalue, atol=1e-9, rtol=0)
        league.append(dict(target_year=year, full_source_pa=int(all_counts['plate_appearances'].sum()),
            known_cohort_pa=int(g['next_pa'].sum()), missing_people=missing.height,
            missing_pa=int(mpa.sum()), missing_relative_value=mvalue,
            full_relative_custom_value=fullvalue, known_relative_value=float(g['audit_relative_value'].sum()),
            origin_index=float(g['audit_origin_index'][0]), target_index=float(g['audit_target_index'][0]),
            reference=replacement))
    selected = {}
    def select(frame, reason):
        assert len(frame); selected.setdefault(frame['row_id'][0], []).append(reason)
    for name, year in FIXED:
        select(q.filter((pl.col('player_name') == name) & (pl.col('origin_year') == year)), 'fixed before scoring')
    errors = q.with_columns(((pl.col('preseason_value')-pl.col('audit_relative_value'))**2 -
                            (pl.col('combined_value')-pl.col('audit_relative_value'))**2).alias('gain'),
                           (pl.col('combined_value')-pl.col('audit_relative_value')).alias('error'))
    select(errors.sort('gain','row_id',descending=[True,False]), 'largest main gain on season-relative label')
    select(errors.sort('gain','row_id'), 'largest main harm on season-relative label')
    select(errors.sort('error','row_id',descending=[True,False]), 'largest false high')
    select(errors.sort('error','row_id'), 'largest false low')
    select(errors.filter(pl.col('next_pa').is_between(200,600)).with_columns(pl.col('error').abs().alias('absolute_error')).sort('absolute_error','row_id'), 'ordinary active diagnostic')
    cases = []
    histories = {}; cells = {}; heads = b.prep.read(b.DIST / 'heads.json')
    for rid, reasons in selected.items():
        o = q.filter(pl.col('row_id') == rid).row(0, named=True)
        year = o['target_year']; key=f"{o['origin_year']}-{o['outer_fold']}"
        if year not in histories: histories[year] = b.prep.read(b.DIST / f'years/{year}.json')
        if key not in cells: cells[key] = b.prep.read(b.DIST / f'cells/{key}.json')['rows']
        display = next(r for r in histories[year]['rows'] if r['row_id'] == rid)
        data = cells[key][str(rid)]; head = heads[key]['rate'][display['branch']]
        predicted = head['intercept'] + np.dot(data['rate_inputs'], head['coefficients'])
        assert np.isclose(predicted, o['combined_rate'], atol=1e-10, rtol=0)
        pool = q.filter((pl.col('origin_year') == o['origin_year']) & (pl.col('prior_debut') == o['prior_debut']) &
                        (pl.col('stage') == o['stage']) & (pl.col('player_id') != o['player_id']))
        distance = ((pl.col('age')-o['age'])/3)**2 + ((pl.col('pa_0')-o['pa_0'])/300)**2 + \
                   ((pl.col('minor_pa_0')-o['minor_pa_0'])/300)**2 + ((pl.col('quality_0')-o['quality_0'])/2)**2
        fields = ['row_id','player_id','player_name','origin_year','target_year','age','stage','pa_0','minor_pa_0','quality_0',
                  'preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate','combined_rate',
                  'preseason_value','combined_value','next_pa','actual_future_relative_rate','next_value',
                  'audit_relative_value','audit_opportunity','audit_hitting','audit_environment']
        peers = pool.with_columns(distance.alias('distance')).sort('distance','player_id').head(4).select(*fields,'distance').to_dicts()
        for p in peers:
            if p['next_pa'] == 0: p['actual_future_relative_rate'] = None
            p['source_history'] = stints.filter((pl.col('player_id')==p['player_id']) & pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts()
        cases.append(dict(origin={k:o[k] for k in fields}, selection=reasons, displayed_forecast=display,
            source_history=stints.filter((pl.col('player_id')==o['player_id']) & pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts(),
            fitted_inputs=data, selected_head=head,
            actual_events={e:o['count_'+e] for e in EVENTS},
            origin_environment={e:o['origin_env_'+e] for e in EVENTS},
            target_environment={e:o['target_env_'+e] for e in EVENTS},
            replacement_reference=o['origin_replacement_rate'], actual_index=o['audit_actual_index'],
            origin_index=o['audit_origin_index'], target_index=o['audit_target_index'], peers=peers,
            algebra='actual minus forecast = opportunity + hitting; common-origin adds environment',
            forecast_unchanged=True))
        if not o['next_pa']: cases[-1]['origin']['actual_future_relative_rate'] = None
    OUT.mkdir(parents=True, exist_ok=True)
    q.select('row_id','player_id','origin_year','target_year','preseason_pa','next_pa','origin_replacement_rate',
        *[a+s for a in ARMS for s in ['_rate','_value']], 'next_value','audit_relative_value',
        'audit_origin_index','audit_target_index','audit_actual_index','audit_opportunity','audit_hitting','audit_environment').write_parquet(OUT / 'ledger.parquet')
    write('scores.json', dict(scopes=scores, intervals=intervals, league=sorted(league,key=lambda x:x['target_year']),
        public_qualification='Unchanged raw-event public conversion assumes the projected league reference equals origin; season-relative scoring is sensitivity, not native WAR or certified neutral public forecasts.'))
    write('cases.json', dict(cases=cases, player_walkthrough_status='pending',
        peer_rule='Same origin/debut/stage; nearest age/current MLB PA/minor PA/production quality, with no future results in distance.'))
    paths = [SOURCE,DATED,CONTRACT,Path(__file__), ROOT/'src/universal_baseball/hitter_value_ledger.py',
             ROOT/'tests/test_hitter_value_ledger.py', b.OUT/'build-report.json',
             ROOT/'reports/model-evidence/hitter-integrated-research-explorer/final-report.json',
             b.DIST/'heads.json'] + [b.DIST/f'cells/{k}.json' for k in cells] + [b.DIST/f'years/{y}.json' for y in histories]
    write('audit.json', dict(source_hashes={str(p):sha256_file(p) for p in paths},
        output_hashes={str(p.relative_to(OUT)):sha256_file(p) for p in OUT.iterdir() if p.is_file()},
        forecasts=30506, rows_reconstructed=30506, full_environments_reconstructed=True,
        predictions_changed=False, new_models_fitted=0, protected_outcomes_used=False,
        scoring_and_arithmetic_complete=True, player_walkthrough_status='pending',
        deployment_approved=False, full_goal_complete=False))
    for s in scores[:2]: print(s['scope'], s['actual_common'], s['actual_relative'], s['losses']['season_relative']['combined'],flush=True)
    print('Audit arithmetic complete; player review pending.',len(cases),'cases.',flush=True)


if __name__ == '__main__':
    main()
