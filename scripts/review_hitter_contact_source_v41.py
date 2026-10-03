"""Close fixed actual source walks before the contact projection comparison."""
import math
import polars as pl
import prepare_hitter_contact_v41 as e
from universal_baseball.storage import sha256_file

NOTES={
    'Aaron Judge|2016':'His 2016 AAA contact is now observed, not missing as in the modern-only table. Its 257 weighted contacts support descriptive shape, but no contact training exists before this cutoff: both challengers must retain the baseline. MLB shape is unobserved here, not zero talent.',
    'Aaron Judge|2024':'Three years of MLB contact are available, unlike the minor-only gradient table. The approximately 807 weighted contacts give substantial shape evidence. These are ground/fly/direction labels, not a direct measurement of exit velocity or a replacement for his established home-run production.',
    'Masyn Winn|2023':'Current brief MLB contact and larger AAA/AA histories remain in distinct buckets. The 100-contact prior strongly moderates his short MLB debut. A contact forecast must not discard stronger minor production merely because a few major-league balls were recorded.',
    'Spencer Steer|2022':'The source retains both minor contact histories and the brief major debut. His AA fraction slightly exceeded BABIP opportunities in the first diagnostic; PA is the correct finite upper bound for this measurement fraction. This is not a retrospective promotion signal.',
    'Nick Kurtz|2024':'There are only 18 A and 10 AA contacts. The displayed probabilities are heavily prior-driven, not estimates of mature MLB talent. The larger upper-minor samples of other players cannot be assigned to him by confidence; pedigree remains in the unchanged count backbone.',
    'Gavin Lux|2023':'A missed current year does not erase prior MLB contact. Recency-weighted 2021/22 evidence remains usable. The source cannot explain why he missed the year or assert his future health; workload is deliberately fixed.',
    'Chase Meidroth|2024':'The larger AAA and preceding AA histories have ample measured contact. A high ground-ball share and few pulled flies are not automatically bad hitting: his walk/strikeout/extra-base production remains supplied separately and the future-MLB test decides whether shape adds signal.',
    'Cody Bellinger|2016':'AA and short AAA contact are observed, unlike the modern-only source. They cannot train a relationship before contact history begins, so the 2016 forecast stays exact baseline. This source repair alone cannot fix his low projected first-year MLB opportunity.'}


def main():
    p=e.OUT/'preflight.json';pre=e.r.read(p);cases=e.r.read(e.OUT/'source-cases.json')
    for path,h in pre['input_hashes'].items():assert sha256_file(e.Path(path))==h,path
    f=pl.read_parquet(e.OUT/'features.parquet');bad=pl.read_parquet(e.OUT/'unreconciled-player-leagues.parquet')
    summary=bad.with_columns(pl.when(pl.col('plate_appearances').is_null()).then(pl.lit('unmatched official player/league'))
        .when(pl.col('plate_appearances')<=0).then(pl.lit('zero official PA')).otherwise(pl.lit('contacts exceed official PA')).alias('reason'))
    e.write('unreconciled-summary.json',summary.group_by('season','bucket','reason').agg(pl.len().alias('rows'),pl.col('contacts').sum()).sort('season','bucket','reason').to_dicts())
    lines=['# V41 source walkthrough completed before fitting','','Raw contact measurements, distinct league buckets, source/missingness and official-count corroboration. No forecast or protected outcomes in this source checkpoint.','',
        f"Unreconciled player/league/seasons: {pre['unreconciled_player_league_seasons']}; raw contacts excluded from this predictor: {pre['unreconciled_contacts']:,}. Player eligibility and their official batting predictors stay unchanged. Four ambiguous 2023 PA keys are also quarantined. The old artifacts are retained; this does not certify or repair their every source join.",'']
    for c in cases:
        key=f"{c['name']}|{c['origin_year']}";assert key in NOTES
        lines.extend([f"## {c['name']}, origin {c['origin_year']}",'',NOTES[key],'','| Year | League | PA | K | UBB | HR |','|---|---|---:|---:|---:|---:|'])
        for h in sorted(c['batting_history'],key=lambda h:(h['season'],h['bucket'])):lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['strike_outs']} | {h['unintentional_walks']} | {h['home_runs']} |")
        lines.extend(['','| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |','|---|---:|---:|---:|---:|'])
        for b in e.r.BUCKETS:
            a=c['actual_contact_inputs']
            if not a[f'shape_{b}_available']:continue
            lines.append(f"| {b} | {math.expm1(a[f'shape_{b}_log_n']):.3f} | {a[f'shape_{b}_coverage']:.5f} | {a[f'shape_{b}_PULL_OFFB']:.5f} | {sum(a[f'shape_{b}_{d}_GB'] for d in ['PULL','CENTER','OPPO']):.5f} |")
        o=f.filter(pl.col('row_id')==c['row_id']).to_dicts()[0]
        peers=f.filter((pl.col('origin_year')==c['origin_year'])&(pl.col('player_id')!=c['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
        distance=sum(((pl.col(k)-o[k])/s)**2 for k,s in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1)])
        peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
        lines.extend(['','Origin-selected peers (no future outcomes used): '+'; '.join(f"{s['player_name']} age {s['age']:.1f}, MLB/AAA/AA PA {s['pa_0']}/{s['AAA_0_pa']}/{s['AA_0_pa']}" for s in peers.iter_rows(named=True))+'.',''])
    lines.extend(['## Interpretation','','The raw ten-bin shape records use coordinate-based direction and scorer/trajectory labels. Cross-level measurement equivalence is not assumed; distinct buckets, measured PA fractions and exposure are supplied. The new forecast test—not this audit—will decide transfer utility. Pre-2016 minor and pre-2021 MLB shape remain unobserved. Rows/buckets with no relevant active-player training support get exact baseline fallbacks.'])
    walk=e.OUT/'source-walkthrough.md';walk.write_text('\n'.join(lines)+'\n',encoding='utf8')
    e.write('source-review.json',dict(source_walkthrough_status='complete',cases=len(cases),source_preflight_sha256=sha256_file(p),walkthrough_sha256=sha256_file(walk),
        excluded_contact_counts_reviewed=True,protected_outcomes_used=False,no_prediction_certification=True))
    print('8 fixed source reviews complete; no fit or predictive disposition.',flush=True)


if __name__=='__main__':main()
