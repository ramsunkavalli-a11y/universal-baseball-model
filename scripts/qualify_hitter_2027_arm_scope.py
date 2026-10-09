"""Carry the previously reviewed complete-official-position arm rule into 2026."""
from collections import defaultdict
from pathlib import Path
import json
import polars as pl
from universal_baseball.older_fielding_source import outs_from_baseball_innings
from universal_baseball.storage import sha256_file
from reconcile_hitter_2027_nonbatting_sources import read_rows,OUT,PUBLIC,write_once


def main():
    path=OUT/'arm-official-scope-annual.parquet';assert not path.exists()
    review=json.loads((PUBLIC/'nonbatting-source-player-review.json').read_text())
    assert review['source_approved_for_estimation']
    usage=defaultdict(lambda:dict(of=0,other=0))
    for r in read_rows('official-fielding'):
        pos=int(r['position']['code']);pid=int(r['player']['id'])
        usage[pid]['of' if pos in (7,8,9) else 'other']+=outs_from_baseball_innings(r['stat']['innings'])
    rows=pl.read_parquet(OUT/'arm-receiving-annual.parquet').filter(pl.col('kind')=='arm').to_dicts()
    changes=[]
    for r in rows:
        u=usage[r['player_id']];old=r['isolated_outfield_quality_valid']
        r['native_split_of_outs']=r['of_outs'];r['native_split_other_outs']=r['other_outs']
        r['of_outs']=u['of'];r['other_outs']=u['other']
        r['scope']='outfield_only_exposure' if u['of'] and not u['other'] else (
            'mixed_position_exposure' if u['of'] else 'non_outfield_exposure')
        r['isolated_outfield_quality_valid']=bool(r['native_match'] and u['of']>0 and u['other']==0)
        r['position_scope_basis']='complete_official_fielding_history'
        if old!=r['isolated_outfield_quality_valid']:changes.append(r)
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(path)
    write_once(PUBLIC/'arm-official-scope-review.json',dict(
        source_approved_for_estimation=True,recipe='Unchanged V6 complete official position scope',
        rows=len(rows),changes=changes,position_scope_basis='All official positive-out positions, not just returned native event rows',
        player_walkthrough_status='complete',changes_interpretation='These players have non-outfield usage; all-position runner opportunities cannot be called an isolated outfield denominator. Original arm credit is retained, not set to zero.',
        hashes={str(p):sha256_file(p) for p in [path,OUT/'official-fielding-rows.json.gz',OUT/'arm-receiving-annual.parquet',Path(__file__)]}))
    print(f'Official arm scope: {len(rows)} players, {len(changes)} corrected flags')


if __name__=='__main__':main()
