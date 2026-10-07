"""Parse public historical table data without executing HTML or changing metrics."""
from decimal import Decimal
import json
import math
import re

POSITIONS={'1B':3,'2B':4,'3B':5,'SS':6,'LF':7,'CF':8,'RF':9}


def outs_from_baseball_innings(value):
    d=Decimal(str(value));whole=int(d);part=(d-whole)*10
    if d<0 or part not in (0,1,2):
        raise ValueError(f'Invalid baseball innings: {value}')
    return whole*3+int(part)


def decode(text, year):
    if not 2009<=year<=2021:raise ValueError('Outside contracted older source years')
    match=re.search(r'<script\b[^>]*\bid=["\x27]__NEXT_DATA__["\x27][^>]*>(.*?)</script>',text,re.S)
    if not match:raise ValueError('No public dehydrated table found; do not bypass source protection')
    page=json.loads(match[1])['props']['pageProps'];context=page['qsContext']
    if int(context['season'])!=year or int(context['season1'])!=year or context['stats']!='fld' or str(context['qual'])!='0':
        raise ValueError('Unexpected source season or qualification')
    matches=[q for q in page['dehydratedState']['queries'] if q['queryKey'][0]=='leaders/major-league/data']
    if len(matches)!=1:raise ValueError('Nonunique public fielding table')
    query=matches[0]['queryKey'][1];body=matches[0]['state']['data'];rows=body['data']
    if query['season']!=year or query['season1']!=year or query['stats']!='fld' or str(query['qual'])!='0':
        raise ValueError('Returned query differs from requested single-season source')
    if len(rows)!=body['totalCount']:raise ValueError('Incomplete pagination; do not use a qualified/top-page subset')
    if not rows:raise ValueError('Empty historical table is not measured zero defense')
    for row in rows:
        if row['Season']!=year or row['SeasonMin']!=year or row['SeasonMax']!=year:
            raise ValueError('Unexpected season inside source rows')
    return rows,dict(request_context=context,observed_query=query,total_count=body['totalCount'],status=body['status'],
        date_range=body.get('dateRange'),date_range_season=body.get('dateRangeSeason'))


def normalize(row):
    pos=POSITIONS.get(row['Position'])
    if pos is None:return None
    pid=row.get('xMLBAMID');outs=outs_from_baseball_innings(row['Inn'])
    if pid is None or int(pid)<=0:raise ValueError('Missing MLBAM identity; do not join on names')
    decimal=row.get('TInn')
    decimal_valid=decimal is not None and math.isfinite(decimal) and abs(3*decimal-outs)<.001
    rng=row.get('RngR');error=row.get('ErrR');components=[row.get(c) for c in ('ARM','DPR','RngR','ErrR')]
    if any(c is not None and not math.isfinite(c) for c in components):raise ValueError('Nonfinite fielding credit')
    total=row.get('UZR');gap=sum(c or 0 for c in components)-total if total is not None else None
    # Accounting nulls can add as zero; they cannot supply measured conversion skill.
    converted=rng+error if rng is not None and error is not None and outs>0 else None
    return dict(season=row['Season'],player_id=int(pid),fangraphs_id=int(row['playerid']),player_name=row['PlayerName'],
        position=pos,source_position=row['Position'],source_baseball_innings=row['Inn'],source_decimal_innings=decimal,
        fielding_outs=outs,decimal_innings_check=decimal_valid,RngR=rng,ErrR=error,UZR=total,
        older_conversion_runs=converted,older_conversion_rate=1500*converted/outs if converted is not None else None,
        component_sum_gap=gap,ARM=row.get('ARM'),DPR=row.get('DPR'),DRS=row.get('DRS'),rPM=row.get('rPM'),
        BIZ=row.get('BIZ'),Plays=row.get('Plays'),OOZ=row.get('OOZ'),raw_team_id=row.get('teamid'))
