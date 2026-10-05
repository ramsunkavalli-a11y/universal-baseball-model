"""Narrow interrupted-fit recovery; preserve the originally sealed runner bytes."""
from pathlib import Path
import joblib
import numpy as np
from prepare_hitter_evidence_representation import ROOT, OUT, read, save
from universal_baseball.storage import sha256_file


def load_or_fit(path, model, x, y, w):
    if path.exists():
        recovered=joblib.load(path)
        assert type(recovered)==type(model)
        assert recovered.get_params()==model.get_params()
        assert recovered.n_features_in_==x.shape[1]
        return recovered
    return model.fit(x,y,sample_weight=w)


def valid_outputs(q):
    for arm in ['repaired_domestic','repaired_overseas']:
        for suffix in ['raw_p','p','raw_conditional_pa','conditional_pa','pa','rate','value']:
            assert np.isfinite(q[arm+'_'+suffix].to_numpy()).all()
        for suffix, needed in [('workload_only_value','current_rate'),('talent_only_value','current_pa')]:
            column=q[arm+'_'+suffix]
            assert column.is_null().equals(q[needed].is_null())
            values=column.drop_nulls().to_numpy()
            assert np.isfinite(values).all()
            assert not q.filter(~__import__('polars').col('source_addition'))[arm+'_'+suffix].is_null().any()


def main():
    original=ROOT/'scripts/fit_hitter_evidence_representation.py'
    seal=read(OUT/'fit-seal.json')
    assert sha256_file(original)==seal['runner_sha256']
    paths=[Path(__file__),ROOT/'docs/hitter-evidence-representation-fit-recovery.md',original]
    orphans=[OUT/n for n in ['common-participation-2016-2.joblib','common-conditional_pa-2016-2.joblib',
                             'repaired-domestic-rate-2016-2.joblib','repaired-overseas-rate-2016-2.joblib']]
    paths+=orphans
    recovery=dict(original_fit_seal_sha256=sha256_file(OUT/'fit-seal.json'),
                  qualification='Four interrupted-cell model hashes captured after interruption, not at creation',
                  hashes={str(p):sha256_file(p) for p in paths})
    if (OUT/'resume-seal.json').exists():assert read(OUT/'resume-seal.json')==recovery
    else:save('resume-seal.json',recovery)
    source=original.read_text(encoding='utf8')
    replacements=[
        ("m.fit(sub.select(names).to_numpy(),sub[target].to_numpy(),sample_weight=weights(sub))",
         "m=load_or_fit(OUT/f'common-{head}-{y}-{k}.joblib',m,sub.select(names).to_numpy(),sub[target].to_numpy(),weights(sub))"),
        ("m.fit(safe_matrix(active,names),active['actual_relative_rate'].to_numpy(),sample_weight=w)",
         "m=load_or_fit(OUT/f'repaired-{arm}-rate-{y}-{k}.joblib',m,safe_matrix(active,names),active['actual_relative_rate'].to_numpy(),w)"),
        ("assert not p.exists();joblib.dump(m,p,compress=3)",
         "joblib.dump(m,p,compress=3) if not p.exists() else None"),
        ("assert np.isfinite(q.select([n for n in q.columns if n.startswith('repaired_')]).to_numpy()).all()",
         "valid_outputs(q)")]
    for old,new in replacements:
        assert source.count(old)==(2 if old.startswith('assert not p.exists()') else 1)
        source=source.replace(old,new)
    namespace=dict(__file__=str(original),__name__='preserved_fixed_runner',load_or_fit=load_or_fit,valid_outputs=valid_outputs)
    exec(compile(source,str(original),'exec'),namespace)
    namespace['main']()
    for p in orphans:assert sha256_file(p)==recovery['hashes'][str(p)]


if __name__=='__main__':main()
