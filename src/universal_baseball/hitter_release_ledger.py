"""2027 release accounting boundary: explicit component evidence and complete costs.

This integrates existing WAR and path-pricing arithmetic; it is not an estimator
or a claim that supplied component forecasts have passed predictive validation.
"""
from dataclasses import dataclass
from datetime import date
from math import fsum, isclose, isfinite
from typing import Mapping, Sequence

from universal_baseball.player_value_final_aggregation import calculate_final_player_value
from universal_baseball.player_path_value import value_paths

COMPONENTS = frozenset({
    'batting', 'stealing', 'advancement', 'gidp', 'range', 'arm', 'double_play',
    'receiving', 'catcher_throwing', 'blocking', 'framing', 'abs_challenge', 'position', 'league',
    'park', 'replacement',
})
RUNNING = frozenset({'stealing', 'advancement', 'gidp'})
FIELDING = frozenset({'range', 'arm', 'double_play', 'receiving', 'catcher_throwing', 'blocking', 'framing', 'abs_challenge'})
EVIDENCE = frozenset({'individual_history', 'translated_profile', 'comparable_players',
                      'accounting_reference', 'not_applicable'})


@dataclass(frozen=True)
class ComponentEstimate:
    component: str
    context: str
    runs_per_unit: float
    opportunities: float
    unit: float
    opportunity_kind: str
    evidence_tier: str
    estimator_id: str
    source_id: str
    source_cutoff: date

    def projected_runs(self, *, as_of: date) -> float:
        if self.component not in COMPONENTS or self.evidence_tier not in EVIDENCE:
            raise ValueError('Unknown component or evidence tier')
        if not all(isinstance(s, str) and s.strip() for s in [
                self.context, self.opportunity_kind, self.estimator_id, self.source_id]):
            raise ValueError('Missing component context, units or provenance')
        if not isinstance(self.source_cutoff, date) or self.source_cutoff > as_of:
            raise ValueError('Future or unknown component source cutoff')
        if not all(isfinite(v) for v in [self.runs_per_unit,self.opportunities,self.unit]) or self.unit <= 0 or self.opportunities < 0:
            raise ValueError('Invalid component rate/exposure/unit')
        if self.evidence_tier == 'not_applicable' and (self.runs_per_unit != 0 or self.opportunities != 0):
            raise ValueError('Not-applicable component must have zero rate and exposure')
        return self.runs_per_unit*self.opportunities/self.unit


def batting_rate_from_legacy(rate_wins_per_600: float) -> float:
    """Old selected rate uses fixed 10 runs/win, NOT the new assembly's RPW.

    Takes batting rate only, never batting-plus-replacement contribution.
    """
    if not isfinite(rate_wins_per_600):
        raise ValueError('Unknown legacy batting rate')
    return 10.0*rate_wins_per_600


def annual_ledger(*, player_id: int, season: int, as_of: date,
                  estimates: Sequence[ComponentEstimate], runs_per_win: float,
                  fielding_reference: str, batting_reference: str,
                  deployment_status: str) -> dict:
    if type(player_id) is not int or player_id <= 0 or type(season) is not int or season <= as_of.year:
        raise ValueError('Positive identity and future full season required')
    if fielding_reference != 'position_relative':
        raise ValueError('Convert native/intrinsic fielding to the positional reference before assembly')
    if batting_reference not in {'park_neutral', 'observed_context'}:
        raise ValueError('Unknown batting context')
    if deployment_status not in {'development', 'provisional_v1', 'released_v1'}:
        raise ValueError('Explicit release status required')
    keys = [(e.component, e.context) for e in estimates]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate component/context would double count value')
    if {e.component for e in estimates} != COMPONENTS:
        raise ValueError('Every component needs an explicit estimator, including profile estimates')
    detailed = []
    for e in estimates:
        detailed.append(dict(component=e.component, context=e.context,
            runs=e.projected_runs(as_of=as_of), rate=e.runs_per_unit,
            exposure=e.opportunities, unit=e.unit, opportunity_kind=e.opportunity_kind,
            evidence_tier=e.evidence_tier, estimator_id=e.estimator_id, source_id=e.source_id,
            source_cutoff=e.source_cutoff.isoformat()))
    runs = {c:fsum(r['runs'] for r in detailed if r['component'] == c) for c in sorted(COMPONENTS)}
    if batting_reference == 'park_neutral' and any(r['runs'] != 0 for r in detailed if r['component'] == 'park'):
        raise ValueError('Already-neutral batting cannot receive another park adjustment')
    # Reuse the established additive implementation without inheriting its old
    # 2024 product label or replacement amount.
    total = calculate_final_player_value(
        batting_runs=runs['batting'], baserunning_runs=fsum(runs[c] for c in RUNNING),
        defense_runs=fsum(runs[c] for c in FIELDING), positional_runs=runs['position'],
        centering_runs=runs['league'], park_runs=runs['park'],
        replacement_runs=runs['replacement'], runs_per_win=runs_per_win)
    component_war = {c:v/total.runs_per_win for c,v in runs.items()}
    if not isclose(fsum(component_war.values()), total.war, abs_tol=1e-12):
        raise ValueError('WAR components do not reconcile')
    return dict(player_id=player_id, season=season, as_of=as_of.isoformat(),
        aggregation_id='hitter_2027_explicit_component_ledger_v1',
        deployment_status=deployment_status, fielding_reference=fielding_reference,
        batting_reference=batting_reference, component_runs=runs, component_war=component_war,
        runs_above_replacement=total.runs_above_replacement, runs_per_win=total.runs_per_win,
        war=total.war, details=detailed,
        comparable_player_components=sorted({r['component'] for r in detailed if r['evidence_tier']=='comparable_players'}))


def control_value(*, seasons: Sequence[int], first_season: int, war_paths,
                  rights_paths, obligation_paths, tail_complete: bool,
                  breakpoints, rates, discount_rate: float, weights=None,
                  two_way_player: bool=False, includes_pitching: bool=False,
                  assumptions: Mapping[str,str]) -> dict:
    """Price specified paths with dated assumptions and no six-calendar-year shortcut.

    Rights/service and obligations are supplied by the existing control/contract
    engines. This boundary does not infer rights from PA or truncate their tails.
    """
    if type(first_season) is not int or not seasons or any(type(y) is not int for y in seasons) or list(seasons) != list(range(first_season, first_season+len(seasons))):
        raise ValueError('Consecutive annual paths starting at the forecast season required')
    required = {'control_source', 'contract_source', 'rules_scenario', 'pricing_scenario', 'path_model'}
    if set(assumptions) != required or any(not isinstance(v,str) or not v.strip() for v in assumptions.values()):
        raise ValueError('Complete source and scenario labels required')
    if two_way_player and not includes_pitching:
        return dict(status='unavailable', reason='hitter_only_value_cannot_cover_two_way_contract', mean_surplus=None)
    import numpy as np
    for a in [war_paths, rights_paths, obligation_paths]:
        if a is not None and (np.asarray(a).ndim != 2 or np.asarray(a).shape[1] != len(seasons)):
            raise ValueError('Path arrays and calendar years differ')
    result = value_paths(war_paths, rights_paths, obligation_paths, target_kind='whole_war',
        tail_complete=tail_complete, breakpoints=breakpoints, rates=rates,
        discount_rate=discount_rate, weights=weights)
    return dict(**result, seasons=list(seasons), assumptions=dict(assumptions),
                financial_basis='specified path scenario; not independently validated market value')
