"""Preserve incomplete native adjustment measurement separately from valid zero."""
from universal_baseball.arm_receiving_source import normalize_arm, integer_count


def arm_record(raw, native, year):
    if raw['fielder_runs'] is not None:
        result=normalize_arm(raw,native,year)
        result['adjustment_measured']=True
        return result
    assert raw['start_year']==raw['end_year']==raw['timeframe']==year
    assert raw['entity_code']=='Fld'
    assert all(raw['fielder_runs_'+k] is None for k in ('swipe','snipe','freeze'))
    n=integer_count(raw['n_opp_xb']);attempts=integer_count(raw['n_att_xb'])
    outs=integer_count(raw['n_out']);safe=integer_count(raw['n_safe'])
    assert n>0 and attempts<=n and outs+safe==attempts
    of=sum(r['native_outs'] for r in native if r['position'] in (7,8,9))
    other=sum(r['native_outs'] for r in native if r['position'] not in (7,8,9))
    values=[r['arm_runs'] for r in native if r['arm_runs'] is not None]
    return dict(season=year,player_id=int(raw['entity_id']),player_name=raw['entity_name'],
        kind='arm',opportunities=n,attempts=attempts,outs=outs,safe=safe,holds=n-attempts,
        runs=None,runs_per_100=None,native_runs=sum(values) if values else None,
        native_match=False,adjustment_measured=False,
        non_outfield_arm_runs=sum(r['arm_runs'] for r in native
            if r['position'] not in (7,8,9) and r['arm_runs'] is not None),
        of_outs=of,other_outs=other,scope='outfield_only_exposure' if of and not other else (
            'mixed_position_exposure' if of else 'non_outfield_exposure'),
        all_position_quality_valid=False,isolated_outfield_quality_valid=False,numerator_gap=None)
