"""Matched observation replacements; legal history is preserved as source data."""
from datetime import date

import numpy as np
import polars as pl

from .employment_comparison import profiles

FIELDS = ['status_finite_nonmedical', 'status_unresolved_nonmedical',
    'restriction_games_known', 'restriction_games', 'restriction_end_known',
    'restriction_end_days', 'return_report_known', 'return_report_days']
OBS = {n: 'obs_' + n for n in FIELDS}


def numeric(flags, games, end, report, information_date):
    now = date.fromisoformat(information_date)
    values = dict(zip(FIELDS[:2], map(float, flags), strict=True))
    if games is not None and (games <= 0 or int(games) != games):
        raise ValueError('Invalid original game sentence')
    values.update(restriction_games_known=float(games is not None),
        restriction_games=min(games, 1000) / 100 if games is not None else 0.)
    for prefix, value in [('restriction_end', end), ('return_report', report)]:
        values[prefix + '_known'] = float(value is not None)
        values[prefix + '_days'] = float(np.clip((date.fromisoformat(value) - now).days,
                                               -365, 365) / 365) if value else 0.
    return values


def sources(ledger, observations):
    rows = []
    for r in ledger:
        key, a = r['candidate_key'], r['absence']
        o = observations[key]
        assert (r['origin_year'], r['player_id'], r['information_date']) == (
            o['origin_year'], o['player_id'], o['information_date'])
        old = numeric([r[n] for n in FIELDS[:2]], a['original_duration_games'],
                      a['known_calendar_end'], a['reported_return_date'], r['information_date'])
        new = numeric([o['observation_finite_nonmedical'], o['observation_unresolved_nonmedical']],
            o['unresolved_original_duration_games'], o['unresolved_known_calendar_end'],
            o['current_return_date'], r['information_date'])
        rows.append(dict(origin_year=r['origin_year'], player_id=r['player_id'],
            information_date=r['information_date'], captured_legal_class=a['state'],
            observation_has_return=bool(o['observed_after_channel_names']),
            **{'legacy_' + n: v for n, v in old.items()},
            **{OBS[n]: v for n, v in new.items()}))
    return pl.DataFrame(rows, infer_schema_length=None)


def frame(original, source):
    j = original.join(source, on=['origin_year', 'player_id'], how='left', validate='1:1')
    if j.height != original.height or j['information_date'].null_count():
        raise ValueError('Missing observation source')
    if not j['information_date'].equals(j['ctx_information_date']):
        raise ValueError('Mismatched observation cutoff')
    for name in FIELDS:
        if not np.array_equal(j[name].to_numpy(), j['legacy_' + name].to_numpy()):
            raise ValueError('Legacy restriction input does not reconstruct: ' + name)
    result = j.select(original.columns + list(OBS.values()) +
                      ['captured_legal_class', 'observation_has_return'])
    if not result.select(original.columns).equals(original):
        raise ValueError('Original input evidence changed')
    return result


def support(train, test, *, observation):
    keys = ['prior_debut', 'stage', 'age_group', 'mlb_exposure', 'foreign_source',
            'first_team_history', 'restriction_profile', 'employment_category',
            'captured_legal_class', 'observation_has_return']
    def project(f):
        if observation:
            f = f.with_columns([pl.col(OBS[n]).alias(n) for n in FIELDS[:2]])
        return profiles(f)
    tr, te = project(train), project(test)
    counts = tr.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
    return te.select('row_id', *keys).join(counts, on=keys, how='left', validate='m:1').with_columns(
        pl.col('profile_people').fill_null(0))
