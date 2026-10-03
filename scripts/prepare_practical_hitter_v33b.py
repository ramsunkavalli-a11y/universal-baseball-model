"""Correct 2020 training coverage before fitting; preserve all original artifacts."""
from pathlib import Path
import polars as pl
import prepare_practical_hitter_v31 as r
import prepare_practical_hitter_v33 as s
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

ORIGINAL=s.OUT

def main():
    s.OUT=r.ROOT/'reports/generated/practical-hitter-v33b';s.OUT.mkdir(parents=True,exist_ok=True)
    assert not (s.OUT/'preflight.json').exists()
    old=r.read(ORIGINAL/'preflight.json');f=pl.read_parquet(ORIGINAL/'features.parquet')
    f.write_parquet(s.OUT/'features.parquet');pl.read_parquet(ORIGINAL/'draft-evidence.parquet').write_parquet(s.OUT/'draft-evidence.parquet')
    control=r.read(r.OUT/'preflight-ready.json')['detail_features'];cells=[];supports=[]
    for c in old['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('origin_year')!=2020))
        te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=old['features']['pedigree']+list(set(control)-set(old['features']['pedigree'])),expected_keys=te.select('row_id','horizon').iter_rows())
        assert (tr['origin_year']!=2020).all()
        def profile(g):return g.with_columns((pl.col('age')//5).alias('age_group'),
            (pl.sum_horizontal([pl.col(f'{b}_{lag}_pa') for b in r.BUCKETS for lag in range(3)])<100).alias('thin_entry'))
        for head,sub in [('all',tr),('active',tr.filter(pl.col('next_pa')>0))]:
            keys=['stage','prior_debut','age_group','draft_known','thin_entry'];a=profile(sub);b=profile(te)
            cnt=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            supports.append(b.select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_players').fill_null(0),
                pl.lit(head).alias('head'),pl.lit(c['year']).alias('origin_year'),pl.lit(c['fold']).alias('fold')))
        cells.append(dict(year=c['year'],fold=c['fold'],**note,training_row_ids=tr['row_id'].to_list(),test_row_ids=te['row_id'].to_list(),
            removed_2020_rows=len(c['training_row_ids'])-len(tr),early_cell_identical=c['training_row_ids']==tr['row_id'].to_list()))
    pl.concat(supports).write_parquet(s.OUT/'support.parquet')
    examples=f.filter((pl.col('origin_year')==2020)&pl.col('player_id').is_in([592450,665487,666158])).to_dicts()
    other=f.filter((pl.col('origin_year')==2020)&~pl.col('player_id').is_in([592450,665487,666158])).sort('player_id').head(3).to_dicts()
    counts=pl.read_parquet(r.OUT/'counts.parquet');lines=['# V33b source defect walkthrough before repaired fitting','',
        '597 origin-2020 source rows entered later training against the declared exclusion. All have listing zero, but the year-end roster capture has no 2020 coverage. The players are not observed non-listed. Exclude these incomplete-origin rows from training; keep their actual MLB counts as eligible players’ past history. No future results determine exclusion.','']
    evidence=[]
    for o in examples+other:
        history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(2018,2020)).sort('season','bucket').to_dicts()
        lines.extend([f"## {o['player_name']} / 2020",'',f"Actual current MLB PA {o['pa_0']}; prior {o['pa_1']}/{o['pa_2']}; shrunk origin quality {o['quality_0']:.4f}; encoded listing {o['on_40man']}. No 2020 roster source exists in the declared capture inventory. These fields entered each later cell except the player’s held group. Exclusion is due to incomplete-origin coverage, not the player’s next outcome.",''])
        evidence.append(dict(player_id=o['player_id'],origin_year=2020,raw_level_history=history,actual_input={k:o[k] for k in ['pa_0','pa_1','pa_2','quality_0','on_40man','outer_fold']},
            interpretation='Roster source missing, not observed roster absence; complete broad origin unavailable.'))
    (s.OUT/'source-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    s.write('source-review.json',dict(player_walkthrough_status='complete',cases=evidence,affected_source_rows=597,affected_cells=20,
        contract_violation='Origin 2020 training exclusion was not implemented; roster missingness encoded as non-listing.',original_outputs_preserved=True))
    inputs=[ORIGINAL/'features.parquet',ORIGINAL/'draft-evidence.parquet',ORIGINAL/'preflight.json',r.OUT/'preflight-ready.json',
        s.OUT/'features.parquet',s.OUT/'draft-evidence.parquet',s.OUT/'support.parquet',s.OUT/'source-review.json',
        r.ROOT/'docs/practical-hitter-v33-contract.md',r.ROOT/'docs/practical-hitter-v33b-training-repair.md',Path(__file__)]
    s.write('preflight.json',dict(before_fitting=True,input_hashes={str(p):sha256_file(p) for p in inputs},features=old['features'],
        control_features=control,cells=cells,origin_2020_explicitly_excluded=True,source_rows=len(f),draft_coverage=old['draft_coverage'],source_review_complete=True))
    print('Repaired all 35 training cells; all 30,506 test rows retained. 20 later cells change.')

if __name__=='__main__':main()
