"""Pure, league-preserving source repair. Unknown controls never become zeros."""
import hashlib
import polars as pl
from universal_baseball.contact_identity_overlay import contact_identity_residuals
from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.hitter_value_panel import CONTACT_BINS, CONTACT_OUTCOMES
from universal_baseball.hitter_contact_transfer import bucket

KEY = ['game_pk', 'at_bat_index']
PHYSICAL_CODES = ['D', 'E', 'X']
FIELDS = ['season', 'level', 'league_id', 'game_date', 'game_type', 'batter',
          'pitcher', 'stand', 'p_throws', 'type', 'bb_type', 'hc_x', 'hc_y',
          'pa_description', 'terminal_outcome_group', 'terminal_outcome_status',
          'terminal_pitch_number']


def reconcile_contacts(frames):
    raw = pl.concat(frames, how='diagonal_relaxed')
    if not raw['season'].is_in([2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]).all():
        raise ValueError('Contact source outside the locked historical years')
    # Form the union before resolving values. A conflicting contact/noncontact
    # snapshot must not vanish merely because the selected row was not a contact.
    keys = raw.filter(pl.col('type').is_in(PHYSICAL_CODES)).select(KEY).unique()
    versions = raw.join(keys, on=KEY, how='semi')
    resolved = versions.group_by(KEY).agg(
        pl.len().alias('source_row_count'),
        pl.col('source_asset').unique().sort().alias('source_assets'),
        *[pl.when(pl.col(c).drop_nulls().n_unique() <= 1)
          .then(pl.col(c).drop_nulls().first()).otherwise(None).alias(c) for c in FIELDS],
        *[(pl.col(c).drop_nulls().n_unique() > 1).alias(c + '__conflict') for c in FIELDS],
    ).with_columns(pl.concat_list([
        pl.when(pl.col(c + '__conflict')).then(pl.lit(c)).otherwise(None) for c in FIELDS
    ]).list.drop_nulls().alias('conflicting_fields')).drop([c + '__conflict' for c in FIELDS])
    conflicts = resolved.filter(pl.col('conflicting_fields').list.len() > 0).sort(KEY)
    clean = resolved.filter(pl.col('conflicting_fields').list.len() == 0)
    # Only regular-season contacts enter the measurement. Null or conflicting
    # game metadata remains in quarantine, not silently eligible.
    unknown = clean.filter(pl.col('game_type').is_null() | pl.col('league_id').is_null())
    quarantine = pl.concat([conflicts, unknown], how='vertical_relaxed').sort(KEY)
    retained = clean.filter((pl.col('game_type') == 'R') & pl.col('league_id').is_not_null())
    retained = retained.rename({'batter': 'source_batter_id', 'terminal_pitch_number': 'pitch_number'}).sort(KEY)
    return retained, quarantine


def select_authority_games(contacts, controls, quarantine, sample_size=20):
    if controls.unique(['game_id', 'player_id']).height != len(controls):
        raise ValueError('Independent controls must be unique by game and player')
    reasons = {}
    def flag(games, reason):
        for game in games: reasons.setdefault(int(game), set()).add(reason)
    games = contacts.group_by('game_pk').agg(
        pl.col('season').first(), pl.col('league_id').first(), pl.col('level').first(),
        pl.col('league_id').n_unique().alias('league_count'), pl.len().alias('contacts'),
        pl.col('source_batter_id').is_null().any().alias('unknown_source_batter'),
    ).sort('game_pk')
    wanted = set(games['game_pk'].to_list())
    flag(wanted - set(controls['game_id'].to_list()), 'missing_game_controls')
    flag(games.filter(pl.col('unknown_source_batter'))['game_pk'], 'unknown_source_batter')
    flag(games.filter(pl.col('league_count') != 1)['game_pk'], 'conflicting_source_game_league')
    flag(set(quarantine['game_pk'].to_list()) & wanted, 'quarantined_source_sequence')
    uncertain = controls.filter(
        pl.col('expected_contact_count').is_null() | (pl.col('expected_contact_count') < 0)
        | pl.col('league_id').is_null() | pl.col('game_type').is_null()
        | (pl.col('game_type') != 'R') | pl.col('blocking_metadata_conflict')
        | pl.col('nonblocking_metadata_conflict'))
    flag(set(uncertain['game_id'].to_list()) & wanted, 'unresolved_or_uncertain_game_controls')
    leagues = controls.group_by('game_id').agg(pl.col('league_id').drop_nulls().n_unique().alias('control_league_count'),
        pl.col('league_id').drop_nulls().first().alias('control_league_id'))
    mismatch = games.join(leagues, left_on='game_pk', right_on='game_id', how='left').filter(
        (pl.col('control_league_count') != 1) | (pl.col('league_id') != pl.col('control_league_id')))
    flag(mismatch['game_pk'], 'control_source_league_disagreement')
    safe = contacts.filter(~pl.col('game_pk').is_in(list(reasons)))
    residuals = contact_identity_residuals(safe, controls)
    flag(residuals.filter(pl.col('contact_count_difference') != 0)['game_id'], 'player_contact_count_residual')
    game_rows = []
    for r in games.to_dicts():
        why = sorted(reasons.get(r['game_pk'], set()))
        r.update(triggered=bool(why), trigger_reasons=why,
                 sample_hash=hashlib.sha256(f"contact-identity-v1:{r['season']}:{r['league_id']}:{r['game_pk']}".encode()).hexdigest())
        game_rows.append(r)
    membership = pl.DataFrame(game_rows)
    sample = membership.filter(~pl.col('triggered')).sort(['season', 'league_id', 'sample_hash'])\
        .group_by(['season', 'league_id'], maintain_order=True).head(sample_size).select('game_pk')
    membership = membership.join(sample.with_columns(pl.lit(True).alias('unflagged_sample')), on='game_pk', how='left')\
        .with_columns(pl.col('unflagged_sample').fill_null(False)).sort('game_pk')
    return membership, residuals


def overlay_authority(contacts, membership, authority):
    if authority.unique(KEY).height != len(authority):
        raise ValueError('Official sequence identity is not unique')
    selected = membership.filter(pl.col('triggered') | pl.col('unflagged_sample'))['game_pk'].to_list()
    if set(authority['game_pk'].to_list()) != set(selected):
        raise ValueError('Official game set differs from locked membership')
    q = contacts.join(membership.select('game_pk', 'triggered', 'unflagged_sample'), on='game_pk', how='left', validate='m:1')
    if q['triggered'].null_count(): raise ValueError('Source game absent from locked membership')
    q = q.join(authority, on=KEY, how='left', validate='m:1')
    if q.filter((pl.col('triggered') | pl.col('unflagged_sample')) & pl.col('official_batter_id').is_null()).height:
        raise ValueError('Official identity missing for a selected source sequence')
    mismatches = q.filter(pl.col('unflagged_sample') & (pl.col('source_batter_id') != pl.col('official_batter_id')))
    result = q.with_columns(
        pl.when(pl.col('triggered')).then(pl.col('official_batter_id')).otherwise(pl.col('source_batter_id')).alias('batter_mlbam_id'),
        pl.when(pl.col('triggered')).then(pl.lit('official_exception_overlay')).otherwise(pl.lit('source_default')).alias('participant_authority'),
    )
    if result['batter_mlbam_id'].null_count(): raise ValueError('Unresolved final batter identity')
    # Do not silently repair unflagged audit mismatches: return them as failures.
    if not contacts.equals(result.select(contacts.columns)):
        raise AssertionError('Identity overlay changed a physical source field or membership')
    return result.drop('official_batter_id'), mismatches


def contact_cells(contacts):
    """Complete physical ledger plus screened raw cells, not learned adjustment."""
    projection = contacts.with_columns(
        pl.col('stand').alias('batter_side'), pl.col('pa_description').alias('result_description'),
        pl.lit('stored_terminal_narrative').alias('result_description_authority'))
    profile = classify_contact_profile_events(projection)
    events = contacts.join(profile.select(*KEY, 'core_bin', 'contact_profile_status'), on=KEY, how='left', validate='1:1')
    events = events.with_columns(
        pl.col('terminal_outcome_group').replace_strict({'OUT': 'OTHER_OUT', **{o: o for o in CONTACT_OUTCOMES}}, default=None).alias('canonical_outcome'),
        pl.struct('level', 'league_id').map_elements(lambda r: bucket(r['level'], r['league_id']), return_dtype=pl.String).alias('bucket'),
        pl.col('batter_mlbam_id').alias('player_id'),
    ).with_columns((pl.col('core_bin').is_not_null() & pl.col('canonical_outcome').is_not_null()).alias('cell_eligible'))
    grain = ['season', 'league_id', 'bucket', 'player_id']
    exposure = events.group_by(grain).agg(
        pl.len().alias('physical_contacts'), pl.col('cell_eligible').sum().alias('classified_contacts'),
        (pl.col('participant_authority') == 'official_exception_overlay').sum().alias('official_overlay_contacts'),
        (pl.col('terminal_outcome_group') == 'HR').sum().alias('raw_narrative_hr'),
        pl.col('game_pk').n_unique().alias('contact_games'),
    ).with_columns(pl.col(['physical_contacts', 'classified_contacts', 'official_overlay_contacts',
                           'raw_narrative_hr', 'contact_games']).cast(pl.Int64))
    counts = events.filter(pl.col('cell_eligible')).group_by(*grain, 'core_bin', 'canonical_outcome').len(name='count')
    wide = exposure
    for b in CONTACT_BINS:
        by_bin = counts.filter(pl.col('core_bin') == b).group_by(grain).agg(
            *[pl.col('count').filter(pl.col('canonical_outcome') == o).sum().alias(f'count_{b}___{o}') for o in CONTACT_OUTCOMES])
        wide = wide.join(by_bin, on=grain, how='left', validate='1:1')
    names = [f'count_{b}___{o}' for b in CONTACT_BINS for o in CONTACT_OUTCOMES]
    wide = wide.with_columns(pl.col(names).fill_null(0).cast(pl.Int64))
    if not (wide.select(pl.sum_horizontal(names).alias('n'))['n'] == wide['classified_contacts']).all():
        raise AssertionError('Ninety cells do not exhaust classified contacts')
    wide = wide.with_columns(
        *[((pl.col(c) + .5) / (pl.col('classified_contacts') + 45)).alias(c.replace('count_', 'rate_', 1)) for c in names],
        (pl.col('classified_contacts') > 0).alias('detailed_available'))
    return events, counts.sort(*grain, 'core_bin', 'canonical_outcome'), wide.sort(grain)


def measurement_changes(before, after):
    grain = ['season', 'league_id', 'bucket', 'player_id']
    totals = ['physical_contacts', 'classified_contacts', 'raw_narrative_hr']
    delta = before.select(*grain, *[pl.col(c).alias('before_' + c) for c in totals]).join(
        after.select(*grain, *[pl.col(c).alias('after_' + c) for c in totals]), on=grain, how='full', coalesce=True)
    # A lost contact is -1, not 2**32 - 1. Explicitly convert even if the
    # caller supplies a legacy unsigned Polars aggregation.
    delta = delta.with_columns(pl.col([s + c for s in ['before_', 'after_'] for c in totals]).fill_null(0).cast(pl.Int64))
    return delta.with_columns(*[(pl.col('after_' + c) - pl.col('before_' + c)).alias('delta_' + c) for c in totals])
