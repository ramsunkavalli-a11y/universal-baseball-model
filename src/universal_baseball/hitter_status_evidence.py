"""Separate ordered organization evidence, literal reserve listing and absence."""
from collections import defaultdict
from datetime import date

from .hitter_preseason_population import available_date, transaction_key
from .availability_context_v29 import as_of, il_episodes

POSITIVE = {'minor_agreement', 'agreement_unspecified', 'acquisition', 'major_activation'}


def employment_kind(raw, teams):
    text = (raw.get('description') or '').lower()
    kind = (raw.get('typeDesc') or '').lower()
    code = raw.get('typeCode')
    target = (raw.get('toTeam') or {}).get('id')
    source = (raw.get('fromTeam') or {}).get('id')
    if target not in teams and source not in teams:
        return None
    if 'rehab assignment' in text or 'all-stars' in text or 'all stars' in text:
        return None
    if kind in {'released', 'declared free agency', 'free agency'} or 'elected free agency' in text or ' released ' in text:
        return 'release'
    if code == 'RET':
        return 'retirement'
    if code in {'OUT', 'DES'} or 'outrighted' in text or 'designated' in text and 'assignment' in text:
        return 'reserve_departure'
    if target in teams and ('minor league contract' in text or 'minor-league contract' in text):
        return 'minor_agreement'
    if target in teams and (code == 'SFA' or kind == 'signed as free agent' or 'signed ' in text):
        return 'agreement_unspecified'
    if target in teams and (code in {'CU', 'SE'} or 'selected the contract' in text or 'selected contract' in text or ' activated ' in text or 'reinstated' in text):
        return 'major_activation'
    if target in teams and (code in {'TR', 'CLW', 'R5', 'PUR', 'CP'} or kind in {'trade', 'claimed off waivers', 'selected off waivers', 'rule 5 draft', 'purchased'}):
        return 'acquisition'
    return None


def employment_events(raw_events, teams, cutoff):
    unique = {}
    for raw in raw_events:
        known = available_date(raw)
        if known is None or date.fromisoformat(known) > cutoff:
            continue
        kind = employment_kind(raw, teams)
        if kind is None:
            continue
        key = transaction_key(raw)
        if key in unique and unique[key]['raw'] != raw:
            raise ValueError('Conflicting transaction version')
        target = (raw.get('toTeam') or {}).get('id')
        source = (raw.get('fromTeam') or {}).get('id')
        # Releases often report the departing club as toTeam, not fromTeam.
        team = target if target in teams else source
        unique[key] = dict(known_date=known, kind=kind, team_id=team, raw=raw)
    return sorted(unique.values(), key=lambda x: (x['known_date'], str(transaction_key(x['raw']))))


def organization_state(events):
    groups = defaultdict(list)
    for e in events:
        groups[e['known_date']].append(e)
    state = 'unknown'; team = None; explicit_major = False; latest = None; conflict = False
    trace = []
    for day, group in sorted(groups.items()):
        positives = [e for e in group if e['kind'] in POSITIVE]
        positive_teams = {e['team_id'] for e in positives}
        negatives = [e for e in group if e['kind'] in {'release', 'retirement'}]
        reserve_exits = [e for e in group if e['kind'] == 'reserve_departure']
        if positives:
            incompatible = len(positive_teams) != 1 or any(e['team_id'] in positive_teams for e in negatives+reserve_exits)
            if incompatible:
                state = 'ambiguous_same_date'; team = None; explicit_major = False; conflict = True
            else:
                team = next(iter(positive_teams)); conflict = False
                kinds = {e['kind'] for e in positives}
                state = ('major_activation' if 'major_activation' in kinds else 'minor_agreement' if 'minor_agreement' in kinds
                    else 'agreement_unspecified' if 'agreement_unspecified' in kinds else 'acquisition')
                # A same-club organizational action doesn't erase an already established major link.
                explicit_major = state == 'major_activation' or (explicit_major and trace and trace[-1]['team_id'] == team)
        elif negatives:
            affected = [e for e in negatives if team is None or e['team_id'] == team]
            if affected:
                state = 'reported_retirement' if any(e['kind'] == 'retirement' for e in affected) else 'reported_release'
                team = None; explicit_major = False; conflict = False
        elif reserve_exits and (team is None or any(e['team_id'] == team for e in reserve_exits)):
            state = 'reserve_departure_organization_unconfirmed'; explicit_major = False
            if team is None and len({e['team_id'] for e in reserve_exits}) == 1:
                team = reserve_exits[0]['team_id']
        latest = day
        trace.append(dict(date=day, kinds=sorted({e['kind'] for e in group}),
            state=state, team_id=team, explicit_major_link=explicit_major, same_date_conflict=conflict))
    return dict(state=state, team_id=team, explicit_major_link=explicit_major,
        same_date_conflict=conflict, latest_date=latest, trace=trace)


def absence_state(records, cutoff, return_reports=()):
    groups = defaultdict(list)
    for r in as_of(records, cutoff):
        groups[r['event_date']].append(r)
    state = 'no_captured_restriction'; duration_games = None; end = None; retired = False; trace = []
    for day, group in sorted(groups.items()):
        kinds = {r['kind'] for r in group}
        restrictions = kinds & {'permanent_ineligible', 'deceased', 'finite_ineligible',
            'restricted', 'administrative_leave', 'ineligible_unspecified', 'suspended_unspecified'}
        clears = kinds & {'reinstated', 'nonmedical_activation'}
        if state == 'deceased':
            pass
        elif state == 'permanent_ineligible' and 'reinstated' not in clears:
            pass
        elif restrictions and clears:
            state = 'ambiguous_same_date_restriction'; duration_games = None; end = None
        elif 'deceased' in restrictions:
            state = 'deceased'; duration_games = None; end = None
        elif 'permanent_ineligible' in restrictions:
            state = 'permanent_ineligible'; duration_games = None; end = None
        elif restrictions and state not in {'permanent_ineligible', 'deceased'}:
            finite = [r for r in group if r['kind'] == 'finite_ineligible']
            game = [r for r in group if r.get('duration_games')]
            if finite:
                years = {int(r['duration_years']) for r in finite}
                if len(years) != 1:
                    raise ValueError('Conflicting finite durations')
                # Feb 29 has a valid Feb 28 anniversary in non-leap years.
                try: end = day.replace(year=day.year+next(iter(years)))
                except ValueError: end = day.replace(year=day.year+next(iter(years)), day=28)
                state = 'finite_calendar_ineligibility'; duration_games = None
            elif game:
                durations = {r['duration_games'] for r in game}
                if len(durations) != 1:
                    raise ValueError('Conflicting game suspension durations')
                state = 'finite_game_suspension'; duration_games = next(iter(durations)); end = None
            else:
                state = 'suspension_unspecified' if restrictions == {'suspended_unspecified'} else 'unresolved_nonmedical'
                duration_games = None; end = None
        elif clears:
            # Only explicit legal reinstatement clears permanent legal ineligibility.
            if state != 'deceased' and (state != 'permanent_ineligible' or 'reinstated' in clears):
                state = 'reported_nonmedical_reinstatement'; duration_games = None; end = None
        elif state in {'finite_game_suspension','suspension_unspecified'} and any(r['kind']=='mlb_activation' and r.get('il_kind') != 'activation'
                and not any(w in r['description'].lower() for w in ['injured', 'disabled', 'paternity', 'bereavement', 'restricted', 'administrative']) for r in group):
            state = 'reported_nonmedical_reinstatement'; duration_games = None; end = None
        if 'retired' in kinds: retired = True
        elif kinds & {'org_acquisition', 'minor_contract', 'foreign_return_signing'}: retired = False
        if restrictions or clears or 'retired' in kinds:
            trace.append(dict(date=day.isoformat(), kinds=sorted(kinds), state=state))
    if end is not None and cutoff >= end:
        state = 'finite_end_elapsed_return_unconfirmed'; end = None
    eligible = [r for r in return_reports if date.fromisoformat(r['known_date']) <= cutoff
        and date.fromisoformat(r['event_date']) <= cutoff]
    report = max(eligible, key=lambda r:r['known_date']) if eligible and state in {
        'finite_game_suspension','finite_calendar_ineligibility'} else None
    return dict(state=state, original_duration_games=duration_games,
        known_calendar_end=end.isoformat() if end else None,
        reported_return_date=report['reported_return_date'] if report else None,
        return_report=report, retired_evidence=retired,
        hard_unavailable=state in {'permanent_ineligible','deceased'}, trace=trace)


def reconcile(population_row, raw_events, records, teams, return_reports=()):
    cutoff = date.fromisoformat(population_row['information_date'])
    employment = organization_state(employment_events(raw_events, teams, cutoff))
    absence = absence_state(records, cutoff, return_reports)
    literal = population_row['returned_40man']
    conflict = population_row['roster_cross_team_conflict'] or population_row['roster_status_conflict'] or employment['same_date_conflict']
    negative_conflict = not literal and employment['explicit_major_link'] and not conflict
    positive_conflict = literal and employment['state'] in {'reported_release','reported_retirement','reserve_departure_organization_unconfirmed'}
    spells = il_episodes(records, cutoff)[0]
    return dict(candidate_key=population_row['candidate_key'], player_id=population_row['player_id'],
        origin_year=population_row['origin_year'], target_year=population_row['target_year'], information_date=cutoff.isoformat(),
        literal_returned_40man=literal, employment=employment, absence=absence,
        status_major_link=bool(literal and not conflict and not positive_conflict or employment['explicit_major_link'] and not conflict),
        status_minor_agreement=employment['state']=='minor_agreement',
        status_agreement_unspecified=employment['state']=='agreement_unspecified',
        status_acquisition_only=employment['state']=='acquisition',
        status_released=employment['state']=='reported_release',
        status_employment_unknown=employment['state']=='unknown' and not literal,
        status_employment_conflict=bool(conflict or positive_conflict),
        status_negative_listing_conflict=bool(negative_conflict), status_positive_listing_conflict=bool(positive_conflict),
        status_finite_nonmedical=absence['state'] in {'finite_game_suspension','finite_calendar_ineligibility'},
        status_unresolved_nonmedical=absence['state'] in {'unresolved_nonmedical','suspension_unspecified','ambiguous_same_date_restriction'},
        status_hard_unavailable=absence['hard_unavailable'],
        status_medical_evidence_open=any(s['open'] for s in spells),
        status_medical_scope_interrupted=any(s['closure_kind']=='observation_scope_exit' for s in spells),
        clinical_spells=spells, full_annual_availability_coverage=population_row['origin_year']>=2015,
        current_rights_fully_certified=False, medical_recovery_certified=False,
        new_PA_forecast=None, forecast_eligibility_approved=False)
