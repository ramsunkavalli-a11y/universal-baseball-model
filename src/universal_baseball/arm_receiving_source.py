"""Opportunity and native-component checks; no model or future outcomes."""
import math

THROW_TYPES = ('on_target', 'low', 'high', 'scoop', 'wide', 'bounce')


def close(a, b):
    return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(a-b) <= 1e-8


def integer_count(value):
    assert isinstance(value, (int, float)) and math.isfinite(value)
    assert value >= 0 and int(value) == value
    return int(value)


def arm_metadata(meta, year, whole_team):
    assert 2016 <= year <= 2025
    assert meta['season_start'] == meta['season_end'] == year
    assert meta['game_type'] == 'Regular' and meta['entity_code'] == 'Fld'
    assert meta['is_team_type'] is False and meta['splitYears'] is False
    assert meta['tot_n'] == 1 and meta['target_base'] == meta['key_base_out'] == 'All'
    assert meta['team'] == '' and meta['with_team_only'] is whole_team


def receiving_metadata(meta, year):
    assert 2021 <= year <= 2025
    assert meta['type'] == 'fielder_3' and meta['gameType'] == ['R']
    assert meta['season'] == [str(year)] and meta['validSeasons'] == [year]
    assert meta['min'] == meta['minSplit'] == 1 and meta['splitYear'] == '1'
    assert meta['secondarySplit'] == ['year'] and not meta['validTeams']


def normalize_arm(raw, native, year):
    assert raw['start_year'] == raw['end_year'] == raw['timeframe'] == year
    assert raw['entity_code'] == 'Fld'
    n = integer_count(raw['n_opp_xb'])
    attempted = integer_count(raw['n_att_xb'])
    outs, safe = integer_count(raw['n_out']), integer_count(raw['n_safe'])
    assert n > 0 and attempted <= n and outs + safe == attempted
    assert close(raw['rate_att_xb'], attempted/n)
    runs = float(raw['fielder_runs'])
    assert close(runs, sum(raw['fielder_runs_'+k] for k in ('swipe', 'snipe', 'freeze')))
    measured = [r['arm_runs'] for r in native if r['arm_runs'] is not None]
    native_runs = sum(measured) if measured else None
    native_match = native_runs is not None and close(runs, native_runs)
    non_of = sum(r['arm_runs'] for r in native
                 if r['position'] not in (7, 8, 9) and r['arm_runs'] is not None)
    of_outs = sum(r['native_outs'] for r in native if r['position'] in (7, 8, 9))
    other_outs = sum(r['native_outs'] for r in native if r['position'] not in (7, 8, 9))
    # All-position denominators cannot isolate OF skill if INF credit is present.
    scope = 'outfield_only_exposure' if of_outs and not other_outs else (
        'mixed_position_exposure' if of_outs else 'non_outfield_exposure')
    return dict(season=year, player_id=int(raw['entity_id']), player_name=raw['entity_name'],
                kind='arm', opportunities=n, attempts=attempted, outs=outs, safe=safe,
                holds=n-attempted, runs=runs, runs_per_100=100*runs/n,
                native_runs=native_runs, native_match=native_match,
                non_outfield_arm_runs=non_of, of_outs=of_outs, other_outs=other_outs,
                scope=scope, all_position_quality_valid=native_match,
                isolated_outfield_quality_valid=native_match and scope == 'outfield_only_exposure',
                numerator_gap=None if native_runs is None else runs-native_runs)


def normalize_receiving(raw, native, year):
    assert int(raw['year']) == year
    n, outs = integer_count(raw['n_plays']), integer_count(raw['n_outs'])
    assert n > 0 and outs <= n and 0 <= raw['avg_expected_rate_out'] <= 1
    assert n == sum(integer_count(raw['n_'+k]) for k in THROW_TYPES)
    assert outs == sum(integer_count(raw['outs_'+k]) for k in THROW_TYPES)
    oaa = float(raw['total_oaa'])
    expected = n*raw['avg_expected_rate_out']
    assert close(oaa, outs-expected)
    assert close(oaa, sum(raw['oaa_'+k] for k in THROW_TYPES))
    assert close(raw['avg_oaa'], oaa/n)
    # Empirical native conversion, independently checked for every source row.
    runs = .75*oaa
    measured = [r['fielding_runs_prevented_on_rec1b'] for r in native
                if r['position'] == 3 and r['fielding_runs_prevented_on_rec1b'] is not None]
    native_runs = sum(measured) if measured else None
    match = native_runs is not None and close(runs, native_runs)
    return dict(season=year, player_id=int(raw['player_id']), player_name=raw['name'],
                kind='receiving', opportunities=n, outs=outs, expected_outs=expected,
                oaa=oaa, runs=runs, runs_per_100=100*runs/n,
                native_runs=native_runs, native_match=match, quality_valid=match,
                numerator_gap=None if native_runs is None else runs-native_runs)
