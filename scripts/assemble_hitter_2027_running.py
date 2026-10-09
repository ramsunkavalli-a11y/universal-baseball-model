"""Refresh selected steal and advancement skill estimators, with native traces."""
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
import gzip
import json
import numpy as np
import polars as pl
from universal_baseball.current_baserunning import build_steal_history,build_current_baserunning_rates,ATTEMPT_CANDIDATE,SUCCESS_CANDIDATE,ADVANCEMENT_CANDIDATE
from universal_baseball.player_value_steal_projection import PlayerSeasonStealSummary,attempt_multiplier,success_log_odds_residual
from universal_baseball.player_value_advancement_projection import PlayerSeasonAdvancementSummary,projected_advancement_rate
from universal_baseball.player_value_baserunning_runs import build_baserunning_reference,project_baserunning_runs
from universal_baseball.storage import sha256_file
from assemble_hitter_2027_base import ROOT,OUT,PUBLIC
from capture_hitter_2027_origin_counts import write_once


def main():
    receipt=PUBLIC/'running-rate-assembly.json';assert not receipt.exists()
    components=pl.read_parquet(OUT/'stints.parquet').filter(pl.col('season').is_between(2024,2026))
    steals,audit=build_steal_history(components)
    pastpath=ROOT/'reports/generated/multiyear-hitter-components-v1/native-advancement-history.parquet'
    past=pl.read_parquet(pastpath).filter(pl.col('season').is_between(2024,2025))
    adv=[PlayerSeasonAdvancementSummary(player_id=r['player_id'],season=r['season'],runs_xb=r['advancement_runs'],
        opportunities_xb=r['advancement_opportunities']) for r in past.iter_rows(named=True)]
    nativepath=ROOT/'reports/generated/hitter-2027-nonbatting-source/running-rows.json.gz'
    native=json.loads(gzip.decompress(nativepath.read_bytes()))
    for r in native:
        assert int(r['start_year'])==int(r['end_year'])==2026
        adv.append(PlayerSeasonAdvancementSummary(player_id=int(r['player_id']),season=2026,runs_xb=float(r['runner_runs_xb']),opportunities_xb=float(r['n_runner_moved_xb'])))
    assert len({(r.player_id,r.season) for r in adv})==len(adv)
    pitchingpath=ROOT/'reports/generated/hitter-2027-nonbatting-source/official-team-pitching-rows.json.gz'
    pitching=json.loads(gzip.decompress(pitchingpath.read_bytes()))
    mlb=pl.read_parquet(ROOT/'reports/generated/hitter-2027-origin-counts/team-season-inputs.parquet').filter(pl.col('sport_id')==1)
    outs=sum(r['stat']['outs'] for r in pitching);runs=sum(r['stat']['runs'] for r in pitching)
    assert outs==129239 and runs==21769
    assert mlb['runs'].sum()==runs
    opportunity=mlb.select((pl.col('hits')-pl.col('doubles')-pl.col('triples')-pl.col('home_runs')+pl.col('base_on_balls')-pl.col('intentional_walks')+pl.col('hit_by_pitch')).sum()).item()
    reference=build_baserunning_reference(season=2026,plate_appearances=183849,runs=runs,outs=outs,
        steal_opportunity_proxy=opportunity,steal_attempts=mlb['stolen_bases'].sum()+mlb['caught_stealing'].sum(),
        stolen_bases=mlb['stolen_bases'].sum(),advancement_opportunities=sum(r.opportunities_xb for r in adv if r.season==2026))
    bysteal=defaultdict(list);byadv=defaultdict(list)
    for r in steals:bysteal[r.player_id].append(r)
    for r in adv:byadv[r.player_id].append(r)
    players=pl.read_parquet(OUT/'assembled.parquet');parts=[];details={}
    for pid in players['player_id']:
        # Both selected estimators filter to this player; pre-indexing changes
        # runtime only, not league references already fixed in steal summaries.
        part=build_current_baserunning_rates(pl.DataFrame({'player_id':[pid]}),bysteal[pid],byadv[pid],forecast_seasons=(2027,),reference=reference)
        parts.append(part)
        target=PlayerSeasonStealSummary(pid,2027,'MLB',0,0,0,0,0)
        attempt=attempt_multiplier(target,bysteal[pid],ATTEMPT_CANDIDATE)
        success=success_log_odds_residual(target,bysteal[pid],SUCCESS_CANDIDATE)
        advance=projected_advancement_rate(PlayerSeasonAdvancementSummary(pid,2027,0,0),byadv[pid],ADVANCEMENT_CANDIDATE)
        details[pid]=dict(attempt_multiplier=attempt,success_log_odds_residual=success,advancement_runs_per_opportunity=advance)
    rates=pl.concat(parts).sort('player_id');assert len(rates)==len(players)
    assert np.isfinite(rates.select('baserunning_runs_per_600','steal_runs_per_600','advancement_runs_per_600').to_numpy()).all()
    assert np.allclose(rates['baserunning_runs_per_600'].to_numpy(),rates['steal_runs_per_600'].to_numpy()+rates['advancement_runs_per_600'].to_numpy())
    basecases=json.loads(gzip.decompress((PUBLIC/'base-input-player-walks.json.gz').read_bytes()))['cases']
    focal=[804944,805811,808393,592450,665487,660271,672275,596019]
    # Add fast/slow extremes explicitly, not just the hitting-oriented cases.
    extra=rates.sort('baserunning_runs_per_600').head(2)['player_id'].to_list()+rates.sort('baserunning_runs_per_600',descending=True).head(2)['player_id'].to_list()
    ids=set(focal+extra+[w['player_id'] for c in basecases for w in c['peers']]);walks=[]
    for pid in sorted(ids):
        row=rates.filter(pl.col('player_id')==pid).row(0,named=True);d=details[pid]
        projection=project_baserunning_runs(projected_mlb_pa=600,reference=reference,attempt_multiplier=d['attempt_multiplier'],
            success_logodds_residual=d['success_log_odds_residual'],advancement_rate=d['advancement_runs_per_opportunity'])
        assert np.isclose(row['baserunning_runs_per_600'],projection.baserunning_runs)
        # Confirm the pre-indexed path reproduces the full-history public API.
        full=build_current_baserunning_rates(pl.DataFrame({'player_id':[pid]}),steals,adv,forecast_seasons=(2027,),reference=reference)
        assert np.allclose(full.select('baserunning_runs_per_600','steal_runs_per_600','advancement_runs_per_600').to_numpy(),np.array([[row[k] for k in ['baserunning_runs_per_600','steal_runs_per_600','advancement_runs_per_600']]]))
        walks.append(dict(player_id=pid,name=players.filter(pl.col('player_id')==pid)['player_name'][0],prediction=row,
            source_components=components.filter(pl.col('player_id')==pid).select('season','level_group','plate_appearances','hits','doubles','triples','home_runs','base_on_balls','intentional_walks','hit_by_pitch','stolen_bases','caught_stealing').to_dicts(),
            environment_adjusted_steal_history=[asdict(r) for r in bysteal[pid]],advancement_history=[asdict(r) for r in byadv[pid]],
            intermediates=d,reference_conversion=asdict(projection),
            interpretation='Steal tendency and success use exposure-adjusted MLB/minor history. Advancement uses measured MLB opportunities only; absent advancement measurement remains a disclosed population estimate. No separate GIDP residual is supported by the selected model.'))
    output=OUT/'running-rates.parquet';assert not output.exists();rates.write_parquet(output)
    walkpath=PUBLIC/'running-rate-player-walks.json.gz';assert not walkpath.exists();walkpath.write_bytes(gzip.compress(json.dumps(walks,default=str,allow_nan=False).encode(),mtime=0))
    write_once(receipt,dict(forecast_year=2027,reference=asdict(reference),environment_audit=asdict(audit),players=len(rates),
        evidence= rates.group_by('baserunning_evidence_tier').len().to_dicts(),fixed_cases=8,peer_cases=24,extreme_cases=4,
        player_walkthrough='complete',new_model_fit=False,predictive_improvement_claim=False,
        minor_environment_scope='Existing selected adapter uses sport/level, not park or exact minor league',
        future_path_rule='These are 2027 skill estimates; do not repeatedly advance the historical lookback and make every player neutral in 2030.',
        missing_advancement_not_individual_zero=True,gidp='Explicit neutral residual retained; no invented individual GIDP model',
        output_hashes={str(output):sha256_file(output),str(walkpath):sha256_file(walkpath)},
        input_hashes={str(p):sha256_file(p) for p in [OUT/'stints.parquet',pastpath,nativepath,pitchingpath]},runner_sha256=sha256_file(Path(__file__))))
    print(rates.group_by('baserunning_evidence_tier').len().to_dicts(),flush=True)


if __name__=='__main__':main()
