"""Source-only repair; preserve V70's initial audit and all existing forecasts."""
from datetime import date
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
import audit_hitter_employment_v70 as e

original_event=e.event
original_state=e.state
MLB_TEAMS=set(pl.read_parquet(e.ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet')['team_id'])


def event(raw):
    result=original_event(raw)
    if result is None and raw.get('typeDesc')=='Status Change' and ' activated ' in raw.get('description','').lower() and raw.get('toTeam',{}).get('id') in MLB_TEAMS:
        result=dict(transaction_id=raw['id'],player_id=raw['person']['id'],status='attached',type_code=raw.get('typeCode'),
            type_description=raw.get('typeDesc'),description=raw.get('description'),recorded_date=raw.get('date'),
            effective_date=raw.get('effectiveDate'),resolution_date=raw.get('resolutionDate'))
    if result is None:return None
    if not raw.get('date'):raise ValueError('Employment announcement lacks record date')
    result['available_date']=date.fromisoformat(raw['date'][:10]).isoformat()
    result['date_qualification']='Recorded announcement date, not independently verified first-publication vintage.'
    return result


def state(records,year):
    result=original_state(records,year)
    if result['recorded_open_fa']==1 and result['latest_employment_date'][:4]!=str(year):
        result['recorded_open_fa']=-1
    return result


def main():
    e.OUT=e.ROOT/'reports/generated/hitter-employment-v70b';e.event=event;e.state=state
    e.main()
    r=e.prior.read(e.OUT/'audit.json');paths=[Path(__file__),e.ROOT/'docs/hitter-employment-v70-date-repair.md',e.ROOT/'reports/generated/hitter-employment-v70/audit.json']
    r['source_hashes'].update({str(p):sha256_file(p) for p in paths})
    r.update(date_rule='Recorded dates for explicit employment events; other fields retained, publication vintage qualified.',
        old_unresolved_FA='Unknown after its recorded year',medical_date_rules_changed=False)
    e.write('audit.json',r)


if __name__=='__main__':main()
