import importlib.util
import sys
from pathlib import Path
import polars as pl

spec=importlib.util.spec_from_file_location('rate_audit',Path(__file__).parents[1]/'scripts/audit_hitter_rate_support.py')
audit=importlib.util.module_from_spec(spec)
script_path=str(Path(__file__).parents[1]/'scripts')
sys.path.insert(0,script_path)
try:
    spec.loader.exec_module(audit)
finally:
    sys.path.remove(script_path)


def test_dominant_level_preserves_absence_and_does_not_use_future():
    data={b+'_0_pa':[0,10,0] for b in audit.BUCKETS}
    data['DSL_0_pa']=[167,10,0];data.update(age=[16.,23.,40.],age_unknown=[0,0,1])
    f=pl.DataFrame(data)
    a=audit.tagged(f)
    assert a['dominant_level'].to_list()==['DSL','MLB','absent']
    assert a['audit_age_band'].to_list()==['<=17','21-23','unknown']
    assert audit.tagged(f.with_columns(pl.lit(700).alias('next_pa'))).select(a.columns).equals(a)
