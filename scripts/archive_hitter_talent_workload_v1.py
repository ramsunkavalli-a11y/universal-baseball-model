"""Archive talent/workload evidence without replacing delivered forecasts."""
import shutil
from pathlib import Path
from fit_hitter_talent_workload_v1 import OUT,PACKAGE
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file


def main():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names=['prefit-manifest.json','fit-manifest.json','predictions.parquet','nested-talent.parquet',
           'draft-evidence.parquet','cumulative-predictions.parquet','score-report.json']
    for n in names:shutil.copyfile(OUT/n,PACKAGE/n)
    code=[Path(__file__),Path('scripts/verify_hitter_talent_workload_v1.py'),Path('docs/hitter-talent-workload-v1-result.md')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},
        'code':{str(p):sha256_file(p) for p in code},'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(PACKAGE)


if __name__=='__main__':main()
