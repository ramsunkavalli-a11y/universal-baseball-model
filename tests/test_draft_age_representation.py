import polars as pl
from universal_baseball.draft_age_representation import materialize


def test_known_age_is_cutoff_only_and_unknown_does_not_become_college():
    rows=[]
    for known,unknown,age,year,draft in [(1,0,24,2024,2021),(1,1,27,2024,2024),(0,0,19,2024,None)]:
        q=dict(draft_known=known,age_unknown=unknown,age=age,origin_year=year,
               draft_year=draft,draft_rank_low_exposure=.4,next_pa=777)
        q.update({f'{b}_{k}_pa':0 for b in ['MLB','AAA','AA','Aplus','A','Aminus','DSL',
                    'RK120','RK121','RK124','RK128','RK134','RKother','MEX'] for k in range(3)})
        rows.append(q)
    f=pl.DataFrame(rows);out=materialize(f)
    assert out['draft_age_known'].to_list()==[1,0,0]
    assert out['draft_age_proxy'].to_list()==[21,None,None]
    assert out['draft_age_centered'].to_list()==[0,0,0]
    alt=materialize(f.with_columns(pl.lit(0).alias('next_pa')))
    assert out.select('draft_age_known','draft_age_proxy','draft_age_centered','draft_age_low_exposure').equals(
        alt.select('draft_age_known','draft_age_proxy','draft_age_centered','draft_age_low_exposure'))
