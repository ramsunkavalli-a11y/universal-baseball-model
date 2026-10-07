"""Native difficulty-adjusted measurements, preserving exact opportunities."""
import math


def number(row,key):
    value=float(row[key]);assert math.isfinite(value), (key,row[key])
    return value


def normalize(kind,year,row,native):
    assert kind in ('throwing','blocking') and 2016<=year<=2025
    assert int(row['start_year'])==year
    assert not row['end_year'] or int(row['end_year'])==year
    pid=int(row['player_id']);assert pid==native['player_id'] and native['season']==year and native['position']==2
    if kind=='throwing':
        n=number(row,'sb_attempts');num=number(row,'caught_stealing_above_average');factor=.65
        cs=number(row,'n_cs');expected=n*number(row,'est_cs_pct')
        assert 0<=cs<=n and 0<=expected<=n
        assert math.isclose(num,cs-expected,abs_tol=1e-8)
        assert math.isclose(number(row,'cs_aa_per_throw'),num/n,abs_tol=1e-8)
        assert math.isclose(number(row,'catcher_stealing_runs'),factor*num,abs_tol=1e-8)
        context={key:row[key] for key in ('rate_cs','est_cs_pct','pop_time','runner_distance_from_second','seasonal_runner_speed')}
    else:
        assert year>=2018
        n=number(row,'pitches');cs=number(row,'n_pbwp');expected=number(row,'x_pbwp');num=expected-cs;factor=.25
        assert 0<=cs<=n and 0<=expected<=n
        assert math.isclose(number(row,'blocks_above_average_per_game'),40*num/n,abs_tol=1e-8)
        assert math.isclose(sum(number(row,'diff_pbwp_'+s) for s in ('easy','medium','tough')),num,abs_tol=1e-8)
        assert math.isclose(sum(number(row,'freq_pbwp_'+s) for s in ('easy','medium','tough')),1.,abs_tol=1e-8)
        # CSV display columns are rounded. Use the exact expected-minus-actual
        # numerator; do not infer exact native runs from the rounded display.
        assert abs(number(row,'blocks_above_average')-num)<=.500001
        assert abs(number(row,'catcher_blocking_runs')-factor*num)<=.500001
        context={key:row[key] for key in ('freq_pbwp_easy','freq_pbwp_medium','freq_pbwp_tough','blocks_above_average','catcher_blocking_runs')}
    assert n>0 and n.is_integer()
    native_runs=native[kind+'_runs'];assert native_runs is not None
    assert math.isclose(factor*num,native_runs,abs_tol=1e-8), (kind,year,pid,factor*num,native_runs)
    return dict(component=kind,season=year,player_id=pid,player_name=row['player_name'],
                opportunities=int(n),numerator=num,runs=factor*num,rate_per_1000=1000*factor*num/n,
                observed_events=cs,expected_events=expected,native_outs=native['native_outs'],
                exposure_valid=native['exposure_valid'],measurement_valid=native['exposure_valid'] and native['native_outs']>0,
                measurement_scope='success given tracked attempts, not deterrence' if kind=='throwing' else 'difficulty-adjusted blocking chances, not framing pitches',
                source_context=context)
