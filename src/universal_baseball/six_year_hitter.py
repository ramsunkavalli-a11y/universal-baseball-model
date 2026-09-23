"""Long-horizon labels and service accounting; never equate calendar and control."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import polars as pl

from universal_baseball.team_control import SERVICE_DAYS_PER_YEAR, FREE_AGENCY_SERVICE_YEARS


def extend_labels(panel: pl.DataFrame, targets: pl.DataFrame) -> pl.DataFrame:
    if panel['origin_year'].max() > 2025 or targets['season'].max() > 2025:
        raise ValueError('Protected future evidence')
    if targets.unique(['season', 'player_id']).height != targets.height:
        raise ValueError('Duplicate target identity')
    seasons = targets['season'].unique().to_list()
    out = panel
    for h in range(4, 7):
        out = out.join(targets.select((pl.col('season')-h).alias('origin_year'), 'player_id',
            pl.col('component_war').alias(f'war_h{h}'), pl.col('mlb_pa').alias(f'pa_h{h}')),
            on=['origin_year', 'player_id'], how='left', validate='1:1', maintain_order='left')
        complete = (pl.col('origin_year')+h).is_in(seasons)
        out = out.with_columns(complete.alias(f'complete_h{h}'), *[
            pl.when(complete).then(pl.col(f'{c}_h{h}').fill_null(0)).otherwise(None).alias(f'{c}_h{h}')
            for c in ('war', 'pa')])
    return out.with_columns(sum(pl.col(f'war_h{h}') for h in range(1, 7)).alias('war_c6'))


def mature_mask(panel, cutoff, horizon, excluded_ids=()):
    if cutoff > 2025 or horizon not in range(1, 7):
        raise ValueError('Invalid horizon/cutoff')
    year = panel['origin_year'].to_numpy()
    return ((year+horizon <= cutoff) & np.isfinite(panel[f'war_h{horizon}'].to_numpy())
            & ~((year < 2020) & (year+horizon >= 2020))
            & ~np.isin(panel['player_id'].to_numpy(), excluded_ids))


@dataclass(frozen=True)
class ServiceSeason:
    season: int
    service_days: int
    value: float


def account_control_path(opening_days: int | None, seasons: list[ServiceSeason], *, terminal=False):
    """Account a GIVEN service path, not forecast one from expected PA.

    Includes the entire season that reaches six years. A terminal path (known
    career end) has no tail; an incomplete living path has an unknown tail, not 0.
    This is pre-statutory-FA production across organizations, not contract value.
    """
    if opening_days is not None and (not isinstance(opening_days, int) or opening_days < 0):
        raise ValueError('Invalid opening service')
    if [s.season for s in seasons] != sorted({s.season for s in seasons}):
        raise ValueError('Seasons must be unique and increasing')
    if seasons and [s.season for s in seasons] != list(range(seasons[0].season, seasons[-1].season+1)):
        raise ValueError('Missing calendar seasons cannot be silently skipped')
    for s in seasons:
        if not isinstance(s.service_days, int) or not 0 <= s.service_days <= SERVICE_DAYS_PER_YEAR:
            raise ValueError('Annual service must be an integer from 0 to 172')
        if not math.isfinite(s.value):
            raise ValueError('Value must be finite')
    if opening_days is None:
        return {'observed_window_value': None, 'full_control_value': None,
                'exhaustion_year': None, 'tail_unresolved': True, 'status': 'unknown_opening_service'}
    threshold = SERVICE_DAYS_PER_YEAR*FREE_AGENCY_SERVICE_YEARS
    balance, value, exhausted = opening_days, 0., None
    already = balance >= threshold
    if not already:
        for s in seasons:
            if balance >= threshold:
                break
            value += s.value
            balance += s.service_days
            if balance >= threshold:
                exhausted = s.season
    complete = already or exhausted is not None or terminal
    return {'observed_window_value': value, 'full_control_value': value if complete else None,
            'exhaustion_year': exhausted, 'tail_unresolved': not complete,
            'status': 'already_statutorily_eligible' if already else 'complete_given_path' if complete else 'unresolved_tail'}
