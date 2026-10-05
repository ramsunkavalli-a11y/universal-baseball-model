"""Reproduce all five historical profiles and extend source-only forecast inputs."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.hitter_forecast_translation import translation_inputs
from universal_baseball.hitter_talent_bridge import EVENTS
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'reports/generated/hitter-base-inputs-2025-reviewed'
OUT = ROOT/'reports/generated/hitter-translation-inputs-2025'


def read(p): return json.loads(p.read_text(encoding='utf8'))


def write(p,o):
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(o,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def independent_profile(history, graph):
    """Independent event extraction and CLR adjustment, no bridge helpers."""
    supported=0.;total=0.;weighted=np.zeros(8);offsets=graph['offsets']
    for r in history.iter_rows(named=True):
        weight=(1.,.8,.6)[2025-r['season']];pa=r['plate_appearances'];total+=weight*pa
        if pa == 0 or r['bucket'] not in offsets:continue
        v=[r['strike_outs'],r['unintentional_walks'],r['hit_by_pitch'],
           r['babip_hits']-r['doubles']-r['triples'],r['doubles'],r['triples'],r['home_runs']]
        c=np.asarray([pa-sum(v),*v],dtype=float)
        assert (c>=0).all() and c.sum()==pa
        raw=np.log((c+.5)/(pa+4));z=raw-raw.mean()-np.asarray(offsets[r['bucket']]);p=np.exp(z-z.max());p/=p.sum()
        weighted+=weight*pa*p;supported+=weight*pa
    prior=np.asarray(graph['mlb_reference']);p=weighted/supported if supported else prior
    return p,supported,total,(p-prior)/.1 if supported else np.zeros(8)


def main():
    review=read(BASE/'review.json');assert review['historical_model_input_equivalence'] and review['source_player_walkthrough_status']=='complete'
    for kind in ['input_hashes','output_hashes']:
        for p,h in review[kind].items():assert sha256_file(Path(p))==h,p
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'review.json').exists()
    count_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet';counts=pl.read_parquet(count_path)
    historical_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet'
    historical=pl.read_parquet(historical_path);current_path=BASE/'assembled-before-translation.parquet';current=pl.read_parquet(current_path)
    frame=pl.concat([historical.select('row_id','player_id','origin_year'),current.select('row_id','player_id','origin_year')])
    assert len(historical)==63282 and len(current)==4030 and frame['row_id'].n_unique()==len(frame)
    cases=read(BASE/'completed-player-walks.json')['cases'];case_ids=sorted({walk['player_id'] for c in cases for walk in [c['primary'],*c['exposure_peers']]})
    fixed_rows=[];fold_reviews=[];input_paths=[count_path,historical_path,current_path,BASE/'review.json',BASE/'completed-player-walks.json',
        Path(__file__),ROOT/'src/universal_baseball/hitter_forecast_translation.py',ROOT/'src/universal_baseball/hitter_talent_bridge.py',
        ROOT/'docs/hitter-2025-translation-input-contract.md']
    hashes={str(p):sha256_file(p) for p in input_paths}
    for fold in range(5):
        fp=OUT/f'forecast-inputs-{fold}.parquet';np_=OUT/f'fold-{fold}.json'
        assert not fp.exists() and not np_.exists(), 'Do not overwrite fold outputs'
        profiles,graphs=translation_inputs(counts,frame,held_fold=fold,source_cutoff=2025)
        names=[c for c in profiles.columns if c!='row_id']
        old_path=ROOT/f'reports/generated/hitter-talent-bridge-v74/features-{fold}.parquet'
        old_note_path=old_path.parent/f'translation-{fold}.json';old_note=read(old_note_path)
        assert sha256_file(old_path)==old_note['features_sha256']
        a=profiles.filter(pl.col('row_id').is_in(historical['row_id'])).sort('row_id');b=pl.read_parquet(old_path,columns=['row_id',*names]).sort('row_id')
        assert a['row_id'].equals(b['row_id'])
        for c in names:
            if a[c].dtype in [pl.Float32,pl.Float64]:
                assert np.allclose(a[c].to_numpy(),b[c].to_numpy(),rtol=0,atol=1e-12,equal_nan=True), (fold,c)
            else:assert a[c].equals(b[c],check_dtypes=False),(fold,c)
        assert graphs[:-1]==old_note['graphs'], 'Historical graphs changed with new sources'
        assert graphs[-1]['cutoff']==2025
        q=current.join(profiles.filter(pl.col('row_id').is_in(current['row_id'])),on='row_id',validate='1:1')
        assert q.select(current.columns).equals(current) and not any(c.startswith('next_') for c in q.columns)
        q.write_parquet(fp)
        walks=[]
        for pid in case_ids:
            r=q.filter(pl.col('player_id')==pid).row(0,named=True)
            hist=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(2023,2025))
            p,supported,total,d=independent_profile(hist,graphs[-1])
            assert np.allclose(p,[r[f'translated_probability_{e}'] for e in EVENTS],atol=1e-12,rtol=0)
            assert np.allclose(d,[r[f'translated_{e}'] for e in EVENTS],atol=1e-12,rtol=0)
            assert np.isclose(supported,r['translation_supported_pa']) and np.isclose(total,r['translation_total_pa'])
            assert r['translated_missing']==float(supported==0)
            walks.append(dict(player_id=pid,fold=fold,player_name=r['player_name'],stage=r['stage'],source_history=hist.to_dicts(),
                actual_profile={c:r[c] for c in names},independent_probability=p.tolist(),
                judgments=['Source probabilities and supported exposure reconstruct independently from counts and graph offsets.',
                    'No supported recent production: prior/missing indicators are inputs, not proof of zero future MLB ability.' if supported==0 else
                    'Transported source evidence exists; it does not eliminate sampling, promotion-selection or park uncertainty.'],
                source_review_complete=True,prediction_review='Pending candidate fitting; no future outcomes used.'))
        fixed_rows.extend(walks)
        note=dict(fold=fold,source_cutoff=2025,profiles_matched=63282,fields_matched=len(names),graphs=graphs,
            historical_graphs_unchanged=True,forecast_rows=len(q),forecast_missing=int(q['translated_missing'].sum()),
            source_walks=len(walks),forecast_input_sha256=sha256_file(fp),
            input_hashes={**hashes,str(old_path):sha256_file(old_path),str(old_note_path):sha256_file(old_note_path)},
            candidate_fitted=False,protected_outcomes_used=False)
        write(np_,note);fold_reviews.append({k:note[k] for k in ['fold','profiles_matched','fields_matched','forecast_rows','forecast_missing','source_walks']})
        print(f'Fold {fold}: all historical profiles/graphs unchanged; {len(q)} new source-only inputs; {len(walks)} independent player walks.',flush=True)
    write(OUT/'completed-player-walks.json',dict(walks=fixed_rows,source_only=True,protected_outcomes_used=False))
    write(OUT/'review.json',dict(source_review_status='complete',folds=fold_reviews,historical_rows_per_fold=63282,
        historical_graphs_unchanged=True,forecast_population=4030,source_walks=len(fixed_rows),
        qualification='Own-origin cross-level evidence, not park-neutral/selection-corrected MLE or a forecast accuracy certification.',
        candidate_ready_to_fit=False,candidate_frozen=False,protected_outcomes_used=False,
        remaining=['availability evidence','qualified foreign/new entrant coverage','actual forecast support','production fitting and replay'],
        input_hashes=hashes,output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix in ['.parquet','.json']}))


if __name__=='__main__':main()
