"""Explicit historical source metadata inspection, no scoring or 2026 access."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re

import requests

from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/arm-receiving-v6'


def capture(item):
    kind,year=item;assert kind in ('arm','receiving') and year in (2022,2025)
    if kind=='arm':
        endpoint='baserunning';params=dict(type='Fld',game_type='Regular',n=1,season_start=year,season_end=year,split='no',team='',with_team_only=1)
    else:
        endpoint='first-base-scoops-receiving';params={'type':'fielder_3','season[]':year,'splitYear':1,'min':1,'minSplit':1,'gameType[]':'R'}
    path=OUT/f'{kind}-{year}.response'
    if not path.exists():
        r=requests.get('https://baseballsavant.mlb.com/leaderboard/'+endpoint,params=params,timeout=45);r.raise_for_status();path.write_bytes(r.content)
    text=path.read_text(encoding='utf8')
    names=sorted(set(re.findall(r'(?<![\w$.])(?:const|var|let)\s+(\w+)\s*=',text)))
    decoded={};samples={}
    for name in names:
        try:value=embedded(text,name)
        except AssertionError:continue
        if isinstance(value,dict):decoded[name]=value
        elif isinstance(value,list) and value and isinstance(value[0],dict):samples[name]=dict(rows=len(value),sample=value[:1])
    report=dict(kind=kind,year=year,requested=params,path=str(path),sha256=sha256_file(path),variables=names,
                metadata=decoded,samples=samples,model_fit=False)
    p=OUT/f'{kind}-{year}-inspection.json';assert not p.exists();save(p,report)
    print(json.dumps(report,indent=2)[:6000])
    return report


def main():
    protections();OUT.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:reports=list(pool.map(capture,[(k,y) for k in ('arm','receiving') for y in (2022,2025)]))
    p=OUT/'pilot-inspection.json';assert not p.exists();save(p,dict(captures=reports,no_2026_outcomes=True,model_fit=False))


if __name__=='__main__':main()
