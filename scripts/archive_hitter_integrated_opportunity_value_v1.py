"""Archive fixed integration evidence without replacing a forecast package."""
import shutil
from pathlib import Path

from build_hitter_integrated_opportunity_value_v1 import OUT, PACKAGE, CODE, PLAN
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file


def main():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names=['prefit-manifest.json','build-manifest.json','predictions.parquet',
           'component-predictions.parquet','cumulative-predictions.parquet','score-report.json']
    for name in names:
        target=PACKAGE/name
        if target.exists() and sha256_file(target)!=sha256_file(OUT/name):
            raise ValueError('Refusing to overwrite different archived evidence: '+str(target))
        shutil.copyfile(OUT/name,target)
    code=[*CODE,PLAN,Path(__file__),Path('scripts/verify_hitter_integrated_opportunity_value_v1.py'),
          Path('docs/hitter-integrated-opportunity-value-v1-result.md')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},
        'code':{str(p):sha256_file(p) for p in code},'protected_outcomes_used':False,
        'production_forecasts_changed':False,'decision':'retain research evidence, reject integrated deployment'})
    print(PACKAGE)


if __name__=='__main__':main()
