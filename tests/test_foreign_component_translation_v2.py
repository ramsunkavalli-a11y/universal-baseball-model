import numpy as np
import pytest

from universal_baseball.foreign_component_translation import References, profile
from universal_baseball.foreign_component_translation_v2 import fit, histories, pooled_source
from test_foreign_component_translation import row,pair,input_row


def test_identical_pool_at_calibration_and_prediction():
    rows=[row(1,2013),dict(row(1,2012),so=5),row(None,2012),row(None,2013),row(None,2014,'MLB')]
    h=histories(rows); refs=References(rows)
    x,n=pooled_source(1,'NPB',2013,h,refs,[])
    source=input_row(); source['origin_year']=2013
    for l in ['NPB','KBO']:
        for lag in range(3):
            a=source['foreign_history_counts'][f'{l}_{lag}']; a['season']=2013-lag
            a['player_identity_and_stat_observed']=(l=='NPB' and lag in [0,1])
            a['counts']=row(1,2013-lag,l) if lag==0 else dict(row(1,2013-lag,l),so=5)
    refs=References(rows+[row(None,2013,'MLB')])
    model=fit([],refs,2013,[],h)
    p=profile(source,model,refs)
    assert np.allclose(x,p['leagues'][0]['source_relative_clr'])
    assert n['observed_source_pa']==200 and n['observed_source_years']==[2012,2013]


def test_future_history_cannot_enter_calibration():
    rows=[row(),row(None),row(None,2014,'MLB'),row(1,2014)]
    refs=References(rows)
    a=fit([pair()],refs,2014,[],histories(rows))
    corrupt=[dict(row(1,2014),so=60),dict(row(1,2099),so=60)]
    b=fit([pair()],refs,2014,[],histories(rows[:3]+corrupt))
    assert a==b


def test_history_primary_reconciliation_and_older_evidence():
    rows=[row(),row(None),row(None,2014,'MLB'),row(None,2012),dict(row(1,2012),so=2)]
    refs=References(rows)
    a=fit([pair()],refs,2014,[],histories(rows))
    b=fit([pair()],refs,2014,[],histories(rows[:-1]))
    assert a['pairs'][0]['source_relative_clr']!=b['pairs'][0]['source_relative_clr']
    assert a['pairs'][0]['target_relative_clr']==b['pairs'][0]['target_relative_clr']
    assert a['pairs'][0]['weight']==b['pairs'][0]['weight']
    with pytest.raises(ValueError):fit([pair()],refs,2014,[],histories([dict(row(),so=19)]))
