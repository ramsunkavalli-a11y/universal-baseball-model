"""One documented repair: pool fallback exposures instead of erasing MLB history."""
import numpy as np
from universal_baseball.hitter_role_budget_v1 import keys,cell,supported,predict
from universal_baseball.hitter_role_budget_v1 import evidence as original_evidence
from universal_baseball.defense_repertoire import ROLES,normalized,family


def evidence(row,annual,dh_outs):
    result=original_evidence(row,annual,dh_outs)
    y,pid=row['origin_year'],row['player_id']
    past=[r for r in annual if r['player_id']==pid and y-2<=r['season']<=y]
    minor=[r for r in past if not r['is_mlb']]
    latest=max((r['season'] for r in minor),default=None)
    fallback=[r for r in past if (r['is_mlb'] and r['season']<y) or (not r['is_mlb'] and r['season']==latest)]
    vector=sum((.5**(y-r['season'])*np.array([r[f'outs_{p}'] for p in ROLES[:-1]]+[r['starts_10']*dh_outs],float)
                for r in fallback),np.zeros(9))
    if vector.sum()==0:
        vector=np.array([str(p)==str(row.get('source_position')) for p in ROLES],float)
    a=result['reliability']
    shares=normalized(a*normalized(result['current_vector'])+(1-a)*normalized(vector))
    role=ROLES[int(shares.argmax())] if shares.sum() else 0
    result.update(role_shares=shares.tolist(),role=role,family=family(role),fallback_vector=vector.tolist(),
                  fallback_kind='pooled_recent_exposure' if fallback else 'roster_or_unknown',
                  fallback_season=max((r['season'] for r in fallback),default=None),
                  fallback_sources=[dict(season=r['season'],is_mlb=r['is_mlb'],weight=.5**(y-r['season']),
                                         fielding_outs=sum(r[f'outs_{p}'] for p in ROLES[:-1]),DH_starts=r['starts_10']) for r in fallback],
                  unknown=not bool(shares.sum()))
    return result
