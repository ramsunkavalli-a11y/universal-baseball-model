"""Own-season, held-player source calibration for the minor tracking comparison."""
import math
import numpy as np
import polars as pl
from universal_baseball.post_arrival_history import player_fold

LEAGUES = (112, 117, 123)
# Denominator and unit scale for a constant reference distribution.
METRICS = {'mean_ev': ('measured_ev_contacts', 10.),
           'ev95': ('measured_ev_contacts', 10.),
           'best_half_ev': ('measured_ev_contacts', 10.),
           'mean_la': ('measured_la_contacts', 20.),
           'la_sd': ('measured_la_contacts', 20.),
           'hard_air_fraction': ('measured_pair_contacts', 1.)}


def best_half(values):
    a = np.sort(np.asarray(values, dtype=float))
    if not len(a):
        return None
    if not np.isfinite(a).all():
        raise ValueError('Only valid finite readings may enter best-half EV')
    return float(a[-math.ceil(len(a) / 2):].mean())


def feature_names():
    coverage, measurements = [], []
    for lag in range(3):
        for league in LEAGUES:
            p = f'msc_{league}_{lag}_'
            coverage += [p + s for s in ('ev_sample', 'la_sample', 'pair_sample',
                                         'pair_coverage', 'source_available')]
            coverage += [p + m + '_known' for m in METRICS]
            measurements += [p + m for m in METRICS]
            measurements += [p + 'best_half_sample', p + 'hard_air_sample']
    return coverage, measurements


def references(annual, held_fold):
    """Each season's references use that season only; never future MLB labels."""
    a = annual.with_columns(pl.Series('_fold', [player_fold(p) for p in annual['player_id']]))
    a = a.filter(pl.col('_fold') != held_fold)
    refs = []
    for group in a.partition_by('season', 'league_id', as_dict=False):
        season, league = int(group['season'][0]), int(group['league_id'][0])
        r = dict(season=season, league_id=league, held_fold=held_fold,
                 reference_people=group['player_id'].n_unique(),
                 player_ids=sorted(group['player_id'].to_list()), metrics={})
        for m, (denom, scale) in METRICS.items():
            known = group.filter(pl.col(m).is_not_null() & (pl.col(denom) > 0))
            if not len(known):
                r['metrics'][m] = dict(mean=None, scale=scale, people=0, exposure=0)
                continue
            x, w = known[m].to_numpy(), known[denom].to_numpy().astype(float)
            mean = float(np.average(x, weights=w))
            sd = float(np.sqrt(np.average((x-mean)**2, weights=w)))
            r['metrics'][m] = dict(mean=mean, scale=sd if sd >= 1e-6 else scale,
                                   people=known['player_id'].n_unique(), exposure=int(w.sum()),
                                   constant_reference=sd < 1e-6)
        refs.append(r)
    return refs


def materialize(features, annual, held_fold):
    if annual.unique(['player_id', 'season', 'league_id']).height != len(annual):
        raise ValueError('Duplicate annual tracking identities')
    if annual['season'].max() > 2024:
        raise ValueError('Protected source season prohibited')
    refs = references(annual, held_fold)
    lut = {(r['season'], r['league_id']): r for r in refs}
    coverage, measurements = feature_names()
    out = features
    for lag in range(3):
        for league in LEAGUES:
            p = f'msc_{league}_{lag}_'
            sub = annual.filter(pl.col('league_id') == league)
            rows = []
            for r in sub.iter_rows(named=True):
                ref = lut.get((r['season'], league))
                z = dict(player_id=r['player_id'], _msc_season=r['season'])
                for kind in ('ev', 'la', 'pair'):
                    n = int(r[f'measured_{kind}_contacts'])
                    z[p+kind+'_n'] = n
                    z[p+kind+'_sample'] = float(np.log1p(n)/np.log(601))
                z[p+'pair_coverage'] = float(r['pair_coverage'])
                for m in METRICS:
                    stat = ref['metrics'][m] if ref else None
                    known = r[m] is not None and stat is not None and stat['mean'] is not None
                    z[p+m+'_known'] = float(known)
                    z[p+m] = float((r[m]-stat['mean'])/stat['scale']) if known else 0.
                z[p+'best_half_sample'] = z[p+'best_half_ev']*z[p+'ev_sample']
                z[p+'hard_air_sample'] = z[p+'hard_air_fraction']*z[p+'pair_sample']
                rows.append(z)
            if not rows:
                # Useful for source-mutation and absent-context regression tests.
                out = out.with_columns([pl.lit(0.).alias(c) for c in coverage+measurements if c.startswith(p)] +
                    [pl.lit(0).alias(p+k+'_n') for k in ('ev', 'la', 'pair')])
            else:
                out = out.with_columns((pl.col('origin_year')-lag).alias('_msc_season'))
                out = out.join(pl.DataFrame(rows), on=['player_id', '_msc_season'], how='left', validate='m:1')
                out = out.drop('_msc_season').with_columns([
                    pl.col(c).fill_null(0.) for c in coverage+measurements if c.startswith(p) and c in out.columns])
                out = out.with_columns([pl.col(p+k+'_n').fill_null(0) for k in ('ev', 'la', 'pair')])
            # Availability is not the same as a player's own measurement.
            available = [s for s, l in lut if l == league]
            out = out.with_columns((pl.col('origin_year')-lag).is_in(available).cast(pl.Float64).alias(p+'source_available'))
    for league in LEAGUES:
        out = out.with_columns(pl.sum_horizontal([pl.col(f'msc_{league}_{lag}_ev_n') for lag in range(3)]).alias(f'msc_{league}_ev_n'))
    out = out.with_columns(pl.sum_horizontal([pl.col(f'msc_{l}_ev_n') for l in LEAGUES]).alias('msc_own_ev_n'))
    assert out.select(features.columns).equals(features)
    return out, refs


def route(full, train_ids, test_ids, minimum_people=20):
    """Forecast eligibility uses own evidence and mature TRAINING support only."""
    active = full.filter(pl.col('row_id').is_in(train_ids) & (pl.col('next_pa') > 0))
    context = []
    for league in LEAGUES:
        sub = active.filter(pl.col(f'msc_{league}_ev_n') > 0)
        context.append(dict(league_id=league, rows=len(sub), people=sub['player_id'].n_unique(),
                            predebut_people=sub.filter(pl.col('prior_debut') == 0)['player_id'].n_unique(),
                            enabled=sub['player_id'].n_unique() >= minimum_people))
    coverage, measurements = feature_names()
    disabled = [c for c in coverage+measurements if any(
        c.startswith(f'msc_{r["league_id"]}_') for r in context if not r['enabled'])]
    routed = full.with_columns([pl.lit(0.).alias(c) for c in disabled])
    enabled = [pl.col(f'msc_{r["league_id"]}_ev_n') > 0 for r in context if r['enabled']]
    routed = routed.with_columns((pl.any_horizontal(enabled) if enabled else pl.lit(False)).alias('msc_eligible'))
    test = routed.filter(pl.col('row_id').is_in(test_ids)).sort('row_id')
    train = routed.filter(pl.col('row_id').is_in(train_ids) & (pl.col('next_pa') > 0)).sort('row_id')
    return train, test, context, disabled


def support_tags(g):
    # Real exposures, not the last-level label, define the comparison profile.
    return g.with_columns((pl.col('age')//5).cast(pl.Int64).alias('msc_age_band'),
        pl.when(pl.col('pooled_AAA_pa') >= 100).then(pl.lit('AAA100plus'))
        .when(pl.col('pooled_AAA_pa') > 0).then(pl.lit('AAAbrief'))
        .when(pl.col('pooled_AA_pa') >= 100).then(pl.lit('AA100plus'))
        .when(pl.col('pooled_AA_pa') > 0).then(pl.lit('AAbrief'))
        .otherwise(pl.lit('belowAA')).alias('msc_exposure_band'),
        pl.when(pl.col('msc_own_ev_n') == 0).then(pl.lit('untracked'))
        .when(pl.col('msc_own_ev_n') < 50).then(pl.lit('under50'))
        .when(pl.col('msc_own_ev_n') < 200).then(pl.lit('50to199'))
        .otherwise(pl.lit('200plus')).alias('msc_sample_band'),
        pl.when(pl.col('scout_listed_0') < 0).then(pl.lit('unknown'))
        .when(pl.col('scout_listed_0') == 0).then(pl.lit('unlisted'))
        .when(pl.col('scout_rank_score_0') >= .8).then(pl.lit('high_rank'))
        .otherwise(pl.lit('other_listed')).alias('msc_rank_band'))
