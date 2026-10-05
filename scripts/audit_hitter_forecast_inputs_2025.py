"""Source-only 2025 assembly boundary audit; never loads 2026 outcomes."""
from pathlib import Path
import json
import numpy as np
import polars as pl

from universal_baseball.hitter_forecast_inputs import pooled_inputs,BUCKETS
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import materialize as historical_pool,DRAFT
from universal_baseball.hitter_numeric_history import repair

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/'reports/generated'
OUT=GEN/'hitter-forecast-inputs-2025'
FIXED=[592450,701762,670541,808982,691406,656555]


def write(name,value):
    path=OUT/name;assert not path.exists(),f'Preserve {path}'
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def required():
    return ['row_id','origin_year','player_id',*[f'{s}_{k}' for s in ['pa','quality'] for k in range(3)],
            *[f'{b}_{k}_pa' for b in BUCKETS for k in range(3)]]


def main():
    assert not OUT.exists(),'Preserve prior boundary audit'
    source=GEN/'practical-hitter-v31'
    counts=pl.read_parquet(source/'counts.parquet');stints=pl.read_parquet(source/'dated-stints.parquet')
    assert counts['season'].max()==stints['season'].max()==2025
    draft=pl.scan_parquet(DRAFT).filter(pl.col('draft_year')<=2025).collect()
    assert draft['draft_year'].max()==2025
    hist=pl.read_parquet(GEN/'practical-hitter-numeric-repair-v53/features.parquet').select(required()).sort('row_id')
    # Compare to the actual corrected definition, not the old inferred integer bug.
    old=historical_pool(hist,counts.filter(pl.col('season')<=2024),draft.filter(pl.col('draft_year')<=2024))
    old,changes=repair(old,counts.filter(pl.col('season')<=2024))
    new=pooled_inputs(hist,counts.filter(pl.col('season')<=2024),draft.filter(pl.col('draft_year')<=2024),source_cutoff=2024)
    checked=0
    for name in new.columns:
        a,b=old[name],new[name]
        if a.dtype in [pl.String] or name in ['draft_year','pick_number']:
            assert a.to_list()==b.to_list(),name
        else:assert np.allclose(a.to_numpy(),b.to_numpy(),atol=1e-12,rtol=0),name
        checked+=hist.height
    # Original saved V53 pooled fields also agree; the draft elapsed repair is retained.
    saved=pl.read_parquet(GEN/'practical-hitter-numeric-repair-v53/features.parquet').sort('row_id')
    for name in [c for c in new.columns if c.startswith('pooled_') or c=='draft_elapsed']:
        assert np.allclose(new[name].to_numpy(),saved[name].to_numpy(),atol=1e-12,rtol=0),name
    target=pl.read_parquet(GEN/'multiyear-hitter-v1/targets.parquet')
    assert target['season'].max()==2025
    meta={r['season']:r for r in target.unique('season').to_dicts()}
    values={(r['season'],r['player_id']):r for r in target.to_dicts()}
    lut={(r['season'],r['player_id'],r['bucket']):r for r in counts.to_dicts()}
    rows=[]
    for i,pid in enumerate(FIXED):
        row=dict(row_id=i,player_id=pid,origin_year=2025)
        for k in range(3):
            y=2025-k
            for b in BUCKETS:row[f'{b}_{k}_pa']=float(lut.get((y,pid,b),{}).get('plate_appearances',0))
            pa=row[f'MLB_{k}_pa'];row[f'pa_{k}']=pa
            assert pa==values.get((y,pid),{}).get('mlb_pa',0)
            v=values.get((y,pid),{}).get('component_war',0.)
            rep=570*meta[y]['schedule_fraction']/meta[y]['league_pa']
            row[f'quality_{k}']=600*(v-rep*pa)/(pa+1200)
        rows.append(row)
    f=pl.DataFrame(rows)
    correct=pooled_inputs(f,counts,draft,source_cutoff=2025)
    legacy=historical_pool(f,counts,draft.filter(pl.col('draft_year')<=2024))
    # This source diagnostic deliberately demonstrates the old cutoff, not a forecast.
    cases=[]
    for i,pid in enumerate(FIXED):
        history=stints.filter((pl.col('player_id')==pid)&pl.col('season').is_between(2023,2025)).sort('season','bucket')
        assert history.height,pid
        r=correct.row(i,named=True);o=legacy.row(i,named=True)
        expected=sum(w*lut.get((2025-k,pid,'MLB'),{}).get('plate_appearances',0) for k,w in enumerate([1.,.8,.6]))
        assert np.isclose(r['pooled_MLB_pa'],expected)
        cases.append(dict(player_id=pid,player_name=history['player_name'][-1],origin_year=2025,target_year=2026,
            source_history=history.select('season','bucket','plate_appearances','strike_outs','unintentional_walks','home_runs').to_dicts(),
            origin_inputs=f.row(i,named=True),correct_inputs=r,
            legacy_cutoff_diagnostic=dict(pooled_MLB_pa=o['pooled_MLB_pa'],pooled_MLB_K=o['pooled_MLB_K'],pooled_MLB_HR=o['pooled_MLB_HR']),
            expected_precision_PA=float(expected),old_builder_omitted_2025_PA=int(f[f'pa_0'][i]),
            forecast_produced=False,review='Real 2025 production now enters exactly once at recency 1; 2024 and 2023 at .8 and .6. This is source readiness, not an accuracy gain.'))
    # Source extent is measured, never inferred from an artifact's name.
    families=[]
    for name,path,column,needed in [
        ('domestic batting',source/'counts.parquet','season',2025),
        ('dated names age position',source/'dated-stints.parquet','season',2025),
        ('draft pedigree',DRAFT,'draft_year',2025),
        ('reviewed MLB tracking',GEN/'hitter-statcast-full-history/annual-launch-features.parquet','season',2025),
        ('December 31 roster',GEN/'hitter-arrival-source-repair-v1/year-end-rosters.parquet','season',2025),
        ('preseason scouting',GEN/'hitter-preseason-readiness-v67/ranks.parquet','season',2026)]:
        # Existing paths are all earlier reviewed sources; do not open a live 2026 page.
        extent=pl.scan_parquet(path).select(pl.len().alias('rows'),pl.col(column).min().alias('earliest'),pl.col(column).max().alias('latest')).collect().row(0,named=True)
        families.append(dict(family=name,path=str(path),sha256=sha256_file(path),required_latest=needed,**extent,
            coverage_ready=extent['latest']>=needed,qualification='Retrospective source; preseason scouting needs separately verified publication vintage'))
    OUT.mkdir()
    correct.write_parquet(OUT/'source-case-features.parquet')
    inputs=[Path(__file__),ROOT/'src/universal_baseball/hitter_forecast_inputs.py',ROOT/'tests/test_hitter_forecast_inputs.py',
        ROOT/'docs/hitter-candidate-freeze-preparation.md',source/'counts.parquet',source/'dated-stints.parquet',DRAFT,
        GEN/'practical-hitter-numeric-repair-v53/features.parquet',GEN/'multiyear-hitter-v1/targets.parquet']
    report=dict(source_only=True,new_fits=0,forecasts_produced=0,protected_outcomes_used=False,source_cutoff=2025,
        historical_rows=hist.height,historical_features=new.width,historical_fields_checked=checked,
        corrected_historical_definition_reproduced=True,legacy_numeric_repair=changes,
        player_walkthrough_status='complete',source_cases=cases,families=families,
        candidate_ready_to_freeze=False,readiness_gaps=[r['family'] for r in families if not r['coverage_ready']],
        input_hashes={str(p):sha256_file(p) for p in inputs},output_sha256=sha256_file(OUT/'source-case-features.parquet'))
    write('report.json',report)
    print(f'{checked} historical fields agree; six real 2025 source walks. Freeze not ready: '+', '.join(report['readiness_gaps']))
    for c in cases:print(c['player_name'],'2025 MLB PA',c['old_builder_omitted_2025_PA'],'old/new precision',c['legacy_cutoff_diagnostic']['pooled_MLB_pa'],c['expected_precision_PA'])


if __name__=='__main__':main()
