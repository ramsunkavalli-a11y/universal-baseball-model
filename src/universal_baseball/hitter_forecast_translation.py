"""Explicit predictor-year extension of the sealed, held-player talent bridge.

Translation is learned from same-season cross-level pairs, not future MLB
outcomes. It is not a park-neutral or population-selection-corrected MLE.
"""
import numpy as np
import polars as pl
from .hitter_talent_bridge import EVENTS, PROFILE_FEATURES, event_counts, make_pairs, fit_graph, translated_probability
from .post_arrival_history import player_fold


def translation_inputs(source, frame, *, held_fold, source_cutoff):
    if not isinstance(source_cutoff, int) or not 2011 <= source_cutoff <= 2025:
        raise ValueError('Only declared predictor origins through 2025')
    if held_fold not in range(5):
        raise ValueError('Unknown held-player fold')
    if source['season'].max() > source_cutoff or frame['origin_year'].max() > source_cutoff:
        raise ValueError('Future predictor source')
    if frame['row_id'].n_unique() != len(frame) or frame.unique(['player_id','origin_year']).height != len(frame):
        raise ValueError('Duplicate feature identities')
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
        assert all(player_fold(pid) != held_fold for pid in note['mlb_reference_people'])
    profiles = []
    for r in frame.iter_rows(named=True):
        y, pid = r['origin_year'], r['player_id']
        total, supported = 0., 0.
        weighted = np.zeros(8); buckets = set()
        for lag, weight in enumerate([1., .8, .6]):
            for s, c in lut.get((pid, y-lag), []):
                exposure = weight*s['plate_appearances']; total += exposure
                if s['bucket'] in graphs[y] and exposure > 0:
                    supported += exposure
                    weighted += exposure*translated_probability(c, graphs[y][s['bucket']])
                    buckets.add(s['bucket'])
        p = weighted/supported if supported else priors[y]
        d = (p-priors[y])/.1 if supported else np.zeros(8)
        profiles.append(dict(row_id=r['row_id'], **dict(zip(PROFILE_FEATURES[:8], d)),
            translated_log_exposure=np.log1p(supported)/np.log(1201),
            translated_supported_fraction=supported/total if total else 0.,
            translated_reliability=supported/(supported+1200), translated_missing=float(supported == 0),
            translation_supported_pa=supported, translation_total_pa=total, translation_buckets=','.join(sorted(buckets)),
            **{f'translated_probability_{e}':p[i] for i,e in enumerate(EVENTS)}))
    return pl.DataFrame(profiles), notes
