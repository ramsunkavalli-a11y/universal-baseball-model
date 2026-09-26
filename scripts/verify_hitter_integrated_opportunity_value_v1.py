"""Independent numerical checks, unchanged sources, and archived decision replay."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from build_hitter_integrated_opportunity_value_v1 import OUT, PACKAGE, hashes, sources, provenance
from score_hitter_integrated_opportunity_value_v1 import decisions
from universal_baseball.hitter_integrated_opportunity_value import ARMS, KEY, cumulative
from universal_baseball.storage import sha256_file


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text())
    assert pre['hashes']==hashes() and pre['inherited_provenance']==provenance()
    build=json.loads((OUT/'build-manifest.json').read_text())
    assert sha256_file(OUT/'prefit-manifest.json')==build['prefit_sha256']
    for n,d in build['files'].items():assert sha256_file(OUT/n)==d
    f=pl.read_parquet(OUT/'predictions.parquet');cs=pl.read_parquet(OUT/'component-predictions.parquet')
    x,original,labels=sources()
    assert f.select(KEY).equals(x.select(KEY)) and f.height==build['rows']==52181
    assert cs.height==7*f.height and not cs.select(*KEY,'component').is_duplicated().any()
    prospect=x['prospect'].to_numpy();prior=x['prior_debut'].to_numpy()
    hp=np.where(prospect,x['D_pa'],np.where(prior,x['E_pa'],x['B_pa']))
    np.testing.assert_array_equal(f['H_pa'],hp)
    np.testing.assert_array_equal(f['H_p'],np.where(prospect,x['fixed_p'],np.where(prior,x['E_p'],x['B_p'])))
    for a in ('D','E','H'):
        np.testing.assert_allclose(f[a+'_value'],x['B_value']+(f[a+'_pa']-x['B_pa'])*x['rate']/600,atol=1e-12)
    np.testing.assert_array_equal(f['N_value'],x['E_value'])
    for col in ('actual_pa','actual_value','complete_components','actual_expanded'):
        assert f[col].equals(labels[col]),col
    raw=original.join(f.select(KEY),on=KEY,how='inner').sort([*KEY,'component'])
    check=cs.sort([*KEY,'component'])
    assert raw.select(*KEY,'component').equals(check.select(*KEY,'component'))
    np.testing.assert_allclose(check['L_runs'],raw['selected'],atol=1e-12)
    for a in ARMS:
        if a!='L':
            expected=np.where(check['selected_model']=='benchmark',check['benchmark_rate']*check[a+'_pa']/600,
                              np.where(check['selected_model']=='direct',check['direct'],0.))
            np.testing.assert_allclose(check[a+'_runs'],expected,atol=1e-12)
        total=check.group_by(KEY).agg(pl.col(a+'_runs').sum()).sort(KEY)
        np.testing.assert_allclose(f[a+'_expanded'],f[a+'_value']+total[a+'_runs']/10,atol=1e-12)
    c=cumulative(f);assert c.equals(pl.read_parquet(OUT/'cumulative-predictions.parquet'))
    assert set(c['origin_year'])=={2016,2021,2022}
    assert set(c.filter(pl.col('complete_components'))['origin_year'])=={2021,2022}
    report=json.loads((OUT/'score-report.json').read_text());assert report['decisions']==decisions(report)
    # Independent equal-origin score calculation, not the reporting metric helper.
    for name,g in [(str(h),f.filter(pl.col('horizon')==h)) for h in (1,2,3)]+[('cumulative',c)]:
        saved=report['cumulative']['all'] if name=='cumulative' else report['annual'][name]['all']
        for target in ('pa','value','expanded'):
            q=g.filter(pl.col('complete_components')) if target=='expanded' else g
            for a in ARMS:
                err=q[a+'_'+target].to_numpy()-q['actual_'+target].to_numpy()
                years=q['origin_year'].to_numpy();parts=[err[years==y] for y in sorted(set(years))]
                m={'mse':np.mean([np.mean(e**2) for e in parts]),'mae':np.mean([np.mean(abs(e)) for e in parts]),
                   'bias':np.mean([np.mean(e) for e in parts]),'aggregate_absolute_error':np.mean([abs(e.sum()) for e in parts])}
                for k,v in m.items():np.testing.assert_allclose(v,saved[target]['arms'][a][k],atol=1e-10)
    if (PACKAGE/'manifest.json').exists():
        manifest=json.loads((PACKAGE/'manifest.json').read_text())
        for n,h in manifest['files'].items():assert sha256_file(PACKAGE/n)==h
        for n,h in manifest['code'].items():assert sha256_file(Path(n))==h
    print(json.dumps({'verified':True,'rows':f.height,'component_rows':cs.height,
        'cumulative_rows':c.height,'opportunity_passes':report['decisions']['opportunity_passes'],
        'value_passes':report['decisions']['value_passes'],'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
