"""One reusable interface for reviewed defensive talent estimators.

Returns skill rates, never WAR. A downstream exposure model must supply actual
position-specific outs, received pitches or runner opportunities. Missing history
is a disclosed prior, not a measured average defender. No new age model is fitted.
"""
from collections import defaultdict
from universal_baseball.defense_reference_history import annual_references, history as range_history
from universal_baseball.defense_first_base_prior import reference, estimate
from universal_baseball.catcher_framing_baseline import history as framing_history
from universal_baseball.catcher_throw_block_baseline import history as catcher_history
from universal_baseball.arm_receiving_baseline import history as arm_history


class DefenseRates:
    def __init__(self, *, origin, native, framing, catcher, arm_receiving):
        if not isinstance(origin,int):raise ValueError('Integer origin required')
        self.origin=origin
        self.native=native
        self.by={k:defaultdict(list) for k in ('native','framing','catcher','other')}
        for kind,rows,keys in [('native',native,('season','player_id','position')),
                ('framing',framing,('season','player_id')),
                ('catcher',catcher,('season','player_id','component')),
                ('other',arm_receiving,('season','player_id','kind'))]:
            identities=set()
            for r in rows:
                if r['season']>origin:raise ValueError('Future defensive input')
                key=tuple(r[k] for k in keys)
                if key in identities:raise ValueError('Duplicate defensive input')
                identities.add(key);self.by[kind][r['player_id']].append(r)
        self.references=annual_references(native)
        self.first_base={fold:reference(native,origin,fold) for fold in range(5)}

    def player(self,player_id):
        pid=player_id;y=self.origin;fold=pid%5;rows=[]
        def add(component,context,rate,unit,exposure,n,reliability,estimator,prior=0.):
            rows.append(dict(player_id=pid,origin_year=y,target_year=y+1,
                component=component,context=context,runs_per_unit=rate,rate_unit=unit,
                opportunity_kind=exposure,weighted_history_opportunities=n,reliability=reliability,
                evidence_tier='individual' if n>0 else 'comparable',
                individual_evidence_observed=n>0,prior_runs_per_unit=prior,estimator_id=estimator,
                general_minor_transfer_validated=False,projected_opportunities=None,projected_runs=None))
        for position in range(3,10):
            h=range_history(self.by['native'][pid],y,position,fold,self.references)
            prior=self.first_base[fold]['rate'] if position==3 else 0.
            rate=estimate(h['weighted_raw_runs'],h['history_outs'],prior) if position==3 else h['centered']
            add('range',str(position),rate,1500.,'defensive_outs',h['history_outs'],h['reliability'],
                'native_range_v28_first_base_prior' if position==3 else
                'native_range_v26_position_centered' if position in (7,8,9) else 'native_range_v3_history',prior)
        h=framing_history(self.by['framing'][pid],y)
        add('framing','2',h['history_rate'],1000.,'received_pitches',h['history_pitches'],h['reliability'],'framing_v4_history')
        for kind in ('throwing','blocking'):
            h=catcher_history(kind,self.by['catcher'][pid],y)
            add('catcher_throwing' if kind=='throwing' else kind,'2',h['history'],
                100. if kind=='throwing' else 1000.,'steal_attempts' if kind=='throwing' else 'blocking_chances',
                h['history_opportunities'],h['reliability'],'catcher_v5_'+kind+'_history')
        for kind in ('arm','receiving'):
            h=arm_history(kind,self.by['other'][pid],y)
            add(kind,'OF' if kind=='arm' else '3',h['history'],100.,
                'runner_advancement_opportunities' if kind=='arm' else 'received_throws',
                h['history_opportunities'],h['reliability'],'arm_receiving_v6_'+kind+'_history')
        return rows
