"""Repair only a deterministic value product, preserving all sealed fitted heads."""
from pathlib import Path
import json

import numpy as np
import polars as pl

from prepare_hitter_shared_events import OUT,ROOT,read,save,verify
from universal_baseball.storage import sha256_file


def main():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    original=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet')==original['predictions_sha256']
    assert not (OUT/'review-receipt.json').exists()
    receipt=OUT/'value-correction.json'
    if not receipt.exists():
        q=pl.read_parquet(OUT/'predictions.parquet')
        corrected=q.with_columns(*[(pl.col(a+'_pa')*(pl.col(a+'_rate')/600+pl.col('origin_replacement_rate'))).alias(a+'_value') for a in ['shared_domestic','shared_foreign']])
        unchanged=[n for n in q.columns if n not in ['shared_domestic_value','shared_foreign_value']]
        assert corrected.select(unchanged).equals(q.select(unchanged))
        corrected.write_parquet(OUT/'compatible-predictions.parquet')
        save('compatible-fit-report.json',dict(original, predictions_sha256=sha256_file(OUT/'compatible-predictions.parquet')))
        save('value-correction.json',dict(original_predictions_sha256=sha256_file(OUT/'predictions.parquet'),
            compatible_predictions_sha256=sha256_file(OUT/'compatible-predictions.parquet'),
            maximum_absolute_value_change={a:float(np.max(abs((corrected[a+'_value']-q[a+'_value']).to_numpy()))) for a in ['shared_domestic','shared_foreign']},
            fitted_heads_changed=0,features_changed=0,nonvalue_columns_exact=True,
            hashes={str(p):sha256_file(p) for p in [Path(__file__),ROOT/'docs/hitter-shared-event-value-correction.md',OUT/'compatible-fit-report.json',OUT/'compatible-predictions.parquet']}))
    else:verify(read(receipt)['hashes'])
    source=(ROOT/'scripts/review_hitter_shared_events.py').read_text(encoding='utf8')
    replacements=[("OUT/'predictions.parquet'","OUT/'compatible-predictions.parquet'"),
        ("OUT/'fit-report.json'","OUT/'compatible-fit-report.json'"),
        ("['predictions.parquet','scores.json'","['compatible-predictions.parquet','scores.json'")]
    counts={}
    for old,new in replacements:
        counts[old]=source.count(old);assert counts[old]==(2 if old=="OUT/'predictions.parquet'" else 1)
        source=source.replace(old,new)
    if not (OUT/'review-correction-seal.json').exists():
        save('review-correction-seal.json',dict(original_review_sha256=sha256_file(ROOT/'scripts/review_hitter_shared_events.py'),
            correction_runner_sha256=sha256_file(Path(__file__)),in_memory_path_replacements=counts,new_model_fits=0))
    namespace=dict(__name__='__main__',__file__=str(ROOT/'scripts/review_hitter_shared_events.py'))
    exec(compile(source,str(ROOT/'scripts/review_hitter_shared_events.py'),'exec'),namespace)


if __name__=='__main__':main()
