"""Historical mover samples and explicit role/support limits, not fitted MLEs."""
from collections import defaultdict
from datetime import date

from .post_arrival_history import player_fold

COUNTS = ['pa', 'ab', 'hits', 'doubles', 'triples', 'hr', 'bb', 'ibb', 'hbp', 'so', 'sf']
HITTER_CODES = {str(i) for i in range(2, 11)} | {'O', 'I', 'Y'}


def role(positions):
    known = set(positions)
    hitter = bool(known & HITTER_CODES)
    pitcher = '1' in known
    return 'mixed' if hitter and pitcher else 'hitter' if hitter else 'pitcher' if pitcher else 'unknown'


def aggregate_foreign(rows, league):
    grouped = {}
    for r in rows:
        if r['season'] > 2024:
            raise ValueError('Future foreign source')
        if r['player_id'] is None:
            continue  # Original source remains intact; mapping gaps are reported separately.
        key = (r['season'], r['player_id'], league)
        if key not in grouped:
            grouped[key] = dict(season=r['season'], player_id=r['player_id'], league=league,
                                source_name=r.get('english_name') or r.get('player_name_ja') or r.get('player_name_ko'),
                                birth_date=r.get('birth_date'), role='unknown', **{c: 0 for c in COUNTS})
        dest = grouped[key]
        if r.get('birth_date') and dest['birth_date'] != r['birth_date']:
            raise ValueError('Conflicting foreign birthday')
        for c in COUNTS:
            dest[c] += r[c]
    return list(grouped.values())


def make_pairs(annual, minimum=30):
    lookup = {}
    for r in annual:
        key = (r['season'], r['player_id'], r['league'])
        if key in lookup:
            raise ValueError('Duplicate annual identity')
        if r['season'] > 2024:
            raise ValueError('Future support source')
        lookup[key] = r
    pairs = []
    for a in annual:
        if a['pa'] < minimum:
            continue
        foreign = a['league'] in {'NPB', 'KBO'}
        destinations = ['MLB', 'AAA'] if foreign else ['NPB', 'KBO']
        for lag in [0, 1]:
            for league in destinations:
                b = lookup.get((a['season'] + lag, a['player_id'], league))
                if b is None or b['pa'] < minimum:
                    continue
                # Same-season samples are unordered. Consecutive directions stay separate.
                if lag == 0 and not foreign:
                    continue
                overseas = a if foreign else b
                domestic = b if foreign else a
                birthday = overseas['birth_date']
                age = (date(overseas['season'], 12, 31) - date.fromisoformat(birthday)).days / 365.2425 if birthday else None
                prior = [r for r in annual if r['player_id'] == a['player_id']
                         and r['league'] == 'MLB' and r['season'] < overseas['season']]
                pairs.append(dict(player_id=a['player_id'], fold=player_fold(a['player_id']),
                    mechanism='same_season' if lag == 0 else 'consecutive_season',
                    a=a['league'], b=b['league'], from_year=a['season'], through_year=b['season'],
                    minimum_pa=minimum, from_pa=a['pa'], to_pa=b['pa'],
                    touches_2020=a['season'] == 2020 or b['season'] == 2020,
                    domestic_role=domestic['role'], foreign_source_name=overseas['source_name'],
                    foreign_age=age,
                    foreign_age_band='unknown' if age is None else 'under25' if age < 25
                    else '25to29' if age < 30 else '30to34' if age < 35 else '35plus',
                    foreign_pa_band='under100' if overseas['pa'] < 100 else '100to299' if overseas['pa'] < 300 else '300plus',
                    foreign_contact_band='lowK' if overseas['so'] / overseas['pa'] < .15 else 'middleK' if overseas['so'] / overseas['pa'] < .25 else 'highK',
                    foreign_power_band='highHR' if overseas['hr'] / overseas['pa'] >= .04 else 'lowerHR',
                    prior_observed_100_PA_MLB_seasons=sum(r['pa'] >= 100 for r in prior),
                    prior_MLB_left_truncated=True, full_first_debut_certified=False,
                    foreign_counts={c: overseas[c] for c in COUNTS},
                    from_counts={c: a[c] for c in COUNTS}, to_counts={c: b[c] for c in COUNTS}))
    return pairs


def support(pairs, cutoff, held_fold, *, minimum=30):
    selected = [p for p in pairs if p['through_year'] <= cutoff and p['fold'] != held_fold
                and p['minimum_pa'] == minimum and not p['touches_2020']]
    groups = defaultdict(list)
    for p in selected:
        groups[p['mechanism'], p['a'], p['b'], p['domestic_role']].append(p)
    return [dict(cutoff=cutoff, held_fold=held_fold, minimum_pa=minimum,
                 mechanism=k[0], a=k[1], b=k[2], domestic_role=k[3], pairs=len(v),
                 people=len({p['player_id'] for p in v}),
                 player_ids=sorted({p['player_id'] for p in v}),
                 max_source_year=max(p['through_year'] for p in v))
            for k, v in sorted(groups.items())]


def profile_support(pairs, case, cutoff, held_fold):
    known = [p for p in pairs if p['through_year'] <= cutoff and p['fold'] != held_fold
             and p['minimum_pa'] == 30 and not p['touches_2020'] and p['domestic_role'] in {'hitter', 'mixed'}]
    selected = [p for p in known if p['mechanism'] == 'consecutive_season'
                and p['a'] == case['league'] and p['b'] == 'MLB']
    def people(rows):
        return len({r['player_id'] for r in rows})
    age = case['age']
    band = 'unknown' if age is None else 'under25' if age < 25 else '25to29' if age < 30 else '30to34' if age < 35 else '35plus'
    same_age = [p for p in selected if p['foreign_age_band'] == band]
    return dict(cutoff=cutoff, held_fold=held_fold, league=case['league'],
                direct_hitter_mover_people=people(selected), same_age_people=people(same_age),
                same_age_contact_power_people=people([p for p in same_age if
                    p['foreign_contact_band'] == case['contact_band'] and p['foreign_power_band'] == case['power_band']]),
                direct_player_ids=sorted({p['player_id'] for p in selected}),
                direct_sparse_warning=people(selected) < 20, universal_translation_approved=False)
