"""Archive reviewed evidence, excluding private exports and fitted handles."""
import shutil
import evaluate_hitter_reliability_v50 as e
from universal_baseball.storage import sha256_file

def main():
    assert e.prior.old.r.read(e.OUT/'report.json')['player_walkthrough_status']=='complete'
    dest=e.ROOT/'reports/model-evidence/practical-hitter-reliability-v50';dest.mkdir(parents=True,exist_ok=True)
    names=['scores.json','intervals.json','cases.json','verification.json','report.json','player-walkthrough.md','preflight-summary.json','fit-report.json','primary-loss-case-check.json']
    manifest=[]
    for name in names:
        source=e.OUT/name;shutil.copy2(source,dest/name);assert sha256_file(source)==sha256_file(dest/name)
        manifest.append(dict(name=name,sha256=sha256_file(source),bytes=source.stat().st_size))
    e.write('evidence-manifest.json',dict(files=manifest,raw_exports_and_models_excluded=True))
    shutil.copy2(e.OUT/'evidence-manifest.json',dest/'evidence-manifest.json')
    print('Archived nine reviewed compact evidence files.',flush=True)

if __name__=='__main__':main()
