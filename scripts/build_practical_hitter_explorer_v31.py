"""Historical, team-filtered research view; never rewrites the frozen forecast."""
import gzip
import json
from pathlib import Path
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file


def team_map():
    mapping={};hashes={}
    for year in r.YEARS:
        paths=[r.OLD/f'affiliated-team-context/captures/teams-{year}-sport-{sport}.json' for sport in [1,11,12,13,14,15,16]]
        paths += [r.OLD/f'opportunity-history-sources-pre2020/captures/{year}/teams.json.gz',r.OLD/f'opportunity-history-sources-v2/captures/{year}/teams.json.gz',
            r.ROOT/f'model_artifacts/advanced-rookie-repair-v3/raw/{year}/teams.json.gz',r.ROOT/f'model_artifacts/shortseason-hitting-source-v1/raw/{year}/teams.json.gz']
        for path in paths:
            if not path.exists():continue
            hashes[str(path)]=sha256_file(path)
            data=json.load(gzip.open(path,'rt',encoding='utf8')) if path.suffix=='.gz' else json.loads(path.read_text(encoding='utf8'))
            data=data.get('payload',data)
            for t in data['teams']:
                assert int(t['season'])==year
                mlb=t['sport']['id']==1
                mapping[(year,t['id'])]=dict(club=t['name'],org=t['name'] if mlb else t.get('parentOrgName') or 'Unknown affiliation')
    return mapping,hashes


def main():
    report=r.read(r.OUT/'score-report.json');assert report['player_walkthrough_status']=='complete'
    f=pl.read_parquet(r.OUT/'scored-predictions.parquet');mapping,hashes=team_map();support=pl.read_parquet(r.OUT/'conditional-head-support.parquet')
    supportmap={}
    for s in support.iter_rows(named=True):supportmap.setdefault(s['row_id'],{})[s['head']]=s['conditional_profile_players']
    rows=[]
    for s in f.iter_rows(named=True):
        t=mapping.get((s['origin_year'],s['team_id']),dict(club='Unknown club',org='Unknown affiliation'))
        a={k:s[k] for k in ['row_id','player_id','player_name','origin_year','target_year','age','stage','source_position','on_40man','pa_0','pa_1','pa_2','quality_0',
            'DSL_0_pa','AAA_0_pa','AA_0_pa','career_mlb_observed_pa','career_mlb_left_truncated','age_unknown','last_stat_gap','next_pa','next_value',
            'v24_pa','v24_value','steamer_pa','steamer_value','legacy_n_pa','legacy_n_value','hard_unavailable','needs_availability_scenario']}
        a.update(t);a['support']=supportmap[s['row_id']]
        for arm in ['base_hurdle','detail_hurdle','direct_detail']:
            a[arm]=dict(pa=s[arm+'_pa'],value=s[arm+'_value'])
            if arm.endswith('hurdle'):a[arm].update(p=[s[arm+f'_p{i}'] for i in range(4)],conditional_pa=[s[arm+f'_conditional_pa{i}'] for i in [1,2,3]],conditional_value=[s[arm+f'_conditional_value{i}'] for i in [1,2,3]])
        # Only contribution-weighted histogram rate is shown as a diagnostic;
        # invalid unbounded linear outputs are not exposed as usable ratings.
        a['contribution_rate']=s['rate_hist_pa_rate'];rows.append(a)
    counts=pl.read_parquet(r.OUT/'counts.parquet');history={}
    for s in counts.select('season','player_id','bucket','plate_appearances','strike_outs','unintentional_walks','home_runs','doubles','triples','babip_hits','babip_opportunities').iter_rows(named=True):
        pid=s.pop('player_id');history.setdefault(str(pid),[]).append(s)
    dest=r.OUT/'explorer';dest.mkdir(exist_ok=True)
    for name,obj in [('data.json',rows),('history.json',history),('scores.json',report['scores'])]:
        (dest/name).write_text(json.dumps(obj,allow_nan=False,separators=(',',':')),encoding='utf8')
    template=r.ROOT/'src/universal_baseball/templates/practical_hitter_explorer_v31.html'
    (dest/'index.html').write_text(template.read_text(encoding='utf8'),encoding='utf8')
    r.write('explorer-report.json',dict(rows=len(rows),target_years=sorted(f['target_year'].unique()),
        affiliation_unknown=sum(a['org']=='Unknown affiliation' for a in rows),
        source_hashes=hashes,template_sha256=sha256_file(template),protected_2026_unchanged=True,
        description='Historical research forecasts with actual next-year outcomes, not a new 2026 production forecast. Organization from same-origin captured listing/club, not future team.'))
    print(f'Built separate historical explorer: {dest}; {len(rows)} forecasts.')


if __name__=='__main__':main()
