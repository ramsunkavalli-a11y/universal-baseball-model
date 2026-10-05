"""Independent raw arithmetic and complete source-only player review."""
from collections import defaultdict
from pathlib import Path
import math
import re
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import audit_hitter_tracking_2025 as audit

OUT = audit.OUT; ROOT = audit.ROOT
AMENDMENT = ROOT/'docs/hitter-2025-contact-denominator-amendment.md'


def independent_annual(rows):
    ev = np.array([float(r['launch_speed']) for r in rows if r['launch_speed'] is not None and 0 <= float(r['launch_speed']) <= 130])
    la = np.array([float(r['launch_angle']) for r in rows if r['launch_angle'] is not None and -90 <= float(r['launch_angle']) <= 90])
    pairs = [(float(r['launch_speed']), float(r['launch_angle'])) for r in rows
             if r['launch_speed'] is not None and r['launch_angle'] is not None
             and 0 <= float(r['launch_speed']) <= 130 and -90 <= float(r['launch_angle']) <= 90]
    air = sum(e >= 95 and 8 <= a <= 50 for e, a in pairs)
    sweet = sum(e >= 95 and 8 <= a <= 32 for e, a in pairs)
    return dict(terminal_nonbunt_contacts=len(rows), measured_ev_contacts=len(ev), measured_la_contacts=len(la),
        measured_pair_contacts=len(pairs), mean_ev=float(ev.mean()) if len(ev) else None,
        ev95=float(np.quantile(ev, .95, method='linear')) if len(ev) else None,
        hard_hit_fraction=float((ev >= 95).mean()) if len(ev) else None,
        mean_la=float(la.mean()) if len(la) else None, la_sd=float(la.std(ddof=1)) if len(la) > 1 else None,
        sweet_spot_fraction=float(((la >= 8) & (la <= 32)).mean()) if len(la) else None,
        hard_sweet_spot_contacts=sweet, hard_air_contacts=air, pair_coverage=len(pairs)/len(rows),
        hard_air_fraction=air/len(pairs) if len(pairs) else None,
        first_date=min(r['game_date'] for r in rows), last_date=max(r['game_date'] for r in rows))


def main():
    assert not (OUT/'final-source-review.json').exists(), 'Preserve final review'
    initial = audit.read(OUT/'initial-audit.json')
    for p, h in initial['input_hashes'].items():
        assert sha256_file(audit.Path(p)) == h
    plays = audit.read(OUT/'residual-play-review.json'); corrections = []; extra_keys = []
    for c in plays['cases']:
        for g in c['games']:
            if g['comparison']['residual'] == -1:
                selected = [p for p in g['official_player_plays'] if not p['source'] and not p['inplay_pitch_events']
                    and p['result']['eventType'] == 'field_out' and 'out on batter interference' in p['result']['description'].lower()]
                noncontact, physical_award = 1, 0; kind = 'noncontact_interference_AB'
            elif g['comparison']['residual'] == 1:
                selected = [p for p in g['official_player_plays'] if p['source'] and p['inplay_pitch_events']
                    and p['result']['eventType'] == 'field_error'
                    and 'reaches on a defensive shift violation error' in p['result']['description'].lower()]
                noncontact, physical_award = 0, 1; kind = 'measured_shift_award_without_AB'
            else:
                raise ValueError('Unexpected residual')
            assert len(selected) == 1
            p = selected[0]; pk = g['comparison']['game_pk']; num = p['at_bat_number']
            if physical_award:
                sp = p['source'][0]; ip = p['inplay_pitch_events'][0]
                assert float(sp['launch_speed']) == ip['hitData']['launchSpeed']
                assert float(sp['launch_angle']) == ip['hitData']['launchAngle']
                assert ip['details']['violation']['type'] == 'defensive_shift'
                extra_keys.append((pk, num))
            corrections.append(dict(player_id=c['player_id'], player_name=c['player_name'], game_pk=pk,
                at_bat_number=num, classification=kind, noncontact_AB=noncontact,
                physical_award_without_AB=physical_award, official_description=p['result']['description']))
    assert len(corrections) == 2
    reconciled = pl.read_parquet(OUT/'player-reconciliation.parquet')
    adjustment = {r['player_id']: r['physical_award_without_AB']-r['noncontact_AB'] for r in corrections}
    reconciled = reconciled.with_columns(pl.Series('documented_adjustment', [adjustment.get(p, 0) for p in reconciled['player_id']]))
    assert ((reconciled['official_contacts']+reconciled['documented_adjustment']) == reconciled['source_contacts']).all()
    for c in ['singles', 'doubles', 'triples', 'home_runs']:
        assert reconciled[c].equals(reconciled[c+'_source'])
    reconciled.write_parquet(OUT/'reviewed-player-reconciliation.parquet')
    # Independent Python selection and NumPy summaries directly from preserved raw rows.
    raw = pl.concat([pl.read_parquet(audit.source.OUT/f'2025-{m:02}.parquet') for m in range(3, 11)])
    by_player = defaultdict(list)
    for r in raw.iter_rows(named=True):
        desc = (r['des'] or '').lower()
        if r['type'] != 'X' or not (r['events'] or '').strip():
            continue
        if r['events'] == 'field_error' and 'reaches on an interference error' in desc:
            continue
        if re.search(r'\bbunt\b', desc):
            continue
        by_player[int(r['batter'])].append(r)
    annual = pl.read_parquet(OUT/'annual-launch-features-2025.parquet'); field_checks = 0
    for a in annual.iter_rows(named=True):
        expected = independent_annual(by_player[a['player_id']])
        for k, v in expected.items():
            actual = a[k]
            if k.endswith('_date'):
                assert str(actual) == v
            elif v is None:
                assert actual is None, (a['player_id'], k)
            else:
                assert math.isclose(actual, v, rel_tol=0, abs_tol=1e-10), (a['player_id'], k)
            field_checks += 1
    assert len(annual) == len(by_player) and sum(len(v) for v in by_player.values()) == initial['nonbunt_contacts']
    q = pl.read_parquet(OUT/'launch-events-2025.parquet')
    q = q.with_columns(pl.Series('physical_award_without_AB', [k in extra_keys for k in q.select('game_pk', 'at_bat_number').iter_rows()]))
    assert q['physical_award_without_AB'].sum() == 1
    q.write_parquet(OUT/'launch-events-reviewed-2025.parquet')
    fixed = audit.read(OUT/'fixed-player-walks.json')['cases']
    # Fixed cases plus both residuals, zero-measurement and single-measurement stress cases.
    pids = [c['player_id'] for c in fixed] + [r['player_id'] for r in corrections] + [693409, 679631]
    official = {r['player_id']: r for r in reconciled.to_dicts()}
    annual_by = {r['player_id']: r for r in annual.to_dicts()}
    walks = []
    for pid in pids:
        focal = annual_by[pid]
        peer_pool = sorted((p for p in annual_by if p != pid),
                           key=lambda p: (abs(annual_by[p]['terminal_nonbunt_contacts']-focal['terminal_nonbunt_contacts']), p))[:3]
        walks.append(dict(player_id=pid, player_name=official[pid]['player_name'], official_2025=official[pid],
            raw_rows=len([r for r in raw.iter_rows(named=True) if int(r['batter']) == pid]),
            measured_annual=focal, independently_reconstructed=independent_annual(by_player[pid]),
            input_row=next((c['input_row'] for c in fixed if c['player_id'] == pid), None),
            corrections=[r for r in corrections if r['player_id'] == pid],
            peers=[dict(player_id=p, player_name=official[p]['player_name'], annual=annual_by[p]) for p in peer_pool],
            judgment=('No measured EV; retain explicit unknown metrics, not zero-speed talent.' if focal['measured_ev_contacts'] == 0
                      else 'One measured contact is correctly observed but does not establish stable talent.' if focal['measured_ev_contacts'] == 1
                      else 'Actual sample and missingness enter unchanged definitions; this is not a prediction or approval of accuracy.')))
    audit.write(OUT/'completed-player-review.json', dict(cases=walks, selection_rule='Six fixed cases, every residual, zero and one measured-contact stress cases; three closest contact-exposure peers by player ID tie break',
        outcome_selected_cases=False, protected_outcomes_used=False, player_walkthrough_status='complete'))
    report = dict(source_approved_for_existing_tracking_inputs=True, protected_outcomes_used=False, new_model_fits=0,
        raw_rows=len(raw), normal_nonbunt_contacts=len(q), complete_pairs=int(q['complete_pair'].sum()),
        people=len(annual), reconciled_people=len(reconciled), exact_player_hit_counts=True,
        exact_corrected_player_contacts=True, corrections=corrections, venue_missing=q['venue_id'].null_count(),
        historical_fields_compared=initial['historical_fields_compared'], historical_equivalence=True,
        independent_annual_fields_checked=field_checks, player_walkthrough_status='complete', cases=len(walks),
        original_publication_vintage_verified=False, qualification='Current provider values may include estimates and retrospective revisions; not camera-only or verified original preseason vintage',
        candidate_frozen=False, input_hashes={str(p): sha256_file(p) for p in [AMENDMENT, audit.CONTRACT, Path(__file__),
            OUT/'initial-audit.json', OUT/'residual-play-review.json']},
        output_hashes={str(p): sha256_file(p) for p in [OUT/'annual-launch-features-through-2025.parquet',
            OUT/'launch-events-reviewed-2025.parquet', OUT/'reviewed-player-reconciliation.parquet', OUT/'completed-player-review.json']})
    assert report['venue_missing'] == 0 and initial['invalid_ev'] == initial['invalid_la'] == 0
    audit.write(OUT/'final-source-review.json', report)
    print(f'Reviewed {len(reconciled)} player denominators, {field_checks} raw annual fields and {len(walks)} case walks; tracking source qualified', flush=True)


if __name__ == '__main__':
    main()
