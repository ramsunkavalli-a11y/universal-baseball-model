"""Use complete position usage, retaining old source/support artifacts unchanged."""
from collections import defaultdict
from pathlib import Path
import json
import polars as pl
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save
import audit_arm_receiving_support_v6 as audit

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reports/generated/arm-receiving-v6'
OUT=BASE/'official-scope'
PUBLIC=ROOT/'reports/model-evidence/arm-receiving-v6/official-scope'


def main():
    protections()
    assert not (OUT/'extension-review.json').exists()
    prior=json.loads((BASE/'extension-review.json').read_text())
    for group in ('input_hashes','output_hashes'):
        for p,h in prior[group].items():assert sha256_file(Path(p))==h,p
    official_audit=ROOT/'reports/generated/multiyear-hitter-components-v1/source-audit.json'
    official_note=json.loads(official_audit.read_text())['mlb_fielding']
    official_path=Path(official_note['path'])
    assert sha256_file(official_path)==official_note['sha256']
    usage=defaultdict(lambda:dict(of=0,other=0))
    for r in pl.read_parquet(official_path).filter(pl.col('season').is_between(2016,2025)).to_dicts():
        assert r['level_group']=='MLB'
        n=r['fielding_outs'] or 0
        assert n>=0
        usage[r['season'],r['player_id']]['of' if str(r['position_code']) in ('7','8','9') else 'other']+=n
    records=pl.read_parquet(BASE/'annual.parquet').to_dicts();changes=[]
    for r in records:
        if r['kind']!='arm':continue
        u=usage[r['season'],r['player_id']]
        old=r['isolated_outfield_quality_valid']
        r['native_split_of_outs']=r['of_outs'];r['native_split_other_outs']=r['other_outs']
        r['of_outs']=u['of'];r['other_outs']=u['other']
        r['scope']='outfield_only_exposure' if u['of'] and not u['other'] else (
            'mixed_position_exposure' if u['of'] else 'non_outfield_exposure')
        r['isolated_outfield_quality_valid']=bool(r['native_match'] and u['of']>0 and u['other']==0)
        r['position_scope_basis']='complete_official_fielding_history'
        if old!=r['isolated_outfield_quality_valid']:
            changes.append(dict(season=r['season'],player_id=r['player_id'],player_name=r['player_name'],
                old_flag=old,new_flag=r['isolated_outfield_quality_valid'],official_of_outs=u['of'],official_other_outs=u['other']))
    assert len(changes)==100 and all(r['old_flag'] and not r['new_flag'] for r in changes)
    OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    pl.DataFrame(records,infer_schema_length=None).write_parquet(OUT/'annual.parquet')
    files=[Path(__file__),BASE/'extension-review.json',BASE/'annual.parquet',official_audit,official_path,
           ROOT/'docs/arm-receiving-v6-official-scope-amendment.md',ROOT/'scripts/audit_arm_receiving_support_v6.py']
    report=dict(rows=len(records),scope_changes=changes,position_scope_basis='complete_official_fielding_history',
        player_walkthrough_status='complete',support_audit_allowed=True,model_fit_allowed=False,
        original_source_walkthrough=str(BASE/'extension-player-walkthrough.json'),
        no_model_fit=True,no_2026_outcomes=True,
        input_hashes={str(p):sha256_file(p) for p in files},
        output_hashes={str(OUT/'annual.parquet'):sha256_file(OUT/'annual.parquet')})
    save(OUT/'extension-review.json',report);save(PUBLIC/'extension-review.json',report)
    # Reuse the unchanged audited recipe, with explicit separate destinations.
    audit.OUT=OUT; audit.PUBLIC=PUBLIC
    audit.main()
    save(OUT/'execution-receipt.json',dict(runner_sha256=sha256_file(Path(__file__)),
         delegated_audit_sha256=sha256_file(ROOT/'scripts/audit_arm_receiving_support_v6.py'),
         output_directory=str(OUT),public_directory=str(PUBLIC),
         original_labels_unchanged=True,no_model_fit=True,no_2026_outcomes=True))
    print('Corrected position-scope flags:',len(changes))


if __name__=='__main__':main()
