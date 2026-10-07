"""Preserve failed audit; explicitly separate legacy assembly and reference folds."""
from pathlib import Path
import polars as pl
import audit_defense_reference_v25 as audit

ROOT = Path(__file__).resolve().parents[1]
_read_parquet = pl.read_parquet
_write = audit.write
_paths = audit.input_paths
original_bridge = _read_parquet(audit.BRIDGE)
original_folds = {r['row_id']: r['outer_fold'] for r in original_bridge.select(['row_id','outer_fold']).to_dicts()}


def read_parquet(path, *args, **kwargs):
    q = _read_parquet(path, *args, **kwargs)
    if Path(path).resolve() == audit.BRIDGE.resolve():
        q = q.with_columns(pl.col('outer_fold').alias('assembly_outer_fold'),
                           (pl.col('player_id') % 5).alias('outer_fold'))
    return q


def write(path, value):
    value['fold_semantics'] = 'Assembly fold retained; reference fold is player ID modulo five and excludes every person in that group.'
    if path.name == 'player-walks.json.gz':
        for case in value['cases']:
            for rec in case['records']:
                rid = rec['forecast']['row_id']
                role = rec['origin_role']
                role['reference_fold'] = role.pop('outer_fold')
                role['assembly_outer_fold'] = original_folds[rid]
    _write(path, value)


def paths():
    return [*_paths(), Path(__file__), ROOT/'docs/defense-reference-v25-fold-amendment.md',
            ROOT/'docs/defense-reference-v25-execution-note.md']


if __name__ == '__main__':
    audit.OUT = ROOT/'reports/generated/defense-reference-v25/fold-repair'
    audit.PUBLIC = ROOT/'reports/model-evidence/defense-reference-v25/fold-repair'
    audit.pl.read_parquet = read_parquet
    audit.write = write
    audit.input_paths = paths
    audit.main()
