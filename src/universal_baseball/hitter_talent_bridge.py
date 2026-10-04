"""Fold- and origin-local coherent event evidence, not park-neutral MLEs."""
from itertools import combinations

import numpy as np
import polars as pl

from universal_baseball.post_arrival_history import player_fold

EVENTS = ['other', 'K', 'UBB', 'HBP', '1B', '2B', '3B', 'HR']
PROFILE_FEATURES = [f'translated_{e}' for e in EVENTS] + [
    'translated_log_exposure', 'translated_supported_fraction',
    'translated_reliability', 'translated_missing']
SCOUT_FEATURES = [f'scout_{c}_{lag}' for lag in range(3)
                  for c in ['list_available', 'listed', 'rank_score']]


def event_counts(source):
    if source.unique(['season', 'player_id', 'bucket']).height != source.height:
        raise ValueError('Duplicate source identities')
    x = source.select('strike_outs', 'unintentional_walks', 'hit_by_pitch',
                      'babip_hits', 'doubles', 'triples', 'home_runs').to_numpy().astype(float)
    pa = source['plate_appearances'].to_numpy().astype(float)
    singles = x[:, 3] - x[:, 4] - x[:, 5]
    known = np.column_stack([x[:, 0], x[:, 1], x[:, 2], singles, x[:, 4], x[:, 5], x[:, 6]])
    counts = np.column_stack([pa - known.sum(1), known])
    if not np.isfinite(counts).all() or (counts < 0).any() or not np.allclose(counts.sum(1), pa):
        raise ValueError('Invalid mutually exclusive event counts')
    return counts


def clr(prob):
    z = np.log(prob)
    return z - z.mean(axis=-1, keepdims=True)


def translated_probability(counts, offset):
    prob = (np.asarray(counts, dtype=float) + .5) / (np.sum(counts) + 4)
    z = clr(prob) - offset
    z -= z.max()
    p = np.exp(z)
    p /= p.sum()
    if not np.isfinite(p).all() or (p <= 0).any() or not np.isclose(p.sum(), 1):
        raise ValueError('Invalid translated probabilities')
    return p


def make_pairs(source, counts):
    """Construct source-only pairs once; cutoff/fold filters are applied at fit."""
    groups = {}
    for i, r in enumerate(source.iter_rows(named=True)):
        if r['plate_appearances'] >= 30:
            groups.setdefault((r['player_id'], r['season']), []).append((r, i))
    pairs = []
    for (pid, year), group in groups.items():
        for (a, ai), (b, bi) in combinations(sorted(group, key=lambda v: v[0]['bucket']), 2):
            pa, pb = a['plate_appearances'], b['plate_appearances']
            delta = clr((counts[ai] + .5) / (pa + 4)) - clr((counts[bi] + .5) / (pb + 4))
            pairs.append(dict(player_id=pid, season=year, fold=player_fold(pid),
                              a=a['bucket'], b=b['bucket'], weight=2 / (1 / pa + 1 / pb),
                              delta=delta.tolist()))
    return pairs


def fit_graph(pairs, *, cutoff, held_fold):
    selected = [p for p in pairs if p['season'] <= cutoff and p['fold'] != held_fold]
    reached = {'MLB'}
    while True:
        new = reached | {p['b'] for p in selected if p['a'] in reached} | {
            p['a'] for p in selected if p['b'] in reached}
        if new == reached:
            break
        reached = new
    valid = [p for p in selected if p['a'] in reached and p['b'] in reached]
    levels = sorted(reached - {'MLB'})
    lut = {b: i for i, b in enumerate(levels)}
    design = np.zeros((len(valid), len(levels)))
    target = np.zeros((len(valid), 8))
    for i, p in enumerate(valid):
        root = np.sqrt(p['weight'])
        if p['a'] != 'MLB':
            design[i, lut[p['a']]] = root
        if p['b'] != 'MLB':
            design[i, lut[p['b']]] = -root
        target[i] = root * np.asarray(p['delta'])
    coef = np.linalg.lstsq(design, target, rcond=None)[0] if levels else np.zeros((0, 8))
    if len(levels) and np.linalg.matrix_rank(design) != len(levels):
        raise ValueError('Connected graph is rank deficient')
    offsets = {'MLB': np.zeros(8), **{b: coef[i] for b, i in lut.items()}}
    observed = {b for p in selected for b in [p['a'], p['b']]}
    note = dict(cutoff=cutoff, held_fold=held_fold, pair_count=len(valid),
                people=sorted({p['player_id'] for p in valid}),
                max_source_year=max((p['season'] for p in valid), default=None),
                connected_buckets=sorted(reached), disconnected_buckets=sorted(observed - reached),
                offsets={b: x.tolist() for b, x in offsets.items()},
                edges=[dict(a=a, b=b, pairs=sum(p['a'] == a and p['b'] == b for p in valid),
                            people=len({p['player_id'] for p in valid if p['a'] == a and p['b'] == b}))
                       for a, b in sorted({(p['a'], p['b']) for p in valid})])
    assert all(player_fold(pid) != held_fold for pid in note['people'])
    return offsets, note


def materialize(source, frame, *, held_fold):
    """Each feature row uses its own origin, including rows later used in training."""
    if source['season'].max() > 2024 or frame['origin_year'].max() > 2024:
        raise ValueError('Future predictor source')
    counts = event_counts(source)
    pairs = make_pairs(source, counts)
    lut = {}
    for i, r in enumerate(source.iter_rows(named=True)):
        lut.setdefault((r['player_id'], r['season']), []).append((r, counts[i]))
    graphs, notes, priors = {}, [], {}
    for year in sorted(frame['origin_year'].unique()):
        graphs[year], note = fit_graph(pairs, cutoff=year, held_fold=held_fold)
        notes.append(note)
        mask = np.array([r['season'] == year and r['bucket'] == 'MLB' and player_fold(r['player_id']) != held_fold
                         for r in source.iter_rows(named=True)])
        aggregate = counts[mask].sum(0) + .5
        if not mask.any():
            raise ValueError('Missing origin MLB reference environment')
        priors[year] = aggregate / aggregate.sum()
        note['mlb_reference'] = priors[year].tolist()
        note['mlb_reference_people'] = source.filter(pl.Series(mask))['player_id'].to_list()
    profiles = []
    for r in frame.iter_rows(named=True):
        y, pid = r['origin_year'], r['player_id']
        total, supported = 0., 0.
        weighted = np.zeros(8)
        buckets = set()
        for lag, weight in enumerate([1., .8, .6]):
            for s, c in lut.get((pid, y - lag), []):
                exposure = weight * s['plate_appearances']
                total += exposure
                if s['bucket'] in graphs[y] and exposure > 0:
                    supported += exposure
                    weighted += exposure * translated_probability(c, graphs[y][s['bucket']])
                    buckets.add(s['bucket'])
        p = weighted / supported if supported else priors[y]
        d = (p - priors[y]) / .1 if supported else np.zeros(8)
        profiles.append(dict(row_id=r['row_id'], **dict(zip(PROFILE_FEATURES[:8], d)),
                             translated_log_exposure=np.log1p(supported) / np.log(1201),
                             translated_supported_fraction=supported / total if total else 0.,
                             translated_reliability=supported / (supported + 1200),
                             translated_missing=float(supported == 0),
                             translation_supported_pa=supported, translation_total_pa=total,
                             translation_buckets=','.join(sorted(buckets)),
                             **{f'translated_probability_{e}': p[i] for i, e in enumerate(EVENTS)}))
    return frame.join(pl.DataFrame(profiles), on='row_id', validate='1:1'), notes
