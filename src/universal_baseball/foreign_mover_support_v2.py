"""Additive repair: distinguish an overseas 2020 season from domestic cancellation."""
from collections import defaultdict

from .foreign_mover_support import COUNTS, aggregate_foreign, role
from .foreign_mover_support import make_pairs as original_pairs


def make_pairs(annual, minimum=30):
    pairs = original_pairs(annual, minimum)
    for p in pairs:
        domestic_year = p['from_year'] if p['a'] in {'MLB', 'AAA'} else p['through_year']
        p['domestic_year'] = domestic_year
        p['domestic_2020_exception'] = domestic_year == 2020
    return pairs


def support(pairs, cutoff, held_fold, *, minimum=30):
    selected = [p for p in pairs if p['through_year'] <= cutoff and p['fold'] != held_fold
                and p['minimum_pa'] == minimum and not p['domestic_2020_exception']]
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
    selected = [p for p in pairs if p['through_year'] <= cutoff and p['fold'] != held_fold
                and p['minimum_pa'] == 30 and not p['domestic_2020_exception']
                and p['domestic_role'] in {'hitter', 'mixed'}
                and p['mechanism'] == 'consecutive_season' and p['a'] == case['league'] and p['b'] == 'MLB']
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
