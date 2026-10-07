"""Dated source pilot: inspect framing opportunities, no fitting or 2026 data."""
import json
import argparse
from pathlib import Path
import re

import polars as pl
import requests

from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file
from source_defensive_positions_v2 import embedded

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/generated/catcher-native-opportunity-v3"


def capture(year, all_pitches=False):
    assert year in (2016,2019,2025)
    OUT.mkdir(parents=True,exist_ok=True)
    suffix="-all" if all_pitches else ""
    path=OUT/f"framing-{year}{suffix}.response"
    params=dict(type="catcher",seasonStart=year,seasonEnd=year,team="",min=1,
                sortColumn="rv_tot",sortDirection="desc")
    if all_pitches:
        params["minPitches"]=1
    if not path.exists():
        r=requests.get("https://baseballsavant.mlb.com/leaderboard/catcher-framing",params=params,timeout=45)
        r.raise_for_status()
        path.write_bytes(r.content)
    content=path.read_text(encoding="utf8")
    # Inspect year metadata before any metric payload. If unsupported, don't
    # parse potentially default-season measurements.
    variables=re.findall(r"(?<![\w$.])(?:const|var|let)\s+(\w+)\s*=",content)
    found={}
    for name in ("serverParams","params","searchParams"):
        try:
            value=embedded(content,name)
        except AssertionError:
            continue
        if isinstance(value,dict):
            found[name]=value
    report=dict(year=year,path=str(path),sha256=sha256_file(path),requested=params,
                metadata=found,variable_names=sorted(set(variables)),measurements_parsed=False)
    save(OUT/f"inspection-{year}{suffix}.json",report)
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--all-pitches",action="store_true")
    args=parser.parse_args()
    protections()
    for year in (2016,2019,2025):
        capture(year,args.all_pitches)
