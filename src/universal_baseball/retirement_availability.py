"""Reversible, dated reported-retirement state; no guessed injury or career end."""
from datetime import date

RETURN_CODES={'SFA','CLW','TR','R5','PUR','CP','CU','SE'}


def known_date(raw):
    dates=[date.fromisoformat(str(raw[k])[:10]) for k in ('date','effectiveDate','resolutionDate') if raw.get(k)]
    if not dates:raise ValueError('Undated retirement/context transaction')
    return max(dates)


def events(captures,maximum):
    out={}
    for year,path,payload in captures:
        for raw in payload['transactions']:
            # Never inspect a future description before the date gate.
            known=known_date(raw)
            if known>maximum:continue
            pid=(raw.get('person') or {}).get('id');tid=raw.get('id')
            if pid is None or tid is None:continue
            code=raw.get('typeCode');text=raw.get('description') or '';lower=text.lower()
            kind='retired' if code=='RET' else 'return' if code in RETURN_CODES or (
                ('reinstated' in lower or 'activated' in lower) and ('retirement' in lower or 'retired list' in lower)) else None
            if kind is None:continue
            effective=date.fromisoformat(str(next(raw[k] for k in ('effectiveDate','resolutionDate','date') if raw.get(k)))[:10])
            key=(int(tid),int(pid),known,text)
            record=dict(transaction_id=int(tid),player_id=int(pid),known_date=known,event_date=effective,
                kind=kind,type_code=code,description=text,capture_year=year,source_path=str(path))
            if key in out and out[key]['event_date']!=effective:raise ValueError('Conflicting retirement transaction version')
            out[key]=record
    return list(out.values())


def state(records,cutoff):
    selected={}
    for r in records:
        if r['known_date']>cutoff:continue
        key=r['transaction_id'];old=selected.get(key)
        if old is None or old['known_date']<r['known_date']:selected[key]=r
        elif old['known_date']==r['known_date'] and old!=r:raise ValueError('Conflicting equal-date versions')
    ordered=sorted(selected.values(),key=lambda r:(r['event_date'],r['known_date'],r['transaction_id']))
    retirement=None;returned=None
    for r in ordered:
        if r['kind']=='retired':retirement=r;returned=None
        elif retirement is not None and r['kind']=='return':returned=r;retirement=None
    return dict(reported_retired=retirement is not None,retirement=retirement,return_evidence=returned)
