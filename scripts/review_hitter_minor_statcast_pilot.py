"""Independently verify request semantics and capped-cache impact before recovery."""
from datetime import date
import json
from pathlib import Path
import polars as pl
from universal_baseball.hitter_minor_statcast_source_v2 import validate_contact_response
from universal_baseball.hitter_statcast_measurement import project_measurements
from universal_baseball.storage import sha256_file
import capture_hitter_minor_statcast as capture

ROOT,OUT,CONTRACT=capture.ROOT,capture.OUT,capture.CONTRACT
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')


def environments(year):
    root=OLD/(f'prospect-pbp-hurdle-source/{year}' if year<2024 else 'prospect-talent-current-evidence/2024')
    paths=[f for f in sorted(root.rglob(f'current_talent_game_summary_{year}_*.parquet')) if not f.name.endswith('_mlb.parquet')]
    assert len(paths)==(5 if year<2024 else 4)
    frames=[];hashes={}
    for p in paths:
        report=p.parent.parent/'report.json';r=json.loads(report.read_text(encoding='utf8'))
        assert r['accepted'] and int(r['season'])==year
        hashes.update({str(p):sha256_file(p),str(report):sha256_file(report)})
        frames.append(pl.read_parquet(p).select('season','game_date','game_pk','player_id','league_id',
            'level_group','expected_contact_count','batting_plate_appearances'))
    env=pl.concat(frames).unique()
    assert env.unique(['game_pk','player_id']).height==len(env)
    return env,hashes


def checked_receipts(report):
    for r in report['receipts']:
        assert r['accepted'] and not r['capped']
        for p,h in r['outputs'].items():assert sha256_file(Path(p))==h
    return True


def main():
    report=json.loads((OUT/'pilot-capture.json').read_text(encoding='utf8'));checked_receipts(report)
    envs={};hashes={str(Path(__file__)):sha256_file(Path(__file__)),str(CONTRACT):sha256_file(CONTRACT)}
    audits=[];raws={}
    for r in report['receipts']:
        y=int(r['start'][:4])
        if y not in envs:
            envs[y],h=environments(y);hashes.update(h)
        path=next(Path(p) for p in r['outputs'] if p.endswith('.parquet'))
        raw=pl.read_parquet(path);validate_contact_response(raw,date.fromisoformat(r['start']),date.fromisoformat(r['end']))
        raws[(r['start'],r['tracked_flag'])]=raw
        keyed=raw.with_columns(pl.col('game_pk').cast(pl.Int64),pl.col('batter').cast(pl.Int64).alias('player_id'))
        joined=keyed.join(envs[y],on=['game_pk','player_id'],how='left',validate='m:1')
        assert joined['league_id'].null_count()==0
        terminal=joined.filter(pl.col('events').fill_null('').str.strip_chars().ne(''))
        counts=terminal.group_by('game_pk','player_id').len().join(envs[y],on=['game_pk','player_id'])
        residual=counts.filter(pl.col('len')!=pl.col('expected_contact_count'))
        # Also include official participants with no returned contact: zero-contact
        # participants are expected; missing positive counts are not.
        official=envs[y].filter(pl.col('game_pk').is_in(keyed['game_pk'].unique().to_list()))
        missing=official.join(counts.select('game_pk','player_id'),on=['game_pk','player_id'],how='anti').filter(pl.col('expected_contact_count')>0)
        assert residual.is_empty() and missing.is_empty()
        launch,_=project_measurements(raw.filter(pl.col('events').fill_null('').ne('')),y)
        launch=launch.join(envs[y].select('game_pk','player_id','league_id','level_group'),on=['game_pk','player_id'],validate='m:1')
        audits.append(dict(date=r['start'],tracked_flag=r['tracked_flag'],raw_rows=len(raw),terminal_rows=len(terminal),
            normal_nonbunt_contacts=len(launch),unmatched_identities=0,unexplained_positive_contact_residuals=0,
            environments=launch.group_by('league_id','level_group').agg(pl.len().alias('contacts'),pl.col('complete_pair').sum().alias('pairs'),
                pl.col('game_pk').n_unique().alias('games')).sort('league_id').to_dicts()))
    paired=[]
    for day in ['2022-07-01','2023-07-01']:
        assert raws[(day,False)].sort(capture.KEY).equals(raws[(day,True)].sort(capture.KEY))
        paired.append(dict(date=day,identical_projected_rows=True,omit_flag_loses_no_pilot_contact=True))
    legacy=pl.concat([pl.read_csv(p,columns=capture.COLUMNS,schema_overrides={c:pl.String for c in capture.COLUMNS},
        null_values=['','null']) for p in sorted(capture.LEGACY.glob('*.csv'))])
    old_terminal=legacy.filter((pl.col('type')=='X')&pl.col('events').is_not_null())
    dates=[];case_rows=[]
    names=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet').select('player_id','player_name').unique('player_id')
    for day in ['2023-04-07','2023-06-09']:
        fresh=raws[(day,False)].filter((pl.col('type')=='X')&pl.col('events').is_not_null())
        prior=old_terminal.filter(pl.col('game_date')==day)
        missing=fresh.join(prior.select(capture.KEY),on=capture.KEY,how='anti')
        overlap=fresh.join(prior.select(capture.KEY),on=capture.KEY,how='inner')
        dates.append(dict(date=day,new_terminal_contacts=len(fresh),old_terminal_contacts=len(prior),
            recovered_missing_contacts=len(missing),overlap_contacts=len(overlap)))
        stats=fresh.with_columns(pl.col('batter').cast(pl.Int64).alias('player_id'),pl.col('launch_speed').cast(pl.Float64))
        stats=stats.group_by('player_id').agg(pl.len().alias('new_contacts'),pl.col('launch_speed').mean().alias('new_mean_ev'))
        olds=prior.group_by(pl.col('batter').cast(pl.Int64).alias('player_id')).agg(pl.len().alias('old_contacts'))
        stats=stats.join(olds,on='player_id',how='left').with_columns(pl.col('old_contacts').fill_null(0)).join(names,on='player_id')
        eligible=stats.filter(pl.col('new_contacts')>=3)
        picks=[eligible.sort(['new_mean_ev','player_id'],descending=[True,False]).row(0,named=True),
            eligible.sort(['new_mean_ev','player_id']).row(0,named=True)]
        case_rows.extend(dict(date=day,selection='highest/lowest same-day mean EV among >=3 contacts; no future outcome used',**p) for p in picks)
    capture.write(OUT/'pilot-review.json',dict(contact_request_approved=True,tracked_flag_choice='omit',
        approval_scope='bounded source capture only; no source/model/deployment approval',audits=audits,paired=paired,
        capped_legacy_comparisons=dates,source_case_traces=case_rows,input_hashes=hashes,
        pilot_report_sha256=sha256_file(OUT/'pilot-capture.json'),contract_sha256=sha256_file(CONTRACT),
        source_walkthrough_status='pilot_only_full_source_pending',model_fits=0,protected_outcomes_used=False))
    print(json.dumps(dict(audits=audits,legacy_comparisons=dates,cases=case_rows),indent=2))


if __name__=='__main__':main()
