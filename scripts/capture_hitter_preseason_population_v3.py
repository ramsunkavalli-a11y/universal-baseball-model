"""Complete qualified capture with player-preserving transaction reconciliation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import capture_hitter_preseason_population as original
import capture_hitter_preseason_population_v2 as corrected
from universal_baseball.hitter_preseason_population import reconcile_transactions
from universal_baseball.storage import sha256_file


def main():
    authority = corrected.authority()
    metas, checks = [], []
    for year in range(2012, 2026):
        cutoff = original.read(original.CONFIG)[str(year)]['date']
        teams, meta = original.capture(f'teams-{year}.json', original.BASE+'/teams', dict(sportId=1,season=year))
        metas.append(meta)
        ids = sorted({t['id'] for t in teams['teams']})
        assert len(ids) == 30
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(original.roster, team, year, '40Man') for team in ids]
            for future in as_completed(futures):
                _, meta = future.result()
                metas.append(meta)
        start = f'{year-1}-10-01'
        whole, meta = original.capture(f'transactions-{year}.json', original.BASE+'/transactions',dict(startDate=start,endDate=cutoff))
        metas.append(meta)
        windows = list(corrected.months(start,cutoff))
        partition = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(original.capture,f'transactions-{year}-{a}-{b}.json',original.BASE+'/transactions',
                                   dict(startDate=a,endDate=b)): (a,b) for a,b in windows}
            for future in as_completed(futures):
                data, meta = future.result()
                metas.append(meta)
                a,b = futures[future]
                partition.append((a,b,data['transactions']))
        check = reconcile_transactions(whole['transactions'],partition,start,cutoff)
        checks.append(dict(season=year,cutoff=cutoff,**check))
        print('Captured',year,cutoff,'30 team listings;',check,flush=True)
    original.write(original.OUT/'capture-report-v3.json',dict(
        captures=metas,transaction_checks=checks,completed_years=list(range(2012,2026)),authority=authority,
        date_config_sha256=sha256_file(original.CONFIG),code_sha256=sha256_file(Path(__file__)),
        mechanics_sha256=sha256_file(original.ROOT/'src/universal_baseball/hitter_preseason_population.py'),
        transaction_amendment_sha256=sha256_file(original.ROOT/'docs/hitter-preseason-population-transaction-amendment.md'),
        source_review_status='pending',new_fits=0,protected_2026_opened=False,forecasts_changed=False))


if __name__ == '__main__': main()
