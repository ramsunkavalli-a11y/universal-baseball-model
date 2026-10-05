"""Preserve old timing provenance and consistently derive corrected timing."""
from datetime import date
import numpy as np
from .employment_comparison import FLAGS, corrected_frame


def timing(information_day, latest_day):
    now=date.fromisoformat(information_day)
    if latest_day is None:return dict(employment_evidence_unknown=1.,employment_evidence_age_years=0.)
    age=(now-date.fromisoformat(latest_day)).days
    if age<0:raise ValueError('Future employment date')
    return dict(employment_evidence_unknown=0.,employment_evidence_age_years=min(age,3650)/365)


def complete_frame(frame, indicators, dates):
    import polars as pl
    n=corrected_frame(frame,indicators)
    j=n.join(dates,on=['origin_year','player_id'],how='left',suffix='_timing',validate='1:1')
    if j['information_date'].null_count() or not (j['information_date']==j['ctx_information_date']).all():
        raise ValueError('Missing or mismatched timing origin')
    for field in ['employment_evidence_unknown','employment_evidence_age_years']:
        if not np.array_equal(frame[field].to_numpy(),j['old_'+field].to_numpy()):
            raise ValueError('Old timing input fails source reconstruction')
        j=j.with_columns(pl.col('new_'+field).cast(frame.schema[field]).alias(field))
    j=j.select(frame.columns)
    unchanged=[c for c in frame.columns if c not in {*FLAGS,'signed_first_team_work',
        'employment_evidence_unknown','employment_evidence_age_years'}]
    if not frame.select(unchanged).equals(j.select(unchanged)):raise ValueError('Changed unrelated inputs')
    return j
