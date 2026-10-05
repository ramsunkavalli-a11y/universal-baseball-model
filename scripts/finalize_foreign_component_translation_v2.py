"""Append completed manual history-repair review and publish bounded evidence."""
import json

from prepare_foreign_component_translation_v2 import ROOT,OUT,OLD,read,save,verify
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'final-review.json').exists(),'Preserve completed evidence'
    review=read(OUT/'independent-review.json');verify(review['hashes'])
    receipt=read(OUT/'fit-receipt.json');verify(receipt['source_hashes']);verify(receipt['artifact_hashes'])
    result=ROOT/'docs/hitter-foreign-component-history-repair-result.md'
    text=result.read_text(encoding='utf8')
    for token in ['21.28%','8.23%','Ohtani','Yoshida','Fukudome','Thames','Unobserved','twenty-seven']:
        assert token in text,token
    cases=read(OUT/'reviewed-cases.json')['cases'];assert len(cases)==14
    compact=[];lines=['# Matched overseas history repair player arithmetic','','The first source histories, actual observations and peers remain unchanged. Append corrected models and profiles. No new workload or full-value forecast.','']
    for c in cases:
        p=c['translated_profile'];q=c['repaired_profile'];m=c['repaired_model']
        compact.append(dict(name=c['name'],player_id=c['player_id'],origin_year=c['origin_year'],
            first_probability=p['translated_probability'] if p else None,
            repaired_probability=q['translated_probability'] if q else None,
            observed_probability=c['observed_next_MLB_probability'],observed_MLB_PA=c['observed_next_MLB_PA'],
            repaired_coefficients=m['coefficients'] if m else None,people_by_league=m['people_by_league'] if m else None))
        lines += [f"## {c['name']} before {c['origin_year']+1}",'',json.dumps(c,ensure_ascii=False), '']
    controls=read(OLD/'ordinary-and-unresolved-controls.json')
    lines += ['## Preserved ordinary and unresolved controls','',json.dumps(controls,ensure_ascii=False),'']
    walk=OUT/'player-walkthrough.md';assert not walk.exists()
    walk.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    final=dict(status='history_repair_review_complete_affine_talent_replacement_withheld',
        player_walkthrough_status='complete_for_component_inputs',case_count=14,
        same_pair_targets_weights_and_source_prediction_histories=True,
        component_optima_checked=review['component_optima_checked'],profiles_reconstructed=review['profiles_reconstructed'],
        tests=review['tests'],protected_freeze=review['protected_freeze'],
        full_hitter_forecasts_changed=False,translation_replacement_approved=False,
        predictive_improvement_established=False,goal_achieved=False,
        source_hashes=receipt['source_hashes'],
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [result,walk,OUT/'independent-review.json',OUT/'reviewed-cases.json',ROOT/'scripts/finalize_foreign_component_translation_v2.py']})
    save(OUT/'final-review.json',final)
    evidence=ROOT/'reports/model-evidence/foreign-component-translation-v2'
    save(evidence/'final-review.json',final)
    save(evidence/'case-comparison.json',dict(cases=compact,ordinary_unresolved_controls=controls,
         private_walkthrough_sha256=sha256_file(walk),manual_review_path=str(result.relative_to(ROOT))))
    print(json.dumps(dict(review='complete',profiles=3205,case_count=14,full_hitter_forecasts_changed=False,translation_replacement_approved=False)),flush=True)


if __name__=='__main__':main()
