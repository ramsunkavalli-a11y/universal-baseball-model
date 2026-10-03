"""Require reviewed actual players, independent counts and saved-fit arithmetic."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
import evaluate_hitter_bounded_workload_v62 as e


def main():
    cases=e.read(e.OUT/'cases.json');review=e.read(e.ROOT/'config/hitter_bounded_workload_v62_case_notes.json')
    notes={(r['name'],r['origin']):r['note']for r in review['cases']}
    assert len(notes)==len(cases)
    v=e.read(e.OUT/'verification.json');assert v['replayed_heads']==70
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    lines=['# Smooth playing time actual player reviews','',review['summary'],'',
        'Identical 30,506 forecasts and fixed corrected V53 hitting; seventy smooth heads replay.',
        'Fractional-logit means are not appearance probabilities. Hitting plus replacement is not full WAR.',
        'All additive terms reconstruct the saved predictor; they explain fitted arithmetic, not causal effects.',
        'Peers use origin-known stage/debut, age and workload, not future success.','']
    for c in cases:
        r=c['origin'];key=r['player_name'],r['origin_year'];assert key in notes and len(notes[key])>150
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
            f"Demonstrated reference {r['workload_reference']:.3f} PA; profile support {c['profile_support']['workload_profile_players']} distinct training people.",
            f"Baseline appearance {r['repaired_p']:.4f} × conditional PA {r['repaired_conditional_pa']:.3f} = {r['repaired_pa']:.3f} expected PA.",
            f"Smooth squared {r['smooth62_pa']:.3f}; bounded mean {r['bounded62_pa']:.3f}; next-year actual {r['next_pa']} PA.",
            f"Fixed hitting {r['repaired_rate']:.3f} versus realized {r['next_batting_rate']:.3f} per 600 PA." if r['next_pa']>0 else
                f"Fixed hitting {r['repaired_rate']:.3f}; no realized rate exists because actual PA is zero.",
            f"Offense: baseline {r['repaired_value']:.3f}, smooth {r['smooth62_value']:.3f}, bounded {r['bounded62_value']:.3f}, actual {r['next_value']:.3f}.",
            '',notes[key],'','Known source counts:']
        for h in c['source_history']:
            lines.append(f"- {h['season']} {h['bucket']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} unintentional walks.")
        lines+=['','Reconstructed pooled inputs with recency 1/.8/.6 and fixed 100-PA prior:']
        for level,z in pooled.items():
            lines.append(f"- {level}: weighted PA {z['weighted_pa']:.3f}, K {z['weighted_k']:.3f}, HR {z['weighted_hr']:.3f}; K {z['k_after_fixed100']:.6f}, HR {z['hr_after_fixed100']:.6f}. Actual inputs verified.")
        lines+=['','Observation inputs and exposed training people:']
        for n in e.previous.ADDED[1:]:lines.append(f'- {n}: {r[n]:.6f}; exposed people {c["added_feature_support"][n]}.')
        for a,h in c['heads'].items():
            t=h['trace'];assert np.isclose(t['raw_pa'],r[a+'_raw_pa'],atol=1e-8)
            assert np.isclose(t['intercept']+sum(z['term']for z in t['all_terms']),t['eta'],atol=1e-10)
            lines += ['',f"Saved {a}: intercept {t['intercept']:.6f}, additive predictor {t['eta']:.6f}, link {t['link']}, raw PA {t['raw_pa']:.6f}.",
                f"After bounds/policy {r[a+'_pa']:.6f}; solver gradient {h['solver']['gradient_max']:.3g}; training people {h['training_players']}.",
                'Largest fitted terms in predictor units, not additive PA units:']
            for z in sorted(t['all_terms'],key=lambda z:abs(z['term']),reverse=True)[:10]:
                lines.append(f"- {z['feature']}: {z['term']:+.6f}.")
            lines += ['Scaled core inputs: '+', '.join(f'{n}={t["scaled_inputs"][n]:.5f}'for n in
                ['age_centered','MLB_0_pa','AAA_0_pa','AA_0_pa','workload_reference','draft_rank','scout_rank_score_0'])+'.']
            lines+=['Availability terms: '+('; '.join(f"{z['feature']}={z['term']:+.6f}"for z in t['all_terms']if z['feature'].startswith('op_'))or'none')+'.']
        lines+=['','Cutoff-known relevant records:']
        for z in c['cutoff_records']:
            if z.get('il_kind')or z['kind']in ['mlb_return','mlb_activation','restricted','administrative_leave','suspended_unspecified','org_acquisition']:
                lines.append(f"- Known {z['available_date']}, occurred {z['event_date']}: {z['description']}.")
        lines+=['','Origin-known peers:']
        for z in c['peers']:
            lines.append(f"- {z['player_name']}: age {z['age']}, MLB PA {z['pa_0']}/{z['pa_1']}, minor PA {z['minor_pa_0']}; baseline/smooth/bounded {z['repaired_pa']:.2f}/{z['smooth62_pa']:.2f}/{z['bounded62_pa']:.2f}, actual {z['next_pa']} PA and {z['next_value']:.3f} offense.")
        lines.append('')
    lines+=['## Decision after review','',review['summary'],review['next_step']]
    (e.OUT/'player-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8');e.write('reviewed-cases.json',cases)
    v.update(player_walkthrough_status='complete',pooled_counts_independently_reconstructed=True);e.write('verification.json',v)
    report=dict(player_walkthrough_status='complete',decision=review['decision'],research_baseline='corrected V53',
        not_deployment_approval=True,integrity=v,full_cohort_profile_certification=False,input_hashes=pre['input_hashes'],
        output_hashes={str(e.OUT/n):sha256_file(e.OUT/n)for n in ['scores.json','intervals.json','verification.json',
            'player-walkthrough.md','reviewed-cases.json','predictions.parquet','context-term-audit.json']},
        reviewer_hash=sha256_file(e.ROOT/'config/hitter_bounded_workload_v62_case_notes.json'),
        review_code_hashes={str(e.ROOT/'scripts'/n):sha256_file(e.ROOT/'scripts'/n)for n in
            ['score_hitter_bounded_workload_v62.py','audit_hitter_bounded_context_v62.py','finalize_hitter_bounded_workload_v62.py']})
    e.write('report.json',report);archive=e.ROOT/'reports/model-evidence/hitter-bounded-workload-v62';archive.mkdir(parents=True,exist_ok=True)
    for n in ['report.json','scores.json','intervals.json','verification.json','player-walkthrough.md','context-term-audit.json']:(archive/n).write_bytes((e.OUT/n).read_bytes())
    print(str(len(cases))+' actual reviews complete; '+review['decision'],flush=True)


if __name__=='__main__':main()
