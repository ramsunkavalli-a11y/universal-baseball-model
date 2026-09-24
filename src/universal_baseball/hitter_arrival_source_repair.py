"""Versioned historical source repairs; archived panels remain immutable."""
from datetime import date
import polars as pl

COHORTS = ['prior_debut', 'prospect', 'minor_returner', 'recent_debut']
FEATURES = [f'league_{name}_lag{k}' for k in range(3)
            for name in ('mexican_pa_share', 'known_pa_share')]


def census_rows(payload, season):
    if not 1960 <= season <= 2025:
        raise ValueError('Unsupported or protected census')
    people = payload.get('people')
    if not isinstance(people, list) or not people:
        raise ValueError('Empty census')
    rows = []
    for person in people:
        debut = date.fromisoformat(person['mlbDebutDate'][:10])
        if debut > date(season, 12, 31):
            raise ValueError('Future debut in historical census')
        rows.append({'player_id': int(person['id']), 'mlb_debut_date': debut})
    f = pl.DataFrame(rows)
    if f['player_id'].n_unique() != f.height:
        raise ValueError('Duplicate census identity')
    return f


def corrected_cohorts(panel, debuts):
    if debuts['player_id'].n_unique() != debuts.height:
        raise ValueError('Duplicate debut identity')
    if debuts['mlb_debut_date'].max() > date(2025, 12, 31):
        raise ValueError('Protected debut')
    q = panel.drop([c for c in COHORTS if c in panel.columns]).join(
        debuts.select('player_id', pl.col('mlb_debut_date').dt.year().alias('_debut')),
        on='player_id', how='left', validate='m:1', maintain_order='left')
    q = q.with_columns((pl.col('_debut') <= pl.col('origin_year')).fill_null(False).alias('prior_debut'))
    minors = pl.col('stage').is_in(['Upper minors', 'Lower minors'])
    return q.with_columns(
        (minors & ~pl.col('prior_debut')).alias('prospect'),
        (minors & pl.col('prior_debut')).alias('minor_returner'),
        (pl.col('prior_debut') & (pl.col('_debut') >= pl.col('origin_year')-1)).fill_null(False).alias('recent_debut'),
    ).drop('_debut')


def attach_leagues(panel, annual):
    if annual['season'].max() > 2024:
        raise ValueError('Future league context')
    q = panel
    for k in range(3):
        a = annual.select((pl.col('season')+k).alias('origin_year'), 'player_id',
             pl.col('mexican_pa_share').alias(FEATURES[2*k]),
             pl.col('known_pa_share').alias(FEATURES[2*k+1]))
        q = q.join(a, on=['origin_year', 'player_id'], how='left', validate='m:1', maintain_order='left')
        q = q.with_columns(pl.col(FEATURES[2*k+1]).fill_null(0.))
    return q


def attach_roster(panel, roster):
    if roster.filter(pl.col('as_of_date') != pl.date(pl.col('season'), 12, 31)).height:
        raise ValueError('Roster must be December 31')
    if set(panel['origin_year']) - set(roster['season']):
        raise ValueError('Incomplete roster seasons')
    r = roster.select(pl.col('season').alias('origin_year'), 'player_id',
                      pl.lit(1).cast(panel.schema['on_40man']).alias('on_40man'))
    return panel.drop('on_40man').join(r, on=['origin_year', 'player_id'], how='left',
        validate='m:1', maintain_order='left').with_columns(pl.col('on_40man').fill_null(0))
