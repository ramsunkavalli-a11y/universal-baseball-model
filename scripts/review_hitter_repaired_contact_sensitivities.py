"""Supplement the locked walks with weighted-rate and all-player extremes."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
import evaluate_hitter_repaired_contact_information as e
from review_hitter_repaired_contact_information import peers


def main():
    verification = e.read(e.OUT / 'verification.json')
    assert sha256_file(e.Path(verification['scored_path'])) == verification['scored_sha256']
    q = pl.read_parquet(verification['scored_path']); pre = e.read(e.OUT / 'preflight.json'); e.verify_inputs(pre)
    selected = {}
    established = q.filter(pl.col('prior_debut') == 1).with_columns(
        ((pl.col('translated_ridge_value') - pl.col('next_value')) ** 2 -
         (pl.col('joint_all_value') - pl.col('next_value')) ** 2).alias('gain'))
    rate = q.filter((pl.col('prior_debut') == 0) & (pl.col('next_pa') > 0)).with_columns(
        (pl.col('next_pa') * ((pl.col('translated_ridge_rate') - pl.col('next_relative_rate')) ** 2 -
                             (pl.col('joint_rate') - pl.col('next_relative_rate')) ** 2)).alias('gain'))
    for g, label in [(established, 'all-player established-value sensitivity'), (rate, 'actual-PA-weighted prospect-rate sensitivity')]:
        for descending, why in [(True, 'largest gain'), (False, 'largest harm')]:
            r = g.sort('gain', descending=descending).row(0, named=True)
            selected.setdefault(r['row_id'], []).append(label + ' ' + why)
    # Existing raw walkthroughs remain immutable. This adds only diagnostics.
    counts = pl.read_parquet(e.bridge.COUNTS)
    measures = pl.concat([pl.read_parquet(e.SOURCE / f'cell-features-{y}.parquet') for y in e.info.YEARS])
    support = pl.read_parquet(e.WORK / 'profiles.parquet')
    cases = []
    with threadpool_limits(limits=2):
        for rid, reasons in selected.items():
            r = q.filter(pl.col('row_id') == rid).row(0, named=True)
            f = e.bridge.previous.tagged(e.full(r['outer_fold'])); row = f.filter(pl.col('row_id') == rid)
            sr = row.row(0, named=True)
            note = e.read(e.OUT / f"fit-{r['origin_year']}-{r['outer_fold']}.json")
            traces = {}
            for h in note['heads']:
                a = h['arm']; cols = pre['features'][a]
                assert sha256_file(e.Path(h['path'])) == h['sha256']
                m = joblib.load(h['path']); x = e.safe_matrix(row, cols)[0]; terms = x * m.coef_
                raw = float(m.intercept_ + terms.sum())
                assert np.isclose(raw, r[a + '_raw_rate'], atol=1e-10, rtol=0)
                parts = {block: float(sum(t for c, t in zip(cols, terms) if c in names))
                         for block, names in [('coverage', e.info.COVERAGE), ('mix', e.info.SHAPE), ('detail', e.info.DETAIL)]}
                traces[a] = dict(intercept=float(m.intercept_), raw_prediction=raw,
                    primary_prediction=r[a + '_rate'], all_player_prediction=r[a + '_all_rate'],
                    block_contributions=parts, neutral_detail_probe=raw - parts['detail'],
                    effects=sorted([dict(feature=c, raw_input=sr[c], scaled_input=float(v), coefficient=float(b), effect=float(t))
                                    for c, v, b, t in zip(cols, x, m.coef_, terms)], key=lambda z: abs(z['effect']), reverse=True))
            history = counts.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year']))
            contact = measures.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year']))
            cases.append(dict(row_id=rid, player_id=r['player_id'], player_name=r['player_name'], origin_year=r['origin_year'],
                target_year=r['target_year'], outer_fold=r['outer_fold'], age=r['age'], stage=r['stage'], prior_debut=r['prior_debut'],
                information_date=next(c['information_date'] for c in pre['cells'] if c['year'] == r['origin_year'] and c['fold'] == r['outer_fold']),
                selection=reasons, source_history=history.sort('season', 'bucket').to_dicts(),
                contact_history=[{key: value for key, value in s.items() if not key.startswith('rate_') and (not key.startswith('count_') or value != 0)} for s in contact.sort('season', 'league_id').to_dicts()],
                actual_MLB_history=counts.filter((pl.col('player_id') == r['player_id']) & (pl.col('season') == r['target_year']) & (pl.col('bucket') == 'MLB')).to_dicts(),
                contact_inputs=row.select(e.info.FEATURES + ['dc_physical_exposure', 'dc_classified_exposure', 'dc_actual_leagues', 'dc_source_seasons']).to_dicts()[0],
                forecasts={a: {c: r[a + '_' + c] for c in ['rate', 'pa', 'value']} for a in ['preseason', 'translated_ridge', *e.ARMS, *[a + '_all' for a in e.ARMS]]},
                arrival_probability=r['preseason_p'], conditional_pa=r['preseason_conditional_pa'],
                actual=dict(pa=r['next_pa'], rate=r['next_relative_rate'], value=r['next_value']),
                supported_fold=r['dc_supported_fold'], active_profile_support=support.filter(pl.col('row_id') == rid).to_dicts(),
                linear_traces=traces, peers=peers(f, q, sr)))
    e.write('sensitivity-cases.json', dict(player_walkthrough_status='pending', cases=cases,
        selection_limit='Added after scores to explain declared sensitivities; no fits or tuning changed',
        input_hashes={str(p): sha256_file(p) for p in [e.Path(__file__), e.OUT / 'verification.json',
                      e.Path(verification['scored_path']), e.OUT / 'cases.json', e.OUT / 'preflight.json']}))
    for c in cases:
        print(c['player_name'], c['origin_year'], c['selection'], c['forecasts']['translated_ridge'],
              c['forecasts']['joint'], c['forecasts']['joint_all'], c['actual'], flush=True)


if __name__ == '__main__': main()
