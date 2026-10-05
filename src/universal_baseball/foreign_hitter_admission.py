"""Batting-input admission uses dated role evidence, never future performance."""
from collections import defaultdict

COUNTS=['plate_appearances','at_bats','hits','doubles','triples','home_runs',
    'base_on_balls','intentional_walks','hit_by_pitch','strike_outs','sac_bunts','sac_flies']


def materialize(foreign_inputs,population,stints):
    pop={r['candidate_key']:r for r in population}
    if len(pop)!=len(population):raise ValueError('Duplicate source population')
    domestic=defaultdict(list)
    for s in stints:domestic[s['player_id']].append(s)
    seen=set();rows=[]
    for f in foreign_inputs:
        key=f['candidate_key']
        if key in seen:raise ValueError('Duplicate foreign source')
        seen.add(key);p=pop[key]
        if (f['player_id'],f['origin_year'],f['information_date'])!=(p['player_id'],p['origin_year'],p['information_date']):
            raise ValueError('Mismatched source cutoff or identity')
        if f['original_source_origin']!=p['current_model_origin']:raise ValueError('Changed original membership')
        if p['current_model_origin']:continue
        hint=f['dated_role_hint'];mixed=hint in {'two_way_hint','two_way_or_conflicting_hints'}
        eligible=hint=='hitter_hint' or mixed
        prior=sorted([dict(s) for s in domestic[f['player_id']] if s['season']<=f['origin_year']],
            key=lambda s:(s['season'],s['sport_id'],s['team_id']))
        history=[]
        for lag in range(3):
            year=f['origin_year']-lag;group=defaultdict(list)
            for s in prior:
                if s['season']==year:group[s['bucket']].append(s)
            history.append(dict(season=year,milb_season_canceled=year==2020,levels={level:dict(
                counts={c:sum(s[c] for s in part) for c in COUNTS},stint_rows=len(part),
                reported_positions=sorted({s['position'] for s in part}),observed=True)
                for level,part in sorted(group.items())},absent_level_is_unknown_not_zero_talent=True))
        domestic_pa=sum(s['plate_appearances'] for s in prior if s['season']>=f['origin_year']-2)
        mlb_pa=sum(s['plate_appearances'] for s in prior if s['season']>=f['origin_year']-2 and s['sport_id']==1)
        if (domestic_pa,mlb_pa)!=(f['recent_observed_domestic_pa'],f['recent_observed_MLB_pa']):
            raise ValueError('Foreign/domestic source histories disagree')
        rows.append(dict(candidate_key=key,player_id=f['player_id'],player_name=p['player_name'],origin_year=f['origin_year'],
            information_date=f['information_date'],dated_role_hint=hint,qualified_for_batting_input=eligible,
            mixed_role_uncertain=mixed,ordinary_fulltime_hitter_role_certified=False,
            disposition='qualified_batting_with_mixed_role_flag' if mixed else 'qualified_batting' if eligible else
                'pitcher_only_not_hitter_admission' if hint=='pitcher_hint' else 'unresolved_role',
            actual_prior_domestic_stints=prior,three_year_domestic_history=history,
            recent_observed_domestic_pa=domestic_pa,recent_observed_mlb_pa=mlb_pa,
            career_observed_mlb_pa=sum(s['plate_appearances'] for s in prior if s['sport_id']==1),
            recent_foreign_pa=f['recent_foreign_pa'],domestic_source_before_2008_unknown=True,
            current_employment_guaranteed=False,new_forecast=None))
    return rows
