"""Complete the paired source review, without fitting or changing forecasts."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
import audit_hitter_employment_v70 as e


def main():
    out=e.ROOT/'reports/generated/hitter-employment-v70b';r=e.prior.read(out/'audit.json')
    for p,h in r['source_hashes'].items():assert sha256_file(Path(p))==h,p
    cases=e.prior.read(out/'cases.json');notes_path=e.ROOT/'config/hitter_employment_v70_review.json';notes=e.prior.read(notes_path)
    assert set(notes['cases'])=={f"{c['origin']['player_id']}|{c['origin']['origin_year']}" for c in cases}
    lines=['# Roster and employment source review','',
        'No new model fitted and no existing forecast changed. Initial all-fields-maximum source audit is preserved; repaired employment announcements use recorded dates with qualified publication vintages. Nine fixed cases trace actual sources, inputs, saved paths and outcomes.',''];lean=[]
    for c in cases:
        a=c['origin'];key=f"{a['player_id']}|{a['origin_year']}";assert len(notes['cases'][key])>200
        assert np.isclose(a['preseason_p']*a['preseason_conditional_pa'],a['preseason_pa'],atol=1e-8)
        lines += [f"## {a['player_name']} / {a['origin_year']} to {a['target_year']}",'',
            f"Player {a['player_id']}, row {a['row_id']}, fold {a['outer_fold']}, age {a['age']}. Latest captured employment: "+str(c['source_state']['latest_events']), '',
            '| Known season | Level | PA | HR | K | UBB |','| --- | --- | ---: | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Existing appearance {a['preseason_p']:.6f} × active PA {a['preseason_conditional_pa']:.3f} = expected PA {a['preseason_pa']:.3f}; fixed hitting {a['baseline_rate']:.6f}/600; offense {a['preseason_value']:.6f}. Actual {a['next_pa']} PA and offense {a['next_value']:.6f}. No MLB PA is not observed zero talent.",'',
            'All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: '+str(c['actual_training_exposure'])+'.','']
        for head,t in c['saved_paths'].items():
            lines += [f"Saved {head}: reference {t['reference']:.6f}; raw additive {t['raw_prediction']:.6f}; linked probability {t['linked_probability']}. Largest path terms:"]
            for term in t['terms']:lines.append(f"- {term['feature']}: input {term['input']:.6f}; path term {term['path_effect']:+.6f}.")
            lines += ['','Roster path accounting, not a causal effect: '+str(t['roster_terms']), '']
        lines += [notes['cases'][key],'','| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} | {p['pa_0']} | {p['preseason_pa']:.2f} | {p['next_pa']} | {p['preseason_value']:.3f} | {p['next_value']:.3f} |")
        lines.append('');lean.append({k:c[k] for k in ['source_state','actual_inputs','source_history','saved_paths','actual_training_exposure','peers']}|
            dict(player=a['player_name'],player_id=a['player_id'],origin_year=a['origin_year'],review_note=notes['cases'][key],
                forecasts={k:a[k] for k in ['preseason_p','preseason_conditional_pa','preseason_pa','baseline_rate','preseason_value','next_pa','next_value']}))
    lines += ['## Decision','',notes['decision'],'',notes['next_step']]
    (out/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    e.OUT=out;e.write('reviewed-case-summary.json',lean)
    r['player_walkthrough_status']='complete';r['review_notes_sha256']=sha256_file(notes_path);e.write('audit.json',r)
    paths=[out/n for n in ['features.parquet','diagnostic-forecasts.parquet','scores.json','support.json','audit.json','reviewed-case-summary.json','player-walkthrough.md']]
    code=[Path(__file__),notes_path,e.ROOT/'docs/hitter-employment-v70-result.md']
    e.write('report.json',dict(player_walkthrough_status='complete',decision=notes['decision'],next_step=notes['next_step'],source_hashes=r['source_hashes'],
        output_hashes={str(p):sha256_file(p) for p in paths},review_hashes={str(p):sha256_file(p) for p in code},new_models_fitted=0,
        protected_outcomes_used=False,forecasts_changed=False,whole_goal_complete=False))
    archive=e.ROOT/'reports/model-evidence/hitter-employment-v70';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','support.json','audit.json','reviewed-case-summary.json','player-walkthrough.md']:(archive/n).write_bytes((out/n).read_bytes())
    (archive/'initial-audit.json').write_bytes((e.ROOT/'reports/generated/hitter-employment-v70/audit.json').read_bytes())
    (archive/'initial-scores.json').write_bytes((e.ROOT/'reports/generated/hitter-employment-v70/scores.json').read_bytes())
    print('Source/date repair reviewed; all forecasts unchanged; no fitted candidate yet.',flush=True)


if __name__=='__main__':main()
