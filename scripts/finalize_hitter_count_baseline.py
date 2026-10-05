"""Seal completed readable review and export modest research evidence, no adoption."""
from pathlib import Path
import json
from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import ROOT,OUT,read,save,verify


def main():
    assert not (OUT/'final-review.json').exists()
    pre=read(OUT/'preflight.json');verify(pre['source_hashes'])
    fit=read(OUT/'fit-report.json');receipt=read(OUT/'review-receipt.json');verify(receipt['hashes'])
    qualification=read(OUT/'review-qualification.json');verify(qualification['hashes'])
    refs=read(OUT/'reference-review.json');verify(refs['hashes'])
    assert fit['new_heads']==receipt['heads_replayed']==105 and qualification['independent_all_score_checks']==8
    walks=read(OUT/'player-walks.json')['cases'];assert len(walks)==13
    assert len({r['row_id'] for r in walks})==13
    docs=[ROOT/f'docs/{n}' for n in ['hitter-count-baseline-result.md','hitter-count-baseline-player-review.md']]
    assert all(p.exists() for p in docs)
    text=docs[1].read_text(encoding='utf8')
    assert all(r['forecast']['player_name'].split()[0] in text for r in walks)
    scores=read(OUT/'scores.json');allscore=next(s for s in scores['scopes'] if s['scope']=='all')
    assert allscore['scores']['count']['value_rmse']>allscore['scores']['current']['value_rmse']
    assert allscore['scores']['count']['rate_rmse']>allscore['scores']['current']['rate_rmse']
    artifacts=[OUT/n for n in ['preflight.json','source-review.json','reference-review.json','fit-seal.json','fit-report.json',
        'predictions.parquet','review-receipt.json','review-qualification.json','scores.json','player-walks.json']]
    final=dict(player_walkthrough_status='complete',cases=13,new_heads=105,disposition='Not adopted; retain incumbent',
        protected_outcomes_used=False,completed_2026_evaluation_unchanged=True,deployment_approved=False,
        reasonability_status='Reviewed; foreign adaptation/power and important player errors remain, not an unqualified pass',
        research_goal_remains_active=True,hashes={str(p):sha256_file(p) for p in [Path(__file__),*docs,*artifacts]})
    save('final-review.json',final)
    public=ROOT/'reports/model-evidence/hitter-count-baseline/report.json';assert not public.exists();public.parent.mkdir(parents=True)
    compact=[]
    for r in walks:
        o=r['forecast'];compact.append(dict(row_id=r['row_id'],player_id=o['player_id'],player_name=o['player_name'],origin=o['origin_year'],
            why=r['why'],branch=r['branch'],past_baseline_rate=r['past_baseline_rate'],incumbent_rate=o['current_rate'],
            count_rate=o['count_rate'],actual_rate=o['actual_relative_rate'] if o['next_pa'] else None,
            expected_PA=o['count_pa'],actual_PA=o['next_pa'],incumbent_value=o['current_value'],count_value=o['count_value'],actual_value=o['actual_relative_value'],
            predicted_probability=r['predicted_probability'],actual_counts=r['actual_counts'],
            fixed_fit_source_removal_rate_changes={k:v['change'] for k,v in r['probes'].items()},
            support=[dict(subset=s['subset'],people=s['people']) for s in r['support']],
            interpretation='Next-year conditional MLB hitting and batting-plus-replacement, not full WAR or trade value'))
    value=dict(final,scores=scores,player_cases=compact,source_horizon_qualification='docs/hitter-shared-production-horizon-qualification.md',
        readable_result='docs/hitter-count-baseline-result.md',readable_player_review='docs/hitter-count-baseline-player-review.md')
    public.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print('Thirteen walkthroughs complete. Research evidence exported; incumbent and 2026 evaluation unchanged.')


if __name__=='__main__':main()
