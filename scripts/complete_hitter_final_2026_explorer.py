"""Add verified same-season minor-team affiliations to the first display build."""
import json
import math
from pathlib import Path
from universal_baseball.storage import sha256_file
from build_hitter_final_2026_explorer import ROOT,DEST,OLD,read,write

OUT=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'


def main():
    assert not OUT.exists()
    initial=read(DEST/'build-review.json')
    for p,h in initial['output_hashes'].items():assert sha256_file(Path(p))==h
    data=read(DEST/'data.json')
    paths=[OLD/f'affiliated-team-context/captures/teams-2025-sport-{s}.json' for s in [1,11,12,13,14,16]]
    teams={}
    for p in paths:
        payload=read(p);payload=payload.get('payload',payload)
        for t in payload['teams']:
            assert int(t['season'])==2025
            teams[t['id']]=dict(club=t['name'],org=t['name'] if t['sport']['id']==1 else t.get('parentOrgName') or 'Unknown organization')
    original=read(DEST/'data.json')
    changed=0
    for r in data['players']:
        if r['team_id'] in teams:
            new=teams[r['team_id']]
            changed+=int(r['org']!=new['org'] or r['club']!=new['club'])
            r.update(new)
    for a,b in zip(original['players'],data['players']):
        assert {k:v for k,v in a.items() if k not in ['org','club']}=={k:v for k,v in b.items() if k not in ['org','club']}
    assert any(r['org']=='San Francisco Giants' and r['stage']=='Upper minors' for r in data['players'])
    OUT.mkdir(parents=True)
    write(OUT/'data.json',data)
    (OUT/'index.html').write_text((DEST/'index.html').read_text(encoding='utf8'),encoding='utf8')
    write(OUT/'build-review.json',dict(status='same-origin_team_filter_complete_forecasts_unchanged',players=4030,affiliation_changes=changed,
        initial_unknown_organizations=initial['unknown_organizations'],unknown_organizations=sum(r['org']=='Unknown organization' for r in data['players']),
        correction='Initial display builder loaded only MLB team listing and left minor teams unknown; preserved that build, added existing 2025 all-level listings before browser opening. No forecast or score change.',
        team_filter='Captured 2025 source affiliation, not 2026 destinations or MLB roster projection.',UI_validation='pending',
        input_hashes={str(p):sha256_file(Path(p)) for p in [__file__,DEST/'data.json',DEST/'build-review.json',*paths]},
        output_hashes={str(p):sha256_file(p) for p in [OUT/'data.json',OUT/'index.html']}))
    print(json.dumps(dict(explorer=str(OUT),affiliation_changes=changed,unknown_organizations=sum(r['org']=='Unknown organization' for r in data['players']))),flush=True)


if __name__=='__main__':main()
