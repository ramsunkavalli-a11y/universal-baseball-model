"""Dated raw contact evidence; no learned park/opponent adjustment."""
import numpy as np
import polars as pl
from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.hitter_value_panel import CONTACT_BINS, CONTACT_OUTCOMES

YEARS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
CELLS = [f'count_{b}___{o}' for b in CONTACT_BINS for o in CONTACT_OUTCOMES]
COVERAGE = [f'dc_log_{b}' for b in BUCKETS] + [
    'dc_log_physical', 'dc_classified_fraction', 'dc_available',
    *[f'dc_source_year_available_{lag}' for lag in range(3)],
    *[f'dc_canceled_{lag}' for lag in range(3)]]
SHAPE = [f'dc_mix_{b}' for b in CONTACT_BINS]
DETAIL = [f'dc_detail_{b}___{o}' for b in CONTACT_BINS for o in CONTACT_OUTCOMES]
FEATURES = COVERAGE + SHAPE + DETAIL


def validate(measurements):
    grain = ['season', 'league_id', 'bucket', 'player_id']
    if measurements.unique(grain).height != measurements.height:
        raise ValueError('Duplicate actual-league contact measurement')
    if not measurements['season'].is_in(YEARS).all():
        raise ValueError('Contact predictor season outside certified history')
    if not measurements['bucket'].is_in(BUCKETS).all():
        raise ValueError('Unknown league bucket')
    if measurements.filter((pl.col('league_id') == 125) & (pl.col('bucket') != 'MEX')).height:
        raise ValueError('Mexico collapsed into affiliated level')
    a = measurements.select(CELLS).to_numpy().astype(float)
    n = measurements['classified_contacts'].to_numpy().astype(float)
    physical = measurements['physical_contacts'].to_numpy().astype(float)
    if not np.isfinite(a).all() or (a < 0).any() or not np.array_equal(a.sum(1), n):
        raise ValueError('Ninety cells do not exhaust classified contact exposure')
    if not np.isfinite(physical).all() or (physical < n).any():
        raise ValueError('Classified exposure exceeds physical contacts')


def materialize(frame, measurements):
    validate(measurements)
    if frame['origin_year'].max() > 2024:
        raise ValueError('Protected predictor origin')
    if frame['row_id'].n_unique() != len(frame):
        raise ValueError('Duplicate row identity')
    lookup = {}
    for r in measurements.select('player_id', 'season', 'league_id', 'bucket',
                                 'physical_contacts', 'classified_contacts', *CELLS).iter_rows(named=True):
        lookup.setdefault((r['player_id'], r['season']), []).append(r)
    x = np.zeros((len(frame), len(FEATURES)))
    physical = np.zeros(len(frame)); classified = np.zeros(len(frame))
    leagues, seasons = [], []
    for i, r in enumerate(frame.select('player_id', 'origin_year').iter_rows(named=True)):
        total = np.zeros((len(CONTACT_BINS), len(CONTACT_OUTCOMES)))
        level = np.zeros(len(BUCKETS)); seen_leagues, seen_seasons = set(), set()
        for lag, w in enumerate([1., .8, .6]):
            year = r['origin_year'] - lag
            for s in lookup.get((r['player_id'], year), []):
                physical[i] += w * s['physical_contacts']
                classified[i] += w * s['classified_contacts']
                level[BUCKETS.index(s['bucket'])] += w * s['physical_contacts']
                total += w * np.array([s[c] for c in CELLS]).reshape(total.shape)
                seen_leagues.add(s['league_id']); seen_seasons.add(year)
        available = classified[i] > 0
        p = (total + .5) / (classified[i] + 45)
        mix = p.sum(1)
        detail = p - mix[:, None] / len(CONTACT_OUTCOMES)
        values = [*np.log1p(level) / np.log(1201), np.log1p(physical[i]) / np.log(1201),
                  classified[i] / physical[i] if physical[i] else 0., float(available),
                  *[float(r['origin_year'] - lag in YEARS) for lag in range(3)],
                  *[float(r['origin_year'] - lag == 2020) for lag in range(3)],
                  *((mix - .1) / .1 if available else np.zeros(len(mix))),
                  *(detail.ravel() / .1 if available else np.zeros(detail.size))]
        x[i] = values
        leagues.append(','.join(map(str, sorted(seen_leagues))))
        seasons.append(','.join(map(str, sorted(seen_seasons))))
    result = frame.select('row_id').with_columns(
        *[pl.Series(c, x[:, j]) for j, c in enumerate(FEATURES)],
        pl.Series('dc_physical_exposure', physical), pl.Series('dc_classified_exposure', classified),
        pl.Series('dc_actual_leagues', leagues), pl.Series('dc_source_seasons', seasons))
    if not np.isfinite(result.select(FEATURES).to_numpy()).all():
        raise ValueError('Nonfinite raw contact inputs')
    return result


def tagged(frame):
    return frame.with_columns(
        pl.when(pl.col('dc_classified_exposure') == 0).then(0)
        .when(pl.col('dc_classified_exposure') < 50).then(1)
        .when(pl.col('dc_classified_exposure') < 200).then(2).otherwise(3).alias('dc_band'))


def assembly(raw, anchor, available, *, prior_debut, primary, supported):
    """Keep unmeasured and unsupported predictions on the locked anchor."""
    raw, anchor = np.asarray(raw, float), np.asarray(anchor, float)
    eligible = np.asarray(available, bool) & bool(supported)
    if primary:
        eligible &= np.asarray(prior_debut) == 0
    if raw.shape != anchor.shape or not np.isfinite(raw).all() or not np.isfinite(anchor).all():
        raise ValueError('Invalid forecast array')
    return np.where(eligible, raw, anchor)
