"""Append date clarification without changing sealed results or forecasts."""
import shutil
from pathlib import Path
from evaluate_hitter_prospect_workload_specialization import OUT, EARLIER, CURRENT, ROOT, read, write, verify
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'date-clarification.json').exists()
    verify(read(OUT/'completed-review.json')['hashes'])
    inherited = EARLIER/'preflight.json'
    verify(read(inherited)['input_hashes'])
    path = CURRENT/'preflight.json'
    assert read(inherited)['input_hashes'][str(path)]==sha256_file(path)
    cells = read(path)['cells']
    years = sorted({c['year'] for c in cells})
    dates = []
    for year in years:
        origin = [c for c in cells if c['year']==year]
        assert len(origin)==5
        actual_dates = {c['information_date'] for c in origin}
        assert len(actual_dates)==1
        date = actual_dates.pop()
        assert date.startswith(str(year+1)+'-') and year+1<=2025
        dates.append(dict(statistical_origin=year,target_season=year+1,ranking_information_date=date,folds=5))
    write('date-clarification.json',dict(dates=dates,correction='Sealed report end-of-year wording is too strong; season-end statistics plus coming-season preseason rankings.',
        forecasts_changed=False,scores_changed=False,protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [path,inherited,OUT/'completed-review.json',
            ROOT/'docs/hitter-prospect-workload-specialization-date-clarification.md',Path(__file__)]}))
    dest = ROOT/'reports/model-evidence/hitter-prospect-workload-specialization/date-clarification.json'
    shutil.copyfile(OUT/'date-clarification.json',dest)
    assert sha256_file(OUT/'date-clarification.json')==sha256_file(dest)
    print(dates,flush=True)


if __name__=='__main__':main()
