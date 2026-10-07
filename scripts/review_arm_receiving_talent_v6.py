"""Walk fixed, score-selected and small samples before final disposition."""
from collections import defaultdict
from pathlib import Path
import json
import math
import polars as pl
from evaluate_arm_receiving_talent_v6 import ROOT,SOURCE,OUT,PUBLIC
from review_arm_receiving_pilot_v6 import FIXED
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.arm_receiving_baseline import PRIOR
from universal_baseball.storage import sha256_file


def main():
    protections()
    assert not (OUT/'player-walkthrough.json').exists()
    report=json.loads((OUT/'report.json').read_text())
    for group in ('input_hashes','output_hashes'):
        for p,h in report[group].items():assert sha256_file(Path(p))==h,p
    history=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual.parquet').to_dicts():history[r['kind'],r['player_id']].append(r)
    capture=json.loads((SOURCE.parent/'extension-capture.json').read_text());raw={}
    for cap in capture['captures']:
        path=Path(cap['path']);assert sha256_file(path)==cap['sha256']
        for r in embedded(path.read_text(encoding='utf8'),'data'):
            raw[cap['kind'],cap['year'],int(r['entity_id'] if cap['kind']=='arm' else r['player_id'])]=dict(
                raw=r,source_path=str(path),source_sha256=cap['sha256'])
    rows=pl.read_parquet(OUT/'predictions.parquet').to_dicts();walks=[];missing=[]
    def trace(r):
        kind,pid,y=r['kind'],r['player_id'],r['origin_year']
        key='isolated_outfield_quality_valid' if kind=='arm' else 'quality_valid'
        past=[];future=[]
        for s in history[kind,pid]:
            entry=dict(measurement=s,**raw[kind,s['season'],pid])
            if y-2<=s['season']<=y:
                entry.update(weight=2.**(s['season']-y),used_for_history=bool(s[key]))
                past.append(entry)
            if y<s['season']<=r['window_end']:
                entry['scope_qualified_for_target']=bool(s[key]);future.append(entry)
        n=sum(s['measurement']['opportunities']*s['weight'] for s in past if s['used_for_history'])
        runs=sum(s['measurement']['runs']*s['weight'] for s in past if s['used_for_history'])
        assert n==r['history_opportunities'] and runs==r['history_runs']
        assert abs(100*runs/(n+PRIOR[kind])-r['history'])<1e-12
        target=r['quality_rate']
        if target is None:
            judgment='Future quality is unknown, not zero skill. Check exit, limited opportunities and position-scope flags; this case does not enter quality scores.'
        elif r['history']*target<0:
            judgment='Past and later adjusted quality have opposite signs. The retained historical mean misses this reversal; no injury or skill-change cause is established by these data.'
        elif abs(r['history']-target)<abs(target):
            judgment='Qualified past history moves the estimate toward later measured MLB quality. This is a conditional talent case, not a delivered-value win.'
        else:
            judgment='Neutral is closer than this history estimate. History level or development is not captured adequately; do not retune the prior to this player.'
        return dict(origin_forecast=r,past=past,future=future,
            intermediate=dict(weighted_opportunities=n,weighted_runs=runs,neutral_prior_opportunities=PRIOR[kind],
                reliability=r['reliability'],formula='100 * weighted_runs / (weighted_opportunities + prior_opportunities)'),
            neutral=0.,candidate=r['history'],later_quality=target,
            candidate_error=None if target is None else r['history']-target,
            baseball_judgment=judgment,not_a_playing_time_or_WAR_forecast=True)
    for kind in ('arm','receiving'):
        cohort=[r for r in rows if r['kind']==kind and r['origin_year']==2022]
        measured=[r for r in cohort if r['quality_rate'] is not None]
        by_id={r['player_id']:r for r in cohort};selected=defaultdict(list)
        for pid in FIXED[kind]:
            if pid in by_id:selected[pid].append('fixed_before_scoring')
            else:missing.append(dict(kind=kind,player_id=pid,reason='No origin-eligible source history'))
        for r in sorted(cohort,key=lambda r:(r['history_opportunities'],r['player_id']))[:2]:selected[r['player_id']].append('two_smallest_histories')
        def improvement(r):return abs(r['quality_rate'])-abs(r['history']-r['quality_rate'])
        selectors=[('largest_gain',max(measured,key=improvement)),('largest_deterioration',min(measured,key=improvement)),
            ('largest_false_high',max(measured,key=lambda r:r['history']-r['quality_rate'])),
            ('largest_false_low',min(measured,key=lambda r:r['history']-r['quality_rate'])),
            ('median_candidate_absolute_error',sorted(measured,key=lambda r:(abs(r['history']-r['quality_rate']),r['player_id']))[len(measured)//2])]
        for label,r in selectors:selected[r['player_id']].append(label)
        for pid,rules in selected.items():
            focal=by_id[pid]
            peers=sorted((r for r in cohort if r['player_id']!=pid),
                key=lambda r:(abs((r['age'] or 27)-(focal['age'] or 27)),abs(r['history_opportunities']-focal['history_opportunities']),r['player_id']))[:3]
            walks.append(dict(kind=kind,player_id=pid,selection=rules,primary=trace(focal),peers=[trace(r) for r in peers],
                peer_selection='Three nearest origin-known age, then weighted opportunities, then ID; no future selection.'))
    review=dict(walks=walks,absent_fixed=missing,player_walkthrough_status='complete',focal_cases=len(walks),peer_cases=3*len(walks),
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'report.json',OUT/'predictions.parquet',SOURCE/'annual.parquet']},
        no_model_fit=True,no_2026_outcomes=True)
    save(OUT/'player-walkthrough.json',review);save(PUBLIC/'player-walkthrough.json',review)
    print([(w['kind'],w['primary']['origin_forecast']['player_name'],w['selection'],round(w['primary']['candidate'],4),w['primary']['later_quality']) for w in walks])


if __name__=='__main__':main()
