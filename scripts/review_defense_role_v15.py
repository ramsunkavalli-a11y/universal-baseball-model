"""Trace source periods into unchanged v14 roles and separated later reality."""
from pathlib import Path
import json

import polars as pl

from capture_defense_role_v15 import ROOT, OUT, PUBLIC, WALK, read, receipt
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file

JUDGMENTS={
    (660271,2022):'Reviewed 153 DH starts and zero eight-position fielding outs. Pitching outs belong to pitching, not hitter fielding. Broad fallback infield jobs are not missing-role recovery.',
    (660271,2023):'Reviewed 135 DH starts and no eight-position fielding use; the P/DH corrections have exact dates. Pure DH is observed role, not an empty role vector.',
    (660271,2024):'All 159 starts are DH; no observed hitter field position. Old quality evidence must not be converted into unobserved infield assignment.',
    (656941,2023):'DH starts rise from 28 of 106 LF/DH starts before August to 29 of 54 afterwards. This supports a role shift but does not establish the later 144-DH-start season. The separately dated November DH plan remains an omitted assignment input.',
    (670541,2024):'LF and DH both remain observed. An accurate role split cannot fix the fixed 547 expected PA versus 199 realized PA; workload and role are different errors.',
    (677951,2024):'All 4181 defensive outs are SS, with no current 3B use. Old 2022 3B is repertoire, not continuing 2024 assignment. Keeping that distinction does not prove the forecast defensive quality is correct.',
    (805811,2024):'The four 2024 levels all show only 1B and DH. AAA is eight September games, not a full upper-minor season. Earlier 2023 RF is real repertoire; Bride and Aranda had real 2B/3B history that Eldridge lacked.',
    (672275,2024):'Catcher assignment persists. The fixed workload/quality underestimates remain separate from current-role source recovery; catcher games do not themselves measure framing skill.',
    (663728,2024):'C and DH are both observed, unlike pure DH. The later 705 PA and 38 DH starts cannot be inferred solely from an earlier catcher role; fixed workload still limits delivery.',
    (678882,2024):'The source preserves both CF and SS at the cutoff. A later CF/2B switch is not supplied by the 2024 log. Neither primary-position pooling nor forced current-role persistence can guarantee the switch.',
    (694192,2023):'Large AA CF history and a tiny AAA stint stay separate. The later corner-outfield role is a genuine assignment change; no own MLB defensive quality is measured at the origin.',
    (614177,2022):'DH and some corner-outfield use are observed, but later 65 PA reflects opportunity loss. Missing native outcomes for a tiny fielding stint must remain unknown rather than a zero-quality result.',
    (694497,2023):'The short September MLB assignment is predominantly LF, while earlier AA use is predominantly CF. That is evidence of a role transition, not proof a 23-game MLB stint should erase developmental repertoire. Previous final-value gain partly canceled other errors.',
    (621439,2024):'CF use is current: 2301 MLB outs in 2024, including 484 after August 1, with no late MLB DH starts. The 2023 DH season must not dominate this restored assignment or be mistaken for proof of future health.',
    (660670,2023):'The current RF assignment is coherent. The later 222 PA versus fixed 588 predicted is chiefly a workload miss; better role measurement is not an injury predictor.',
    (592450,2023):'CF, RF and DH remain visible separately. The separately dated December CF expectation is not automatically a model input. The later hitting/value breakout cannot certify an assignment model.',
    (571771,2022):'Full role repertoire matters for a multi-position player. Recent use cannot justify treating every infielder/outfielder as equally plausible for every other player.',
    (672386,2024):'Current C use dominates, with DH only after August in this year. Older high-DH seasons are not necessarily continuing assignment; late five-DH-start evidence also should not imply a permanent switch.',
    (682928,2023):'SS persists in both periods. Near-perfect final value in the prior run concealed a large defense-quality miss; a sensible role is not certification of the skill estimate.'}


def roles(records):
    if not records:return 'No represented position use in this scope; not inferred absence'
    return '; '.join(f"{r['position']} {r['fielding_outs']} outs / {r['reviewed_starts']} starts"
                     for r in sorted(records,key=lambda r:r['position_code']) if r['position_code']!=1)


def main():
    protections()
    verify=read(OUT/'independent-verification.json');assert verify['source_integrity']=='pass'
    assert not (OUT/'player-walkthrough.json').exists()
    periods=pl.read_parquet(OUT/'verified-role-periods.parquet')
    walk=read(WALK);assert len(walk['cases'])==19
    cases=[];lines=['# Dated position evidence and unchanged forecasts','',
        'These are source checks, not new projections. Outs measure fielding time; DH starts remain a separate count. '
        'The earlier reference and job-capped forecasts are reproduced unchanged. Later results are separated from cutoff-known records.',
        '', 'The same nineteen focal cases and 57 origin-blind peer records are retained. '
        'All 114 requested annual scopes match exactly; this bounded success does not certify every player or year.','']
    for case in walk['cases']:
        records=[]
        for old in case['records']:
            pid,y=old['player_id'],old['origin']
            current=periods.filter((pl.col('player_id')==pid)&(pl.col('season')==y)).to_dicts()
            record=dict(player_id=pid,name=old['name'],row_id=old['row_id'],origin=y,target=old['target'],
                fold=old['fold'],stage=old['stage'],age=old['age'],source_history=old['source_history'],
                certified_current_role_periods=current,
                old_role_inputs={k:old[k] for k in ['own_job_shares','own_weight','evidence_kind',
                    'minor_fallback_season','learned_allowed_shares','seed_shares','profile','role_prior']},
                expected_PA_unchanged=old['expected_PA'],batting_unchanged=old['batting_fixed'],
                skill_channels_unchanged=old['skill_channels'],unchanged_forecasts=old['arms'],
                later_reality_only=dict(PA=old['actual_PA'],**old['actual']),
                new_forecast=None,no_new_fit=True,
                baseball_judgment=JUDGMENTS.get((pid,y),
                    'Origin-blind comparison retained. Inspect current positions, older repertoire and separately recorded later outcomes; '
                    'no fitted replacement or individual accuracy claim follows from a correctly measured assignment.'))
            records.append(record)
        cases.append(dict(selection=case['selection'],peer_rule=case['peer_rule'],records=records))
        focal=records[0]
        lines.extend([f"## {focal['name']} origin {focal['origin']}",'',focal['baseball_judgment'],''])
        for index,record in enumerate(records):
            label='Focal' if index==0 else 'Origin blind peer'
            lines.extend([f"{label}: {record['name']} ({record['player_id']}); age {record['age']}; {record['stage']}; fold {record['fold']}.",''])
            for sport in sorted({r['sport_id'] for r in record['certified_current_role_periods']}):
                for period in ('before_August','August_onward'):
                    subset=[r for r in record['certified_current_role_periods'] if r['sport_id']==sport and r['period']==period]
                    lines.append(f"Sport {sport}, {period.replace('_',' ')}: {roles(subset)}.")
            ref=record['unchanged_forecasts']['reference'];cand=record['unchanged_forecasts']['candidate'];actual=record['later_reality_only']
            fmt=lambda values: ', '.join(f'{x:.2f}' for x in values)
            lines.extend(['', 'Unchanged role forecast, outs in C, 1B, 2B, 3B, SS, LF, CF, RF order:',
                f"Reference [{fmt(ref['position_outs'])}], DH {ref['DH_starts']:.2f}; "
                f"prior candidate [{fmt(cand['position_outs'])}], DH {cand['DH_starts']:.2f}.",
                f"Later reality only: [{fmt(actual['position_outs'])}], DH {actual['DH_starts']}; "
                f"PA forecast {record['expected_PA_unchanged']:.2f} versus actual {actual['PA']}.",
                'No new forecast. Full source history, numerical role inputs, learned prior and fixed skill channels are in the linked machine-readable trace.',''])
    manifest=read(OUT/'explicit-scope-manifest.json');extras=[]
    old_pairs={(r['player_id'],r['origin']) for c in walk['cases'] for r in c['records']}
    diagnosis=read(ROOT/'reports/generated/defense-jobs-v14/source-profile-diagnosis.json')
    for case in manifest['cases']:
        if (case['player_id'],case['season']) in old_pairs:continue
        current=periods.filter((pl.col('player_id')==case['player_id'])&(pl.col('season')==case['season'])).to_dicts()
        contributor=next((r for r in diagnosis['Eldridge_prior_contributors']
            if r['player_id']==case['player_id'] and r['origin_year']==case['season']),None)
        extras.append(dict(**case,current_source=current,
            saved_prior_contributor=contributor,
            qualification='Diagnostic prior contributor chosen to explain a saved prior, not independent validation.'
                if contributor else 'Added prior-year role contrast; not a new forecast.'))
        lines.extend([f"## Additional source contrast {case['name']} {case['season']}",''])
        for sport in sorted({r['sport_id'] for r in current}):
            for period in ('before_August','August_onward'):
                subset=[r for r in current if r['sport_id']==sport and r['period']==period]
                lines.append(f"Sport {sport}, {period.replace('_',' ')}: {roles(subset)}.")
        lines.extend(['',extras[-1]['qualification'],''])
    receipt('player-walkthrough.json',dict(player_walkthrough_status='pending_manual_read',
        focal_cases=19,peer_records=57,total_old_records=sum(len(c['records']) for c in cases),
        cases=cases,additional_source_contrasts=extras,no_fits=True,no_accuracy_claim=True,no_deployment=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),WALK,OUT/'verified-role-periods.parquet',
                                             OUT/'independent-verification.json']}))
    body='\n'.join(lines).rstrip()+'\n'
    for folder in (OUT,PUBLIC):(folder/'player-walkthrough.md').write_text(body,encoding='utf8',newline='\n')
    protections();print('Prepared 19 focal and 57 unchanged peer traces plus five prior-year/contributor contrasts; manual review pending.',flush=True)


if __name__=='__main__':main()
