"""Explicit dependency injection for an otherwise identical shared-head runner."""
from pathlib import Path
from functools import partial
import sys
import numpy as np
import polars as pl
from universal_baseball.baseball_unit_scaler import BaseballUnitScaler
from universal_baseball.storage import sha256_file
import evaluate_hitter_prospect_pooling_v54 as runner

ROOT=runner.ROOT;PRIOR=runner.OUT;OUT=ROOT/'reports/generated/practical-hitter-prospect-units-v55'


def prepare():
    assert runner.read(PRIOR/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists()
    pre=runner.read(PRIOR/'preflight.json')
    assert all(sha256_file(Path(p))==h for p,h in pre['input_hashes'].items())
    source=pl.read_parquet(PRIOR/'features.parquet')
    transformer=BaseballUnitScaler(pre['features']).fit(source.select(pre['features']).to_numpy())
    assert np.isfinite(transformer.transform(source.select(pre['features']).to_numpy())).all()
    OUT.mkdir(parents=True,exist_ok=True);source.write_parquet(OUT/'features.parquet')
    pre['input_hashes'].update({str(p):sha256_file(p) for p in [PRIOR/'predictions.parquet',PRIOR/'report.json',PRIOR/'preflight.json',
        OUT/'features.parquet',Path(__file__),ROOT/'src/universal_baseball/baseball_unit_scaler.py',ROOT/'docs/practical-hitter-prospect-units-v55-contract.md']})
    pre.update(fixed_unit_scaling=True,transformed_inputs_finite=True,source_population_labels_unchanged=True,
        profile_checks_reused_from_actual_identical_subsets=True,
        fixed_references=transformer.mean_.tolist(),fixed_scales=transformer.scale_.tolist())
    runner.OUT=OUT;runner.write('preflight.json',pre)
    print('Identical actual subset checks and fixed-unit transform saved before fitting.',flush=True)


def fit():
    pre=runner.read(OUT/'preflight.json')
    # Only the affine transform constructor changes. Original runner is hashed,
    # weights/settings and outputs are preserved; saved pipelines store the class.
    runner.OUT=OUT
    runner.StandardScaler=partial(BaseballUnitScaler,features=pre['features'])
    runner.fit()


if __name__=='__main__':{'prepare':prepare,'fit':fit}[sys.argv[1]]()
