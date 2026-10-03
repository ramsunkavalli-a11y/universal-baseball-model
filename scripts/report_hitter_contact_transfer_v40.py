"""Complete source-to-input review; no copied legacy winner weights or new fits."""
from pathlib import Path
import audit_hitter_contact_transfer_v40 as e
from universal_baseball.storage import sha256_file


def main():
    audit=e.r.read(e.OUT/'audit.json')
    for p,h in audit['input_hashes'].items():assert sha256_file(Path(p))==h,p
    cases=e.r.read(e.OUT/'cases.json');np=e.r.ROOT/'config/practical_hitter_contact_v40_case_notes.json';notes=e.r.read(np)
    assert len(cases)==len(notes)==8
    lines=['# V40: completed contact-source compatibility walkthrough','',
        'No model fitted or scored. Source hashes verified. Same broad eligibility; missing rows retained as null, not neutral/zero talent. Eight fixed source cases and origin-only same-stage/debut age/exposure/draft peers. No future success used for source selection.','',
        'Earlier gradient target levels are A, High-A, AA, AAA and Rookie only; all target rows have positive observed contact. Earlier folds hold time out but contain repeated train/test players, unlike the present whole-player folds. That is a different validation design, not automatic proof the earlier test is invalid for its stated conditional target. Its score cannot certify future MLB hitting, arrival, workload or value.','',
        'Earlier source contact cells are raw measured counts with a 100-contact source-level-bin prior. Mean prior-opponent/hand and park effects are separate covariates. This is not direct fully park-neutralized player evidence. The universal shape table includes MLB, uses actual league identity and spans 2021–24; the examined older gradient table spans those same years but minor contacts only. Neither inspected table supplies 2016–20 shape measurements.','']
    for c in cases:
        key=f"{c['player_name']}|{c['origin_year']}";assert key in notes
        lines.extend([f"## {c['player_name']}: origin {c['origin_year']}",'',notes[key],'',
            '| Year | Actual league bucket | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|'])
        for h in c['batting_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines.extend(['','Actual source-to-input join: '+str(c['inputs'])+'.','',
            '| Shape year | Actual league ID | Source level | Bin | Observations |','|---|---:|---|---|---:|'])
        for h in c['shape_history']:lines.append(f"| {h['season']} | {h['league_id']} | {h['level_group']} | {h['core_bin']} | {h['occurrence_count']} |")
        lines.extend(['','Old detailed source history (minor-only): '+str(c['old_feature_history'])+'.','',
            'Origin-only peers: '+'; '.join(f"{p['player_name']} (MLB/AAA/AA PA {p['pa_0']}/{p['AAA_0_pa']}/{p['AA_0_pa']}; old contacts {p['materialized_contacts']}; universal MLB/minor shapes {p['shape_mlb']}/{p['shape_minor']})" for p in c['peers'])+'.','',
            'No new forecast/intermediate or predictive outcome is fabricated for this source-only checkpoint.',''])
    lines.extend(['## Source disposition','',
        'Re-use canonical raw measurements only after a new MLB-target assembly with separate league/evidence reliability, proper earlier-source coverage and whole-player/time learning. Do not import the old fitted contact forecast weights as certified MLB talent. Current inputs cannot support a decade-wide contact claim. Universal shape supplies otherwise missing MLB records for the supported 2021–24 source years; earlier sources must be materialized or forecasts remain exact baseline fallback with explicit unsupported labels. A failed transfer coverage check is not a negative contact-model experiment.'])
    path=e.OUT/'source-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    e.write('report.json',dict(source_walkthrough_status='complete',cases=8,old_weights_transfer_certified=False,
        reusable_raw_measurements=True,decade_wide_contact_coverage=False,predictive_claim=False,no_new_fit_or_score=True,
        notes_sha256=sha256_file(np),walkthrough_sha256=sha256_file(path),audit_sha256=sha256_file(e.OUT/'audit.json'),
        protected_outcomes_used=False,frozen_forecast_changed=False))
    print('Eight source walks complete: raw evidence reusable, legacy MLB transfer not certified.')


if __name__=='__main__':main()
