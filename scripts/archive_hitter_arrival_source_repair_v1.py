"""Archive compact derived research evidence, not raw external captures."""
import shutil
from pathlib import Path
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_arrival_source_repair_v1 import OUT
from verify_hitter_arrival_source_repair_v1 import PACKAGE
from universal_baseball.storage import sha256_file


def main():
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names=['prefit-manifest.json','fit-manifest.json','score-report.json','predictions.parquet',
           'source-audit.json','source-changes.parquet','league-context.parquet']
    for name in names:shutil.copyfile(OUT/name,PACKAGE/name)
    diagnostic=Path('reports/generated/hitter-arrival-player-errors-v1')
    for name in ('summary.md','casebook.md','report.json','source-findings.json','player-cases.parquet'):
        dest='prior-diagnostic-'+name
        shutil.copyfile(diagnostic/name,PACKAGE/dest);names.append(dest)
    code=[Path(__file__),Path('scripts/verify_hitter_arrival_source_repair_v1.py'),
          Path('scripts/score_hitter_detail_arrival_v1.py'),Path('src/universal_baseball/multiyear_hitter_followup.py'),
          Path('docs/hitter-arrival-source-repair-v1-result.md'),
          Path('scripts/diagnose_hitter_arrival_player_errors_v1.py'),Path('scripts/summarize_hitter_arrival_player_errors_v1.py')]
    save(PACKAGE/'manifest.json',{'files':{n:sha256_file(PACKAGE/n) for n in names},
        'code':{str(p):sha256_file(p) for p in code},'protected_outcomes_used':False,
        'production_forecasts_changed':False,'raw_source_captures_committed':False})
    print(str(PACKAGE))


if __name__=='__main__':main()
