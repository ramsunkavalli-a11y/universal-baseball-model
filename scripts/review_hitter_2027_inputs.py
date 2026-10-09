"""Source-to-input player checks and held-player 2027 translation assembly."""
import gzip
import json
import numpy as np
import polars as pl
from pathlib import Path
from universal_baseball.hitter_origin_translation_v1 import translation_inputs
from universal_baseball.hitter_translation_reliability import reliable_translation
from universal_baseball.storage import sha256_file
from assemble_hitter_2027_base import ROOT,OUT,PUBLIC
from capture_hitter_2027_origin_counts import write_once


def main():
    receipt=PUBLIC/'base-input-player-review.json'
    assert not receipt.exists()
    review=json.loads((PUBLIC/'base-assembly.json').read_text())
    for p,h in review['output_hashes'].items():assert sha256_file(Path(p))==h
    f=pl.read_parquet(OUT/'assembled.parquet');counts=pl.read_parquet(OUT/'counts.parquet')
    games=pl.read_parquet(OUT/'games.parquet');draft=pl.read_parquet(OUT/'draft.parquet')
    stints=pl.read_parquet(OUT/'stints.parquet');values=pl.read_parquet(OUT/'values.parquet')
    fixed=[804944,805811,808393,592450,665487,660271,672275,596019]
    cases=[]
    for pid in fixed:
        focus=f.filter(pl.col('player_id')==pid).row(0,named=True)
        distance=sum(((pl.col(c)-focus[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('minor_pa_0',300),('draft_rank',.25)])
        peers=f.filter((pl.col('player_id')!=pid)&(pl.col('stage')==focus['stage'])&(pl.col('prior_debut')==focus['prior_debut'])).with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
        walks=[]
        for ident in [pid,*peers['player_id']]:
            row=f.filter(pl.col('player_id')==ident).row(0,named=True)
            history=counts.filter(pl.col('player_id')==ident)
            assert row['career_mlb_observed_pa']==history.filter(pl.col('bucket')=='MLB')['plate_appearances'].sum()
            for k in range(3):
                h=history.filter(pl.col('season')==2026-k)
                mp=h.filter(pl.col('bucket')=='MLB')['plate_appearances'].sum()
                assert row[f'pa_{k}']==mp and row[f'minor_pa_{k}']==h['plate_appearances'].sum()-mp
                v=values.filter((pl.col('player_id')==ident)&(pl.col('season')==2026-k))
                if mp:
                    vr=v.row(0,named=True)
                    expected=600*(vr['component_war']-570*vr['schedule_fraction']/vr['league_pa']*mp)/(mp+1200)
                    assert np.isclose(row[f'quality_{k}'],expected,rtol=0,atol=1e-12)
                else:assert row[f'quality_{k}']==0
            for b in history['bucket'].unique():
                expected=sum(w*history.filter((pl.col('season')==2026-k)&(pl.col('bucket')==b))['plate_appearances'].sum() for k,w in enumerate([1,.8,.6]))
                assert np.isclose(row[f'pooled_{b}_pa'],expected)
            assert row['scout_list_available_0']==0 and row['scout_listed_0']==-1
            walks.append(dict(player_id=ident,name=row['player_name'],input=row,
                source_stints=stints.filter((pl.col('player_id')==ident)&(pl.col('season')>=2024)).to_dicts(),
                draft=draft.filter(pl.col('player_id')==ident).to_dicts(),
                interpretation='Observed level/PA histories and exposure-weighted inputs reconcile. Current absent preseason list is unknown; primary batting position is not yet a defensive role forecast.'))
        cases.append(dict(player_id=pid,primary=walks[0],peers=walks[1:]))
    files=[]
    for fold in range(5):
        path=OUT/f'translation-{fold}.parquet';graphpath=OUT/f'translation-{fold}.json'
        assert not path.exists() and not graphpath.exists()
        overlay,notes=translation_inputs(counts,f,held_fold=fold,source_cutoff=2026)
        q=f.join(overlay,on='row_id',validate='1:1')
        repaired=reliable_translation(q)
        repaired.write_parquet(path)
        write_once(graphpath,dict(fold=fold,graphs=notes,small_sample_repair='Eight centered event inputs multiplied by supported PA/(supported PA+1200)',
            original_event_inputs=q.select('row_id',*[c for c in overlay.columns if c.startswith('translated_') and 'probability' not in c]).filter(pl.col('row_id').is_in([x+2_000_000_000 for x in fixed])).to_dicts(),
            source_hash=sha256_file(OUT/'counts.parquet'),output_sha256=sha256_file(path)))
        files.extend([path,graphpath])
        for case in cases:
            for walk in [case['primary'],*case['peers']]:
                row=repaired.filter(pl.col('player_id')==walk['player_id']).row(0,named=True)
                if row['outer_fold']==fold:
                    walk['translation_inputs']={c:row[c] for c in row if c.startswith(('translated_','translation_'))}
                    assert row['translated_reliability']==row['translation_supported_pa']/(row['translation_supported_pa']+1200)
        print(f'2027 held-player translation fold {fold} complete.',flush=True)
    judgments={804944:'Now 510 A/A+ PA at age 22, not the old 26-PA input. Supported exposure changes the actual predictor; no claim of predicted MLB ability before fitting.',
        805811:'448 current MLB PA takes the incumbent route; 137 AAA PA remains contextual evidence. DH biography does not erase 1B opportunities.',
        808393:'169 ACL PA follows DSL history; no current MLB tracking. Neither missing MLB activity nor missing tracking means zero hitting talent.',
        592450:'285 MLB PA and current measured contact retained; activation in October must not turn the previous injury into a 2027 full-season absence.',
        665487:'704 current MLB PA; historical suspension does not imply future ineligibility.',
        660271:'618 MLB PA and measured hitting history; pitcher output and full two-way salary cannot be included in hitter-only surplus.',
        672275:'345 MLB PA across teams is summed; current dated organization is separate from the largest season stint.',
        596019:'469 MLB PA plus 14 minor rehab-like PA; career exposure and MLB tracking remain the main incumbent evidence.'}
    for case in cases:case['baseball_review']=judgments[case['player_id']]
    walkpath=PUBLIC/'base-input-player-walks.json.gz'
    assert not walkpath.exists();walkpath.write_bytes(gzip.compress(json.dumps(dict(cases=cases),allow_nan=False,default=str).encode(),mtime=0))
    write_once(receipt,dict(source_player_walkthrough='complete',fixed_cases=8,peers=24,source_only=True,
        forecast_fitted=False,availability_pending=True,organization_rights_pending=True,
        origin2026_population=len(f),target_year=2027,missing_current_scout_list_not_unranked=True,
        judgments=judgments,walk_sha256=sha256_file(walkpath),output_hashes={str(p):sha256_file(p) for p in files},
        runner_sha256=sha256_file(Path(__file__)),translation_module_sha256=sha256_file(ROOT/'src/universal_baseball/hitter_origin_translation_v1.py')))


if __name__=='__main__':main()
