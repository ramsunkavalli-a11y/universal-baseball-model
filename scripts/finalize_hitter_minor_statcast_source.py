"""Add reviewed official boundaries and played venues without overwriting source."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.hitter_statcast_measurement import project_measurements,interference_award
from universal_baseball.hitter_statcast_history import annual_launch_features
from universal_baseball.storage import sha256_file
import materialize_hitter_minor_statcast_source as original

ROOT=original.ROOT;SOURCE=original.OUT;OUT=ROOT/'reports/generated/hitter-minor-statcast-reviewed-source'
BOUNDARY=ROOT/'docs/hitter-minor-statcast-reviewed-boundary.md'


def write(name,value):original.capture.write(OUT/name,value)


def classifications(review):
    decisions=[]
    restored={(2022,665032,621453):32,(2024,760455,694200):78,(2024,760508,701296):8}
    for c in review['cases']:
        assert c['backbone_boundary_matches_current_feed']
        key=(c['season'],c['game_pk'],c['player_id'])
        if c['contact_residual']==1:
            p=[p for p in c['plays'] if p['official_event']=='strikeout' and any(r['type']=='X' for r in p['source_rows'])]
            assert len(p)==1 and 'strikes out' in p[0]['official_description'].lower()
            classification='noncontact_strikeout_mislabeled_inplay'
        elif key in restored:
            p=[p for p in c['plays'] if p['at_bat_number']==restored[key]]
            assert len(p)==1 and len(p[0]['source_rows'])==1 and len(p[0]['inplay_pitch_events'])==1
            row=p[0]['source_rows'][0];event=p[0]['inplay_pitch_events'][0]
            assert row['events'] is None and row['type']=='S' and int(row['pitch_number'])==event['pitchNumber']
            hit=event.get('hitData',{})
            for column,field in [('launch_speed','launchSpeed'),('launch_angle','launchAngle')]:
                assert (row[column] is None and hit.get(field) is None) or np.isclose(float(row[column]),float(hit[field]),atol=1e-9)
            classification='official_terminal_metadata_repair'
        else:
            p=[p for p in c['plays'] if not p['source_rows'] and p['official_event'] not in ['strikeout','strikeout_double_play','walk','hit_by_pitch','intent_walk','catcher_interf']]
            assert len(p)==1 and not p[0]['inplay_pitch_events'] and not p[0]['hit_data_events']
            classification='noncontact_batter_interference_AB' if 'out on batter interference' in p[0]['official_description'].lower() else 'physical_contact_missing_pitch_evidence'
        play=p[0]
        decisions.append(dict(season=c['season'],game_pk=c['game_pk'],player_id=c['player_id'],
            at_bat_number=play['at_bat_number'],classification=classification,official_event=play['official_event'],
            official_description=play['official_description'],source_rows=play['source_rows'],residual=c['contact_residual'],
            expected_contact_count=c['expected_contact_count']))
    totals={label:sum(d['classification']==label for d in decisions) for label in set(d['classification'] for d in decisions)}
    assert totals==dict(noncontact_strikeout_mislabeled_inplay=1,official_terminal_metadata_repair=3,
        noncontact_batter_interference_AB=13,physical_contact_missing_pitch_evidence=7)
    return decisions,totals


def main():
    assert not (OUT/'source-report.json').exists(),'Preserve reviewed source'
    report=json.loads((SOURCE/'source-report.json').read_text(encoding='utf8'))
    for group in ['input_hashes','output_hashes']:
        for p,h in report[group].items():assert sha256_file(Path(p))==h
    review=json.loads((SOURCE/'official-contact-and-venue-review.json').read_text(encoding='utf8'))
    assert review['source_report_sha256']==sha256_file(SOURCE/'source-report.json')
    decisions,totals=classifications(review);OUT.mkdir(parents=True,exist_ok=True)
    write('contact-classifications.json',dict(cases=decisions,counts=totals,all_residuals_classified=True))
    overrides=[dict(season=s['season'],**p) for s in review['split_venue_reviews'] for p in s['play_venue_overrides']]
    write('played-venue-overrides.json',dict(games=6,overrides=overrides))
    yearly=[];summary=[];hashes={str(p):sha256_file(p) for p in [BOUNDARY,Path(__file__),SOURCE/'source-report.json',SOURCE/'official-contact-and-venue-review.json']}
    capture=json.loads((original.SOURCE/'season-capture.json').read_text(encoding='utf8'))
    for y in range(2021,2025):
        paths=[Path(p) for r in capture['receipts'] if int(r['start'][:4])==y for p in r['outputs'] if p.endswith('.parquet')]
        raw=pl.concat([pl.read_parquet(p) for p in paths]);changed=[]
        ds=[d for d in decisions if d['season']==y]
        for d in ds:
            if d['classification']!='official_terminal_metadata_repair':continue
            match=(pl.col('game_pk')==str(d['game_pk']))&(pl.col('batter')==str(d['player_id']))&(pl.col('at_bat_number')==str(d['at_bat_number']))
            assert raw.filter(match).height==1
            raw=raw.with_columns(*[pl.when(match).then(pl.lit(v)).otherwise(pl.col(k)).alias(k) for k,v in
                [('type','X'),('events',d['official_event']),('des',d['official_description'])]])
            changed.append(d)
        # Every non-contact outcome is excluded even if provider type says X.
        noncontact=raw['events'].is_in(['strikeout','strikeout_double_play','walk','intent_walk','hit_by_pitch','catcher_interf'])
        selected=raw.filter(raw['events'].fill_null('').str.strip_chars().ne('')&~noncontact)
        launch,excluded=project_measurements(selected,y)
        env,h=original.pilot.environments(y);hashes.update(h)
        schedule,unique,conflict,h=original.schedules(y);hashes.update(h)
        venue=unique.select('game_pk','venue_id','venue_name','home_team_id','away_team_id')
        launch=launch.join(env.select('game_pk','player_id','league_id','level_group'),on=['game_pk','player_id'],validate='m:1')
        launch=launch.join(venue,on='game_pk',how='left',validate='m:1')
        oo=[r for r in overrides if r['season']==y]
        if oo:
            v=pl.DataFrame(oo).select('game_pk','at_bat_number',pl.col('venue_id').alias('played_venue_id'),pl.col('venue_name').alias('played_venue_name'))
            assert v.unique(['game_pk','at_bat_number']).height==len(v)
            launch=launch.join(v,on=['game_pk','at_bat_number'],how='left',validate='m:1').with_columns(
                pl.coalesce('played_venue_id','venue_id').alias('venue_id'),pl.coalesce('played_venue_name','venue_name').alias('venue_name')).drop('played_venue_id','played_venue_name')
        assert launch['venue_id'].null_count()==0 and launch['league_id'].null_count()==0
        launch.write_parquet(OUT/f'launch-events-{y}.parquet')
        # The canonical ledger does NOT gain invented pitches for seven known
        # physical contacts that neither source encoded at pitch grain.
        missing=[d for d in ds if d['classification']=='physical_contact_missing_pitch_evidence']
        known_missing=[]
        for d in missing:
            context=env.filter((pl.col('game_pk')==d['game_pk'])&(pl.col('player_id')==d['player_id'])).row(0,named=True)
            assert 'bunt' not in d['official_description'].lower()
            known_missing.append(dict(**d,league_id=context['league_id'],level_group=context['level_group'],game_date=context['game_date']))
        write(f'missing-physical-contacts-{y}.json',dict(cases=known_missing,no_pitch_identity_fabricated=True))
        normal=selected.filter(~interference_award()).with_columns(pl.col('game_pk').cast(pl.Int64),pl.col('batter').cast(pl.Int64).alias('player_id'))
        cnt=normal.group_by('game_pk','player_id').agg(pl.len().alias('source_contacts'))
        games=raw['game_pk'].cast(pl.Int64).unique().to_list()
        paired=env.filter(pl.col('game_pk').is_in(games)).join(cnt,on=['game_pk','player_id'],how='left').with_columns(pl.col('source_contacts').fill_null(0))
        subtract={(d['game_pk'],d['player_id']):1 for d in ds if d['classification']=='noncontact_batter_interference_AB'}
        add={(d['game_pk'],d['player_id']):1 for d in missing}
        paired=paired.with_columns(pl.Series('noncontact_AB',[subtract.get((r['game_pk'],r['player_id']),0) for r in paired.iter_rows(named=True)]),
            pl.Series('known_missing_contacts',[add.get((r['game_pk'],r['player_id']),0) for r in paired.iter_rows(named=True)]))
        assert paired.select((pl.col('source_contacts')+pl.col('known_missing_contacts')==pl.col('expected_contact_count')-pl.col('noncontact_AB')).all()).item()
        paired.write_parquet(OUT/f'contact-boundary-reconciliation-{y}.parquet')
        for league in launch['league_id'].unique().sort():
            q=launch.filter(pl.col('league_id')==league);a=annual_launch_features(q)
            physical={r['player_id']:sum(m['player_id']==r['player_id'] and m['league_id']==league for m in known_missing) for r in a.iter_rows(named=True)}
            a=a.with_columns(pl.lit(int(league)).alias('league_id'),pl.lit(q['level_group'][0]).alias('level_group'),
                pl.Series('known_missing_physical_contacts',[physical.get(p,0) for p in a['player_id']]),
                pl.col('pair_coverage').alias('pair_coverage_in_returned_contacts'))
            a=a.with_columns((pl.col('terminal_nonbunt_contacts')+pl.col('known_missing_physical_contacts')).alias('official_nonbunt_contact_opportunities'))
            a=a.with_columns((pl.col('measured_pair_contacts')/pl.col('official_nonbunt_contact_opportunities')).alias('pair_coverage'))
            # Independent numpy recomputation of every continuous sample summary.
            for r in a.iter_rows(named=True):
                player=q.filter(pl.col('player_id')==r['player_id']);ev=player.filter(pl.col('valid_ev'))['launch_speed'].to_numpy();la=player.filter(pl.col('valid_la'))['launch_angle'].to_numpy()
                for name,val in [('mean_ev',np.mean(ev) if len(ev) else None),('ev95',np.quantile(ev,.95,method='linear') if len(ev) else None),
                    ('hard_hit_fraction',np.mean(ev>=95) if len(ev) else None),('mean_la',np.mean(la) if len(la) else None),
                    ('la_sd',np.std(la,ddof=1) if len(la)>1 else None),('sweet_spot_fraction',np.mean((la>=8)&(la<=32)) if len(la) else None)]:
                    assert (r[name] is None and val is None) or np.isclose(r[name],val,atol=1e-10)
            yearly.append(a)
        summary.append(dict(season=y,canonical_nonbunt_contacts=len(launch),complete_pairs=int(launch['complete_pair'].sum()),
            metadata_repaired=len(changed),known_missing_physical_contacts=len(missing),exact_player_game_boundaries=len(paired),
            invalid_ev=int(launch['invalid_ev'].sum()),invalid_la=int(launch['invalid_la'].sum())))
    annual=pl.concat(yearly);annual.write_parquet(OUT/'annual-launch-features.parquet')
    for r in review['receipts']:
        p=SOURCE/'official-review'/f'feed-{r["season"]}-{r["game_pk"]}.json.gz'
        assert sha256_file(p)==r['compressed_sha256'];hashes[str(p)]=sha256_file(p)
    write('source-report.json',dict(seasons=summary,annual_player_league_seasons=len(annual),continuous_summaries_independently_verified=True,
        all_player_game_contact_boundaries_reconciled=True,all_launch_venues_resolved=True,input_hashes=hashes,
        output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.is_file()},source_walkthrough_status='pending',
        source_approved=False,models_fitted=0,provider_original_vintage_known=False,protected_outcomes_used=False))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
