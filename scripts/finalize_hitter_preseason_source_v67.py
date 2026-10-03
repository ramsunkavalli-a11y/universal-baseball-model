"""Seal reviewed rank vintage evidence, without certifying a model improvement."""
import numpy as np
import polars as pl
from universal_baseball.historical_prospect_rank import features
from universal_baseball.storage import sha256_file
import prepare_hitter_preseason_readiness_v67 as s

def main():
    r=s.read(s.OUT/'source-report.json');cases=s.read(s.OUT/'source-cases.json')
    rp=s.ROOT/'config/hitter_preseason_rank_v67_source_review.json';ep=s.ROOT/'config/hitter_preseason_rank_v67_release_evidence.json'
    review=s.read(rp);release=s.read(ep)
    assert set(review)=={f"{c['player_id']}|{c['origin_year']}" for c in cases} and all(len(n)>200 for n in review.values())
    assert set(release)=={str(y) for y in range(2011,2026)}
    assert all(d['date'].startswith(y+'-') and d['date'][5:7] in ['01','03'] for y,d in release.items())
    for p,h in r['input_hashes'].items():assert sha256_file(s.Path(p))==h,p
    old=pl.read_parquet(s.BASE).sort('row_id');new=pl.read_parquet(s.OUT/'features.parquet').sort('row_id')
    cols=r['scouting_columns'];assert old.drop(cols).equals(new.drop(cols))
    rank=pl.read_parquet(s.OUT/'ranks.parquet');lookup={(a['season'],a['player_id']):a['rank'] for a in rank.iter_rows(named=True)}
    cap={a['season']:a['list_capacity'] for a in rank.iter_rows(named=True)}
    for a in new.iter_rows(named=True):
        expected=features(a['player_id'],a['origin_year']+1,lookup,cap)
        assert all(np.isclose(a[k],-1 if v is None else v) for k,v in expected.items())
    assert lookup[2017,641355]==13 and lookup[2024,694671]==6 and lookup[2025,701762]==38
    lines=['# Preseason ranking source review','',
        'Source-only checkpoint: no new forecasts, no outcome-dependent source mapping, no protected 2026 access. All 63,282 source identities and all non-scouting fields stay exact. Unknown ranking absence remains encoded -1, as in V53, not zero.','',
        'This is later preseason information, not a repair to a December forecast. Publication evidence establishes availability during the coming preseason; the tables remain retrospective reproductions, not individually certified contemporary archives. The 2022 list was unavailable in January.','',
        '| List | Availability evidence date | Publisher evidence |','| --- | --- | --- |']
    for y,d in release.items():lines.append(f"| {y} | {d['date']} | [{d['basis']}]({d['url']}) |")
    for c in cases:
        key=f"{c['player_id']}|{c['origin_year']}";c['review_note']=review[key]
        lines += ['',f"## {c['player_name']} / {c['origin_year']}",'',review[key],'',
            '| Source season | Level | PA | HR | K |','| --- | --- | ---: | ---: | ---: |']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} |")
        lines += ['',f"Actual old input: {c['old_scouting']}",'',f"Actual later preseason input: {c['preseason_scouting']}",'',
            f"Unchanged retained forecast/intermediates: {c['baseline_forecast']}",'',
            '| Previously selected origin-known peer | Old rank | New preseason rank |','| --- | ---: | ---: |']
        for p in c['peers']:lines.append(f"| {p['player_name']} ({p['player_id']}) | {p['old_rank'] or 'absent/unknown'} | {p['preseason_rank'] or 'absent/unknown'} |")
    lines += ['',f"{r['outside_membership_rows']} ranked player-seasons in the target-year range are outside the original hitter source population. Many are pitchers; no claim that they are all missed hitters. They remain inventoried, not silently admitted using later information. No eligible source row was deleted.",'',
        'Disposition: source review complete with retrospective dating limits. Proceed to the one locked matched readiness comparison after actual support checks. No predictive gain claimed, and no source-only result can authorize deployment.']
    (s.OUT/'source-walkthrough.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    s.write('reviewed-source-cases.json',cases)
    r.update(source_review_status='complete',release_date_review_status='complete_with_retrospective_table_qualification',release_evidence=release,
        all_encoded_rows_reconstructed=True,protected_outcomes_used=False,fitted=False,
        review_hashes={str(p):sha256_file(p) for p in [rp,ep,s.Path(__file__),s.ROOT/'scripts/prepare_hitter_preseason_readiness_v67.py',s.ROOT/'src/universal_baseball/historical_prospect_rank.py']})
    r['output_hashes'].update({str(p):sha256_file(p) for p in [s.OUT/'reviewed-source-cases.json',s.OUT/'source-walkthrough.md']})
    s.write('source-report.json',r)
    archive=s.ROOT/'reports/model-evidence/hitter-preseason-readiness-v67';archive.mkdir(parents=True,exist_ok=True)
    for n in ['source-report.json','reviewed-source-cases.json','source-walkthrough.md']:(archive/n).write_bytes((s.OUT/n).read_bytes())
    print('Reviewed eight source cases, publication evidence and all encoded ranking rows; no forecasts fitted.',flush=True)

if __name__=='__main__':main()
