"""Origin-selected peers and all position/level paths after count calibration."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math
from zipfile import ZipFile

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from archive_minor_count_fits_v20 import digest

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-count-reliability-v20'
OUT=ROOT/'reports/generated/defense-count-reliability-v20'
SOURCE=ROOT/'reports/generated/defense-minor-counts-v18'


def read(p):
    if not p.exists() and p.parent.name=='fits':
        with ZipFile(PUBLIC/'reference-fits.zip') as archive:
            return json.loads(gzip.decompress(archive.read(p.name)).decode('utf8'))
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def write(p,v):
    assert not p.exists()
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(v,f,allow_nan=False,separators=(',',':'))


def main():
    replay=read(PUBLIC/'independent-review.json.gz')
    assert replay['all_posteriors_and_distributions'] and replay['scores_and_2000_person_bootstraps_replayed']
    for p,h in replay['hashes'].items():assert digest(Path(p))==h,p
    allrows=pl.read_parquet(OUT/'predictions.parquet').to_dicts();rs=[r for r in allrows if r['origin_year']==2022]
    levels=read(PUBLIC/'source-levels.json.gz');groups={g['group_id']:g for g in read(PUBLIC/'reference-groups.json.gz')}
    raw=pl.read_parquet(SOURCE/'counts.parquet').select('season','player_id','position_code','normalized_level','team_id',
        'fielding_outs','putOuts','assists','errors','chances','throwingErrors','capture_path').to_dicts()
    official=pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').to_dicts()
    selections=[]
    def choose(r,reason):
        selections.append(dict(player_id=r['player_id'],origin_year=r['origin_year'],position=r['position'],level=r['level'],channel=r['channel'],reason=reason))
    for pid,pos,lev,c,reason in [(686527,9,'COMPLEX',0,'fixed_six_chance_Canzone'),(687518,5,'AA',0,'fixed_sixteen_chance_Frick'),
                               (696285,8,'A',3,'fixed_Young_CF'),(683011,6,'AA',0,'fixed_Volpe_AA')]:
        q=[r for r in rs if (r['player_id'],r['position'],r['level'],r['channel'])==(pid,pos,lev,c)]
        assert len(q)==1;choose(q[0],reason)
    finite=[r for r in rs if r['target_status']=='observed_positive_exposure' and not r['baseline_impossible'] and not r['candidate_impossible']]
    by=defaultdict(list)
    for r in finite:by[r['player_id']].append(r)
    gains={pid:float(np.mean([r['candidate_loss']-r['baseline_loss'] for r in v])) for pid,v in by.items()}
    for pid,reason in [(min(gains,key=lambda p:(gains[p],p)),'largest_person_balanced_finite_gain'),
                       (max(gains,key=lambda p:(gains[p],-p)),'largest_person_balanced_finite_harm')]:
        row=max(by[pid],key=lambda r:abs(r['candidate_loss']-r['baseline_loss']));choose(row,reason)
    residual=lambda r:r['candidate_mean']-r['target_count']/r['target_exposure']
    choose(max(finite,key=lambda r:(residual(r),-r['player_id'])),'largest_raw_rate_overprediction_different_channel_units')
    choose(min(finite,key=lambda r:(residual(r),r['player_id'])),'largest_raw_rate_underprediction_different_channel_units')
    ordinary=sorted(finite,key=lambda r:(abs(residual(r)),r['player_id'],r['position'],r['level'],r['channel']))
    choose(ordinary[len(ordinary)//2],'median_absolute_raw_rate_error')
    chosen_rows=[r for r in rs if any(all(r[k]==s[k] for k in ('player_id','position','level','channel')) for s in selections)]
    if not any(r['level'] in ('DSL','COMPLEX') and r['current_exposure']<20 for r in chosen_rows):
        # The fixed Canzone record normally supplies this contrast.
        thin=sorted((r for r in rs if r['level'] in ('DSL','COMPLEX') and r['current_exposure']<20),
                    key=lambda r:(r['player_id'],r['position'],r['level'],r['channel']))
        if thin:choose(thin[0],'origin_selected_thin_lower_level')
    if not any(r['target_status']!='observed_positive_exposure' for r in rs if any(
        r['player_id']==s['player_id'] and r['position']==s['position'] and r['level']==s['level'] for s in selections)):
        unknown=sorted((r for r in rs if r['target_status']!='observed_positive_exposure'),key=lambda r:(r['player_id'],r['position'],r['level'],r['channel']))
        if unknown:choose(unknown[0],'origin_selected_unknown_same_level_outcome')
    peer_manifest=[];people={(s['origin_year'],s['player_id']) for s in selections}
    for s in selections:
        focal=next(r for r in allrows if all(r[k]==s[k] for k in ('player_id','origin_year','position','level','channel')))
        pool=[r for r in allrows if r['origin_year']==s['origin_year'] and r['position']==s['position'] and r['level']==s['level']
              and r['channel']==s['channel'] and r['player_id']!=s['player_id']]
        def distance(r):
            age=abs(r['age']-focal['age']) if r['age'] is not None and focal['age'] is not None else 100.
            return (age,abs(math.log1p(r['current_exposure'])-math.log1p(focal['current_exposure'])),r['player_id'])
        peers=sorted(pool,key=distance)[:3];people.update((p['origin_year'],p['player_id']) for p in peers)
        peer_manifest.append(dict(focal=s,selection='same origin/position/level/channel; age distance, log current denominator distance, player ID',
                                  peers=[dict(player_id=p['player_id'],age=p['age'],current_exposure=p['current_exposure']) for p in peers]))
    fits={};walks=[]
    for year,pid in sorted(people):
        q=[r for r in allrows if r['origin_year']==year and r['player_id']==pid];assert q
        known=[r for r in levels if r['player_id']==pid and year-2<=r['origin_year']<=year]
        raw_known=[r for r in raw if r['player_id']==pid and year-2<=r['season']<=year]
        future=[r for r in raw if r['player_id']==pid and r['season']==year+1]
        mlb=[dict(season=r['season'],position=r['position_code'],outs=r['fielding_outs']) for r in official
             if r['player_id']==pid and r['season']==year+1 and r['is_mlb'] and r['fielding_outs']>0]
        details=[]
        for r in q:
            gid=r['group_id']
            if gid not in fits:fits[gid]=read(PUBLIC/'fits'/f'{gid}.json.gz')
            g=groups[gid];members=[levels[i] for i in g['source_row_indices']]
            # Sparse records that inflated the old moments are retained, not erased.
            ones=[dict(player_id=m['player_id'],name=m['player_name'],season=m['origin_year'],position=m['position'],level=m['level'],
                       outs=m['outs'],errors=m['errors'],throwingErrors=m['throwingErrors'],chances=m['chances'])
                  for m in members if r['channel']<2 and m['chances']==1]
            details.append(dict(prediction=r,reference_scope=g['scope'],reference_people=len(g['people']),
                                baseline_prior=fits[gid]['baseline'],candidate_prior=fits[gid]['candidate'],
                                one_chance_reference_records=ones,reference_group_id=gid))
        walks.append(dict(origin_year=year,player_id=pid,name=q[0]['player_name'],age=q[0]['age'],known_sources=known,
                          raw_known_source_records_including_thin_prior_positions=raw_known,
                          all_current_positions_and_levels=details,next_minor_position_level_sources=future,
                          next_MLB_exposure_context_only=mlb,
                          MLB_quality_or_value_forecast=None,quality_claim='No defensive talent grade was fitted'))
    paths=[Path(__file__),PUBLIC/'independent-review.json.gz',PUBLIC/'summary.json.gz',OUT/'predictions.parquet',
           SOURCE/'counts.parquet',
           ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet']
    write(PUBLIC/'player-walkthrough.json.gz',dict(selection_manifest=selections,peers=peer_manifest,people=len(people),walks=walks,
        player_walkthrough_status='pending_main_review',future_context_not_fit_input=True,all_positions_retained=True,
        hashes={str(p):sha256_file(p) for p in paths}))
    for s in selections:
        w=next(w for w in walks if w['player_id']==s['player_id'] and w['origin_year']==s['origin_year'])
        d=next(d for d in w['all_current_positions_and_levels'] if all(d['prediction'][k]==s[k] for k in ('position','level','channel')))
        r=d['prediction']
        print(json.dumps(dict(reason=s['reason'],name=w['name'],position=s['position'],level=s['level'],channel=s['channel'],
             current=[r['current_count'],r['current_exposure']],weights=[r['baseline_weight'],r['candidate_weight']],
             rates=[r['baseline_mean'],r['candidate_mean']],strengths=[d['baseline_prior']['strength'],d['candidate_prior']['strength']],
             target=[r['target_count'],r['target_exposure']],status=r['target_status'],
             losses=[r.get('baseline_loss'),r.get('candidate_loss')],next_MLB_outs=sum(v['outs'] for v in w['next_MLB_exposure_context_only']))),flush=True)
    print(dict(selected=len(selections),distinct_player_origins=len(people),walkthrough='pending main review'),flush=True)


if __name__=='__main__':main()
