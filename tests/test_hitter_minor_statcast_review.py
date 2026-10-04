from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from finalize_hitter_minor_statcast_source import classifications


def cases():
    rows=[]
    def case(y,g,p,play,residual=-1):
        return dict(season=y,game_pk=g,player_id=p,contact_residual=residual,
            expected_contact_count=1,backbone_boundary_matches_current_feed=True,plays=[play])
    def play(description,event='field_out'):
        return dict(at_bat_number=1,official_event=event,official_description=description,
            source_rows=[],inplay_pitch_events=[],hit_data_events=[])
    for i in range(13):rows.append(case(2021,100+i,100+i,play('Batter out on batter interference.')))
    for i in range(7):rows.append(case(2021,200+i,200+i,play('Batter flies out to right fielder.')))
    for y,g,p,pa,pitch,ev,la in [(2022,665032,621453,32,4,'81.1','-23'),
        (2024,760455,694200,78,1,None,None),(2024,760508,701296,8,3,'91.1','8')]:
        q=play('Batter makes physical contact.');q['at_bat_number']=pa
        q['source_rows']=[dict(events=None,type='S',pitch_number=str(pitch),launch_speed=ev,launch_angle=la)]
        q['inplay_pitch_events']=[dict(pitchNumber=pitch,hitData=dict(launchSpeed=float(ev) if ev else None,launchAngle=float(la) if la else None))]
        rows.append(case(y,g,p,q))
    q=play('Taylor Jones strikes out (foul).','strikeout');q['source_rows']=[dict(type='X')]
    rows.append(case(2023,721872,622100,q,1))
    return dict(cases=rows)


def test_missing_contact_not_inferred_as_measured_or_interference():
    result,counts=classifications(cases())
    assert counts['physical_contact_missing_pitch_evidence']==7
    assert counts['noncontact_batter_interference_AB']==13
    assert counts['official_terminal_metadata_repair']==3
    assert counts['noncontact_strikeout_mislabeled_inplay']==1


def test_metadata_repair_requires_exact_same_official_pitch_and_values():
    r=cases();r['cases'][20]['plays'][0]['inplay_pitch_events'][0]['pitchNumber']=99
    with pytest.raises(AssertionError):classifications(r)
    r=cases();r['cases'][20]['plays'][0]['inplay_pitch_events'][0]['hitData']['launchSpeed']=120.
    with pytest.raises(AssertionError):classifications(r)


def test_noncontact_interference_cannot_hide_physical_pitch():
    r=deepcopy(cases());r['cases'][0]['plays'][0]['inplay_pitch_events']=[dict(pitchNumber=1)]
    with pytest.raises(AssertionError):classifications(r)
