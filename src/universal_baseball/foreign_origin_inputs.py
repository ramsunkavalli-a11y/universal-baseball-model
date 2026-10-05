"""Origin-only foreign components and separately qualified dated hitter roles."""
from collections import defaultdict
from datetime import date

from .foreign_mover_support import COUNTS, HITTER_CODES


def qualify_role(pair, domestic_rows, population, role_hints):
    year = pair['domestic_year']; pid = pair['player_id']
    codes = {r['position'] for r in domestic_rows if r['player_id'] == pid
             and r['season'] == year and r['plate_appearances'] > 0}
    hitter = bool(codes & HITTER_CODES); pitcher = '1' in codes
    context = next((r for r in population if r['player_id'] == pid and r['origin_year'] == year - 1), None)
    hint = next((r['reviewed_role_hint'] for r in role_hints if r['player_id'] == pid and r['origin_year'] == year - 1), 'unknown')
    if context and int(context['information_date'][:4]) > year:
        raise ValueError('Future dated role context')
    if context is None:
        hint = 'unknown'
    hitter = hitter or hint in {'hitter_hint', 'two_way_hint', 'two_way_or_conflicting_hints'}
    pitcher = pitcher or hint == 'pitcher_hint'
    original = pair['domestic_role']
    qualified = original
    basis = 'recorded_domestic_side_role'
    if original == 'unknown':
        qualified = 'conflicting_hints' if hitter and pitcher else 'hitter_hint' if hitter else 'pitcher_hint' if pitcher else 'unknown'
        basis = 'same_year_domestic_stints_or_dated_preseason_hint' if qualified != 'unknown' else 'unresolved'
    return dict(original_role=original, qualified_role=qualified, role_basis=basis,
                dated_preseason_hint=hint, dated_information_date=context['information_date'] if context else None,
                same_year_domestic_positions=sorted(codes),
                supported_hitter=qualified in {'hitter', 'mixed', 'hitter_hint'},
                full_historical_position_qualified=False)


def materialize_inputs(population, annual, domestic_rows, role_hints):
    by_person = defaultdict(list)
    for r in annual:
        if r['league'] in {'NPB', 'KBO'}:
            by_person[r['player_id']].append(r)
    hints = {(r['player_id'], r['origin_year']): r['reviewed_role_hint'] for r in role_hints}
    domestic = defaultdict(list)
    for r in domestic_rows:
        domestic[r['player_id']].append(r)
    rows = []
    for p in population:
        pid, origin = p['player_id'], p['origin_year']
        known = [r for r in by_person[pid] if r['season'] <= origin]
        recent = [r for r in known if origin - 2 <= r['season'] <= origin]
        if not any(r['pa'] > 0 for r in recent):
            continue
        births = {r['birth_date'] for r in known if r['birth_date']}
        if len(births) > 1:
            raise ValueError('Conflicting cross-league birthday')
        birth = next(iter(births)) if births else None
        age = (date.fromisoformat(p['information_date']) - date.fromisoformat(birth)).days / 365.2425 if birth else None
        counts = {}
        for league in ['NPB', 'KBO']:
            for lag in range(3):
                group = [r for r in recent if r['league'] == league and r['season'] == origin - lag]
                total = {c: sum(r[c] for r in group) for c in COUNTS}
                counts[f'{league}_{lag}'] = dict(season=origin - lag, counts=total,
                    league_source_year_covered=2005 <= origin - lag <= 2024,
                    player_identity_and_stat_observed=bool(group),
                    absent_group_is_not_certified_zero=not bool(group))
        prior = [r for r in domestic[pid] if r['season'] <= origin]
        rows.append(dict(candidate_key=p['candidate_key'], player_id=pid, origin_year=origin,
            information_date=p['information_date'], original_source_origin=p['current_model_origin'],
            birth_date=birth, age_at_information_date=age, foreign_history_counts=counts,
            observed_foreign_history_pa=sum(r['pa'] for r in known),
            recent_foreign_pa=sum(r['pa'] for r in recent),
            recent_observed_domestic_pa=sum(r['plate_appearances'] for r in prior if r['season'] >= origin - 2),
            recent_observed_MLB_pa=sum(r['plate_appearances'] for r in prior if r['season'] >= origin - 2 and r['sport_id'] == 1),
            roster_hitter_codes=p['roster_position_codes'], returned_40man=p['returned_40man'],
            roster_team_ids=p['roster_team_ids'], dated_role_hint=hints.get((pid, origin), 'unknown'),
            positive_MLB_context=p['origin_has_positive_context'],
            historical_rights_fully_verified=False, foreign_role_fully_qualified=False,
            forecast_eligibility_approved=False, MLB_translation_fitted=False,
            experience_before_2005_known=False, domestic_experience_before_2008_known=False))
    return rows
