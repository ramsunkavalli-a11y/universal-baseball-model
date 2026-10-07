"""Fixed names and origin-selected peers, counts through later MLB measurement."""
from collections import defaultdict
from pathlib import Path
import json
import math

import polars as pl

from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-minor-counts-v18'
PUBLIC=ROOT/'reports/model-evidence/defense-minor-counts-v18'
NAMES=('Bobby Witt Jr.','Jeremy Peña','Anthony Volpe','CJ Abrams','Ceddanne Rafaela',
       'Xavier Edwards','Patrick Bailey','Cal Raleigh','Alejandro Kirk','Bryce Eldridge')


def main():
    protections()
    assert not (OUT/'player-walkthrough.json').exists()
    review=json.loads((OUT/'independent-review.json').read_text(encoding='utf8'))
    for path,h in review['hashes'].items():assert sha256_file(Path(path))==h,path
    assert review['status']=='independently_replayed_pending_player_review'
    origins=pl.read_parquet(OUT/'origins.parquet').to_dicts()
    counts=pl.read_parquet(OUT/'counts.parquet').to_dicts()
    labels=pl.read_parquet(OUT/'labels.parquet').to_dicts()
    support=pl.read_parquet(OUT/'profile-support.parquet').to_dicts()
    raw=defaultdict(list);lab=defaultdict(list);sup=defaultdict(list)
    key=lambda r:(r['origin_year'],r['player_id'],r['position'])
    for r in counts:raw[r['season'],r['player_id'],int(r['position_code'])].append(r)
    for r in labels:lab[key(r)].append(r)
    for r in support:sup[key(r)].append(r)
    native=defaultdict(list);catcher=defaultdict(list);official=defaultdict(list)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts():native[r['player_id']].append(r)
    for r in pl.read_parquet(ROOT/'reports/generated/catcher-throw-block-v5/extension-annual.parquet').to_dicts():catcher[r['player_id']].append(r)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').filter(pl.col('is_mlb')).to_dicts():official[r['player_id']].append(r)
    focal=[];resolution=[]
    for name in NAMES:
        rs=[r for r in origins if r['player_name']==name]
        ids={r['player_id'] for r in rs};assert len(ids)==1,(name,ids)
        years={r['origin_year'] for r in rs}
        y=2019 if 2019 in years else max(s for s in years if s<=2022) if any(s<=2022 for s in years) else min(years)
        f=min((r for r in rs if r['origin_year']==y),key=lambda r:(-r['minor_outs'],r['position']))
        focal.append((f,'fixed_name'))
        resolution.append(dict(name=name,player_id=f['player_id'],origin=y,position=f['position']))
    # Source-only older extremes expose the small/large-sample contrast, not favorable outcomes.
    early=[r for r in origins if r['origin_year']==2009 and not r['prior_current_MLB_fielding'] and r['position']==6]
    focal.extend([(min(early,key=lambda r:(r['minor_outs'],r['player_id'])),'older_thin'),
                  (min(early,key=lambda r:(-r['minor_outs'],r['player_id'])),'older_large')])
    def trace(r):
        y,pid,pos=key(r)
        paths=[]
        for s in range(y+1,min(y+5,2025)+1):
            use=[t for t in official[pid] if t['season']==s and 2<=int(t['position_code'])<=9]
            paths.append(dict(season=s,elapsed=s-y,
                official_position_outs=sum(t['fielding_outs'] for t in use if int(t['position_code'])==pos),
                official_other_position_outs={p:sum(t['fielding_outs'] for t in use if int(t['position_code'])==p) for p in range(2,10) if p!=pos and any(int(t['position_code'])==p and t['fielding_outs']>0 for t in use)},
                native_range=[t for t in native[pid] if t['season']==s],
                native_catcher=[t for t in catcher[pid] if t['season']==s] if pos==2 else []))
        return dict(origin=r,raw_source_rows=raw[y,pid,pos],labels=lab[y,pid,pos],
                    chronological_support=sup[y,pid,pos],annual_future_paths=paths,
                    prediction=None,prediction_error=None,no_fitted_forecast=True)
    walks=[];lines=['# Minor defense source and later MLB player review','',
        'These are source and support traces, not fitted predictions. Future absence means unknown quality, not zero talent. Each peer is selected before inspecting future performance.','',
        'Fixed names are resolved against source IDs. The original runner contains an unused FIXED tuple with five incorrect IDs; it does not select source, labels or support. This review uses the names required by the contract, preserves the original runner, and records the corrected mapping.','']
    for r,selection in focal:
        y,pid,pos=key(r)
        pool=[t for t in origins if t['origin_year']==y and t['level']==r['level'] and t['position']==pos and t['player_id']!=pid]
        # Unknown ages are sorted after known age matches; no future fields enter distance.
        peers=sorted(pool,key=lambda t:(abs(t['age']-r['age']) if t['age'] is not None and r['age'] is not None else 999,
                         abs(math.log1p(t['minor_outs'])-math.log1p(r['minor_outs'])),t['player_id']))[:3]
        walks.append(dict(selection=selection,focal=trace(r),peers=[trace(t) for t in peers],
            peer_rule='same origin, level and position; nearest age then log exposure then ID; no future fields',review_status='pending_main_review'))
        lines.extend([f"## {r['player_name']} {y}",'',
            f"Position {pos}, {r['level']}, age {r['age']} ({r['age_basis']}), {r['minor_outs']} minor outs. Prior/current MLB fielding: {r['prior_current_MLB_fielding']}. Levels: {r['level_exposure']}.",'',
            f"Putouts {r['putOuts']}, assists {r['assists']}, errors {r['errors']}, chances {r['chances']}, throwing errors {r['throwingErrors']}, double plays {r['doublePlays']}.",''])
        if pos==2:lines.extend([f"Caught stealing {r['caughtStealing']}, steals allowed {r['stolenBases']}, passed balls {r['passedBall']}, wild pitches {r['wildPitches']}, interference {r['catchersInterference']}, pickoffs {r['pickoffs']}.",''])
        for t in [r,*peers]:
            lines.append(f"{t['player_name']} ({t['player_id']}): age {t['age']}, {t['minor_outs']} outs; PO/A/E {t['putOuts']}/{t['assists']}/{t['errors']}.")
            lines.append('')
            for q in lab[key(t)]:
                s=next((s for s in sup[key(t)] if s['component']==q['component'] and s['window']==q['window']),None)
                lines.append(f"- {q['component']} {q['window']} years: {q['quality_status']}; native runs {q['future_runs']:.3f} / opportunities {q['future_opportunities']}, {q['future_measured_seasons']} seasons; quality {q['quality_rate']}; official same/other outs {q['future_official_position_outs']}/{q['future_other_position_outs']}; missing measured outs {q['unmeasured_official_outs']}. Training all/joint/level-position: {s['training_people']}/{s['joint_people']}/{s['level_position_people']}" if s else f"- {q['component']} {q['window']} years: {q['quality_status']}; incomplete window has no completed test-fold support.")
            lines.append('')
    artifact=dict(status='pending_main_review',fixed_names=NAMES,resolved_ids=resolution,
        unused_runner_FIXED_correction={'683146':677951,'665742':665161,'682626':683011,'671185':669364,'643446':672386},
        walks=walks,no_fit=True,no_2026_outcomes=True,
        hashes={str(p):sha256_file(p) for p in (Path(__file__),OUT/'independent-review.json',OUT/'counts.parquet',OUT/'origins.parquet',OUT/'labels.parquet',OUT/'profile-support.parquet')})
    for folder in (OUT,PUBLIC):
        save(folder/'player-walkthrough.json',artifact)
        path=folder/'player-walkthrough.md';assert not path.exists();path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    protections()
    print(json.dumps(dict(focal=len(walks),peers=sum(len(w['peers']) for w in walks),resolved=resolution)),flush=True)


if __name__=='__main__':main()
