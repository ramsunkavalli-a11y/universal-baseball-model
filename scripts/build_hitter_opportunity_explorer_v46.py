"""Reuse the reviewed local UI for working versus games versus timing research."""
import json
import polars as pl
import evaluate_hitter_late_role_v46 as e
from build_practical_hitter_explorer_v31 import team_map
from universal_baseball.storage import sha256_file


def main():
    assert e.r.read(e.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert e.r.read(e.r.OUT/'report.json')['player_walkthrough_status']=='complete'
    f=pl.read_parquet(e.OUT/'predictions.parquet');assert len(f)==30506 and f['origin_year'].max()==2024 and f['target_year'].max()==2025
    windows=pl.read_parquet(e.OUT/'windows.parquet');window_lookup={}
    for w in windows.iter_rows(named=True):window_lookup.setdefault(w['player_id'],[]).append(w)
    mapping,hashes=team_map();rows=[]
    fields=['row_id','player_id','player_name','origin_year','target_year','age','stage','source_position','next_pa','next_value','origin_replacement_rate','draft_known','draft_year','pick_number','reported_retired','origin_evidence_bridge']
    for o in f.iter_rows(named=True):
        a={k:o[k] for k in fields};a.update(mapping.get((o['origin_year'],o['team_id']),dict(club='Unknown club',org='Unknown affiliation')))
        a['next_batting_rate']=o['next_batting_rate'] if o['next_pa']>0 else None
        for arm,prefix,rate in [('safe_ridge','retired_safe_ridge','safe_ridge_rate'),('games','retired_games','cohort_rate'),('late','late','late_rate')]:a[arm]=dict(pa=o[prefix+'_pa'],rate=o[rate],value=o[prefix+'_value'])
        a['windows']=[w for w in window_lookup.get(o['player_id'],[]) if o['origin_year']-1<=w['season']<=o['origin_year']];rows.append(a)
    history={}
    for h in pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet').select('season','player_id','bucket','plate_appearances','strike_outs','unintentional_walks','home_runs','doubles','triples').iter_rows(named=True):
        pid=h.pop('player_id');history.setdefault(str(pid),[]).append(h)
    public=next(s for s in e.r.read(e.OUT/'scores.json') if s['scope']=='public_active')['scores'];scores={k:public[p] for k,p in [('safe_ridge','retired_safe_ridge'),('games','retired_games'),('late','late'),('steamer','steamer')]}
    reviews=e.r.read(e.ROOT/'config/practical_hitter_late_role_v46_case_notes.json')
    template=e.ROOT/'src/universal_baseball/templates/practical_hitter_batch.html';html=template.read_text(encoding='utf8')
    replacements={
      'Hitter research — best forecast and completed comparisons':'Hitter opportunity research and actual results',
      'Hitter research: the best forecast and what we tested':'Hitter projections and actual results',
      'The working forecast is still <strong>the count-and-draft baseline</strong>. Game involvement is a promising playing-time extension; the contact challengers did not improve the complete forecast. This is a research comparison, not a replacement for the frozen 2026 forecast.':'The working forecast is the <strong>count-and-draft baseline with a dated, reversible retirement rule</strong>. Compare it with the games and late-season-PA research candidates. Timing helps a little overall but does not solve the public playing-time or prospect-readiness gaps. No frozen or deployed 2026 forecast is changed.',
      "const names={safe_ridge:'Working: count + draft baseline',cohort:'Source-corrected comparison',games:'Games / involvement — research',contact_ridge:'Contact + linear batting — not adopted',contact_hist:'Contact + tree batting — not adopted'};":"const names={safe_ridge:'Working: count + draft + retirement',games:'Games / involvement — research',late:'Late-season PA timing — research'};",
      'The games challenger adds actual games played and PA per game. Those show use, not diagnosed health or guaranteed future jobs. The contact challengers add ground/line/fly/pop-up direction profiles with exposure and source flags; these are not fully park-neutralized or tracking-based quality measurements. Uncorroborated PBP rows are excluded from those inputs, not from the player population.':'The games challenger adds annual appearances and stabilized PA per game. The timing candidate adds reliable PA from the final and preceding thirty-day windows in two source years. Window games/PA-per-appearance inputs were withheld because their definitions do not reconcile consistently. Usage is not starts, diagnosed health or a guaranteed future job. All three forecasts apply the same reversible reported-retirement and permanent-status policies.',
      'Listed position is not defensive innings. The old roster listing is incomplete. Contact before 2016 in the minors and before 2021 in MLB is unobserved in these added sources. A missed season is not recorded as bad production. General defense and career/trade value are not in these totals.':'Listed position is not defensive innings. Historical roster-only eligibility can be unverified. The timing windows cover MLB only, not late minor-league promotions or starting jobs. A missed season is not bad hitting; retirement changes opportunity, not ability. General defense and career/trade value are not included.'
    }
    for old,new in replacements.items():assert html.count(old)==1,old;html=html.replace(old,new)
    marker="const review=reviews[r.player_id+'|'+r.origin_year];"
    insertion="""html+='<p class=\"warn\">'+(r.reported_retired?'Cutoff-known reported retirement: expected opportunity is zero while this state remains unreversed. Hitting ability is unchanged. ':'')+(!r.origin_evidence_bridge?'Roster-only eligibility is unverified: no own prior batting, known debut or eligible draft bridge. Not proof the player was invalid or had zero talent.':'')+'</p>';
html+='<h3>Verified MLB usage timing</h3><p>Final and preceding thirty-day windows ending at the last official regular-season game, not a future role assumption.</p><div class=\"scroll\"><table><thead><tr><th>Year</th><th>Annual PA</th><th>Preceding PA</th><th>Late PA</th><th>Preceding avg. team games</th><th>Late avg. team games</th></tr></thead><tbody>'+r.windows.map(w=>'<tr>'+[w.season,n(w.annual_pa),n(w.preceding_pa),n(w.late_pa),n(w.preceding_team_games,2),n(w.late_team_games,2)].map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
if(!r.windows.length)html+='<p>No observed MLB PA in these complete captures. Minor-league counts remain below; this does not imply zero talent.</p>';
"""
    assert html.count(marker)==1;html=html.replace(marker,insertion+marker)
    dest=e.OUT/'explorer';dest.mkdir(parents=True,exist_ok=True)
    for n,o in [('data.json',rows),('history.json',history),('scores.json',scores),('reviews.json',reviews)]:
        (dest/n).write_text(json.dumps(o,allow_nan=False,separators=(',',':')),encoding='utf8')
    (dest/'index.html').write_text(html,encoding='utf8')
    paths=[e.OUT/'predictions.parquet',e.OUT/'report.json',e.OUT/'windows.parquet',e.r.OUT/'report.json',template,e.ROOT/'config/practical_hitter_late_role_v46_case_notes.json']
    hashes.update({str(p):sha256_file(p) for p in paths})
    e.write('explorer-report.json',dict(rows=len(rows),default_model='safe_ridge',historical_only=True,target_maximum=2025,team_filter=True,models_have_completed_walkthroughs=True,source_hashes=hashes,frozen_forecast_changed=False,old_explorer_changed=False,source_timing_visible=True))
    print(dest,flush=True)


if __name__=='__main__':main()
