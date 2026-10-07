"""Explicit sibling rerun: preserve original recipes, replace calendar only."""
from pathlib import Path
import json
import polars as pl

import repair_defense_role_population_v16 as original
from universal_baseball.defense_role_calendar import completed_schedule_context
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import save, protections

ROOT=original.ROOT
DEST=original.OUT/'calendar-repair'
PUBLIC=original.PUBLIC/'calendar-repair'


def write(name,value):
    DEST.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    save(DEST/name,value);save(PUBLIC/name,value)


def main():
    protections()
    inputs=[Path(__file__),ROOT/'docs/defense-role-v16-calendar-amendment.md',
        ROOT/'src/universal_baseball/defense_role_calendar.py',
        ROOT/'scripts/repair_defense_role_population_v16.py',
        original.DEST/'source-review.json']
    write('calendar-execution-seal.json',dict(before_reexecution=True,
        replaced_function='schedule_context; detailed completed states only',
        all_other_source_rules_unchanged=True,no_fits=True,
        input_hashes={str(p):sha256_file(p) for p in inputs}))
    # Reuse the sealed source workflow; substitution and paths are explicit.
    original.DEST=DEST;original.write=write;original.schedule_context=completed_schedule_context
    original.main()
    old=pl.read_parquet(original.OUT/'scope-repair/current-role-source-features.parquet').sort('row_id')
    new=pl.read_parquet(DEST/'current-role-source-features.parquet').sort('row_id')
    fields=[c for c in old.columns if '_full_year_' in c]+['row_id','player_id','origin','fold']
    assert old.select(fields).equals(new.select(fields))
    write('calendar-execution-complete.json',dict(annual_vectors_and_membership_unchanged=True,
        source_receipt_sha256=sha256_file(DEST/'source-review.json'),no_fits=True,
        supersedes_periods_only=str(original.OUT/'scope-repair/source-review.json')))
    protections()


if __name__=='__main__':main()
