"""Package six calendar years, never claim unresolved control/tail is complete."""
from datetime import date
import json
from pathlib import Path
import shutil

import polars as pl

from extend_six_year_hitter_v1 import OUT, OLD, OLD_PACKAGE, save, COMPONENTS
from universal_baseball.storage import sha256_file
from universal_baseball.multiyear_hitter_followup import compare_losses

PACKAGE=Path('model_artifacts/six-year-hitter-v1-2026-09-22')
TEMPLATE=Path('templates/six-year-hitter-v1-explorer.html')


def main():
    current=pl.read_parquet(OUT/'forecast-2026-2031.parquet')
    old=pl.read_parquet(OLD_PACKAGE/'forecast-2026-2028.parquet')
    assert current.select(old.columns).equals(old), 'Earlier forecasts changed'
    assert current.height==3907 and current['player_id'].n_unique()==3907
    assert current['full_control_value'].null_count()==3907
    for h in (4,5,6):
        assert current[f'value_{2025+h}'].is_finite().all()
        assert current[f'expected_pa_h{h}'].is_between(0,750).all()
        assert current[f'activity_h{h}'].is_between(0,1).all()
    notes=json.loads((OUT/'fit-notes.json').read_text())
    assert all(n['latest_label']<=n['origin']<=2025 for n in notes)
    assert all(not(y<2020<=y+n['horizon']) for n in notes for y in n['train_origins'])
    raw=pl.read_parquet(OUT/'predictions.parquet')
    future=raw.filter(pl.col('origin_year')==2025)
    assert future['actual_batting'].null_count()==future.height
    assert future['actual_integrated'].null_count()==future.height
    paired={}
    for h in (4,5,6):
        f=raw.filter((pl.col('origin_year')<2025)&(pl.col('horizon')==h)).with_columns(
            ((pl.col('direct')-pl.col('actual_batting'))**2).alias('loss1'),
            ((pl.col('base')-pl.col('actual_batting'))**2).alias('loss0'))
        paired[str(h)]=compare_losses(f,'loss1','loss0')
    cumulative=pl.read_parquet(OUT/'cumulative-predictions.parquet').with_columns(
        ((pl.col('direct')-pl.col('actual_batting'))**2).alias('loss1'),
        ((pl.col('base')-pl.col('actual_batting'))**2).alias('loss0'))
    paired['cumulative']=compare_losses(cumulative,'loss1','loss0')
    save(OUT/'paired-comparison.json',{'results':paired,'limitation':'Player clusters preserve repeated identities but do not account for shared season shocks. No independent confirmation.'})
    # Display-only historical annotation: explicitly project columns rather than
    # importing current-service/roster/payroll fields from the in-season container.
    service_path=OLD/'league-control/2026-09-08/league-control-snapshot.parquet'
    service=pl.read_parquet(service_path,columns=['player_id','baseline_service_days','baseline_status','mlb_debut_date'])
    service=service.with_columns(pl.lit(True).alias('service_source_present'))
    view=current.join(service,on='player_id',how='left',validate='1:1',maintain_order='left')
    accepted=(pl.col('baseline_status')=='available')&pl.col('baseline_service_days').is_not_null()
    no_debut=pl.col('service_source_present').fill_null(False)&(pl.col('mlb_debut_date').is_null()|(pl.col('mlb_debut_date')>date(2025,12,31)))
    view=view.with_columns(pl.when(accepted).then(pl.col('baseline_service_days')).when(no_debut).then(0).otherwise(None).alias('opening_service_days'),
        pl.when(accepted).then(pl.lit('Recovered opening-2026 service balance; captured retrospectively.'))
        .when(no_debut).then(pl.lit('Official identity/debut evidence supports no MLB debut by the forecast cutoff.'))
        .otherwise(pl.lit('No accepted opening service balance; not assumed to be zero.')).alias('service_status'))
    # Individual source-derived control annotations stay local, not in the public model package.
    keep=['player_id','player_name','age','level','stage','organizations','position_label','opening_service_days','service_status']
    for h in range(1,7): keep += [f'value_{2025+h}',f'expected_pa_h{h}',f'activity_h{h}']+[f'{c}_runs_h{h}' for c in COMPONENTS]
    payload=json.dumps(view.select(keep).to_dicts(),allow_nan=False).replace('</','<\\/')
    evidence='Year-4 batting error fell from 0.574 to 0.539; Year 5 from 0.550 to 0.525; Year 6 from 0.568 to 0.542 versus simpler age/level/workload forecasts. These are different annual targets, not comparisons across horizons. Years 5–6 have no pandemic-free full-path outer test. Player-disjoint tests still favor the richer forecasts, but gains shrink. All are exposed development results.'
    (OUT/'index.html').write_text(TEMPLATE.read_text(encoding='utf-8').replace('__PLAYER_DATA__',payload).replace('__REPORT_DATA__',json.dumps({'evidence':evidence})),encoding='utf-8',newline='\n')
    report={'players':current.height,'years':list(range(2026,2032)),'earlier_columns_unchanged':True,'chronology_checks_passed':True,
        'control_value_complete':False,'unresolved_control_values':3907,'service_annotation_display_only':True,
        'opening_service_known':view['opening_service_days'].len()-view['opening_service_days'].null_count(),
        'opening_service_unknown':view['opening_service_days'].null_count(),
        'already_statutorily_eligible':view.filter(pl.col('opening_service_days')>=1032).height,
        'service_source_sha256':sha256_file(service_path),'service_columns_read':['player_id','baseline_service_days','baseline_status','mlb_debut_date'],
        'source_terms':'Individual historical control annotations remain local; original private workbook/capture tables are not republished.',
        'service_limitation':'Retrospective opening balance, not a certified contemporaneous Dec-31 source. No current-service increments or 2026 performance used.',
        'no_2026_outcomes':True,'status':'six_calendar_year_development_extension_control_objective_open'}
    save(OUT/'delivery-report.json',report)
    PACKAGE.mkdir(exist_ok=True,parents=True)
    for name in ['forecast-2026-2031.parquet','predictions.parquet','cumulative-predictions.parquet','score-report.json','fit-notes.json','input-manifest.json','paired-comparison.json','delivery-report.json']:
        shutil.copyfile(OUT/name,PACKAGE/name)
    save(PACKAGE/'manifest.json',{'version':'six-year-hitter-v1','cutoff':'2025-12-31','control_value_complete':False,
        'files':{p.name:sha256_file(p) for p in PACKAGE.iterdir() if p.name!='manifest.json'},
        'build_code':{str(p):sha256_file(p) for p in [Path(__file__),TEMPLATE,Path('scripts/extend_six_year_hitter_v1.py'),Path('src/universal_baseball/six_year_hitter.py')]}})
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
