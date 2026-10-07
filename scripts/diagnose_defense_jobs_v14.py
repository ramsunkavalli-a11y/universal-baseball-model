"""Post-test source/prior diagnosis, no refitting or replacement forecasts."""

from collections import defaultdict
import numpy as np
import polars as pl

from run_defense_jobs_v14 import OUT, SOURCE, VALUE, ROLES, read, write, check, hashes


def main():
    check();assert not (OUT/'source-profile-diagnosis.json').exists()
    walk=read(OUT/'player-walkthrough.json');assert walk['status']=='complete'
    f=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(OUT/'predictions.parquet')
    source=pl.read_parquet(SOURCE/'source.parquet');quality=pl.read_parquet(VALUE/'channel-predictions.parquet')
    pid_history=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual-usage.parquet').to_dicts():pid_history[r['player_id']].append(r)
    unobserved=[]
    for r in q.to_dicts():
        past=[h for h in pid_history[r['player_id']] if r['origin_year']-2<=h['season']<=r['origin_year']]
        roles={p for p in ROLES[:-1] if any(h[f'outs_{p}']>0 or h[f'starts_{p}']>0 for h in past)}
        if str(r['source_position']).isdigit():roles.add(int(r['source_position']))
        absent=[p for p in ROLES[:-1] if p not in roles and r[f'candidate_{p}']>0]
        if absent:unobserved.append(dict(row_id=r['row_id'],player_id=r['player_id'],name=r['player_name'],origin=r['origin_year'],
            prior_MLB=r['prior_debut'],stage=r['stage'],absent_field_positions=absent,
            allocated_outs=[r[f'candidate_{p}'] for p in absent],
            qualification='Unobserved is not automatically impossible; some cross-position development is legitimate.'))
    provenance=[]
    for case in walk['cases']:
        records=[]
        for w in case['records']:
            raw=source.filter((pl.col('player_id')==w['player_id'])&pl.col('season').is_between(w['origin']-2,w['target']))
            fields=['season','league_id','level_group','normalized_level','position_code','fielding_outs','games_started','source_id',
                    'usage_scope','team_id','team_usage_certified','level_subtype_certified']
            records.append(dict(player_id=w['player_id'],origin=w['origin'],raw_position_sources=raw.select(fields).to_dicts(),
                quality_source_keys=quality.filter(pl.col('row_id')==w['row_id']).select('channel','source_keys').to_dicts()))
        provenance.append(dict(player_id=case['player_id'],origin=case['origin'],records=records))
    # Explain exactly whose non-1B jobs entered Eldridge's primary-role prior.
    case=next(c['records'][0] for c in walk['cases'] if c['records'][0]['name']=='Bryce Eldridge')
    m=read(OUT/f"model-{case['origin']}-{case['fold']}.json")
    tr=f.filter(pl.col('row_id').is_in(m['training_row_ids']) & (pl.col('job_primary_role')==3) &
                (pl.col('job_status')=='no_prior_MLB'))
    contributors=tr.sort(pl.col('actual_4')+pl.col('actual_5')+pl.col('actual_6'),descending=True).select(
        'row_id','player_id','player_name','origin_year','target_year','age','stage','job_own_shares',
        'job_evidence_kind','actual_3','actual_4','actual_5','actual_6','actual_10','next_pa').to_dicts()
    write('source-profile-diagnosis.json',dict(status='diagnosis_complete_no_new_forecast',
        inferred_unobserved_position_rows=len(unobserved),unobserved_allocations=unobserved,
        Eldridge_prior=case['role_prior'],Eldridge_prior_contributors=contributors,
        explicit_defects=[
            'Broad fallback imports unobserved infield jobs into pure-DH players.',
            'Primary 1B groups pool true first basemen with multi-position players; Eldridge borrows their 2B/3B jobs.',
            'Weighted historical usage treats an earlier temporary role like continuing role evidence.',
            'Balancing league jobs can improve total bias and whole-value cancellation without improving individual roles.'],
        source_provenance=provenance,source_hashes=hashes([SOURCE/'source.parquet',SOURCE/'annual-usage.parquet',
            VALUE/'channel-predictions.parquet',OUT/'player-walkthrough.json',OUT/'features.parquet',OUT/'predictions.parquet']),
        no_refits=True,no_replacement_predictions=True,no_2026_outcomes_used=True,no_deployment=True))
    print(f'Diagnosed {len(unobserved)} unobserved-position allocations; retained all source keys and prior contributors.')


if __name__=='__main__':main()
