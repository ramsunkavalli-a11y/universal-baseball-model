import copy
import pytest

from universal_baseball.defense_role_logs import parse_logs, apply_dual_dh, position_totals


def payload(code='8', innings='8.2', started=1, game=123):
    abbreviations={'1':'P','8':'CF','10':'DH'}
    pos=dict(code=code, abbreviation=abbreviations[code])
    row=dict(player=dict(id=1), season='2024', sport=dict(id=1), date='2024-08-01',
        gameType='R', league=dict(id=103), team=dict(id=142), game=dict(gamePk=game),
        position=pos, stat=dict(position=pos, games=1, gamesPlayed=1, gamesStarted=started, innings=innings))
    return dict(stats=[dict(type=dict(displayName='gameLog'),group=dict(displayName='fielding'),splits=[row])])


def parse(p):
    return parse_logs(p,player_id=1,season=2024,sport_id=1,source_id='fixture')


def test_exact_outs_date_period_and_empty_unknown():
    row=parse(payload())[0]
    assert row['fielding_outs']==26 and row['period']=='August_onward'
    assert parse(dict(stats=[]))==[]
    p=payload();p['stats'][0]['splits'][0]['date']='2024-07-31'
    assert parse(p)[0]['period']=='before_August'


@pytest.mark.parametrize('field,value', [('sport',dict(id=11)),('player',dict(id=2)),
    ('season','2025'),('date','2025-04-01'),('gameType','S')])
def test_reject_wrong_scope(field,value):
    p=payload();p['stats'][0]['splits'][0][field]=value
    with pytest.raises(ValueError):parse(p)


def test_truncation_duplicate_and_missing_denominator():
    p=payload();p['stats'][0]['totalSplits']=2
    with pytest.raises(ValueError):parse(p)
    p=payload();p['stats'][0]['splits']*=2
    with pytest.raises(ValueError):parse(p)
    p=payload();del p['stats'][0]['splits'][0]['stat']['gamesStarted']
    with pytest.raises(KeyError):parse(p)


def test_dh_outs_and_bad_baseball_notation():
    with pytest.raises(ValueError):parse(payload('10','1.0'))
    with pytest.raises(ValueError):parse(payload(innings='8.3'))


def correction():
    return dict(player_id=1, season=2024, game_id=123, date='2024-08-01',certified=True,
                source_id='box-fixture', DH_evidence_basis='rule_5_11b_starting_pitcher_in_lineup')


def test_dated_rule_addition_once_and_no_pitcher_outs_as_dh():
    rows=parse(payload('1','6.0'))
    fixed=apply_dual_dh(rows,[correction()])
    dh=next(r for r in fixed if r['position_code']==10)
    assert dh['raw_starts']==0 and dh['reviewed_starts']==1 and dh['fielding_outs']==0
    assert dh['appearances']==0  # certified start, not an invented source appearance
    assert position_totals(fixed)[1,103,1]['fielding_outs']==18
    with pytest.raises(ValueError):apply_dual_dh(fixed,[correction()])
    with pytest.raises(ValueError):apply_dual_dh(rows,[correction(),correction()])
    bad=dict(correction(),date='2024-08-02')
    with pytest.raises(ValueError):apply_dual_dh(rows,[bad])


def test_regular_dual_appearance_and_negative_control():
    p=payload('1','6.0');p['stats'][0]['splits']+=payload('10','0.0',0)['stats'][0]['splits']
    rows=parse(p)
    fixed=apply_dual_dh(rows,[dict(correction(),DH_evidence_basis='boxscore_dual_appearance')])
    assert sum(r['reviewed_starts'] for r in fixed if r['position_code']==10)==1
    assert apply_dual_dh(rows,[dict(correction(),certified=False)])==rows
    p=payload('10','0.0',1)
    with pytest.raises(ValueError):apply_dual_dh(parse(p),[correction()])


def test_source_rows_unchanged():
    p=payload();old=copy.deepcopy(p);parse(p)
    assert p==old
