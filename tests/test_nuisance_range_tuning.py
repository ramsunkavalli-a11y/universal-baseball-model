from universal_baseball.nuisance_range_tuning import plans


def row(pid,y,value=1):
    return dict(player_id=pid,origin_year=y,position=6,window_end=y+3,quality_rate=value)


def test_nuisance_people_cannot_enter_training_or_penalty_validation():
    pool=[row(pid,y) for y in range(2014,2020) for pid in range(100)]
    result=plans(pool,2022,[0,1])
    for p in result:
        for key in p['audit']['training_keys']+p['audit']['test_keys']:assert key[1]%5 not in (0,1)
        assert all(k[1]%5!=p['validation_fold'] for k in p['audit']['training_keys'])


def test_changing_held_person_labels_cannot_change_nuisance_penalty_cells():
    pool=[row(pid,y) for y in range(2014,2020) for pid in range(100)]
    changed=[dict(r,quality_rate=None if r['player_id']%5 in (0,1) else r['quality_rate']) for r in pool]
    assert plans(pool,2022,[0,1])==plans(changed,2022,[0,1])


def test_cutoffs_retain_whole_future_window():
    pool=[row(pid,y) for y in range(2014,2025) for pid in range(100)]
    result=plans(pool,2022,[0,1])
    assert {p['validation_origin'] for p in result}=={2018,2019}
    assert all(k[0]+3<=p['validation_origin'] for p in result for k in p['audit']['training_keys'])
    assert all(k[0]+3<=2022 for p in result for k in p['audit']['test_keys'])
