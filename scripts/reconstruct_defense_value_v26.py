"""Replay the archived unchanged ledger in memory, requiring byte identity."""
from collections import defaultdict
from io import BytesIO
from hashlib import sha256
import polars as pl
from run_defense_reference_history_v26 import ROOT, NATIVE, V12, BRIDGE, sources, read, PUBLIC, ARMS
from universal_baseball.defense_reference_history import history, origin_reference


def reconstruct():
    native, people, refs, measured, official = sources()
    f=pl.read_parquet(V12/'predictions.parquet')
    bridge={r['row_id']:r for r in pl.read_parquet(BRIDGE).to_dicts()}
    cells=defaultdict(list)
    columns=['row_id','channel','history_rate','repair_history','actual_official_exposure','actual_runs']
    for c in pl.read_parquet(V12/'channel-predictions.parquet',columns=columns).filter(
            pl.col('channel').is_in(['range_7','range_8','range_9'])).to_dicts():cells[c['row_id']].append(c)
    values=[]
    for r in f.to_dicts():
        y,pid=r['origin_year'],r['player_id'];b=bridge[r['row_id']];cs=cells[r['row_id']]
        old_OF=sum(c['repair_history'] for c in cs)
        new_OF=offset=0.;observed_offset=0.;unknown=False
        for c in cs:
            p=int(c['channel'][-1]);h=history(people[pid],y,p,pid%5,refs);ref=origin_reference(y,p,pid%5,refs)
            n=b[f'repair_{p}'];offset+=n*ref/1500;new_OF+=n*h['centered']/1500
            source=next((s for s in people[pid] if s['season']==y+1 and s['position']==p),None)
            if c['actual_official_exposure']==0:aoff=0.
            elif c['actual_runs'] is None:aoff=None;unknown=True
            else:
                assert source is not None and source['range_valid']
                aoff=measured[y+1,p]*source['native_outs']/1500
            if aoff is not None:observed_offset+=aoff
        outside=r['repair_history_defense']-old_OF
        complete=r['actual_defense'] is not None;assert not complete or not unknown
        actual=None if not complete else r['actual_defense']-observed_offset
        rec=dict(row_id=r['row_id'],player_id=pid,player_name=r['player_name'],origin_year=y,stage=r['stage'],age=r['age'],
            expected_PA=r['expected_PA'],actual_PA=r['actual_PA'],actual_fielding_outs=r['actual_fielding_outs'],
            position_runs=r['repair_position_runs'],actual_position_runs=r['actual_position_runs'],
            batting_forecast=r['batting_forecast'],actual_batting=r['actual_batting'],non_OF_history_runs=outside,
            legacy_defense=r['repair_history_defense']-offset,centered_defense=outside+new_OF,neutral_defense=outside,
            actual_defense=actual,actual_expanded=None if actual is None else r['actual_batting']+(actual+r['actual_position_runs'])/10,
            original_defense=r['repair_history_defense'],original_expanded=r['repair_history_expanded'],
            projected_reference_offset=offset,observed_reference_offset=None if unknown else observed_offset,
            unknown_target_channels=r['unknown_target_channels'])
        for a in ARMS:rec[a+'_expanded']=r['batting_forecast']+(r['repair_position_runs']+rec[a+'_defense'])/10
        values.append(rec)
    assert len(values)==12432
    buf=BytesIO();pl.DataFrame(values).write_parquet(buf)
    digest=sha256(buf.getvalue()).hexdigest()
    expected=next(h for p,h in read(PUBLIC/'preflight.json.gz')['output_hashes'].items()
                  if p.endswith('value-predictions.parquet'))
    assert digest==expected,('Baseline byte identity failed',digest,expected)
    return values,dict(rows=len(values),saved_sha256=expected,reconstructed_sha256=digest,
                       byte_identity=True,archive_read=False,new_fit=False)


if __name__=='__main__':
    values,receipt=reconstruct();print(receipt)
