"""Preserve fixed workload evidence without changing any delivered forecast."""
import shutil
from pathlib import Path
from fit_hitter_conditional_workload_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from verify_hitter_conditional_workload_v1 import PACKAGE
from universal_baseball.storage import sha256_file


def main():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names=['prefit-manifest.json','fit-manifest.json','predictions.parquet','cumulative-predictions.parquet',
           'references.parquet','score-report.json']
    for n in names:shutil.copyfile(OUT/n,PACKAGE/n)
    code=[Path(__file__),Path('scripts/verify_hitter_conditional_workload_v1.py'),Path('docs/hitter-conditional-workload-v1-result.md')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},'code':{str(p):sha256_file(p) for p in code},
        'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(str(PACKAGE))


if __name__=='__main__':main()
