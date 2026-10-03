"""Complete the source-player review before using the new training population."""
import json
import polars as pl
import materialize_hitter_2020_cohort as m
from universal_baseball.storage import sha256_file

NOTES={
592450:'Judge retains actual 114/447/498 MLB PA and strong pooled batting evidence. The repaired roster membership is present rather than an invented nonlisting. A canceled season is not an exit. His 633 PA next year are an observed training outcome, not an input or a hand-adjusted forecast.',
665487:'Tatis retains 257 actual short-season PA, not an invented 694 full-season batting sample. Only the workload variable is schedule normalized. Captured membership becomes present and 546 next-year PA remain the same target. This is source repair, not a finite-suspension repair for the later 2022 cutoff.',
666158:'Lux retains 523 upper-minor PA/26 HR from 2019 despite no 2020 MiLB games, alongside his small 2020 MLB sample. The source repair restores listing evidence without declaring health or a regular job. Actual 381 future PA are not used to choose him or override his weak MLB batting sample.',
663697:'India was absent from the old selected 2020 subset. His 2019 AA/A+ 512 PA, 11 HR and 110 K remain known, at age 23, with a dated pick 5. A canceled season does not turn him into a zero-talent inactive player. The last observed upper-minor classification is explicitly carried, and listing zero is now an observed soft nonlisting. His later 631 MLB PA are a genuine advancing-player training example, not future backfill.',
679529:'Torkelson is identified by the historical 2020 hitter roster, not by his later MLB arrival. Zero professional competition is preserved as no observations. Birth year gives age 21 and the existing dated capture gives pick 1/college entry. The historical roster position is third base; current embedded draft-person primary position is deliberately unused. No MLB PA in 2021 is an important counterexample to assuming every elite college pick immediately arrives.',
677008:'Kjerstad is another historical roster-only, age-21 drafted hitter with no professional sample. His pick 2 is known, but health and opportunity are not inferred from a full-roster listing. Actual zero next-year MLB PA remains. He is included because of origin-known position/listing, not chosen to hide later failure or claim draft investment guarantees MLB participation.'}


def main():
    out=m.OUT;report=m.r.read(out/'source-report.json')
    assert not (out/'source-review.json').exists()
    for p,h in report['input_hashes'].items():assert sha256_file(m.Path(p))==h,p
    f=pl.read_parquet(out/'origin-2020.parquet');old=pl.read_parquet(m.BASE/'features.parquet').filter(pl.col('origin_year')==2020)
    raw=pl.read_parquet(m.r.OUT/'counts.parquet');provenance=pl.read_parquet(out/'provenance.parquet')
    outside=pl.read_parquet(out/'outside-2021.parquet')
    dated=pl.read_parquet(m.r.OUT/'dated-stints.parquet').filter(pl.col('season')==2021)
    primary=dated.sort(['player_id','plate_appearances'],descending=[False,True]).unique('player_id',keep='first')
    outside=outside.join(primary.select('player_id','player_name','position'),on='player_id',how='left',validate='1:1')
    assert outside['position'].null_count()==0
    outside.write_parquet(out/'outside-2021-classified.parquet')
    outside_groups=outside.group_by('position').agg(pl.len().alias('people'),pl.col('mlb_pa').sum().alias('pa'),pl.col('component_war').sum().alias('value')).to_dicts()
    lines=['# Canceled season source review','',
        f"The origin population is rebuilt from {report['old_subset_rows']} to {len(f)} observable hitters. All non-2020 inputs and all 30,506 evaluation targets remain unchanged. No model has been refitted by this source review.",'',
        'The historical requests cover all 30 MLB teams. Full-roster row positions define newly observed hitters; current person primary-position, active status and age are not used. Missing ages use immutable birth dates, not present-day ages. Canceled MiLB competition creates no event observations. Listings are soft historical source membership, not certified rights or health.','',
        'Outside-cohort 2021 PA by actual source position (diagnostic only, never eligibility): '+json.dumps(outside_groups)+'.','']
    cases=[]
    for pid,note in NOTES.items():
        o=f.filter(pl.col('player_id')==pid).to_dicts()[0];past=old.filter(pl.col('player_id')==pid).to_dicts()
        h=raw.filter((pl.col('player_id')==pid)&pl.col('season').is_between(2018,2020)).sort('season','bucket').to_dicts()
        candidates=f.filter((pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=pid))
        peers=candidates.with_columns((
            ((pl.col('age')-o['age'])/5)**2+((pl.col('pa_0')-o['pa_0'])/300)**2+
            ((pl.col('minor_pa_1')-o['minor_pa_1'])/600)**2+
            (pl.col('draft_known')-o['draft_known'])**2+
            (pl.col('draft_rank')-o['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(3)
        prov=provenance.filter(pl.col('player_id')==pid).to_dicts()[0]
        fields=['player_name','age','age_unknown','stage','snapshot_level','source_position','on_40man','pa_0','pa_1','pa_2','work_0',
            'pooled_mlb_quality','career_mlb_observed_pa','draft_known','pick_number','draft_school_class','next_pa','next_value']
        lines.extend([f"## {o['player_name']}",'',note,'',
            'Old source: '+(json.dumps({k:past[0][k] for k in fields}) if past else 'Not represented in the old 2020 subset')+'.','',
            'Actual rebuilt inputs and targets: '+json.dumps({k:o[k] for k in fields})+'.','',
            'Provenance: '+json.dumps(prov)+'.','',
            '| Year | League | PA | HR | K | UBB |','|---|---|---:|---:|---:|---:|'])
        for c in h:lines.append(f"| {c['season']} | {c['bucket']} | {c['plate_appearances']} | {c['home_runs']} | {c['strike_outs']} | {c['unintentional_walks']} |")
        if not h:lines.append('| — | No professional observations | 0 | 0 | 0 | 0 |')
        lines.extend(['','Peers selected by origin age, stage, debut, workload and draft context, without future outcomes: '+
            '; '.join(f"{p['player_name']} (age {p['age']:g}, prior minor PA {p['minor_pa_1']}; actual 2021 {p['next_pa']} PA/{p['next_value']:.2f})" for p in peers.to_dicts())+'.',''])
        cases.append(dict(player_id=pid,origin_year=2020,selection='Fixed source diagnostic before model fits',inputs={k:o[k] for k in fields},
            old_inputs={k:past[0][k] for k in fields} if past else None,provenance=prov,raw_history=h,
            origin_selected_peers=peers.select('player_id','player_name','age','stage','minor_pa_1','draft_known','pick_number','next_pa','next_value','distance').to_dicts(),judgment=note))
    lines.extend(['## Source decision','',
        'Retain this reconstructed observable population as a candidate historical source. Six source walkthroughs are complete; this is not a predictive improvement or completed hitter model. International entrants never observed on a historical listing remain a coverage gap. The outside-position inventory separates pitcher batting from genuine missed hitter identities. Before fitting, lock the source-extension comparison and support audit, with no new library/settings search.'])
    path=out/'source-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    review=dict(player_walkthrough_status='complete',cases=cases,source_integrity_pass=True,
        numerical_forecast_gain_tested=False,outside_position_groups=outside_groups,source_walkthrough_sha256=sha256_file(path))
    (out/'source-review.json').write_text(json.dumps(review,indent=2),encoding='utf8')
    print('Six source-player walkthroughs complete; outside positions:',outside_groups)


if __name__=='__main__':main()
