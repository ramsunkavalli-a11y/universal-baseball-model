from datetime import date
import polars as pl
from universal_baseball.hitter_current_control import service_events, service_openings
from universal_baseball.hitter_current_control import service_bounds, resolve_selection_option_pairs
from universal_baseball.control_events import OPENING_CONTROL_STATE_SCHEMA
from universal_baseball.roster_entry_source import ROSTER_ENTRY_SCHEMA
from universal_baseball.rights_transactions import RIGHTS_TRANSACTION_SCHEMA


def tx(tid,text,code='SC',day=date(2026,3,1)):
    return pl.DataFrame([dict(as_of_date=date(2026,10,9),transaction_id=1,player_id=1,
        player_name='One',transaction_date=day,effective_date=day,resolution_date=None,
        type_code=code,type_description='',from_team_id=None,to_team_id=tid,
        description=text,source_snapshot_id='source')],schema=RIGHTS_TRANSACTION_SCHEMA)


def test_allstar_activation_does_not_end_mlb_il_service():
    event=service_events(tx(159,'American League All-Stars activated One from the 10-day injured list.'),{147}).row(0,named=True)
    assert event['action']=='preserve_state'


def test_mlb_activation_and_paid_list_are_retained():
    event=service_events(tx(147,'New York Yankees activated One from the 10-day injured list.'),{147}).row(0,named=True)
    assert event['target_state']=='mlb_active'
    event=service_events(tx(147,'New York Yankees placed One on the bereavement list.'),{147}).row(0,named=True)
    assert event['target_state']=='mlb_service_list'


def test_minor_activation_does_not_erase_option():
    event=service_events(tx(105,'Sacramento activated One.'),{137}).row(0,named=True)
    assert event['action']=='preserve_state'


def test_election_closes_service_not_generic_designation():
    assert service_events(tx(147,'One elected free agency.','DFA'),{147})['action'][0]=='close_state'
    assert service_events(tx(147,'Club designated One for assignment.','DFA'),{147})['action'][0]=='review'


def test_old_selected_contract_can_restore_lost_trade_terminal_opening():
    events=service_events(tx(137,'Club selected the contract of One.','SE',date(2023,5,19)),{137})
    openings,trace=service_openings(pl.DataFrame(schema=OPENING_CONTROL_STATE_SCHEMA),events,
        pl.DataFrame(schema=ROSTER_ENTRY_SCHEMA),2026,date(2026,3,25))
    assert openings['roster_state'][0]=='mlb_active'
    assert trace[0]['event_date']==date(2023,5,19)


def test_brief_unknown_list_can_leave_full_service_certain():
    spans=[dict(start_date=date(2026,3,25),end_date=date(2026,9,27),roster_state='mlb_active')]
    events=[dict(event_date=date(2026,8,17),action='review',target_state=None),
            dict(event_date=date(2026,8,20),action='set_state',target_state='mlb_active')]
    assert service_bounds(spans,events,date(2026,3,25),date(2026,9,27),True)==(172,172,3)


def test_unknown_opening_cannot_be_zero_service():
    assert service_bounds([],[],date(2026,3,25),date(2026,3,30),False)==(0,6,6)


def test_select_then_option_does_not_require_ID_order():
    source=pl.concat([tx(137,'Club selected One.','SE'),tx(137,'Club optioned One.','OPT').with_columns(pl.lit(2,dtype=pl.Int64).alias('transaction_id'))])
    events=resolve_selection_option_pairs(service_events(source,{137}),source)
    assert events['action'].to_list()==['preserve_state','set_state']
    assert events['target_state'][1]=='minors_optioned'
