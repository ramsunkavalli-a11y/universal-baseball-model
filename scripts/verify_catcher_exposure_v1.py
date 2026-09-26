"""Independent source/denominator checks on frozen catcher exposure validation."""
from collections import Counter
import json
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file

ROOT=Path('model_artifacts/catcher-exposure-v1-2026-09-26')


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def main():
    freeze=read(ROOT/'validation-freeze.json');sel=read(ROOT/'selection.json');report=read(ROOT/'validation-report.json')
    assert sha256_file(ROOT/'selection.json')==freeze['selection_sha256']
    assert sha256_file(ROOT/'development-report.json')==freeze['development_report_sha256']
    assert report['code_hashes']==freeze['code_hashes']
    for path,h in freeze['code_hashes'].items():assert sha256_file(Path(path))==h
    assert len(sel['games'])==128 and not sel['already_in_cache']
    selected={g['game_pk'] for g in sel['games']}
    assert len(selected)==128 and all(g['season'] in [2016,2018,2021,2024] for g in sel['games'])
    for path,h in sel['prior_selections'].items():
        assert sha256_file(Path(path))==h
        assert not selected&{g['game_pk'] for g in read(Path(path))['games']}
    tables={}
    for path,m in report['artifacts'].items():
        assert sha256_file(Path(path))==m['sha256']
        tables[Path(path).stem]=pl.read_parquet(path)
        assert tables[Path(path).stem].height==m['rows']
    pi=tables['pitches'];ev=tables['events'];rp=tables['runner-pitches']
    key=['game_pk','at_bat_index','event_index']
    assert pi.select(key).unique().height==pi.height==32864
    assert pi['game_source_gate'].all() and pi['runner_state_known'].all()
    assert pi.filter(~pl.col('pre_outs').is_between(0,2)|~pl.col('pre_balls').is_between(0,3)|~pl.col('pre_strikes').is_between(0,2)).is_empty()
    expected_risk=pl.any_horizontal(pl.col(f'runner_{b}').is_not_null() for b in [1,2,3]) | (
        (pl.col('pre_strikes')==2)&(pl.col('runner_1').is_null()|(pl.col('pre_outs')==2)))
    assert pi.select((pl.col('blocking_at_risk')==expected_risk).all()).item()
    assert pi.select(pl.sum_horizontal(pl.col(f'runner_{b}').is_not_null().cast(pl.Int64) for b in [1,2,3]).sum()).item()==rp.height==21474
    for name in ['pitch-checks','player-checks']:
        assert tables[name]['status'].eq('match').all()
    assert tables['team-checks']['status'].eq('matched').all()
    for name in ['state-checks','credit-checks','matchup-checks']:assert tables[name]['match'].all()
    pmap={tuple(r[k] for k in key):r for r in pi.to_dicts()}
    empty_blocking=[];labels=Counter();unlinked=[];raw_keyset=set();raw_eventmap={};physicalmap={}
    captures=read(ROOT/'captures.json');assert captures['selection_sha256']==freeze['selection_sha256']
    payloads={};half_transition_checks=0
    for cap in captures['records']:
        assert 'error' not in cap and cap['game_pk'] in selected
        path=Path(cap['path']);assert sha256_file(path)==cap['sha256'];p=read(path);game=cap['game_pk']
        assert p['gameData']['game']['pk']==game and int(p['gameData']['datetime']['officialDate'][:4])<2026
        payloads[game]=p
        ordered=sorted(p['liveData']['plays']['allPlays'],key=lambda a:a['about']['atBatIndex'])
        assert [a['about']['atBatIndex'] for a in ordered]==list(range(len(ordered)))
        for before,after in zip(ordered,ordered[1:]):
            a=before['about'];b=after['about']
            old=2*(a['inning']-1)+(0 if a['isTopInning'] else 1)
            new=2*(b['inning']-1)+(0 if b['isTopInning'] else 1)
            if old!=new:
                assert new==old+1 and before['count']['outs']==3
                half_transition_checks+=1
        for a in ordered:
            ab=a['about']['atBatIndex']
            for e in a.get('playEvents',[]):
                k=(game,ab,e['index']);raw_eventmap[k]=e
                if e.get('playId'):physicalmap.setdefault((game,ab,e['playId']),[]).append(e)
                if e.get('isPitch'):raw_keyset.add(k)
    assert raw_keyset==set(pmap)
    for row in ev.to_dicts():
        k=(row['game_pk'],row['at_bat_index'],row['event_index']);raw=raw_eventmap[k]
        if row['linked_pitch_index'] is None:
            matched=physicalmap.get((k[0],k[1],raw.get('actionPlayId')),[])
            confirmed=raw.get('type')=='pickoff' or (len(matched)==1 and matched[0].get('type')=='pickoff')
            unlinked.append({**{c:row[c] for c in key+['family']},'anchor':'confirmed_pickoff' if confirmed else 'unresolved_nonpitch_or_missing_link',
                'source_event_type':raw.get('type')})
        else:
            lk=(k[0],k[1],row['linked_pitch_index']);pitch=pmap[lk]
            assert row['link_battery_match'] and row['pitcher_id']==pitch['pitcher_id'] and row['catcher_id']==pitch['catcher_id']
            if row['pitch_link']=='exact_actionPlayId':assert raw['actionPlayId']==pitch['pitch_id']
            elif row['pitch_link']=='exact_event':assert k==lk
            else:raise AssertionError('Unknown link mechanism')
            if row['family'] in ['WP','PB']:
                labels[lk]+=1;assert pitch['blocking_at_risk']
                if all(pitch[f'runner_{b}'] is None for b in [1,2,3]):
                    empty_blocking.append({**{c:row[c] for c in key+['family']},'pre_strikes':pitch['pre_strikes']})
    assert max(labels.values())==1 and len(labels)==248
    assert not ev.filter(pl.col('family').is_in(['WP','PB'])&pl.col('linked_pitch_index').is_null()).height
    assert len(empty_blocking)==9
    assert ev.filter(pl.col('family').is_in(['SB','CS','POCS'])&pl.col('runner_from_base').is_null()).is_empty()
    checks=[]
    for r in ev.filter(pl.col('family').is_in(['SB','CS','POCS'])).to_dicts():
        game=r['game_pk'];ab=r['at_bat_index']
        play=next(a for a in payloads[game]['liveData']['plays']['allPlays'] if a['about']['atBatIndex']==ab)
        movements=[m for m in play.get('runners',[]) if m['details'].get('runner',{}).get('id')==r['runner_id']
            and m['details'].get('playIndex')==r['event_index'] and m['details'].get('movementReason')=='r_'+r['event_type']]
        starts={m['movement'].get('start') for m in movements}
        checks.append({'game_pk':game,'at_bat_index':ab,'event_index':r['event_index'],'runner_id':r['runner_id'],
            'match':starts=={str(r['runner_from_base'])+'B'},'starts':sorted(str(s) for s in starts)})
    assert all(r['match'] for r in checks)
    bylevel=pi.group_by('season','level').agg(pl.len().alias('pitches'),pl.col('blocking_at_risk').sum().alias('blocking_risk_pitches')).sort('season','level')
    out={'verified':True,'games':128,'pitches':pi.height,'blocking_risk_pitches':pi['blocking_at_risk'].sum(),
        'scored_events':ev.height,'event_families':ev.group_by('family').len().sort('family').to_dicts(),
        'runner_pitch_exposures':rp.height,'occupied_next_base_exposures':rp.filter(pl.col('next_base_occupied')).height,
        'empty_base_blocking_failures':empty_blocking,'unlinked_events':unlinked,
        'attempt_movement_start_checks':len(checks),'attempt_start_disagreements':[r for r in checks if not r['match']],
        'half_transition_checks':half_transition_checks,'PA_index_contiguity_games':128,
        'level_year_coverage':bylevel.to_dicts(),
        'positive_player_checks':tables['player-checks'].group_by('metric').agg(pl.len().alias('checks'),
            (pl.col('official')>0).sum().alias('nonzero_checks'),pl.col('official').sum().alias('count_total')).sort('metric').to_dicts(),
        'new_fits':0,'protected_outcomes_used':False,'production_changed':False}
    (ROOT/'verification.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['empty_base_blocking_failures','unlinked_events','level_year_coverage','positive_player_checks']},indent=2))


if __name__=='__main__':main()
