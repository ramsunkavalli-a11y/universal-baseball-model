"""Seal actual source-to-fit reviews, keeping adoption separate from execution."""
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_compatible_value_v63 as e


def main():
    cases=e.read(e.OUT/'cases.json');review=e.read(e.ROOT/'config/hitter_compatible_value_v63_case_notes.json')
    notes={(a['name'],a['origin']):a['note'] for a in review['cases']}
    assert len(cases)==len(notes)==19
    v=e.read(e.OUT/'verification.json');assert v['replayed_heads']==105
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h
    lines=['# Compatible hitting/value: actual player walkthroughs','',review['summary'],'',
        'All 30,506 identities remain; PA is unchanged. Hitting and offense use the common origin event environment and corrected replacement reference.',
        'Offense includes batting plus replacement only: not full WAR, six years of control or market value.',
        'Peers were selected using origin-known stage/debut, age, MLB/minor use and draft rank, never future outcomes. Generic peers are not guaranteed comparable talent.',
        'Exact saved terms explain arithmetic, not causal feature importance. Direct heads have no conditional talent estimate.',
        'V53 prediction tables kept some old descriptive inputs; this review overlays actual fit inputs and preserves old display differences separately. No fit changes.','']
    lean=[]
    for c in cases:
        r=c['origin'];key=(r['player_name'],r['origin_year']);assert key in notes and len(notes[key])>150
        pooled={}
        for level in ['MLB','AAA']:
            h=[a for a in c['source_history'] if a['bucket']==level]
            pa=sum([1,.8,.6][r['origin_year']-a['season']]*a['plate_appearances'] for a in h)
            k=sum([1,.8,.6][r['origin_year']-a['season']]*a['strike_outs'] for a in h)
            hr=sum([1,.8,.6][r['origin_year']-a['season']]*a['home_runs'] for a in h)
            pooled[level]=dict(weighted_pa=pa,weighted_K=k,weighted_HR=hr,K=(k+23)/(pa+100),HR=(hr+3)/(pa+100))
            assert np.isclose(c['inputs'][f'pooled_{level}_K'],pooled[level]['K'],atol=1e-10)
            assert np.isclose(c['inputs'][f'pooled_{level}_HR'],pooled[level]['HR'],atol=1e-10)
        assert np.isclose(r['baseline_pa'],r['repaired_p']*r['repaired_conditional_pa'],atol=1e-10)
        for arm in ['baseline','common_rate']:
            assert np.isclose(r[arm+'_value'],r['baseline_pa']*(r[arm+'_rate']/600+r['origin_replacement_rate']),atol=1e-10)
        if r['next_pa']>0:assert np.isclose(r['next_value'],r['next_pa']*(r['next_batting_rate']/600+r['origin_replacement_rate']),atol=1e-10)
        else:assert r['next_value']==0 and not c['actual_history']
        lines += [f"## {r['player_name']} at the {r['origin_year']} cutoff",'',
            'Selection: '+', '.join(c['selection'])+'.',
            f"Player {r['player_id']}; fold {r['outer_fold']}; next calendar year {r['target_year']}; age {r['age']}; stage {r['stage']}.",
            f"Current/prior MLB PA {r['pa_0']}/{r['pa_1']}/{r['pa_2']}. Draft known {r['draft_known']}, pick {r['pick_number']}, school class {r['draft_school_class'] or 'unknown'}, actual scaled draft elapsed {c['inputs']['draft_elapsed']:.3f}; current rank score {r['scout_rank_score_0']}.",
            f"Exact unchanged opportunity: {r['repaired_p']:.5f} appearance probability × {r['repaired_conditional_pa']:.3f} conditional PA = {r['baseline_pa']:.3f} expected PA; actual {r['next_pa']}.",
            f"Conditional batting /600: baseline {r['baseline_rate']:.5f}, common {r['common_rate_rate']:.5f}; actual {r['next_batting_rate']:.5f}." if r['next_pa']>0 else
                f"Conditional batting /600: baseline {r['baseline_rate']:.5f}, common {r['common_rate_rate']:.5f}; no actual rate exists at zero MLB PA.",
            f"Common-origin index {r['origin_index']:.7f}; corrected replacement per PA {r['origin_replacement_rate']:.8f}.",
            f"Offense: baseline {r['baseline_value']:.5f}, common rate product {r['common_rate_value']:.5f}, relative direct {r['relative_direct_value']:.5f}, common direct {r['common_direct_value']:.5f}, actual {r['next_value']:.5f}.",
            f"Physically possible offense at retained expected PA: [{r['physical_low']:.5f}, {r['physical_high']:.5f}].",'',notes[key],'','Actual cutoff-known counts:']
        for h in c['source_history']:lines.append(f"- {h['season']} {h['bucket']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} unintentional walks.")
        lines += ['','Actual next-year MLB counts:']
        for h in c['actual_history']:lines.append(f"- {h['season']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} unintentional walks.")
        if not c['actual_history']:lines.append('- Certified no MLB participation; not observed zero batting talent.')
        lines += ['','Independent pooled-input reconstruction, recency 1/.8/.6 and fixed 100-PA prior:']
        for level,z in pooled.items():lines.append(f"- {level}: weighted PA {z['weighted_pa']:.3f}, K {z['weighted_K']:.3f}, HR {z['weighted_HR']:.3f}; fitted-input K {z['K']:.6f}, HR {z['HR']:.6f}.")
        lines += ['','Actual narrow training profiles (distinct people):']
        for p in c['actual_training_profiles']:lines.append(f"- {p['head']}: {p['profile_players']}; stage/debut/age/current-workload/quality joint.")
        lines += ['Broader support flags: '+str([{k:p[k] for k in ['head','elapsed_outside','age_outside','quality_outside','unseen_profile','sparse_profile']} for p in c['training_support']])+'.']
        compact_heads={}
        for arm,h in c['heads'].items():
            wanted=r['baseline_rate'] if arm=='baseline_rate' else r[arm+'_raw']
            assert np.isclose(h['raw_prediction'],wanted,atol=1e-8)
            terms=h['feature_effects'];effect='effect' if arm in ['baseline_rate','common_rate'] else 'path_effect'
            assert np.isclose(h['reference']+sum(a[effect] for a in terms),wanted,atol=1e-8)
            lines += ['',f"Saved {arm}: reference {h['reference']:.6f}, predicted {h['raw_prediction']:.6f}. Largest actual fitted terms:"]
            for a in terms[:8]:lines.append(f"- {a['feature']}: input {a['input']:.6f}, fitted contribution {a[effect]:+.6f}.")
            calendar=[a for a in terms if a['feature'].startswith(('reorganized','milb_canceled','league_rate','fraction_'))]
            lines += ['Calendar/context terms: '+(', '.join(f"{a['feature']} {a[effect]:+.6f}" for a in calendar) or 'none')+'.']
            compact_heads[arm]=dict(reference=h['reference'],raw_prediction=h['raw_prediction'],largest_terms=terms[:10],calendar_terms=calendar)
        lines += ['','Origin-selected peers (forecast PA, actual PA; baseline/direct-relative/direct-common/actual offense):']
        for p in c['peers_selected_without_outcomes']:lines.append(f"- {p['player_name']}: {p['baseline_pa']:.2f}, {p['next_pa']}; {p['baseline_value']:.3f}/{p['relative_direct_value']:.3f}/{p['common_direct_value']:.3f}/{p['next_value']:.3f}.")
        lines.append('')
        c.update(review_note=notes[key],pooled_input_reconstruction=pooled)
        lean.append(dict(player=r['player_name'],player_id=r['player_id'],origin_year=r['origin_year'],target_year=r['target_year'],selection=c['selection'],
            actual_forecasts={k:r[k] for k in ['baseline_pa','baseline_rate','common_rate_rate','baseline_value','common_rate_value','relative_direct_value','common_direct_value','next_pa','next_batting_rate','next_value','physical_low','physical_high']},
            source_history=c['source_history'],actual_history=c['actual_history'],actual_inputs=c['inputs'],legacy_display_inputs=c['legacy_display_inputs'],
            actual_training_profiles=c['actual_training_profiles'],saved_terms=compact_heads,peers=c['peers_selected_without_outcomes'],review_note=notes[key],pooled_input_reconstruction=pooled))
    lines += ['## Decision','',review['decision'],review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8');e.write('reviewed-cases.json',cases);e.write('reviewed-case-summary.json',lean)
    v.update(player_walkthrough_status='complete',pooled_inputs_independently_reconstructed=True,actual_corrected_inputs_in_case_metadata=True);e.write('verification.json',v)
    paths=[e.OUT/n for n in ['scores.json','intervals.json','verification.json','source-reconciliation.json','player-walkthrough.md','reviewed-cases.json','reviewed-case-summary.json','predictions.parquet']]
    code=[e.ROOT/'scripts'/n for n in ['score_hitter_compatible_value_v63.py','finalize_hitter_compatible_value_v63.py']]
    report=dict(player_walkthrough_status='complete',decision=review['decision'],research_baseline='V53 PA and relative conditional hitting under corrected reference',integrity=v,
        full_cohort_profile_certification=False,predictive_improvement=False,not_deployment_approval=True,input_hashes=pre['input_hashes'],output_hashes={str(p):sha256_file(p) for p in paths},
        reviewer_hash=sha256_file(e.ROOT/'config/hitter_compatible_value_v63_case_notes.json'),review_code_hashes={str(p):sha256_file(p) for p in code})
    e.write('report.json',report)
    dest=e.ROOT/'reports/model-evidence/hitter-compatible-value-v63';dest.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','source-reconciliation.json','player-walkthrough.md','reviewed-case-summary.json']:(dest/n).write_bytes((e.OUT/n).read_bytes())
    print('19 actual reviews sealed; '+review['decision'],flush=True)


if __name__=='__main__':main()
