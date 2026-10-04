"""The source inventory must not finalize without all actual case reviews."""
import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('candidate_inventory',SCRIPTS/'audit_hitter_candidate_integration.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def fixture_review():
    return {'new_predictive_gain_claimed':False,'cases':[
        {'row_id':1,'source_interpretation':'dated source','forecast_interpretation':'replayed forecast',
         'support_and_peers_limit':'generic controls','disposition':'qualified'}]}


def test_complete_inventory_review():
    module.validate_manual_review([{'origin':{'row_id':1}}],fixture_review())


def test_missing_or_duplicate_review_is_rejected():
    review=fixture_review()
    with pytest.raises(ValueError,match='every saved case'):
        module.validate_manual_review([{'origin':{'row_id':2}}],review)
    review['cases']*=2
    with pytest.raises(ValueError,match='every saved case'):
        module.validate_manual_review([{'origin':{'row_id':1}}],review)


def test_empty_case_or_predictive_claim_is_rejected():
    review=fixture_review();review['cases'][0]['forecast_interpretation']=''
    with pytest.raises(ValueError,match='lacks actual'):
        module.validate_manual_review([{'origin':{'row_id':1}}],review)
    review=fixture_review();review['new_predictive_gain_claimed']=True
    with pytest.raises(ValueError,match='cannot establish'):
        module.validate_manual_review([{'origin':{'row_id':1}}],review)
