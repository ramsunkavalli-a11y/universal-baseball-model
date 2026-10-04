"""Seal verified display, keeping next-year research separate from valuation."""
from pathlib import Path
import json
import numpy as np
from universal_baseball.storage import sha256_file
import build_hitter_comparative_handoff_v72 as b


def main():
    m=b.read(b.OUT/'manifest.json');assert m['browser_verification']=='pending'
    for key in ['source_hashes','artifact_hashes']:
        for path,h in m[key].items():assert sha256_file(Path(path))==h,path
    qa_path=b.ROOT/'reports/model-evidence/hitter-comparative-handoff-v72/browser-qa.json';qa=b.read(qa_path)
    assert qa['status']=='complete' and qa['all_seven_years_checked'] and qa['actual_results_hidden_by_default']
    rows=b.read(b.OUT/'explorer/data.json');notes=b.read(b.OUT/'explorer/comparison-reviews.json')
    assert len(rows)==30506
    for name,stage,label in [('Giants_2025_candidate_all_stages',None,'all'),('Giants_2025_candidate_upper_minors','Upper minors','upper'),('Giants_2025_candidate_current_MLB','Current MLB','MLB')]:
        selected=[r for r in rows if r['target_year']==2025 and r['org']=='San Francisco Giants' and (stage is None or r['stage']==stage)]
        assert len(selected)==qa[name]['players']
        assert round(sum(r['arms']['candidate']['pa'] for r in selected))==qa[name]['expected_PA_rounded']
        assert np.isclose(round(sum(r['arms']['candidate']['value'] for r in selected),1),qa[name]['expected_offense_rounded'])
    checks=[]
    for pid,year in [(701762,2024),(694671,2023)]:
        r=next(r for r in rows if r['player_id']==pid and r['origin_year']==year)
        k='Kurtz_2025' if pid==701762 else 'Langford_2024'
        assert round(r['arms']['candidate']['pa'],1)==qa[k]['candidate_expected_PA_rounded']
        assert round(r['arms']['original']['pa'],1)==qa[k]['original_expected_PA_rounded']
        assert r['next_pa']==qa[k]['actual_PA'] and notes[f'{pid}|{year}']
        for h,qk in [('participation','candidate_refined_participation_people'),('conditional_pa','candidate_refined_active_people')]:assert r['arms']['candidate']['support'][h]==qa[k][qk]
        checks.append(dict(player=r['player_name'],player_id=pid,origin_year=year,arms=r['arms'],actual_PA=r['next_pa'],completed_reviews=notes[f'{pid}|{year}']))
    m.update(browser_verification='complete',research_handoff_complete=True,whole_goal_complete=False,
        disposition='Chosen fresher-ranking research candidate, original comparison retained; public MAE, readiness and calibrated continuous uncertainty remain unfinished.',
        handoff_hashes={str(p):sha256_file(p) for p in [qa_path,Path(__file__),b.ROOT/'docs/hitter-comparative-handoff-v72-result.md',b.ROOT/'docs/practical-hitter-candidate-v72-model-card.md']})
    (b.OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf8')
    archive=qa_path.parent
    (archive/'manifest.json').write_bytes((b.OUT/'manifest.json').read_bytes())
    (archive/'reviewed-browser-cases.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf8')
    print('Comparative research handoff sealed; no new forecasts or production promotion.',flush=True)


if __name__=='__main__':main()
