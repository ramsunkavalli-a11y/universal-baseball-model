"""Copy the reviewed candidate into a separate checksum-locked replay package."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import json
import numpy as np
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_event_logit import VALUES,NEUTRAL_WOBA_SCALE,EVENTS
from prepare_hitter_production_2026 import ROOT,OUT,read

FROZEN=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'


def main():
    assert not FROZEN.exists(),'Preserve any existing freeze; verify rather than overwrite'
    pre=read(OUT/'preflight.json');fit=read(OUT/'fit-report.json');review=read(OUT/'independent-review.json')
    assert review['all_forecasts_replayed']==4030 and review['head_replays_complete'] and review['output_products_replayed']
    assert review['player_walkthrough_status']=='complete_for_construction' and not review['protected_outcomes_used']
    for receipt in [pre,review]:
        for kind in ['input_hashes','output_hashes']:
            for p,h in receipt[kind].items():assert sha256_file(Path(p))==h,p
    assert sha256_file(OUT/'forecast.parquet')==fit['forecast_sha256']
    legacy=ROOT/'model_artifacts/hitter-full-2026-confirmation-forecast-2026-09-20'
    assert legacy.exists(),'Original legacy freeze must remain present'
    FROZEN.mkdir();sources=[];models=[]
    keep=['preflight.json','fit-execution-seal.json','fit-report.json','independent-review.json',
          'forecast.parquet','profile-support.parquet','pre-freeze-player-walks.json']
    for fold in range(5):keep += [f'inputs-{fold}.parquet',f'fit-{fold}.json',f'forecast-{fold}.parquet']
    for note in fit['folds']:
        for h in note['heads']:
            mp=Path(h['path']);assert sha256_file(mp)==h['sha256']
            keep.append(mp.name);models.append(dict(fold=note['fold'],head=h['head'],path=mp.name,
                features=h['features'],target=h['target'],sha256=h['sha256']))
    for name in keep:
        src=OUT/name;dest=FROZEN/name;shutil.copy2(src,dest)
        assert sha256_file(dest)==sha256_file(src);sources.append(dict(path=name,sha256=sha256_file(dest),original_path=str(src)))
    for name in ['hitter-2026-production-fit-contract.md','hitter-2026-final-evaluation-contract.md','hitter-tested-2020-training-correction.md']:
        src=ROOT/'docs'/name;dest=FROZEN/name;shutil.copy2(src,dest)
        sources.append(dict(path=name,sha256=sha256_file(dest),original_path=str(src)))
    for name in ['fit_hitter_production_2026.py','replay_hitter_production_2026.py','freeze_hitter_selected_2026.py']:
        src=ROOT/'scripts'/name;dest=FROZEN/name;shutil.copy2(src,dest)
        sources.append(dict(path=name,sha256=sha256_file(dest),original_path=str(src)))
    manifest=dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),forecast_origin=2025,target_year=2026,horizon=1,
        candidate='Fixed routed domestic-history hitter model',population=4030,model_heads=25,models=models,files=sources,
        source_information='Performance/rosters/status through December 31, 2025; separately verified January 26, 2026 ranks.',
        retrospective_source_vintages_qualified=True,prospect_translation='Own-origin held-player event bridge, not park-neutral MLE.',
        targets=dict(events=EVENTS,event_values=VALUES.tolist(),neutral_woba_scale=NEUTRAL_WOBA_SCALE,
            wins_per_600_conversion=600/(10*NEUTRAL_WOBA_SCALE),origin_replacement_reference=570/182926,
            primary_delivered='Future-season-relative batting plus fixed-origin replacement',secondary_delivered='Common-origin batting plus fixed-origin replacement'),
        coverage=pre['coverage'],unmodeled_rostered_nonpitchers=3,universal_coverage_claim_allowed=False,
        protected_outcomes_used_before_freeze=False,user_authorized_final_evaluation=True,construction_replay_pass=True,
        predictive_validation=False,full_war_model=False,control_or_trade_value_model=False,
        original_legacy_freeze_preserved=True,post_result_retuning_forbidden=True,
        source_provenance='Source and training manifests are copied; external raw source references remain hash-locked, not bundled wholesale.',
        self_contained_forecast_replay=True)
    p=FROZEN/'freeze-manifest.json';p.write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    digest=sha256_file(p);(FROZEN/'freeze-manifest.sha256').write_text(digest+'\n',encoding='ascii',newline='\n')
    for f in manifest['files']:assert sha256_file(FROZEN/f['path'])==f['sha256']
    print(json.dumps(dict(status='frozen',population=4030,heads=25,files=len(sources),manifest_sha256=digest,
        protected_outcomes_used_before_freeze=False,full_model_goal_complete=False)),flush=True)


if __name__=='__main__':main()
