"""Append a reviewed disposition without overwriting source/support receipts."""
from collections import Counter
from pathlib import Path
import json
import math

import polars as pl

from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-minor-counts-v18'
PUBLIC=ROOT/'reports/model-evidence/defense-minor-counts-v18'
EXPECTED=((677951,2019,6),(665161,2019,6),(683011,2019,6),(682928,2019,6),
          (678882,2019,4),(669364,2019,4),(672275,2022,2),(663728,2019,2),
          (672386,2019,2),(805811,2023,9),(456430,2009,6),(500743,2009,6))
NOTES=(
 'Witt develops from negative first-season range to strongly positive later seasons; three-year and five-year labels are not interchangeable. Rookie peers lack measured MLB quality, not zero talent.',
 'Peña has promoted multi-level evidence, modest positive later pooled range and very thin matching prospect support; peers show selection into MLB.',
 'Volpe has positive later range but no same-level advanced-rookie training support; Jiménez is an insufficient-exposure peer, not a measured poor defender.',
 'Abrams has negative later shortstop range despite similarly aged origin profile; his peers lack measured MLB quality. Do not tune an error threshold to Abrams versus Volpe.',
 'Rafaela moves away from second base; center-field success cannot validate the second-base label. Same-position exposure is too small.',
 'Edwards moves toward shortstop and has missing second-base range at positive official exposure. Bae qualifies narrowly at second base; position and measurement selection matter.',
 'Bailey has strong later throwing, near-average pooled blocking and tiny prior prospect support; his raw minor steal counts remain a battery outcome. Peers do not have measured future quality.',
 'Raleigh reaches sufficient throwing exposure only in the five-year window. Earlier blocking training has one person in his fold. Carlos Pérez has cameo exposure, not a stable quality label.',
 'Kirk has positive later throwing/blocking. Campusano and Amaya have inadequate throwing attempts but measurable blocking; Melendez moves to outfield. Their throwing quality remains unknown.',
 'Eldridge origin 2023 is primarily RF, with later 1B exposure; both windows incomplete. Do not convert this trace into a first-base talent claim.',
 'Sutton has nine shortstop chances; nearby old thin peers and zero chronological quality training do not establish a reliable fielding grade.',
 'Rojas has substantial minor exposure but his real pretracking MLB fielding is unmeasured. Escobar also has real pretracking exposure; neither is zero-quality talent.')


def read(p):return json.loads(p.read_text(encoding='utf8'))


def main():
    protections();assert not (OUT/'final-review.json').exists()
    for name in ('source-preflight','source-review','support-preflight','support-review','independent-review','player-walkthrough'):
        for path,h in read(OUT/f'{name}.json')['hashes'].items():assert sha256_file(Path(path))==h,path
    lab=pl.read_parquet(OUT/'labels.parquet').to_dicts()
    indexed={}
    for r in lab:indexed.setdefault((r['component'],r['window'],r['origin_year'],r['level']),[]).append(r)
    cohorts=read(OUT/'support-review.json')['cohorts']
    assert len(cohorts)==len(indexed)
    for c in cohorts:
        rs=indexed[c['component'],c['window'],c['origin'],c['level']];meas=[r for r in rs if r['quality_rate'] is not None]
        expected=dict(rows=len(rs),people=len({r['player_id'] for r in rs}),measured_rows=len(meas),measured_people=len({r['player_id'] for r in meas}),
                      unknown_age_rows=sum(r['age'] is None for r in rs),source_complete_rows=sum(r['source_counts_complete'] for r in rs),
                      statuses=dict(Counter(r['quality_status'] for r in rs)))
        for k,v in expected.items():assert c[k]==v,(k,c[k],v)
    walk=read(OUT/'player-walkthrough.json');origins=pl.read_parquet(OUT/'origins.parquet').to_dicts()
    traces=[]
    for w,identity,note in zip(walk['walks'],EXPECTED,NOTES,strict=True):
        r=w['focal']['origin'];assert (r['player_id'],r['origin_year'],r['position'])==identity
        pool=[t for t in origins if t['origin_year']==r['origin_year'] and t['level']==r['level'] and t['position']==r['position'] and t['player_id']!=r['player_id']]
        selected=sorted(pool,key=lambda t:(abs(t['age']-r['age']) if t['age'] is not None and r['age'] is not None else 999,
                         abs(math.log1p(t['minor_outs'])-math.log1p(r['minor_outs'])),t['player_id']))[:3]
        assert [t['origin']['player_id'] for t in w['peers']]==[t['player_id'] for t in selected]
        for t in (w['focal'],*w['peers']):
            assert t['prediction'] is None and t['prediction_error'] is None
            assert all(q['origin_year']==t['origin']['origin_year'] and q['player_id']==t['origin']['player_id'] for q in t['labels'])
        traces.append(dict(player_id=r['player_id'],origin=r['origin_year'],position=r['position'],player_name=r['player_name'],
                           main_review=note,peer_ids=[t['player_id'] for t in selected]))
    assert (ROOT/'scripts/audit_minor_fielding_counts_v18.py').read_text().count('FIXED')==1
    for name in ('source-preflight','source-review','support-preflight','support-review','independent-review','player-walkthrough'):
        assert (OUT/f'{name}.json').read_bytes()==(PUBLIC/f'{name}.json').read_bytes()
    assert (OUT/'player-walkthrough.md').read_bytes()==(PUBLIC/'player-walkthrough.md').read_bytes()
    paths=[Path(__file__),ROOT/'docs/defense-minor-counts-v18-contract.md',ROOT/'docs/defense-minor-counts-v18-result.md',
           *[OUT/f'{n}.json' for n in ('source-preflight','source-review','support-preflight','support-review','independent-review','player-walkthrough')],OUT/'player-walkthrough.md']
    receipt=dict(status='reviewed_source_and_support_no_forecast',player_walkthrough_status='complete',focal_players=len(traces),peers=36,
        reviewed_cases=traces,cohort_rows_replayed=len(cohorts),raw_origin_label_support_replay='independent-review.json',
        focused_tests={'count':15,'command':'.venv/Scripts/python.exe -X utf8 -m pytest tests/test_minor_fielding_counts.py -p no:cacheprovider -q','observed_exit_code':0},
        selected_next_component='range: fixed three-year same-position MLB quality, genuinely pre-MLB prospects, primary origin 2022 and separate 2021 stress',
        no_accuracy_gain_claimed=True,no_fit=True,no_forecast_or_explorer_change=True,no_2026_outcome_access=True,goal_complete=False,
        previous_goal_turn='No defense progress: read-only Lovich explanation. Revalidated source/support state and completed the next available audit.',
        unresolved=['Every detailed prospect profile is sparse; modern DSL/complex levels have no comparable training level',
                    'Catcher prospect future-quality training remains tiny',
                    'Five-year earlier labels favor later arrivals due pretracking coverage',
                    'Same-position quality does not settle position transfer or delivered player value',
                    'Separate Lovich batting defect remains open'],
        hashes={str(p):sha256_file(p) for p in paths})
    for folder in (OUT,PUBLIC):save(folder/'final-review.json',receipt)
    protections();print(json.dumps(dict(status=receipt['status'],focal_players=12,peers=36,cohort_rows=len(cohorts),goal_complete=False)),flush=True)


if __name__=='__main__':main()
