"""Require every selected actual player review before disposition."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_workload_anchor_v61 as e


def main():
    cases=e.read(e.OUT/'cases.json');review=e.read(e.ROOT/'config/hitter_workload_anchor_v61_case_notes.json')
    notes={(r['name'],r['origin']):r['note']for r in review['cases']}
    assert len(notes)==len(cases)==14
    verification=e.read(e.OUT/'verification.json');assert verification['replayed_heads']==70
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    lines=['# Direct and anchored playing time actual player reviews','',
        'Both global replacements are withheld after review. Corrected V53 remains the research baseline.',
        'The anchored arm keeps observed prior workload outside the trees and learns its adjustment; that reference is not a promised job.',
        'All 30,506 rows remain. Seventy heads replay. Hitting talent and availability overrides are unchanged.',
        'New models predict expected PA only; no appearance probability is invented from a direct mean.',
        'Peer selection uses origin-known stage/debut, age, recent MLB/minor PA and reference workload, not future success.',
        'Tree-path terms account for each fitted output, not causal effects or an additive decomposition of the refit change.','']
    for c in cases:
        r=c['origin'];key=r['player_name'],r['origin_year'];assert key in notes
        assert len(notes[key])>150
        # Independent reconstruction of the fixed pooled count inputs for
        # actual-model audit; never used to refit or choose the player cases.
        pooled={}
        for level in ['MLB','AAA']:
            g=[h for h in c['source_history']if h['bucket']==level]
            pa=sum([1,.8,.6][r['origin_year']-h['season']]*h['plate_appearances']for h in g)
            k=sum([1,.8,.6][r['origin_year']-h['season']]*h['strike_outs']for h in g)
            hr=sum([1,.8,.6][r['origin_year']-h['season']]*h['home_runs']for h in g)
            pooled[level]=dict(weighted_pa=pa,weighted_k=k,weighted_hr=hr,
                k_after_fixed100=(k+23)/(pa+100),hr_after_fixed100=(hr+3)/(pa+100))
            for a in e.ARMS:
                x=c['heads'][a]['all_inputs']
                assert np.isclose(x[f'pooled_{level}_K'],pooled[level]['k_after_fixed100'],atol=1e-10)
                assert np.isclose(x[f'pooled_{level}_HR'],pooled[level]['hr_after_fixed100'],atol=1e-10)
        c['pooled_input_reconstruction']=pooled;c['review_note']=notes[key]
        lines += [f"## {r['player_name']} at the {r['origin_year']} cutoff",'',
            'Selection: '+', '.join(c['selection'])+'.',
            f"Age {r['age']}; stage {r['stage']}; current/prior MLB PA {r['pa_0']}/{r['pa_1']}/{r['pa_2']}; captured listing {r['on_40man']}.",
            f"Reference {r['workload_reference']:.6f} PA; actual workload-profile support {c['profile_support']['workload_profile_players']} distinct training people.",
            f"Preserved baseline appearance {r['repaired_p']:.4f} × conditional PA {r['repaired_conditional_pa']:.3f} = {r['repaired_pa']:.3f} expected PA.",
            f"Direct {r['direct61_pa']:.3f}; anchored {r['anchor61_pa']:.3f}; next-year actual {r['next_pa']} PA.",
            f"Fixed hitting estimate {r['repaired_rate']:.3f} versus observable realized {r['next_batting_rate']:.3f} per 600 PA." if r['next_pa']>0 else
                f"Fixed hitting estimate {r['repaired_rate']:.3f}; no realized hitting rate exists because actual PA is zero.",
            f"Batting plus replacement: baseline {r['repaired_value']:.3f}, direct {r['direct61_value']:.3f}, anchored {r['anchor61_value']:.3f}, actual {r['next_value']:.3f}.",
            '',notes[key],'','Known source counts:']
        for h in c['source_history']:
            lines.append(f"- {h['season']} {h['bucket']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} unintentional walks.")
        lines+=['','Workload reference arithmetic:']
        for y,z in c['reference_by_year'].items():
            lines.append(f"- {y}: {z['actual_pa']} actual PA × 162 / {z['average_team_games']:.6f} league-average completed games = {z['annual_workload_reference']:.6f}, subject to the declared 800 upper bound.")
        lines+=['- Take the maximum annual reference and the fixed 100 floor. Actual batting counts are not annualized.','',
                'Reconstructed pooled count inputs:']
        for level,z in pooled.items():
            lines.append(f"- {level}: weighted PA {z['weighted_pa']:.3f}, K {z['weighted_k']:.3f}, HR {z['weighted_hr']:.3f}; fixed-100 K {z['k_after_fixed100']:.6f}, HR {z['hr_after_fixed100']:.6f}. Actual model inputs verified.")
        lines+=['','Corrected availability inputs:']
        for n in e.ADDED[1:]:lines.append(f'- {n}: {r[n]:.6f}; exposed training people {c["added_feature_support"][n]}.')
        for a,h in c['heads'].items():
            t=h['path_trace']
            assert np.isclose(t['raw_prediction'],r[a+'_head_output'],atol=1e-8)
            if a=='anchor61':assert np.isclose(t['raw_prediction']+r['workload_reference'],r[a+'_raw_pa'],atol=1e-8)
            lines += ['',f"Saved {a} head: node reference {t['reference']:.6f}; output {t['raw_prediction']:.6f} ({h['target']}).",
                f"After addback, raw PA {r[a+'_raw_pa']:.6f}; after bounds/policy {r[a+'_pa']:.6f}. Training people {h['training_players']}.",
                'Largest fitted path terms:']
            for z in t['feature_effects'][:8]:lines.append(f"- {z['feature']}: input {z['input']:.6f}, path term {z['path_effect']:+.6f} PA.")
            terms=[z for z in t['feature_effects']if z['feature'].startswith('op_')]
            lines.append('Availability path terms: '+('; '.join(f"{z['feature']} {z['path_effect']:+.6f}"for z in terms)or'none')+'.')
        lines+=['','Cutoff-known relevant records:']
        for z in c['cutoff_records']:
            if z.get('il_kind') or z['kind']in ['mlb_return','mlb_activation','restricted','administrative_leave','suspended_unspecified','org_acquisition']:
                lines.append(f"- Known {z['available_date']}, occurred {z['event_date']}: {z['description']}.")
        lines+=['','Origin-known comparisons, all retained:']
        for z in c['peers']:
            lines.append(f"- {z['player_name']}: age {z['age']}, current/prior MLB PA {z['pa_0']}/{z['pa_1']}, reference {z['workload_reference']:.2f}; baseline/direct/anchored {z['repaired_pa']:.2f}/{z['direct61_pa']:.2f}/{z['anchor61_pa']:.2f}, actual {z['next_pa']} PA, {z['next_value']:.3f} offense value.")
        lines.append('')
    lines+=['## Decision after review','',
        'Neither global replacement improves the complete forecast enough to adopt. The absence-group gain is real development evidence,',
        'but Lux worsens, McLain remains materially underprojected and sparse elite/medical profiles remain. Established-role use differs',
        'from brief-debut growth; lost Soler/Judge opportunity and adverse Acuna/Yordan outcomes prevent a universal-reference upgrade.',
        'Keep the source correction and saved comparison. Do not tune the reference floor or peak definition to these names.',
        'The corrected baseline remains default; no protected 2026 forecast or deployed explorer changed.']
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    e.write('reviewed-cases.json',cases)
    verification.update(player_walkthrough_status='complete',pooled_counts_independently_reconstructed=True)
    e.write('verification.json',verification)
    report=dict(player_walkthrough_status='complete',decision=review['decision'],
        research_baseline='corrected V53',not_deployment_approval=True,
        integrity=verification,full_cohort_profile_certification=False,
        predictive_result='neither whole-population arm earns adoption; absence and large-regular slices have useful differences',
        input_hashes=pre['input_hashes'],output_hashes={str(e.OUT/n):sha256_file(e.OUT/n)for n in
            ['scores.json','intervals.json','verification.json','player-walkthrough.md','reviewed-cases.json','predictions.parquet']},
        reviewer_hash=sha256_file(e.ROOT/'config/hitter_workload_anchor_v61_case_notes.json'))
    e.write('report.json',report)
    archive=e.ROOT/'reports/model-evidence/hitter-workload-anchor-v61';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','player-walkthrough.md']:
        (archive/n).write_bytes((e.OUT/n).read_bytes())
    print('Fourteen actual reviews complete, pooled counts reconstructed; global replacements withheld.',flush=True)


if __name__=='__main__':main()
