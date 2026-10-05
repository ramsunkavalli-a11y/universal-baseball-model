"""Preserve first fits; change only calibration history under the sealed amendment."""
import argparse
import json

from prepare_foreign_component_translation import ROOT,OUT as OLD,INPUTS,read,save,verify,sources
from universal_baseball.foreign_component_translation import References,profile,training_pairs
from universal_baseball.foreign_component_translation_v2 import fit,histories,pooled_source
from universal_baseball.storage import sha256_file

OUT=ROOT/'reports/generated/foreign-component-translation-v2'


def prepare():
    assert not OUT.exists(),'Inspect existing preparation'
    final=read(OLD/'final-review.json'); assert final['player_walkthrough_status']=='complete_for_component_inputs'
    verify(final['source_hashes']); verify(final['artifact_hashes'])
    original=read(OLD/'preflight.json'); verify(original['source_hashes'])
    rows=sources(); history=histories(rows); refs=References(rows)
    pairs=read(INPUTS/'pair-role-evidence.json')['pairs']
    notes=[]
    for cell in original['cells']:
        group=training_pairs(pairs,cell['origin_year'],cell['excluded_folds'])
        for p in group:
            _,note=pooled_source(p['player_id'],p['a'],p['from_year'],history,refs,cell['excluded_folds'])
            notes.append(dict(origin=cell['origin_year'],excluded_folds=cell['excluded_folds'],
                player_id=p['player_id'],league=p['a'],from_year=p['from_year'],target_year=p['through_year'],**note))
    paths=[ROOT/'docs/hitter-foreign-component-history-amendment.md',ROOT/'src/universal_baseball/foreign_component_translation_v2.py',
           ROOT/'tests/test_foreign_component_translation_v2.py',ROOT/'scripts/prepare_foreign_component_translation_v2.py',
           OLD/'preflight.json',OLD/'final-review.json',OLD/'profiles.json',OLD/'fits.json']
    hashes={**original['source_hashes'],**{str(p.relative_to(ROOT)):sha256_file(p) for p in paths}}
    save(OUT/'preflight.json',dict(source_hashes=hashes,cells=original['cells'],calibration_histories=notes,
        changed='calibration_source_history_only',same_pairs_targets_weights_settings_and_prediction_definition=True,
        original_membership_unchanged=True,all_preflights_before_fits=True))
    print(json.dumps(dict(cells=len(original['cells']),calibration_histories=len(notes),new_fits=0)),flush=True)


def run():
    pre=read(OUT/'preflight.json'); verify(pre['source_hashes'])
    assert not (OUT/'fits.json').exists() and not (OUT/'fit-receipt.json').exists(),'Inspect execution before restarting'
    inputs=read(INPUTS/'origin-inputs.json')['rows']; lut={r['candidate_key']:r for r in inputs}
    pairs=read(INPUTS/'pair-role-evidence.json')['pairs']; rows=sources(); refs=References(rows); history=histories(rows)
    fits=[]; profiles=[]
    old_fits={m['fit_key']:m for m in read(OLD/'fits.json')['fits']}
    for c in pre['cells']:
        m=fit(pairs,refs,c['origin_year'],c['excluded_folds'],history)
        key=f"{c['origin_year']}-"+'-'.join(map(str,c['excluded_folds']))
        old=old_fits[key]
        assert m['people_by_league']==old['people_by_league']
        for a,b in zip(m['pairs'],old['pairs']):
            assert all(a[v]==b[v] for v in ['player_id','league','from_year','target_year','weight','target_relative_clr'])
        fits.append(dict(fit_key=key,**m))
        for member in c['members']:
            p=profile(lut[member['candidate_key']],m,refs)
            profiles.append(dict(**p,outer_fold=member['outer_fold'],fit_key=key))
    assert len(profiles)==3205
    save(OUT/'fits.json',dict(fits=fits)); save(OUT/'profiles.json',dict(profiles=profiles))
    save(OUT/'fit-receipt.json',dict(source_hashes=pre['source_hashes'],component_fits=len(fits)*8,profiles=len(profiles),
        missing_profiles=sum(p['missing_translation'] for p in profiles),independent_review_status='pending',
        player_walkthrough_status='pending',full_hitter_forecasts_changed=False,
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'preflight.json',OUT/'fits.json',OUT/'profiles.json']}))
    print(json.dumps(dict(component_fits=len(fits)*8,profiles=len(profiles),review='pending')),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','fit']); args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
