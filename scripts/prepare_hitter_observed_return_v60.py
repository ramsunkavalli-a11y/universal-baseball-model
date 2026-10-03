"""Source-only observation-state repair; preserved forecasts are not refitted."""
from datetime import date, timedelta
from pathlib import Path
import json
import polars as pl
from universal_baseball.hitter_observed_return import reconcile, as_of
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'reports/generated/practical-hitter-opportunity-status-v59'
WIN=ROOT/'reports/generated/practical-hitter-late-role-v46'
OUT=ROOT/'reports/generated/hitter-observed-return-v60'
FIXED=[('Yordan Alvarez',2022),('Nick Castellanos',2016),('Maikel Franco',2016),
       ('Jarrett Parker',2016),('Kyle Garlick',2022),('Mark Canha',2016),
       ('Gavin Lux',2023),('Matt McLain',2024)]


def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))


def write(n,o):
    (OUT/n).write_text(json.dumps(o,indent=2,default=str,allow_nan=False)+'\n',encoding='utf8')


def main():
    assert read(OLD/'report.json')['player_walkthrough_status']=='complete'
    assert read(OLD/'open-spell-report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'report.json').exists(), 'Preserve completed source test'
    OUT.mkdir(parents=True,exist_ok=True)
    source=pl.read_parquet(OLD/'features.parquet')
    old=pl.read_parquet(OLD/'context.parquet')
    q=pl.read_parquet(OLD/'predictions.parquet')
    records=read(OLD/'records.json')
    manifest=read(WIN/'source-manifest.json')
    windows=pl.read_parquet(WIN/'windows.parquet')
    assert max(manifest['years'])==2024
    paths=[OLD/'records.json',OLD/'features.parquet',OLD/'context.parquet',
           OLD/'predictions.parquet',OLD/'preflight.json',WIN/'source-manifest.json',
           WIN/'windows.parquet',ROOT/'docs/hitter-observed-return-v60-contract.md',
           ROOT/'src/universal_baseball/hitter_observed_return.py',Path(__file__)]
    periods={}
    for s in manifest['sources']:
        if s['window'] in ['preceding','late']:
            periods[s['season'],s['window']]=(s['start'],s['end'])
    win_lookup={}
    for r in windows.iter_rows(named=True):
        win_lookup[r['player_id'],r['season']]=[
            dict(start=periods[r['season'],label][0],end=periods[r['season'],label][1],
                 pa=r[label+'_pa'],label=label)for label in ['preceding','late']]
    calendars={}
    for c in manifest['checks']:
        p=Path(c['schedule_path']);assert sha256_file(p)==c['schedule_sha256']
        paths.append(p)
        calendars[c['season']]=sorted({date.fromisoformat(g['officialDate'])
            for d in read(p)['dates']for g in d['games']
            if g['gameType']=='R' and g['status']['codedGameState']in ['F','O']})
    before={str(p):sha256_file(p)for p in paths}
    write('source-contract.json',dict(before_reconstruction=True,input_hashes=before,
          source_rows=len(source),new_models_fitted=False,protected_outcomes_used=False))
    oldlookup={r['row_id']:r for r in old.iter_rows(named=True)}
    spell_lookup={};rows=[];version_checks=0
    for row in source.iter_rows(named=True):
        pid,y=row['player_id'],row['origin_year'];cutoff=date(y,12,31)
        rs=records.get(str(pid),[])
        ws=[w for year in range(max(2010,y-2),y+1)for w in win_lookup.get((pid,year),[])]
        spells=reconcile(rs,ws,cutoff)
        scope=bool(oldlookup[row['row_id']]['il_scope'])
        since=cutoff-timedelta(days=729)
        days={d for year,ds in calendars.items()if year<=y for d in ds if since<=d<=cutoff}
        possible={d for d in days if any(s['start']<=d<=s['end_upper']for s in spells)}
        opened=[s for s in spells if s['open_observation']]
        observed=[s for s in spells if s['closure_kind']=='observed_MLB_PA_window' and s['end_upper']>=since]
        reported=[s for s in spells if s['closure_kind']=='reported_MLB_roster_return' and s['end_upper']>=since]
        rows.append(dict(row_id=row['row_id'],player_id=pid,origin_year=y,
            medical_scope=scope,recorded_unresolved=float(bool(opened))if scope else None,
            possible_absence_days730_upper=len(possible)if scope else None,
            absence_days730_lower=0 if scope else None,
            observed_return_intervals730=len(observed)if scope else None,
            reported_roster_returns730=len(reported)if scope else None,
            clinical_recovery_certified=False,exact_first_return_date_known=False,
            original_recorded_open=oldlookup[row['row_id']]['il_open'],
            duration_must_not_be_used_as_exact=True))
        if oldlookup[row['row_id']]['il_open']>0 or (row['player_name'],y)in FIXED:
            spell_lookup[row['row_id']]=spells
        if (row['player_name'],y)in FIXED:
            future=dict(transaction_id=-99999,player_id=pid,available_date=f'{y+1}-01-01',
                event_date=f'{y}-01-01',kind='mlb_return',il_kind=None,description='future probe')
            assert reconcile(rs+[future],ws,cutoff)==spells
            version_checks+=1
    repaired=pl.DataFrame(rows,infer_schema_length=None)
    assert len(repaired)==63282 and repaired['row_id'].n_unique()==63282
    repaired.write_parquet(OUT/'observation-states.parquet')
    oldopen=repaired.filter(pl.col('original_recorded_open')>0)
    oldopen.write_parquet(OUT/'old-open-comparison.parquet')
    joined=q.join(repaired,on=['row_id','player_id','origin_year'],validate='1:1')
    assert joined.select(q.columns).equals(q)
    cases=[]
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    for name,y in FIXED:
        g=joined.filter((pl.col('player_name')==name)&(pl.col('origin_year')==y))
        assert len(g)==1,(name,y)
        r=g.row(0,named=True);cutoff=date(y,12,31)
        peers=joined.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=r['player_id'])&
            (pl.col('medical_scope')==r['medical_scope'])&
            ((pl.col('original_recorded_open')>0)==bool(r['original_recorded_open'])))
        peers=peers.with_columns((((pl.col('age')-r['age'])/3)**2+
            ((pl.col('pa_0')-r['pa_0'])/300)**2).alias('distance')).sort('distance','player_id').head(3)
        cases.append(dict(origin=r,spells=spell_lookup[r['row_id']],
            records=as_of(records.get(str(r['player_id']),[]),cutoff),
            windows=win_lookup.get((r['player_id'],y),[]),
            source_history=counts.filter((pl.col('player_id')==r['player_id'])&
                pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
            peers=peers.select('player_name','age','pa_0','original_recorded_open',
                'recorded_unresolved','observed_return_intervals730',
                'possible_absence_days730_upper','repaired_pa','next_pa').to_dicts()))
    write('cases.json',cases);write('spells.json',spell_lookup)
    for p,h in before.items():assert sha256_file(Path(p))==h,p
    evalopen=joined.filter(pl.col('original_recorded_open')>0)
    report=dict(source_rows=len(repaired),old_open_rows=len(oldopen),
        now_observed_closed_rows=len(oldopen.filter(pl.col('recorded_unresolved')==0)),
        evaluation_old_open_rows=len(evalopen),
        evaluation_now_observed_closed_rows=len(evalopen.filter(pl.col('recorded_unresolved')==0)),
        source_closed_people=oldopen.filter(pl.col('recorded_unresolved')==0)['player_id'].n_unique(),
        cases=len(cases),future_version_checks=version_checks,
        player_walkthrough_status='pending',new_models_fitted=False,forecasts_changed=False,
        clinical_recovery_inferred=False,protected_outcomes_used=False,
        original_prediction_sha256=sha256_file(OLD/'predictions.parquet'),input_hashes=before,
        output_hashes={str(OUT/n):sha256_file(OUT/n)for n in
            ['observation-states.parquet','old-open-comparison.parquet','cases.json','spells.json']})
    write('report.json',report)
    print(json.dumps({k:v for k,v in report.items()if 'hash'not in k},indent=2),flush=True)


if __name__=='__main__':
    main()
