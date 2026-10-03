"""Historical team-filtered explorer with explicit participation and conditional PA."""
import json
import polars as pl
from build_practical_hitter_explorer_v31 import team_map
from universal_baseball.storage import sha256_file
import evaluate_hitter_readiness_v49 as e


def main():
    report=e.old.r.read(e.OUT/'report.json');assert report['player_walkthrough_status']=='complete'
    f=pl.read_parquet(e.OUT/'predictions.parquet');assert len(f)==30506 and f['target_year'].max()==2025
    profile={x['row_id']:x['conditional_rank_profile_players'] for x in pl.read_parquet(e.OUT/'conditional-profile.parquet').iter_rows(named=True)}
    mapping,hashes=team_map();rows=[]
    fields=['row_id','player_id','player_name','origin_year','target_year','age','stage','snapshot_level','source_position','next_pa','next_value','origin_replacement_rate','draft_known','draft_year','pick_number','reported_retired','origin_evidence_bridge','scout_listed_0','scout_rank_score_0']
    for o in f.iter_rows(named=True):
        a={k:o[k] for k in fields};a.update(mapping.get((o['origin_year'],o['team_id']),dict(club='Unknown club',org='Unknown affiliation')))
        a['next_batting_rate']=o['next_batting_rate'] if o['next_pa']>0 else None;a['conditional_profile_players']=profile[o['row_id']]
        for arm,prefix,rate in [('safe_ridge','retired_safe_ridge','safe_ridge_rate'),('games','retired_games','cohort_rate'),('fallback','fallback','cohort_rate'),('binary_count','binary_count','cohort_rate'),('binary_scout','binary_scout','cohort_rate')]:
            a[arm]=dict(pa=o[prefix+'_pa'],rate=o[rate],value=o[prefix+'_value'],p=o[prefix+'_p'] if arm.startswith('binary') else None,conditional_pa=o[prefix+'_conditional_pa'] if arm.startswith('binary') else None)
        rows.append(a)
    history={}
    for h in pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet').select('season','player_id','bucket','plate_appearances','strike_outs','unintentional_walks','home_runs','doubles','triples').iter_rows(named=True):
        pid=h.pop('player_id');history.setdefault(str(pid),[]).append(h)
    public=next(s for s in e.old.r.read(e.OUT/'scores.json') if s['scope']=='public_active')['scores']
    scores={k:public[p] for k,p in [('safe_ridge','retired_safe_ridge'),('games','retired_games'),('fallback','fallback'),('binary_count','binary_count'),('binary_scout','binary_scout'),('steamer','steamer')]}
    reviews=e.old.r.read(e.ROOT/'config/practical_hitter_readiness_v49_case_notes.json')
    template=e.ROOT/'src/universal_baseball/templates/practical_hitter_batch.html';html=template.read_text(encoding='utf8')
    replacements={
      'Hitter research — best forecast and completed comparisons':'Hitter readiness and actual MLB results',
      'Hitter research: the best forecast and what we tested':'Hitting forecasts, MLB readiness and actual results',
      'The working forecast is still <strong>the count-and-draft baseline</strong>. Game involvement is a promising playing-time extension; the contact challengers did not improve the complete forecast. This is a research comparison, not a replacement for the frozen 2026 forecast.':'The working forecast remains the <strong>count-and-draft baseline with reversible retirement</strong>. The new research comparisons separate the chance of MLB participation from playing time if active, with and without historical scouting rankings. They are reviewed experiments, not a replacement for the protected 2026 forecast. Select a forecast below to inspect the tradeoffs.',
      "const names={safe_ridge:'Working: count + draft baseline',cohort:'Source-corrected comparison',games:'Games / involvement — research',contact_ridge:'Contact + linear batting — not adopted',contact_hist:'Contact + tree batting — not adopted'};":"const names={safe_ridge:'Working: count + draft + retirement',games:'Direct count + games — research',fallback:'Positive scouting + count fallback — research',binary_count:'MLB chance × PA if active — counts research',binary_scout:'MLB chance × PA if active — scouting research'};",
      'The games challenger adds actual games played and PA per game. Those show use, not diagnosed health or guaranteed future jobs. The contact challengers add ground/line/fly/pop-up direction profiles with exposure and source flags; these are not fully park-neutralized or tracking-based quality measurements. Uncorroborated PBP rows are excluded from those inputs, not from the player population.':'Games and PA per appearance measure historical use, not diagnosed health or guaranteed jobs. The scouting source uses historical preseason ranks only; current biographies, grades and estimated-arrival fields are withheld. A high rank is prospect quality, not guaranteed immediate MLB readiness. Binary research estimates any next-year MLB appearance probability, then PA conditional on that appearance; multiplying them gives expected PA without assuming independence.',
      'Listed position is not defensive innings. The old roster listing is incomplete. Contact before 2016 in the minors and before 2021 in MLB is unobserved in these added sources. A missed season is not recorded as bad production. General defense and career/trade value are not in these totals.':'Listed position is not defensive innings. Some retrospective roster-only membership is unverified. Source rankings are qualified historical reproductions; partial-list absence remains unknown. A missed season is not bad hitting. General defense and career/trade value are not in these totals.',
      '<th class="n">Actual PA</th><th class="n">Batting / 600*</th>':'<th class="n">Actual PA</th><th class="n">MLB chance*</th><th class="n">PA if active*</th><th class="n">Batting / 600*</th>',
      '[n(r[m].pa),n(r.next_pa),n(r[m].rate,2)':'[n(r[m].pa),n(r.next_pa),r[m].p==null?"—":n(100*r[m].p,1)+"%",n(r[m].conditional_pa,1),n(r[m].rate,2)',
      '<p class="muted">*Batting rate is a forecast learned from future MLB participants, weighted by playing time.':'<p class="muted">*MLB chance and PA if active are available only for the two binary research models, not inferred from the direct means. Batting rate is a forecast learned from future MLB participants, weighted by playing time.'
    }
    for old,new in replacements.items():assert html.count(old)==1,old;html=html.replace(old,new)
    marker="const review=reviews[r.player_id+'|'+r.origin_year];"
    insert="""html+='<p><strong>Historical scouting evidence:</strong> '+(r.scout_listed_0===1?'rank '+n(101-100*r.scout_rank_score_0)+' in the '+r.origin_year+' preseason table':r.scout_listed_0===0?'not listed in the complete preseason table; not a zero talent grade':'unknown listing because coverage is missing or partial')+'. Snapshot level: '+esc(r.snapshot_level)+'.</p>';
if(m.startsWith('binary'))html+='<p><strong>Readiness calculation:</strong> '+n(100*a.p,2)+'% chance of any next-year MLB PA × '+n(a.conditional_pa,2)+' PA if active = '+n(a.pa,2)+' expected PA. No appearance means zero delivered value, not zero career talent.</p><p class="warn">Distinct earlier active-label training players in the same coarse stage/debut/age/rank profile: '+n(r.conditional_profile_players)+(r.conditional_profile_players<20?' — sparse. This is a warning, not calibrated confidence.':' — not proof of exact-player support.')+'</p>';
html+='<p class="warn">'+(r.reported_retired?'Cutoff-known reported retirement changes opportunity, not ability. ':'')+(!r.origin_evidence_bridge?'Roster-only eligibility is unverified; no own-history/debut/draft bridge.':'')+'</p>';
"""
    assert html.count(marker)==1;html=html.replace(marker,insert+marker)
    html=html.replace('This product is an approximation, not a full joint outcome distribution.','The two binary models condition workload on participation; the displayed batting-rate product still does not supply a full joint career/value distribution.')
    dest=e.OUT/'explorer';dest.mkdir(parents=True,exist_ok=True)
    for n,o in [('data.json',rows),('history.json',history),('scores.json',scores),('reviews.json',reviews)]:
        (dest/n).write_text(json.dumps(o,allow_nan=False,separators=(',',':')),encoding='utf8')
    (dest/'index.html').write_text(html,encoding='utf8')
    paths=[e.OUT/'predictions.parquet',e.OUT/'report.json',e.OUT/'conditional-profile.parquet',template,e.ROOT/'config/practical_hitter_readiness_v49_case_notes.json']
    hashes.update({str(p):sha256_file(p) for p in paths})
    e.write('explorer-report.json',dict(rows=len(rows),default_model='safe_ridge',historical_only=True,target_maximum=2025,team_filter=True,all_compared_models_reviewed=True,
        explicit_probability_and_conditional_pa=True,source_hashes=hashes,frozen_forecast_changed=False,old_explorer_changed=False))
    print(dest,flush=True)


if __name__=='__main__':main()
