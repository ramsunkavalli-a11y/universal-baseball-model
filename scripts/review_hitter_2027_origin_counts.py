"""Certify reusable event inputs and walk fixed players before any model fit."""
from pathlib import Path
import csv
import json

import polars as pl

from universal_baseball.hitter_season_intake import SPORTS
from universal_baseball.hitter_talent_bridge import event_counts
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v31 import bucket
from capture_hitter_2027_origin_counts import ROOT, OUT, write_once

EVIDENCE = ROOT/'reports/model-evidence/hitter-2027-v1'
FIXED = [804944,805811,808393,592450,665487,660271,672275,596019]


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    destination = EVIDENCE/'origin-input-review.json'
    if destination.exists():
        raise ValueError('Preserve completed source review')
    reviews = [EVIDENCE/'origin-counts-review.json', EVIDENCE/'team-stints-review.json']
    agg, team = [read(p) for p in reviews]
    assert all(r['event_totals_match'] for r in agg['levels'])
    assert team['all_team_totals_match'] and team['all_player_sport_totals_match']
    source = Path(team['output_path'])
    assert sha256_file(source) == team['output_sha256']
    for r in team['team_reviews']:
        assert sha256_file(Path(r['source_path'])) == r['source_sha256']
    f = pl.read_parquet(source)
    f = f.with_columns(pl.Series('bucket',[bucket(r) for r in f.iter_rows(named=True)]),
        pl.col('reported_age').cast(pl.Float64), pl.col('plate_appearances').alias('metadata_pa'),
        pl.col('sport_id').replace_strict(SPORTS).alias('level_group'))
    count_columns = list(dict.fromkeys(['plate_appearances',*[v[0] for v in EVENTS.values()],*[v[1] for v in EVENTS.values()]]))
    c = f.group_by('season','player_id','bucket').agg(pl.col(count_columns).sum()).sort('player_id','bucket')
    exclusive = event_counts(c)
    assert exclusive.sum() == c['plate_appearances'].sum()
    official_path = ROOT/'reports/generated/hitter-final-2026-source/actual-player-events-2026.parquet'
    official = pl.read_parquet(official_path).sort('player_id')
    mlb = c.filter(pl.col('bucket')=='MLB').sort('player_id')
    assert mlb['player_id'].equals(official['player_id'])
    assert (event_counts(mlb) == official.select('other','K','UBB','HBP','1B','2B','3B','HR').to_numpy()).all()
    minor_path = Path('C:/Users/ramav/Documents/Baseball/2026 Data/FanGraphs_MiLB_Batting_2026-09-28.csv')
    with minor_path.open(encoding='utf-8-sig',newline='') as stream:
        fg = {int(r['MLBAMID']):r for r in csv.DictReader(stream)}
    minor = c.filter(pl.col('bucket')!='MLB').group_by('player_id').agg(pl.col('plate_appearances').sum())
    differences=[]
    for r in minor.to_dicts():
        m=fg.get(r['player_id']); fgpa=int(m['PA']) if m else None
        if (fgpa if fgpa is not None else 0) != r['plate_appearances']:
            differences.append(dict(**r,fg_pa=fgpa))
    unexpected_fg=set(fg)-set(minor['player_id'])
    # Fixed source cases and origin-only comparable players, not outcome-selected
    # forecast successes. Talent/outcome walkthroughs follow the actual model test.
    profiles=f.group_by('player_id','bucket').agg(pl.col('plate_appearances').sum(),
        pl.col('reported_age').median(),pl.col('player_name').first(),pl.col('position').first())
    cases=[]
    for pid in FIXED:
        history=f.filter(pl.col('player_id')==pid).sort('sport_id','team_id')
        if history.is_empty():
            raise ValueError(f'Fixed source case absent: {pid}')
        primary=profiles.filter(pl.col('player_id')==pid).sort('plate_appearances',descending=True).row(0,named=True)
        peers=profiles.filter((pl.col('player_id')!=pid)&(pl.col('bucket')==primary['bucket']))
        peers=peers.with_columns((((pl.col('reported_age')-primary['reported_age'])/3)**2+
            ((pl.col('plate_appearances')-primary['plate_appearances'])/200)**2+
            (pl.col('position')!=primary['position']).cast(pl.Int64)).alias('distance')).sort('distance','player_id').head(3)
        ids=[pid,*peers['player_id'].to_list()]
        cases.append(dict(player_id=pid,player_name=primary['player_name'],
            actual_source_rows=history.to_dicts(), assembled_event_inputs=c.filter(pl.col('player_id')==pid).to_dicts(),
            origin_only_peers=peers.to_dicts(),peer_source_rows=f.filter(pl.col('player_id').is_in(ids[1:])).to_dicts(),
            interpretation='Current-season source evidence. No prediction or performance claim has been made.'))
    outputs={}
    for filename, frame in [('team-season-inputs.parquet',f),('counts.parquet',c)]:
        path=OUT/filename
        assert not path.exists(),path
        frame.write_parquet(path)
        outputs[str(path)]=sha256_file(path)
    walk_path=EVIDENCE/'origin-source-player-walkthrough.json'
    write_once(walk_path,dict(selection='Eight fixed cases declared in finalization plan; nearest three same-level age/PA/position peers without outcomes',
        cases=cases,player_walkthrough_status='complete_for_source_intake_only',
        limit='No new fitted model yet; gain/harm/false-high/false-low categories do not apply to an input capture.'))
    review=dict(status='event_inputs_approved_not_a_2027_forecast',source_season=2026,forecast_season=2027,
        team_sources=team['team_sources'],team_season_rows=len(f),player_bucket_rows=len(c),
        mlb_events_match_previously_certified_completed_season=True,
        all_team_and_player_totals_reconcile=True,unclassified_pa=int(f['unclassified_pa'].sum()),
        unclassified_rows=f.filter(pl.col('unclassified_pa')>0).select('player_id','player_name','bucket','unclassified_pa').to_dicts(),
        minor_fg_pa_differences=differences,fg_ids_without_official_minor=sorted(unexpected_fg),
        source_approved_for_event_count_features=True,player_walkthrough_status='complete_for_source_intake_only',
        player_walkthrough_path=str(walk_path),
        output_hashes=outputs,
        input_hashes={str(p):sha256_file(p) for p in [source,official_path,minor_path,*reviews,Path(__file__)]},
        remaining=['2026 roster/absence/debut and international membership refresh',
                   '2026 tracking, defense and running source update',
                   'dated promotion/rehab intervals where required by a feature'],
        claim_limits='Does not certify talent estimates, current ownership, promotion dates or every population member.',
        models_fitted=0,old_forecasts_changed=False)
    write_once(destination,review)
    print(f'Approved {len(c)} event-count rows; eight source cases with 24 peers reviewed. MiLB FG PA differences: {len(differences)}; unclassified PA retained: {review["unclassified_pa"]}',flush=True)


if __name__=='__main__':
    main()
