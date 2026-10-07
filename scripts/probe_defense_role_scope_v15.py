"""Preserve failed plural-sport probe; check three explicit historical routes."""
from capture_defense_role_v15 import ROOT, OUT, capture, check_seal, receipt
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file


def main():
    protections(); check_seal()
    assert not (OUT/'scope-amendment-seal.json').exists()
    receipt('scope-amendment-seal.json', dict(no_fits=True, hashes={str(p):sha256_file(p) for p in
        [ROOT/'docs/defense-role-v15-scope-amendment.md', ROOT/'scripts/probe_defense_role_scope_v15.py']}))
    routes = [
        ('people/805811/stats?stats=gameLog&group=fielding&season=2024&gameType=R&sportId=11', 'probe-Eldridge-2024-singular-11'),
        ('people/805811?hydrate=stats(group=fielding,type=gameLog,season=2024,gameType=R,sportId=11)', 'probe-Eldridge-2024-hydrate-singular-11'),
        ('people/805811?hydrate=stats(group=fielding,type=gameLog,season=2024,gameType=R,sportIds=1,11,12,13,14,16)', 'probe-Eldridge-2024-hydrate-plural')]
    for endpoint,name in routes:
        data=capture(endpoint,name)
        groups=data.get('stats',[]) if 'stats' in data else data.get('people',[{}])[0].get('stats',[])
        rows=[r for g in groups for r in g.get('splits',[])]
        print(name, len(rows), sorted({r.get('sport',{}).get('id') for r in rows}), flush=True)
        if rows:print(rows[0],flush=True)
    protections()


if __name__=='__main__':main()
