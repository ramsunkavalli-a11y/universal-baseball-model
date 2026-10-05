"""Source review gates with equal-window comparisons, not forecast claims."""
import math

from universal_baseball.international_hitter_snapshot_2026 import subtotal


def aligned_peers(history, current, key, focal):
    """Compare exposure in the same 2024-through-snapshot window on both sides."""
    identity = focal.get(key)
    focal_pa = subtotal(history, key, identity, 2026)['counts']['pa']
    people = {}
    for row in current:
        candidate = row.get(key)
        if candidate is None or candidate == identity:
            continue
        entry = people.setdefault(candidate, dict(source_key=candidate,
            name=row.get('player_name_ja') or row.get('player_name_ko'),
            snapshot_pa=0, birth_date=row.get('birth_date')))
        entry['snapshot_pa'] += row['pa']
        if entry['birth_date'] != row.get('birth_date'):
            raise ValueError('Conflicting peer birth dates')
    for entry in people.values():
        counts = subtotal(history, key, entry['source_key'], 2026)
        entry['window_pa'] = counts['counts']['pa']
        entry['window_source_rows'] = counts['source_rows']

    def distance(peer):
        exposure = abs(math.log1p(peer['window_pa']) - math.log1p(focal_pa))
        if focal.get('birth_date') and peer['birth_date']:
            exposure += abs(int(focal['birth_date'][:4]) - int(peer['birth_date'][:4])) / 2
        return exposure, peer['source_key']

    return sorted(people.values(), key=distance)[:3]


def validate_claims(review):
    """A completed source review may not certify model or season completion."""
    if review.get('new_fits') != 0 or review.get('forecasts_changed') is not False:
        raise ValueError('Source-only review changed a model or forecast')
    if review.get('raw_2026_MLB_outcomes_read') is not False:
        raise ValueError('Source review may not read 2026 MLB outcomes')
    if not review.get('independent_reconstruction_pass') or review.get('future_mutation_checks') != 6:
        raise ValueError('Missing source reconstruction or cutoff checks')
    if len(review.get('source_cases', [])) != 6:
        raise ValueError('Six original controls must be retained')
    for case in review['source_cases']:
        if any(case.get(k) is not None for k in
               ('MLB_talent_forecast', 'MLB_opportunity_forecast', 'predictive_outcome')):
            raise ValueError('Source review cannot invent a predictive result')
    for league in ['npb', 'kbo']:
        if review['source_checks'][league]['season_complete'] is not False:
            raise ValueError('Overseas season completion is unqualified')
