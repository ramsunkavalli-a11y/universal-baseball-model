"""Archive reviewed compact research evidence without raw exports or fitted models."""
import shutil
import evaluate_hitter_readiness_v49 as e
from universal_baseball.storage import sha256_file


def main():
    assert e.old.r.read(e.OUT/'report.json')['player_walkthrough_status']=='complete'
    dest=e.ROOT/'reports/model-evidence/practical-hitter-readiness-v49';dest.mkdir(parents=True,exist_ok=True)
    names=['scores.json','probability-scores.json','intervals.json','cases.json','verification.json','report.json','player-walkthrough.md',
        'preflight-summary.json','fit-report.json','origin-profile-diagnostics.json','explorer-report.json','explorer-preview.jpg']
    manifest=[]
    for name in names:
        source=e.OUT/name;assert source.exists(),name
        shutil.copy2(source,dest/name);assert sha256_file(source)==sha256_file(dest/name)
        manifest.append(dict(name=name,source=str(source),sha256=sha256_file(source),bytes=source.stat().st_size))
    e.write('evidence-manifest.json',dict(files=manifest,raw_exports_and_models_excluded=True))
    shutil.copy2(e.OUT/'evidence-manifest.json',dest/'evidence-manifest.json')
    print('Archived',len(manifest),'reviewed evidence files; no raw exports, model handles or full row-ID preflight.',flush=True)


if __name__=='__main__':main()
