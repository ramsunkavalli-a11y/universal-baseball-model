"""Append the manual component decision without changing fits or earlier receipts."""
import json
from pathlib import Path

import polars as pl

from prepare_foreign_component_translation import ROOT, OUT, NPB, KBO, read, save, verify
from universal_baseball.storage import sha256_file

EVIDENCE=ROOT/'reports/model-evidence/foreign-component-translation'
RESULT=ROOT/'docs/hitter-foreign-component-translation-result.md'


def main():
    assert not (OUT/'final-review.json').exists(),'Preserve completed review'
    review=read(OUT/'independent-review.json'); verify(review['hashes'])
    receipt=read(OUT/'fit-receipt.json'); verify(receipt['source_hashes']); verify(receipt['artifact_hashes'])
    cases=read(OUT/'reviewed-cases.json')['cases']; fits=read(OUT/'fits.json')['fits']
    profiles=read(OUT/'profiles.json')['profiles']; pre=read(OUT/'preflight.json')
    text=RESULT.read_text(encoding='utf8')
    for token in ['20.8%','8.23%','Fukudome','Tsutsugo','Aoki','Choo','zero is not an observed hitting rate']:
        assert token in text,token
    controls=read(ROOT/'reports/generated/foreign-mover-support-v2-npb-kbo/ordinary-source-cases.json')['cases']
    ordinary=[]
    for c in controls:
        path=NPB if c['league']=='NPB' else KBO
        rows=pl.read_parquet(path).filter((pl.col('season')==c['origin'])&(pl.col('player_id')==c['player_id']))
        for field,value in c['source_counts'].items():
            assert rows[field].sum()==value
        assert not any(p['player_id']==c['player_id'] and p['origin_year']==c['origin'] for p in profiles)
        ordinary.append(dict(**c,source_reconstructed=True,translated_profile=None,
                             observation='outside_sealed_input_population_not_a_zero_talent_estimate'))
    # Preserve an unmapped control chosen using only source-year exposure and ID.
    unknown=pl.read_parquet(NPB).filter((pl.col('season')==2024)&pl.col('player_id').is_null()&(pl.col('pa')>=100))
    unknown=unknown.sort(['npb_id','player_name_ja']).head(1).to_dicts()
    unresolved=[]
    for r in unknown:
        unresolved.append(dict(league='NPB',season=2024,npb_id=r['npb_id'],source_name=r['player_name_ja'],
            source_counts={k:r[k] for k in ['pa','so','bb','ibb','hbp','hits','doubles','triples','hr']},
            player_id=None,selection='lowest_published_NPB_ID_unmapped_100PA_2024',
            selection_uses_future_results=False,translated_profile=None,observed_future_MLB_PA=None,
            interpretation='Identity unresolved; cannot score a missing identity as zero future MLB use'))
    save(OUT/'ordinary-and-unresolved-controls.json',dict(ordinary=ordinary,unresolved=unresolved))
    lines=['# Overseas component player arithmetic','','Input preparation, not new workload or full value forecasts. Event probabilities are ordered other, K, UBB, HBP, 1B, 2B, 3B, HR. Unknown conditional production stays unobserved for zero MLB PA. The separate result document contains manual baseball judgments.','']
    compact=[]
    for c in cases:
        lines += [f"## {c['name']} before {c['origin_year']+1}",'',
                  'Selection: '+c['selection']+'.','',
                  'Known source seasons and context: '+json.dumps(c['source_input'],ensure_ascii=False)+'.','',
                  'Translated profile and complete reference: '+json.dumps(c['translated_profile'],ensure_ascii=False)+'.','',
                  'Actual fitted coefficients and support: '+json.dumps(c['model'],ensure_ascii=False)+'.','',
                  'Unchanged saved model: '+json.dumps(c['unchanged_saved_forecast'],ensure_ascii=False)+'.','',
                  f"Observed next MLB PA {c['observed_next_MLB_PA']}; event counts {c['observed_next_MLB_counts']}; observed probabilities {c['observed_next_MLB_probability']}. These are diagnostic outcomes, not predictor inputs.",'',
                  'Outcome-blind peers with future observations added only for review: '+json.dumps(c['origin_only_peers'],ensure_ascii=False)+'.','',
                  'No new expected MLB PA or full value is inferred from this conditional batting component. Sparse mover and role support remains explicit.','']
        p=c['translated_profile']; m=c['model']
        compact.append(dict(name=c['name'],player_id=c['player_id'],origin_year=c['origin_year'],
            source_recent_foreign_pa=c['source_input']['recent_foreign_pa'] if c['source_input'] else None,
            translated_probability=p['translated_probability'] if p else None,
            people_by_league=m['people_by_league'] if m else None,
            coefficients=m['coefficients'] if m else None,
            observed_MLB_PA=c['observed_next_MLB_PA'],observed_probability=c['observed_next_MLB_probability'],
            saved_forecast=c['unchanged_saved_forecast'],peers=c['origin_only_peers'],
            new_MLB_PA_forecast=None,new_full_value_forecast=None))
    lines += ['## Ordinary and unresolved source controls','',json.dumps(dict(ordinary=ordinary,unresolved=unresolved),ensure_ascii=False), '',
              'These source controls do not gain a forecast or a zero-talent label from this translation.','']
    walk=OUT/'player-walkthrough.md'; assert not walk.exists()
    walk.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    final=dict(status='component_input_review_complete_not_talent_replacement_approved',
        source_event_and_reference_reconstruction=True,constrained_optima_checked=review['component_optima_checked'],
        profiles_reconstructed=review['profiles_reconstructed'],manual_player_cases=len(cases),
        ordinary_controls=len(ordinary),unresolved_identity_controls=len(unresolved),
        player_walkthrough_status='complete_for_component_inputs',predictive_improvement_established=False,
        reasonability='contact_and_power_compression_in_consequential_cases',
        translation_replacement_approved=False,full_hitter_forecasts_changed=False,goal_achieved=False,
        tests=review['tests'],protected_freeze=review['protected_freeze'],
        source_hashes=receipt['source_hashes'],
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'independent-review.json',
            OUT/'ordinary-and-unresolved-controls.json',OUT/'reviewed-cases.json',walk,RESULT,Path(__file__)]})
    save(OUT/'final-review.json',final)
    save(EVIDENCE/'final-review.json',final)
    save(EVIDENCE/'case-summary.json',dict(cases=compact,ordinary=ordinary,unresolved=unresolved,
         private_full_arithmetic_sha256=sha256_file(walk),manual_review_path=str(RESULT.relative_to(ROOT))))
    save(EVIDENCE/'support-summary.json',dict(cells=[{k:v for k,v in c.items() if k not in ['members','mover_keys']} for c in pre['cells']],
        reference_summary=pre['reference_summary'],missing_profiles=sum(p['missing_translation'] for p in profiles),
        profiles=len(profiles),source_origins=pre['input_origins'],source_additions=pre['added_source_origins'],
        lower_bound_event_fits=sum(len(m['slope_lower_bound_events']) for m in fits),
        upper_bound_event_fits=sum(len(m['slope_upper_bound_events']) for m in fits),
        warning='Fold support is conditional on observed MLB moves; no arrival or full-hitter performance certification'))
    print(json.dumps({k:v for k,v in final.items() if k not in ['source_hashes','artifact_hashes','tests','protected_freeze']}),flush=True)


if __name__=='__main__': main()
