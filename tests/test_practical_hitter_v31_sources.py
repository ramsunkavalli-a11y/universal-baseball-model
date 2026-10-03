import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('v31_source',Path(__file__).parents[1]/'scripts/prepare_practical_hitter_v31.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_mexican_triple_a_is_separate():
    assert m.bucket({'league_id':125,'sport_id':11})=='MEX'
    assert m.bucket({'league_id':117,'sport_id':11})=='AAA'

def test_dsl_and_complex_are_distinct():
    assert m.bucket({'league_id':130,'sport_id':16})=='DSL'
    assert m.bucket({'league_id':121,'sport_id':16})=='RK121'
    assert m.bucket({'league_id':120,'sport_id':16})=='RK120'

def test_advanced_rookie_not_modern_single_a():
    assert m.bucket({'league_id':128,'sport_id':16})=='RK128'
    assert m.bucket({'league_id':123,'sport_id':14})=='A'
