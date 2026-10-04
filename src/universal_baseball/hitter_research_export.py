"""Historical assembly semantics; never select a branch from a future outcome."""
import math

ARMS = {
    'combined': 'Reviewed prospect and MLB branches',
    'preseason': 'Previous current forecast',
    'precision_coverage': 'Minor exposure comparison — not adopted',
    'precision_measurements': 'Minor measurements comparison — not adopted',
}


def branch(record):
    if not record['prior_debut']:
        return 'Translated prospect Ridge'
    if record['sc_tracked']:
        return 'MLB Statcast Ridge'
    return 'Current rate fallback'


def export_row(r, context, support, information_date, reviewed):
    known = context['context_reason'] == 'known' and context['context_parent'] is not None
    flags = []
    for name, key in [('Appearance', 'participation'), ('Active workload', 'conditional_pa')]:
        if support[key] < 20:
            flags.append(f'{name} profile has fewer than 20 earlier distinct players; this is a warning, not certification.')
    if not known:
        flags.append('Origin organization unresolved; no future affiliation substituted.')
    if not r['prior_debut']:
        flags.append('Next-year non-arrival does not measure eventual MLB or career talent.')
    if not r['sc_tracked']:
        flags.append('No recent own MLB launch measurements; unknown is not a talent penalty.')
    if r['msc_eligible'] and r['minimum_profile_people'] < 20:
        flags.append('Minor measurement comparison has thin league/sample profile support.')
    if not r['origin_evidence_bridge']:
        flags.append('Roster eligibility has no own-history/debut/draft evidence bridge.')
    if r['needs_availability_scenario']:
        flags.append('Exceptional availability requires a separate scenario.')
    if r['hard_unavailable'] or r['reported_retired']:
        flags.append('A cutoff-known permanent-status or reported-retirement rule affects opportunity.')
    result = dict(row_id=r['row_id'], player_id=r['player_id'], player_name=r['player_name'],
        origin_year=r['origin_year'], target_year=r['target_year'], fold=r['outer_fold'],
        cell=f"{r['origin_year']}-{r['outer_fold']}", age=r['age'], position=r['source_position'],
        stage=r['stage'], branch=branch(r), org=context['context_parent'] if known else 'Unknown affiliation',
        club=context['context_club'], team_basis=context['context_basis'], team_reason=context['context_reason'],
        club_year=context['context_club_year'], rights_date=context['context_rights_date'],
        information_date=information_date, pa=r['preseason_pa'], p=r['preseason_p'],
        conditional_pa=r['preseason_conditional_pa'], raw_p=r['preseason_raw_p'],
        raw_conditional_pa=r['preseason_raw_conditional_pa'], replacement_rate=r['origin_replacement_rate'],
        next_pa=r['next_pa'], next_value=r['next_value'],
        next_rate=r['actual_future_relative_rate'] if r['next_pa'] > 0 else None,
        rates={a:r[a+'_rate'] for a in ARMS}, values={a:r[a+'_value'] for a in ARMS},
        public_match=bool(r['pa_0'] > 0 and r['steamer_index'] is not None and r['zips_index'] is not None),
        steamer_pa=r['steamer_pa'] if r['steamer_index'] is not None else None,
        steamer_value=r['steamer_value'] if r['steamer_index'] is not None else None,
        mlb_ev_n=r['sc_own_ev_n'], minor_ev_n=r['msc_own_ev_n'], minor_comparison_enabled=r['msc_eligible'],
        participation_people=support['participation'], workload_people=support['conditional_pa'],
        minor_profile_people=r['minimum_profile_people'] if r['msc_eligible'] else None,
        scout_listed=bool(r['scout_listed_0']), scout_rank_score=r['scout_rank_score_0'],
        draft_known=bool(r['draft_known']), pick_number=r['pick_number'], draft_year=r['draft_year'],
        reviewed=r['row_id'] in reviewed, flags=flags)
    assert math.isclose(result['pa'], result['p'] * result['conditional_pa'], abs_tol=1e-10)
    for a in ARMS:
        assert math.isclose(result['values'][a], result['pa'] * (result['rates'][a]/600 + result['replacement_rate']), abs_tol=1e-10)
    return result
