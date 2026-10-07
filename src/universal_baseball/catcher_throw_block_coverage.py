"""Preserve early throwing context discrepancies without inventing exposure."""
import math
from universal_baseball.catcher_throw_block import normalize,number


def qualified(kind,year,row,native):
    if kind!='throwing' or math.isclose(number(row,'caught_stealing_above_average'),
            number(row,'n_cs')-number(row,'sb_attempts')*number(row,'est_cs_pct'),abs_tol=1e-8):
        out=normalize(kind,year,row,native)
        out['context_identity_valid']=True
        return out
    assert year in (2016,2017), 'New context incompatibility needs a separate source review'
    assert int(row['start_year'])==year and int(row['end_year'])==year
    assert int(row['player_id'])==native['player_id'] and native['season']==year and native['position']==2
    n=number(row,'sb_attempts');num=number(row,'caught_stealing_above_average')
    assert n>0 and n.is_integer()
    assert math.isclose(.65*num,native['throwing_runs'],abs_tol=1e-8)
    assert math.isclose(.65*num,number(row,'catcher_stealing_runs'),abs_tol=1e-8)
    return dict(component=kind,season=year,player_id=int(row['player_id']),player_name=row['player_name'],
                opportunities=int(n),numerator=num,runs=.65*num,rate_per_1000=650*num/n,
                observed_events=number(row,'n_cs'),expected_events=n*number(row,'est_cs_pct'),
                native_outs=native['native_outs'],exposure_valid=native['exposure_valid'],measurement_valid=False,
                context_identity_valid=False,measurement_scope='native contribution measured; opportunity/expected identity inconsistent; talent unknown',
                source_context={k:row[k] for k in ('rate_cs','est_cs_pct','cs_aa_per_throw','pop_time','runner_distance_from_second','seasonal_runner_speed')})
