"""Same-fit source-removal probes, not new forecasts or predictive experiments."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from prepare_hitter_evidence_representation import ROOT, GEN, OUT, read, save
from prepare_practical_hitter_v33 import safe_matrix
from universal_baseball.hitter_evidence_representation import RECENCY, minor_evidence, FOREIGN_TALENT_FEATURES
from universal_baseball.storage import sha256_file


def main():
    fit=read(OUT/'fit-report.json');cases=read(OUT/'reviewed-cases.json')['cases']
    counts=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet');results=[]
    for pid,y,bucket in [(670541,2018,'DSL'),(643217,2017,'Aminus')]:
        case=next(c for c in cases if c['origin']['player_id']==pid and c['origin']['origin_year']==y)
        a=case['actual_model_inputs'];k=a['outer_fold'];one=pl.DataFrame([a])
        cell=next(c for c in fit['cells'] if c['origin']==y and c['fold']==k)
        h=next(h for h in cell['heads'] if h['head']=='rate' and h['arm']=='overseas')
        assert sha256_file(Path(h['path']))==h['sha256'];m=joblib.load(h['path']);names=h['features']
        history=counts.filter(pl.col('player_id')==pid).to_dicts()
        graph=next(g for g in read(GEN/f'hitter-talent-bridge-v74/translation-{k}.json')['graphs'] if g['cutoff']==y)
        nmlb=sum(RECENCY[lag]*a[f'pa_{lag}'] for lag in range(3))
        original,note=minor_evidence(history,graph,origin=y,mlb_exposure=nmlb,foreign_exposure=0.)
        assert all(np.isclose(a[n],v,atol=1e-12) for n,v in original.items())
        removed=[r for r in history if r['bucket']!=bucket]
        new,newnote=minor_evidence(removed,graph,origin=y,mlb_exposure=nmlb,foreign_exposure=0.)
        probe=one.with_columns([pl.lit(v).alias(n) for n,v in new.items()])
        before=float(m.predict(safe_matrix(one,names))[0]);after=float(m.predict(safe_matrix(probe,names))[0])
        assert np.isclose(before,case['origin']['repaired_overseas_rate'],atol=1e-10)
        results.append(dict(player_id=pid,name=a['player_name'],origin=y,removed_level=bucket,
                            baseline_rate=before,coherent_source_removed_rate=after,change=after-before,
                            old_precision_PA=note['supported_precision_PA'],new_precision_PA=newnote['supported_precision_PA'],
                            features_changed=list(new),model_sha256=h['sha256'],
                            qualification='Same fitted parameters and recomputed coherent minor profile; artificial history, no validation or deployment'))
    for pid,y in [(808982,2024),(660271,2018),(807799,2024),(673548,2021),(807799,2022)]:
        c=next(c for c in cases if c['origin']['player_id']==pid and c['origin']['origin_year']==y)
        effects=c['mechanics']['overseas_rate']['feature_effects']
        production=sum(t['effect'] for t in effects if t['feature'] in FOREIGN_TALENT_FEATURES)
        control=sum(t['effect'] for t in effects if t['feature'].startswith('evidence_foreign_') and t['feature'] not in FOREIGN_TALENT_FEATURES)
        results.append(dict(player_id=pid,name=c['origin']['player_name'],origin=y,
                            baseline_rate=c['origin']['repaired_overseas_rate'],foreign_production_effect=production,
                            foreign_exposure_and_missingness_effect=control,
                            qualification='Exact linear accounting; production neutrality with exposure unchanged is a mechanics probe, not an alternative forecast'))
    save('mechanics-probes.json',dict(new_fits=0,results=results,protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'reviewed-cases.json',OUT/'fit-report.json']}))
    for r in results:print(r)


if __name__=='__main__':main()
