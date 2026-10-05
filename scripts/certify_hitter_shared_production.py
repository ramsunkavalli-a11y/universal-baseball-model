"""Independent source-profile arithmetic before the fixed fit, no labels used."""
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.hitter_shared_production import FEATURES
from universal_baseball.hitter_evidence_representation import check_cutoff
from run_hitter_shared_production import ROOT,OUT,read,save,verify,source_data,FIXED_NAMES


def main():
    assert not (OUT/'source-review.json').exists()
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);assert pre['checks_before_fits']==105
    doc=ROOT/'docs/hitter-shared-production-source-review.md';assert doc.exists()
    walks=read(OUT/'source-walks.json');assert {(r['player_name'],r['origin_year']) for r in walks}==set(FIXED_NAMES)
    raw,history,sources,foreign=source_data();checks=0;profile_values=0
    for k in range(5):
        f=pl.read_parquet(OUT/f'features-{k}.parquet');assert f.height==63314
        assert f['origin_year'].max()==2024 and f['target_year'].max()==2025
        event=f.select(FEATURES[:8]).to_numpy();assert np.allclose(event.sum(1),0,atol=1e-10)
        mass=np.expm1(f['shared_log_exposure'].to_numpy()*np.log(1201))
        assert np.allclose(f['shared_reliability'],mass/(1200+mass),atol=1e-12)
        assert ((f['shared_supported_fraction']>=0)&(f['shared_supported_fraction']<=1+1e-12)).all()
        for r in f.iter_rows(named=True):check_cutoff(r,sources.get(f'{r["origin_year"]}:{r["player_id"]}'))
        for g in read(OUT/f'graphs-{k}.json').values():
            assert g['max_source_year']<=g['cutoff'] and k in g['excluded_folds']
            assert all(player_fold(pid) not in g['excluded_folds'] for pid in g['people']+g['mlb_reference_people'])
        for c in [c for c in pre['cells'] if c['fold']==k]:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
            assert not set(tr['player_id']) & set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and 2020 not in tr['target_year']
        profile_values+=f.height*10
    for r in walks:
        s=r['source'];ref=np.asarray(s['reference']);num=1200*ref.copy();mass=0.
        for c in s['contributions']:
            if c['source']!='foreign':
                h=next(h for h in r['raw_history'] if h['season']==c['season'] and h['bucket']==c['bucket'])
                known=np.array([h['strike_outs'],h['unintentional_walks'],h['hit_by_pitch'],
                    h['babip_hits']-h['doubles']-h['triples'],h['doubles'],h['triples'],h['home_runs']],float)
                cnt=np.r_[h['plate_appearances']-known.sum(),known]
                assert cnt.min()>=0 and cnt.sum()==h['plate_appearances']
                g=read(OUT/f'graphs-{player_fold(h["player_id"])}.json')[f'{r["origin_year"]}:{player_fold(h["player_id"])}']
                z=np.log((cnt+.5)/(cnt.sum()+4));z-=z.mean();z-=np.asarray(g['offsets'][c['bucket']]);z-=z.max();p=np.exp(z);p/=p.sum()
                assert np.isclose(c['precision_PA'],[1,.8,.6][r['origin_year']-h['season']]*cnt.sum())
            else:
                # Use the sealed profile's declared identity, not a name lookup.
                f=pl.read_parquet(OUT/'features-0.parquet').filter(pl.col('row_id')==r['row_id']).row(0,named=True)
                fp=foreign[(f'{r["origin_year"]}:{f["player_id"]}',f['outer_fold'])]
                z=np.log(c['original_probability'])-np.log(fp['MLB_reference'])+np.log(ref);z-=z.max();p=np.exp(z);p/=p.sum()
            assert np.allclose(p,c['probability'],atol=1e-12)
            num+=c['precision_PA']*p;mass+=c['precision_PA'];checks+=1
        expected=(num/(1200+mass)-ref)/.1
        assert np.allclose(expected,[r['features'][n] for n in FEATURES[:8]],atol=1e-12)
    save('source-review.json',dict(source_walkthrough_status='complete',approved_for_fit=True,
        independently_reconstructed_contributions=checks,all_matrix_profile_values_checked=profile_values,
        graph_exclusions_checked=True,information_dates_checked=True,checks_before_fits=105,
        protected_outcomes_used=False,deployment_approved=False,hashes={str(p):sha256_file(p) for p in [
            Path(__file__),doc,OUT/'source-walks.json',OUT/'preflight.json']}))
    print('Source walkthrough and independent arithmetic certified; fixed historical fit may proceed.')


if __name__=='__main__':main()
