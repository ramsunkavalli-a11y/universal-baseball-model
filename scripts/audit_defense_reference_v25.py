"""Reconcile saved talent/value references; no loss-based selection or model fit."""
from collections import defaultdict
from pathlib import Path
import json
import math
import gzip
import polars as pl
from universal_baseball.defense_reference import (
    OUTFIELD, center, cutoff_center, relative_runs, relative_rate,
    reference_offset, neutral_position_prior)
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import write
from run_hitter_finite_return_baseline import protections

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'reports/model-evidence/defense-reference-v25'
OUT = ROOT / 'reports/generated/defense-reference-v25'
NATIVE = ROOT / 'reports/generated/defense-native-range-v3/component-ledger.parquet'
OFFICIAL = ROOT / 'reports/generated/defense-position-opportunity-v7/source.parquet'
V12 = ROOT / 'reports/generated/defense-value-v12'
BRIDGE = ROOT / 'reports/generated/defense-transition-v10/predictions.parquet'
MINOR = ROOT / 'reports/generated/defense-minor-counts-v18/counts.parquet'
OP = ('ratio', 'repair', 'transition')
SKILL = ('neutral', 'history', 'calibrated')
FOCAL = (545361, 664023, 665742, 641355, 592206, 678882, 677951, 575929)
SCHEDULE = {2: 12.5, 3: -12.5, 4: 2.5, 5: 2.5, 6: 7.5, 7: -7.5, 8: 2.5, 9: -7.5}


def read(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf8') as stream:
        return json.load(stream)


def close(a, b):
    assert (a is None and b is None) or (a is not None and b is not None and
        math.isclose(a, b, rel_tol=0, abs_tol=1e-8)), (a, b)


def position(r, prefix):
    return sum(r[f'{prefix}_{p}'] * v / 4374 for p, v in SCHEDULE.items()) - 17.5 * r[f'{prefix}_10'] / 162


def input_paths():
    return [Path(__file__), ROOT/'src/universal_baseball/defense_reference.py',
        ROOT/'docs/defense-reference-v25-contract.md', NATIVE, OFFICIAL, BRIDGE, MINOR,
        V12/'predictions.parquet', V12/'channel-predictions.parquet', V12/'final-review.json',
        ROOT/'reports/model-evidence/defense-older-quality-v24/final-review.json.gz']


def main():
    protections()
    assert not (PUBLIC/'preflight.json.gz').exists(), 'Immutable audit already begun'
    PUBLIC.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    for p in [V12/'final-review.json', ROOT/'reports/model-evidence/defense-older-quality-v24/final-review.json.gz']:
        r = read(p)
        assert r['player_walkthrough_status'] == 'complete'
        for path, h in r['hashes'].items(): assert sha256_file(Path(path)) == h, path
    paths = input_paths()
    write(PUBLIC/'preflight.json.gz', dict(model_fits=0, before_accounting=True,
        reference_choice='Position-relative OF value, preserving intrinsic skill separately; not selected by accuracy.',
        focal_2022_players=list(FOCAL), no_2026_selection=True, player_walkthrough_status='pending',
        hashes={str(p): sha256_file(p) for p in paths}))
    native = pl.read_parquet(NATIVE).to_dicts()
    nmap = {(r['season'], r['player_id'], r['position']): r for r in native}
    by_person = defaultdict(list)
    for r in native: by_person[r['player_id']].append(r)
    assert len(nmap) == len(native) == 13304
    official = defaultdict(int)
    for r in pl.read_parquet(OFFICIAL).iter_rows(named=True):
        if r['is_mlb'] and r['position_code'].isdigit():
            official[r['season'], r['player_id'], int(r['position_code'])] += r['fielding_outs']
    annual = []
    for year in range(2016, 2026):
        for p in OUTFIELD:
            rows = [r for r in native if r['season'] == year and r['position'] == p and r['range_valid']]
            c = center(rows); assert c['rate'] is not None
            for r in rows:
                assert r['native_outs'] > 0 and abs(r['native_outs'] - official[year,r['player_id'],p]) <= 5
                assert abs(r['native_outs'] - official[year,r['player_id'],p]) / max(r['native_outs'],official[year,r['player_id'],p]) <= .01
            total = sum(n for (y, pid, pos), n in official.items() if y == year and pos == p)
            qualified = sum(official[year,r['player_id'],p] for r in rows)
            centered = sum(relative_runs(r['range_runs'], p, r['native_outs'], c['rate']) for r in rows)
            close(centered, 0)
            annual.append(dict(season=year, position=p, **c, official_total_outs=total,
                measured_official_outs=qualified, missing_official_outs=total-qualified,
                centered_measured_runs=centered))
    amap = {(r['season'],r['position']): r for r in annual}
    cutoffs = [cutoff_center(native, y, fold, p) for y in (2022,2023,2024) for fold in range(5) for p in OUTFIELD]
    assert all(c['held_people_excluded'] and c['rate'] is not None and max(c['seasons']) <= c['origin'] for c in cutoffs)
    cmap = {(c['origin'],c['fold'],c['position']): c for c in cutoffs}
    f = pl.read_parquet(V12/'predictions.parquet'); b = pl.read_parquet(BRIDGE)
    chans = pl.read_parquet(V12/'channel-predictions.parquet')
    assert f.height == b.height == 12432 and chans.height == 149184
    assert set(f['row_id']) == set(b['row_id']) == set(chans['row_id'])
    bm = {r['row_id']: r for r in b.to_dicts()}; fm = {r['row_id']: r for r in f.to_dicts()}
    groups = defaultdict(list)
    for c in chans.iter_rows(named=True): groups[c['row_id']].append(c)
    offsets = []; channel_audit = []; case_details = {}
    totals = defaultdict(lambda: defaultdict(float))
    for rid, r in fm.items():
        q = bm[rid]; cells = groups[rid]
        assert len(cells) == 12 and len({c['channel'] for c in cells}) == 12
        assert q['outer_fold'] == r['player_id'] % 5
        actual = [c['actual_runs'] for c in cells]
        close(sum(actual) if all(v is not None for v in actual) else None, r['actual_defense'])
        close(position(q,'actual'), r['actual_position_runs'])
        close(None if r['actual_defense'] is None else r['actual_batting']+(r['actual_defense']+r['actual_position_runs'])/10, r['actual_expanded'])
        detail = []
        actual_offset = 0.; actual_missing = False
        poff = {o: 0. for o in OP}
        for c in cells:
            for skill in SKILL:
                rate = 0. if skill == 'neutral' else c['history_rate']
                if skill == 'calibrated' and c['channel'].startswith('range_') and c['quality_evidence_observed'] and c['range_calibration_fit_allowed'] and c['saved_range_calibration'] is not None:
                    rate = c['saved_range_calibration']
                close(rate, c[skill+'_quality'])
                for o in OP:
                    n = q[f'{o}_{c["channel"][-1]}'] if c['channel'].startswith('range_') else q[f'{o}_native_{c["channel"]}']
                    close(n, c[o+'_predicted_opportunities'])
                    close(n * rate / c['rate_unit'], c[o+'_'+skill])
            if c['channel'] not in ('range_7','range_8','range_9'): continue
            p = int(c['channel'][-1]); y = r['origin_year']; pid = r['player_id']
            ref = cmap[y,q['outer_fold'],p]; observed_ref = amap[y+1,p]
            source = nmap.get((y+1,pid,p))
            measured = c['actual_official_exposure'] > 0 and c['actual_runs'] is not None
            if measured:
                assert source is not None and source['range_valid']
                close(source['range_runs'], c['actual_runs'])
                close(source['native_outs'], c['actual_native_opportunities'])
                aoff = reference_offset(p,source['native_outs'],observed_ref['rate'])
            elif c['actual_official_exposure'] == 0:
                close(c['actual_runs'],0.); aoff=0.
            else:
                aoff=None; actual_missing=True
            if aoff is not None: actual_offset += aoff
            off = {o: reference_offset(p,c[o+'_predicted_opportunities'],ref['rate']) for o in OP}
            for o in OP: poff[o] += off[o]
            hist = [s for s in by_person[pid] if s['position'] == p and y-2 <= s['season'] <= y and s['range_valid']]
            weighted_outs = sum(s['native_outs']*2.**(s['season']-y) for s in hist)
            weighted_runs = sum(s['range_runs']*2.**(s['season']-y) for s in hist)
            close(weighted_outs,c['history_opportunities']); close(weighted_outs/(weighted_outs+3000),c['reliability'])
            close(1500*weighted_runs/(weighted_outs+3000),c['history_rate'])
            d = dict(row_id=rid,player_id=pid,origin=y,position=p,quality_observed=c['quality_evidence_observed'],
                history_outs=weighted_outs,history_runs=weighted_runs,reliability=c['reliability'],
                raw_history_rate=c['history_rate'],cutoff_reference_rate=ref['rate'],
                relative_measured_history_rate=relative_rate(c['history_rate'] if c['quality_evidence_observed'] else None,p,ref['rate']),
                legacy_raw_zero_in_relative_units=relative_rate(0.,p,ref['rate']),
                neutral_position_prior=neutral_position_prior(p,ref['rate']),
                predicted_offsets=off,actual_official_outs=c['actual_official_exposure'],
                actual_native_outs=source['native_outs'] if measured else 0 if c['actual_official_exposure']==0 else None,
                actual_raw_range=c['actual_runs'],actual_reference_rate=observed_ref['rate'],actual_offset=aoff,
                actual_relative_range=None if aoff is None else c['actual_runs']-aoff,
                history_sources=hist,cutoff_center=ref)
            detail.append(d)
            channel_audit.append({k:v for k,v in d.items() if k not in ('history_sources','cutoff_center','neutral_position_prior','predicted_offsets')})
        for o in OP:
            pos = position(q,o); close(pos,r[o+'_position_runs'])
            for skill in SKILL:
                arm = o+'_'+skill; raw = sum(c[arm] for c in cells)
                close(raw,r[arm+'_defense']); close(r['batting_forecast']+(pos+raw)/10,r[arm+'_expanded'])
                # Moving an offset between columns is ONLY a change of coordinates.
                close((raw-poff[o])+(pos+poff[o]),raw+pos)
                close(r['batting_forecast']+(raw-poff[o]+pos)/10,r[arm+'_expanded']-poff[o]/10)
        offset = dict(row_id=rid,player_id=r['player_id'],origin_year=r['origin_year'],
            actual_reference_offset=None if actual_missing else actual_offset,
            complete_defined_target=r['actual_defense'] is not None,
            **{o+'_cutoff_offset':poff[o] for o in OP})
        offsets.append(offset); case_details[rid] = detail
        for o in OP:
            totals[y,o]['all_forecast_offset'] += poff[o]
            totals[y,o]['rows'] += 1
            if offset['complete_defined_target']:
                totals[y,o]['complete_rows'] += 1
                totals[y,o]['complete_forecast_offset'] += poff[o]
                totals[y,o]['complete_actual_offset'] += actual_offset
                for d in detail:
                    totals[y,o][str(d['position'])+'_forecast_offset'] += d['predicted_offsets'][o]
                    totals[y,o][str(d['position'])+'_actual_offset'] += d['actual_offset']
    cases=[]
    minor = pl.read_parquet(MINOR).filter(pl.col('season').is_between(2020,2022)).to_dicts()
    minor_by_person = defaultdict(list)
    for s in minor: minor_by_person[s['player_id']].append(s)
    for pid in FOCAL:
        focal = next(r for r in bm.values() if r['origin_year']==2022 and r['player_id']==pid)
        def key(q):
            age = q['age'] if q['age'] is not None else 27.
            fa = focal['age'] if focal['age'] is not None else 27.
            return abs(age-fa), abs(q['role_defensive_sample']-focal['role_defensive_sample']),q['row_id']
        peers = sorted([q for q in bm.values() if q['origin_year']==2022 and q['stage']==focal['stage'] and
            q['repertoire_primary_role']==focal['repertoire_primary_role'] and q['player_id']!=pid], key=key)[:3]
        assert len(peers)==3
        records=[]
        for q in [focal,*peers]:
            rid=q['row_id']; year=q['origin_year']; player=q['player_id']
            sources=[s for s in by_person[player] if year-2<=s['season']<=year+1]
            records.append(dict(forecast=fm[rid],origin_role={k:q[k] for k in ('stage','age','outer_fold','repertoire_primary_role','role_defensive_sample','role_evidence_source')},
                origin_and_future_native_records=sources,
                origin_minor_source_counts=minor_by_person[player],
                exposure={o:{str(p):q[f'{o}_{p}'] for p in range(2,11)} for o in (*OP,'actual')},
                channels=groups[rid],reference_calculations=case_details[rid]))
        cases.append(dict(focal_player_id=pid,origin=2022,peer_rule='Same stage and repertoire role; nearest known age, exposure, row ID; no future outcomes.',records=records))
    pl.DataFrame(offsets).write_parquet(OUT/'reference-offsets.parquet')
    pl.DataFrame(channel_audit,infer_schema_length=None).write_parquet(OUT/'range-reference-ledger.parquet')
    write(PUBLIC/'player-walks.json.gz',dict(cases=cases,model_fits=0,player_walkthrough_status='pending',
        no_new_predictions=True,hashes={str(p):sha256_file(p) for p in paths}))
    write(PUBLIC/'report.json.gz',dict(model_fits=0,saved_assemblies_replayed=12432*9,
        saved_channels_replayed=149184,annual_centers=annual,cutoff_centers=cutoffs,
        forecast_reference_totals=[dict(origin=y,opportunity_arm=o,**v) for (y,o),v in sorted(totals.items())],
        identities_retained=12432,OF_channel_records=len(channel_audit),
        unknown_positive_exposure_OF_records=sum(r['actual_official_outs']>0 and r['actual_raw_range'] is None for r in channel_audit),
        coordinate_identity_pass=True,new_accuracy_comparison=False,deployment_approved=False,
        definition_limit='Research position-relative OF accounting; not exact FanGraphs WAR or universal lower-minors talent.',
        player_walkthrough_status='pending',previous_goal_turn='Read-only Lovich explanation: no defense progress.',
        hashes={str(p):sha256_file(p) for p in paths},
        output_hashes={str(p):sha256_file(p) for p in [OUT/'reference-offsets.parquet',OUT/'range-reference-ledger.parquet',PUBLIC/'player-walks.json.gz']}))
    protections(); print('All saved accounting replayed. Reference offsets and fixed walks saved; review pending.',flush=True)


if __name__ == '__main__': main()
