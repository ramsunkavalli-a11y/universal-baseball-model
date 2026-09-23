"""Inventory dated states, without selecting or scoring a new path model."""
import json
from pathlib import Path
import shutil
import numpy as np
import polars as pl
from build_historical_projection_state_v1 import OUT, YEARS, BASE, hashes
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.historical_projection_state import validate_states, mature_vectors
from universal_baseball.player_path_distribution import age_groups
from universal_baseball.storage import sha256_file

PACKAGE=Path('model_artifacts/historical-projection-state-v1-2026-09-23')
CUTOFFS=(2012,2013,2014,2015,2016,2019,2021,2022,2025)


def snapshots(ledger,cutoff,legacy=False):
    f=mature_vectors(ledger,cutoff).filter(pl.col('horizon')==1)
    if legacy:f=f.filter(pl.col('origin_year')>=2016)
    return f.with_columns((1/pl.len().over('player_id')).alias('identity_weight'),
        pl.Series('age_band',age_groups(f['age'].to_numpy())))


def support(f):
    w=f.group_by('player_id').agg(pl.col('identity_weight').sum()).sort('player_id')['identity_weight'].to_numpy()
    return {'snapshots':f.height,'players':len(w),'effective_players':float(w.sum()**2/(w@w)) if len(w) else 0.}


def inventory(f):
    groups={'never_debuted':pl.col('prospect'),'recent_debut':pl.col('recent_debut'),
        'minor_returner':pl.col('minor_returner'),
        'young_brief_mlb':(pl.col('age')<=23)&pl.col('mlb_pa_lag0').is_between(1,99)}
    cells=[{'stage':keys[0],'age_band':keys[1],**support(g)}
        for keys,g in f.partition_by('stage','age_band',as_dict=True).items()]
    return {**support(f),'origins':sorted(f['origin_year'].unique().to_list()),
        'groups':{name:support(f.filter(expr)) for name,expr in groups.items()},
        'age_stage_cells':sorted(cells,key=lambda r:(r['stage'],r['age_band']))}


def query_support(f,query,cutoff):
    """Diagnostic same-age/stage pools; no matching policy or fallback is chosen."""
    pools={}
    for cell,g in f.partition_by('stage','age_band',as_dict=True).items():
        masses=g.group_by('player_id').agg(pl.col('identity_weight').sum().alias('mass'),pl.len().alias('n')).sort('player_id')
        by_id={r['player_id']:(r['mass'],r['n']) for r in masses.to_dicts()}
        w=masses['mass'].to_numpy()
        pools[cell]=(g.height,len(w),float(w.sum()),float(w@w),by_id)
    rows=[]
    for pid,stage,age in query.select('player_id','stage','age').iter_rows():
        band=int(age_groups([age])[0]);n,k,m,s,ids=pools.get((stage,band),(0,0,0.,0.,{}))
        own,own_n=ids.get(pid,(0.,0));denom=max(0.,s-own**2)
        rows.append({'cutoff':cutoff,'player_id':pid,'stage':stage,'age_band':band,
            'snapshots':n-own_n,'players':k-int(pid in ids),
            'effective_players':float((m-own)**2/denom) if denom>0 else 0.,
            'excluded_self_snapshots':own_n})
    return pl.DataFrame(rows)


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    build=json.loads((OUT/'build-manifest.json').read_text())
    for name,sha in build['files'].items():assert sha256_file(OUT/name)==sha
    states=pl.read_parquet(OUT/'states.parquet');validate_states(states)
    ledger=pl.read_parquet(OUT/'residual-ledger.parquet')
    panel=pl.read_parquet(BASE/'panel.parquet')
    coverage=[]
    for year in YEARS:
        f=states.filter(pl.col('origin_year')==year)
        ids=set(panel.filter(pl.col('origin_year')==year)['player_id'])
        assert set(f['player_id'])==ids and f.height==3*len(ids)
        coverage.append({'origin':year,'players':len(ids),'rows':f.height,
            'year1_evidence':f.filter(pl.col('horizon')==1).group_by('year1_evidence').len().to_dicts(),
            'missing_forecasts':{c:f[c].null_count()+int(f[c].is_nan().sum()) for c in
                ('delivered_p','delivered_pa','delivered_value','research_conditional_rate','h1_rate_anchor')},
            'pa_range':[f['delivered_pa'].min(),f['delivered_pa'].max()],
            'conditional_pa_range':[f['delivered_conditional_pa'].min(),f['delivered_conditional_pa'].max()]})
    support_rows=[];queries=[]
    for cutoff in CUTOFFS:
        f=snapshots(ledger,cutoff)
        support_rows.append({'cutoff':cutoff,'rebuilt':inventory(f),'previous_matched_archive':inventory(snapshots(ledger,cutoff,True))})
        queries.append(query_support(f,panel.filter(pl.col('origin_year')==cutoff),cutoff))
    q=pl.concat(queries);q.write_parquet(OUT/'query-support.parquet')
    report={'status':'three_year_marginal_archive_rebuilt_not_a_validated_path_model',
        'coverage':coverage,'support':support_rows,'query_support':q.group_by('cutoff').agg(
            pl.len().alias('queries'),pl.col('players').min().alias('minimum_same_cell_players'),
            pl.col('effective_players').min().alias('minimum_same_cell_effective_players'),
            (pl.col('players')==0).sum().alias('queries_without_same_cell_history'),
            (pl.col('players')<21).sum().alias('queries_below_previous_21_identity_rule')).sort('cutoff').to_dicts(),
        'readiness':{'historical_marginal_inputs_available':True,'first_complete_residual_cutoff':2015,
            'earliest_existing_outer_cutoff':2016,'joint_architecture_validated':False,
            'six_year_states_rebuilt':False,'new_prediction_accuracy_measured':False,
            'next':'Freeze one three-year projection-anchored path contract; retain support fallbacks and success calibration gates. Do not fit before that contract.'},
        'limitations':['Historical recipes use exposed development choices; refitted coefficients are vintage-safe, not independently pristine model selection.',
            'Early H1 values use aggregate-stat Ridge fallback, not modern detailed-contact features.',
            'Rate heads condition on eventual MLB participation and are not identified universal latent talent.',
            'Marginal opportunity and value forecasts do not identify skill-opportunity dependence or persistent uncertainty.',
            'No trained 2009-2011 forecast states; no 2020 origin; pandemic-crossing vectors excluded.',
            'Support counts are not rare-success calibration, nor independent careers per snapshot.',
            'Stronger research PA ensemble not backfilled; whole WAR, rights/costs and control tail remain open.'],
        'production_forecasts_changed':False,'protected_outcomes_used':False}
    save(OUT/'support-audit.json',report)
    lines=['# Historical forecast archive rebuilt','',
        '2026-09-23. **Input-building milestone, not a model upgrade.** Live forecasts and the explorer are unchanged.','',
        '## What changed','',
        f"Reconstructed 2012–2015: **{build['backfilled_rows']:,} player/year/horizon forecasts**, covering Years 1–3.",
        f"Combined archive: **{build['rows']:,} records** across 11 starting seasons, through the 2025 cutoff.",
        'Each record separates MLB participation, playing time conditional on participation,',
        'research hitting-rate estimates, and delivered batting/replacement value. These are not full WAR.',
        'Older models were refitted using labels available at the time, not today’s fitted coefficients.',
        'These are reconstructed forecasts under current fixed recipes, not forecasts published in those years.','',
        '## Verification','',
        '- Reproduced 2016 and 2022 opportunity/conditional-head forecasts at all three horizons.',
        '- Reproduced independently fitted H1 rate anchors at both overlaps and all four backfill origins.',
        '- Early raw mean values match the existing archive; later rich mean values are reused, not refitted.',
        '- Changing future labels and future predictors left the tested 2016 H3 pipeline and H1 rate anchor unchanged.',
        '- Full starting populations retained; forecasts have unique keys, cutoff checks and no missing prediction fields.',
        '- Zero playing time produces an unknown observed hitting rate, not zero talent. Future outcomes stay missing.','',
        '## Usable three-year history','',
        'A complete forecast/error vector must have finished before the next model is fit. Pandemic-crossing',
        'paths are excluded. Counts below are starting-year snapshots, with repeated players identified explicitly.','',
        '| Model cutoff | Previous matched snapshots | Rebuilt snapshots | Distinct players | Young brief-MLB snapshots / players |',
        '|---|---:|---:|---:|---:|']
    for r in support_rows:
        a,b=r['previous_matched_archive'],r['rebuilt'];g=b['groups']['young_brief_mlb']
        lines.append(f"| {r['cutoff']} | {a['snapshots']:,} | {b['snapshots']:,} | {b['players']:,} | {g['snapshots']} / {g['players']} |")
    lines += ['', 'Every identity has total weight one across its eligible snapshots. A subset’s effective support can',
        'be smaller than its distinct-player count. The packaged audit includes age/stage cells, never-debuted',
        'players, recent debuts, minor-league returners and effective support. Query diagnostics exclude every',
        'snapshot of the query player itself; they do not select a new matching/fallback rule.',
        'Sparse cells remain: 25 of the 4,572 queries at 2016 and one of the 3,907 at 2025 have fewer',
        'than the previous 21-identity rule in their same-age/stage pool after self-exclusion. A future',
        'architecture must declare its broader fallback; these rows cannot be silently dropped.','',
        '## What this does—and does not—enable','',
        'The missing matched-history problem at the 2016 outer fold is repaired. A three-year anchored-path',
        'experiment can now be specified against dated forecast errors. That is permission to design a test,',
        'not evidence that a particular joint model works or that rare prospect upside is sufficiently supported.',
        'No new accuracy claim is made here; the previous population-only path model remains rejected.','',
        'There is still no mature reconstructed three-year error history at 2012–2014 cutoffs. The first is',
        '2015 (one starting season); the 2016 cutoff has only two. Early anchors have less detailed features',
        'than modern forecasts. A residual from an older fallback is not automatically portable to a modern stack.',
        'Whole-vector residuals contain realized variation and selection, not separately measured development',
        'or pure talent. Do not add another independent season-noise layer to them without identifying what',
        'has already been included. Six-year states and full remaining-control dollar values remain incomplete.','',
        '## Next bounded step','',
        'Freeze one three-year path specification: how projected ability and playing opportunities interact,',
        'what uncertainty persists between years, what developmental changes are supported, and how sparse',
        'states borrow strength. Compare with the delivered mean and the existing distribution controls on',
        'the same players. Preserve prospect-success checks, player exclusions, pandemic separation and',
        'Monte Carlo stability rules. Do not improve apparent results with an after-the-fact blend or FV floor.','',
        '## Reproduce','', '```powershell',
        '.venv/Scripts/python.exe -X utf8 scripts/build_historical_projection_state_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/audit_historical_projection_state_v1.py',
        '.venv/Scripts/python.exe -X utf8 scripts/verify_historical_projection_state_v1.py','```','',
        'The original pre-fit contract is saved in the package. Do not overwrite/refreeze it after fitting.']
    Path('docs/historical-projection-state-v1-result.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names=('prefit-manifest.json','build-manifest.json','states.parquet','residual-ledger.parquet',
        'overlap-checks.json','future-mutation-check.json','support-audit.json','query-support.parquet')
    for name in names:shutil.copyfile(OUT/name,PACKAGE/name)
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},
        'audit_code':{str(p):sha256_file(p) for p in (Path(__file__),Path('scripts/verify_historical_projection_state_v1.py'))},
        'production_forecasts_changed':False,'protected_outcomes_used':False})
    print(json.dumps({'rows':states.height,'support':[{'cutoff':r['cutoff'],**support(snapshots(ledger,r['cutoff']))} for r in support_rows]}))


if __name__=='__main__':main()
