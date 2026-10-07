"""Explicit small source-rounding allowance; preserve original parser behavior."""
import math
from universal_baseball.older_fielding_source import normalize


def normalized_with_precision(row):
    result=normalize(row)
    if result is None:return None
    decimal=result['source_decimal_innings']
    gap=3*decimal-result['fielding_outs'] if decimal is not None and math.isfinite(decimal) else None
    result['original_decimal_innings_check']=result['decimal_innings_check']
    result['decimal_innings_gap_outs']=gap
    result['decimal_innings_check']=gap is not None and abs(gap)<=.02
    if not result['decimal_innings_check']:raise ValueError('Decimal innings differ by more than documented source precision')
    if result['component_sum_gap'] is not None and abs(result['component_sum_gap'])>.001:
        raise ValueError('UZR component accounting exceeds documented source precision')
    return result
