"""Actual 2026 fielding positions at all affiliated levels, not bio labels."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip
import json
import polars as pl
import capture_hitter_2027_nonbatting_sources as source
from universal_baseball.position_role_source import project_fielding_usage_splits
from universal_baseball.defense_position_history import annual_usage,LEAGUE_LEVEL
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-position-source'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    receipt=PUBLIC/'position-source-2026.json';assert not receipt.exists()
    source.OUT=OUT;OUT.mkdir(parents=True,exist_ok=True)
    tasks=[(f'fielding-{sport}','https://statsapi.mlb.com/api/v1/stats',dict(stats='season',group='fielding',season=2026,
        sportIds=sport,gameType='R',playerPool='ALL',limit=20000),'json') for sport in [11,12,13,14,16]]
    with ThreadPoolExecutor(max_workers=3) as pool:captures=list(pool.map(source.capture,tasks))
    old=ROOT/'reports/generated/hitter-2027-nonbatting-source/official-fielding-rows.json.gz'
    selections=[(1,old)]+[(int(c['source'].split('-')[-1]),Path(c['parsed_path'])) for c in captures]
    frames=[]
    for sport,path in selections:
        rows=json.loads(gzip.decompress(path.read_bytes()));by={}
        for r in rows:
            league=int(r['league']['id']);assert league in LEAGUE_LEVEL
            by.setdefault(league,[]).append(r)
        for league,items in sorted(by.items()):
            f=project_fielding_usage_splits(items,season=2026,league_id=league,level_group=LEAGUE_LEVEL[league])
            # Splits are player/position/league totals. A displayed last team
            # must not become a stint or evidence of club ownership.
            key=['season','league_id','player_id','position_code']
            assert f.unique(key).height==len(f),'Duplicate fielding scope'
            frames.append(f.with_columns(pl.lit(sport).alias('sport_id'),pl.lit(f'official2026:{sport}').alias('source_id'),
                pl.lit(f'league:{league}').alias('usage_scope'),pl.lit(LEAGUE_LEVEL[league]).alias('normalized_level'),
                pl.lit(True).alias('level_subtype_certified'),pl.lit(False).alias('team_usage_certified'),pl.lit(sport==1).alias('is_mlb')))
    fielding=pl.concat(frames,how='vertical_relaxed');annual=annual_usage(fielding)
    for name,f in [('fielding',fielding),('annual-usage',annual)]:
        p=OUT/f'{name}.parquet';assert not p.exists();f.write_parquet(p)
    cases=[]
    for pid in [804944,805811,808393,592450,665487,660271,672275,596019]:
        f=fielding.filter(pl.col('player_id')==pid)
        cases.append(dict(player_id=pid,source_positions=f.select('normalized_level','position_abbreviation','games_played','games_started','source_innings','fielding_outs').to_dicts(),
            interpretation='Observed positions define evidence, not guaranteed future assignments. DH gets zero defensive outs; last listed team is not rights authority.'))
    write_once(receipt,dict(season=2026,scopes=6,rows=len(fielding),players=fielding['player_id'].n_unique(),
        annual_rows=len(annual),captures=captures,cases=cases,source_walkthrough='pending',
        output_hashes={str(OUT/f'{n}.parquet'):sha256_file(OUT/f'{n}.parquet') for n in ['fielding','annual-usage']},
        runner_sha256=sha256_file(Path(__file__))))
    print(f'2026 position source: {len(fielding)} position/league rows.',flush=True)


if __name__=='__main__':main()
