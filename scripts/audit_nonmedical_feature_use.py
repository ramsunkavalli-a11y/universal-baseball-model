"""Explain the exact null result from saved trees; do not fit another variant."""
from collections import Counter

import joblib
import numpy as np
import polars as pl

from run_hitter_nonmedical_opportunity import ROOT, BASE, OUT, read, save, verify
from universal_baseball.nonmedical_opportunity import FIELDS, OBS
from universal_baseball.storage import sha256_file


def main():
    if (OUT / 'feature-use-audit.json').exists():
        raise ValueError('Preserve completed diagnostic')
    pre = read(OUT / 'preflight.json')
    verify(pre['hashes'])
    reports = {'corrected_job': read(BASE / 'fit-report.json'), 'observation': read(OUT / 'fit-report.json')}
    path = ROOT / 'scripts/audit_nonmedical_feature_use.py'
    save('feature-use-source-seal.json', dict(before_read_only_audit=True,
        code_sha256=sha256_file(path), new_fits=0))
    models, details = {}, []
    for arm, report in reports.items():
        for cell in report['cells']:
            for h in cell['heads']:
                p = ROOT / h['path']
                assert sha256_file(p) == h['sha256']
                m = joblib.load(p)
                target = set(FIELDS if arm == 'corrected_job' else OBS.values())
                all_use, relevant = Counter(), Counter()
                for trees in m._predictors:
                    for tree in trees:
                        for node in tree.nodes:
                            if not node['is_leaf']:
                                name = h['features'][int(node['feature_idx'])]
                                all_use[name] += 1
                                if name in target:
                                    relevant[name] += 1
                details.append(dict(arm=arm, head=h['head'], origin=cell['origin'], fold=cell['fold'],
                    model_sha256=h['sha256'], all_feature_split_counts=dict(all_use),
                    tested_feature_split_counts={n: relevant[n] for n in sorted(target)}))
                models[arm, cell['origin'], cell['fold'], h['head']] = m
    node_matches, baseline_matches = 0, 0
    for cell in reports['observation']['cells']:
        for h in cell['heads']:
            a = models['corrected_job', cell['origin'], cell['fold'], h['head']]
            b = models['observation', cell['origin'], cell['fold'], h['head']]
            assert np.array_equal(a._baseline_prediction, b._baseline_prediction)
            baseline_matches += 1
            assert len(a._predictors) == len(b._predictors)
            for aa, bb in zip(a._predictors, b._predictors, strict=True):
                assert len(aa) == len(bb)
                for at, bt in zip(aa, bb, strict=True):
                    assert np.array_equal(at.nodes, bt.nodes)
                    node_matches += 1
    q = pl.read_parquet(OUT / 'predictions.parquet')
    prediction_checks = 0
    for suffix in ['raw_p', 'raw_conditional_pa', 'p', 'conditional_pa', 'pa', 'rate', 'value']:
        assert np.array_equal(q['corrected_job_' + suffix], q['observation_' + suffix])
        prediction_checks += q.height
    assert all(not any(d['tested_feature_split_counts'].values()) for d in details)
    result = dict(status='exact_null_explained_by_unused_tested_inputs', models_inspected=len(details),
        paired_initial_prediction_matches=baseline_matches, paired_tree_node_array_matches=node_matches,
        exact_prediction_field_checks=prediction_checks, tested_feature_splits=0,
        source_changed_rows=122, changed_evaluated_origins=89, new_fits=0,
        clinical_or_business_value_of_availability_rejected=False,
        interpretation='The eight inputs are never used in either saved tree ensemble. This contrast cannot validate or reject their real baseball importance.',
        cells=details, code_sha256=sha256_file(path),
        predictions_sha256=sha256_file(OUT / 'predictions.parquet'))
    save('feature-use-audit.json', result)
    print(__import__('json').dumps({k: v for k, v in result.items() if k != 'cells'}), flush=True)


if __name__ == '__main__':
    main()
