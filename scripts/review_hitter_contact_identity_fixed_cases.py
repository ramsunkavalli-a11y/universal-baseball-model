"""Trace repaired historical contact measurements through fixed player cases."""
from pathlib import Path
import json
import polars as pl
from universal_baseball.hitter_contact_identity_rebuild import contact_cells, measurement_changes
from universal_baseball.storage import sha256_file
from rebuild_hitter_contact_identity import ROOT, OUT, WORK, YEARS, read, write

FIXED = [(647228, 2024, 'Adam Hall'), (676045, 2024, 'Casey Martin'),
         (665888, 2024, 'Cristopher Navarro'), (694808, 2024, 'Zach Kokoska'),
         (543482, 2024, 'Drew Maggi'), (678760, 2024, 'Eddys Leonard'),
         (640457, 2018, 'Austin Meadows'), (643446, 2018, 'Jeff McNeil'),
         (668804, 2018, 'Bryan Reynolds'), (701762, 2024, 'Nick Kurtz'),
         (694671, 2023, 'Wyatt Langford')]
KNOWN_EVENTS = [(750493, 74, 647228, 676045), (750929, 76, 665888, 694808), (752195, 39, 543482, 678760)]


def main():
    target = OUT / 'fixed-cases.json'
    if target.exists(): raise FileExistsError('Preserve original source walkthrough')
    assembly = read(OUT / 'assembly.json')
    assert assembly['source_gate'] == 'pending_player_review'
    assert assembly['official_sha256'] == sha256_file(OUT / 'official.json')
    source = pl.read_parquet(ROOT / 'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    official_path = ROOT / 'reports/generated/practical-hitter-v31/counts.parquet'
    official = pl.scan_parquet(official_path).filter(pl.col('season') <= 2024).collect()
    original_cases = read(ROOT / 'reports/model-evidence/hitter-detailed-contact-compatibility/cases.json')
    case_lookup = {(c['player_id'], c['origin_year']): c for c in original_cases}
    inputs = [Path(__file__), ROOT / 'src/universal_baseball/hitter_contact_identity_rebuild.py',
        ROOT / 'src/universal_baseball/contact_profile.py', OUT / 'assembly.json', OUT / 'official.json',
        ROOT / 'docs/hitter-contact-identity-rebuild-contract.md', official_path,
        ROOT / 'reports/generated/hitter-preseason-readiness-v68/features.parquet']
    before_features, after_features, before_cells, after_cells, changes = [], [], [], [], []
    known_rows = []
    selection = {(pid, y): ['fixed_source_diagnostic'] for pid, y, _ in FIXED}
    labels = {pid: label for pid, _, label in FIXED}
    for y in YEARS:
        report = next(r for r in assembly['years'] if r['year'] == y)
        assert report['unflagged_mismatch_contacts'] == 0
        for p, h in report['artifact_hashes'].items(): assert sha256_file(Path(p)) == h
        original_path = WORK / f'contacts-{y}.parquet'
        original = pl.read_parquet(original_path).sort(['game_pk', 'at_bat_index'])
        repaired_path = WORK / 'assembly' / f'repaired-{y}.parquet'
        repaired = pl.read_parquet(repaired_path).sort(['game_pk', 'at_bat_index'])
        assert original.equals(repaired.select(original.columns)), 'Physical ledger changed'
        before_source = original.filter(pl.col('source_batter_id').is_not_null()).with_columns(
            pl.col('source_batter_id').alias('batter_mlbam_id'), pl.lit('source_default').alias('participant_authority'))
        _, bc, bf = contact_cells(before_source)
        af = pl.read_parquet(WORK / 'assembly' / f'cell-features-{y}.parquet')
        ac = pl.read_parquet(WORK / 'assembly' / f'cell-counts-{y}.parquet')
        if original['source_batter_id'].null_count() == 0:
            group = ['season', 'league_id', 'bucket', 'core_bin', 'canonical_outcome']
            assert bc.group_by(group).agg(pl.col('count').sum()).sort(group).equals(ac.group_by(group).agg(pl.col('count').sum()).sort(group))
        before_features.append(bf); after_features.append(af); before_cells.append(bc); after_cells.append(ac)
        changes.append(measurement_changes(bf, af))
        inputs.extend([original_path, repaired_path, WORK / 'assembly' / f'cell-counts-{y}.parquet',
                       WORK / 'assembly' / f'cell-features-{y}.parquet', OUT / f'controls-{y}.parquet'])
        if y == 2024:
            for game, seq, old, new in KNOWN_EVENTS:
                row = repaired.filter((pl.col('game_pk') == game) & (pl.col('at_bat_index') == seq))
                assert len(row) == 1 and row['source_batter_id'][0] == old and row['batter_mlbam_id'][0] == new
                assert row['terminal_outcome_group'][0] == 'HR'
                known_rows.extend(row.to_dicts())
        print('Source cases prepared', y, 'contacts', len(original), flush=True)
    before = pl.concat(before_features); after = pl.concat(after_features)
    bc = pl.concat(before_cells); ac = pl.concat(after_cells); delta = pl.concat(changes)
    for reason, column, descending in [('largest_contact_gain', 'delta_physical_contacts', True),
        ('largest_contact_loss', 'delta_physical_contacts', False), ('largest_HR_gain', 'delta_raw_narrative_hr', True),
        ('largest_HR_loss', 'delta_raw_narrative_hr', False)]:
        row = delta.sort([column, 'season', 'player_id', 'league_id'], descending=[descending, False, False, False]).to_dicts()[0]
        selection.setdefault((row['player_id'], row['season']), []).append(reason)
    # Coverage-selected DSL and ordinary controls remain fixed from the signed
    # first-season source review. Neither was selected by future MLB success.
    for pid, why in [(660685, 'DSL_largest_2016_origin_exposure'), (650334, 'ordinary_unchanged_2016_control')]:
        selection.setdefault((pid, 2016), []).append(why)
    labels.update({p['id']: p['fullName'] for p in read(OUT / 'display-names-2016.json')['people']})
    cases = []
    for (pid, origin), reasons in sorted(selection.items(), key=lambda x: (x[0][1], x[0][0])):
        origin_row = source.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == origin))
        histories = official.filter((pl.col('player_id') == pid) & pl.col('season').is_between(origin - 2, origin)).sort('season', 'bucket')
        window = pl.col('season').is_between(origin - 2, origin) & (pl.col('player_id') == pid)
        controls = []
        for y in range(origin - 2, origin + 1):
            if y not in YEARS: continue
            q = pl.read_parquet(OUT / f'controls-{y}.parquet').filter(pl.col('player_id') == pid)
            controls.extend(q.group_by('league_id').agg(pl.len().alias('player_games'),
                pl.col('batting_PA').sum().alias('PA'), pl.col('batting_AB').sum().alias('AB'),
                pl.col('batting_SO').sum().alias('K'), pl.col('expected_contact_count').sum().alias('expected_contacts'),
                pl.col('expected_contact_count').is_null().sum().alias('unknown_counts'))
                .with_columns(pl.lit(y).alias('season')).to_dicts())
        event_changes = []
        for y in range(origin - 2, origin + 1):
            if y not in YEARS: continue
            q = pl.read_parquet(WORK / 'assembly' / f'changed-{y}.parquet')
            event_changes.extend(q.filter((pl.col('source_batter_id') == pid) | (pl.col('batter_mlbam_id') == pid)).to_dicts())
        peers = []
        if len(origin_row) == 1:
            o = origin_row.to_dicts()[0]; labels.setdefault(pid, o['player_name'])
            population = source.filter((pl.col('origin_year') == origin) & (pl.col('stage') == o['stage'])
                & (pl.col('prior_debut') == o['prior_debut']) & (pl.col('player_id') != pid))
            position_peers = population.filter(pl.col('source_position') == o['source_position'])
            same_position = len(position_peers) >= 4
            if same_position: population = position_peers
            exposure = [c for c in source.columns if c.endswith('_0_pa') and not c.startswith('pooled_')]
            distances = [(pl.col('age') - o['age']) ** 2 / 9,
                         4 * (pl.col('scout_rank_score_0') - o['scout_rank_score_0']) ** 2]
            distances += [(pl.col(c) - o[c]) ** 2 / 62500 for c in exposure]
            peers_frame = population.with_columns(pl.sum_horizontal(distances).alias('origin_distance')).sort('origin_distance', 'player_id').head(4)
            for p in peers_frame.select('player_id', 'player_name', 'age', 'stage', 'source_position', 'scout_rank_score_0', *exposure, 'origin_distance').to_dicts():
                peer_filter = (pl.col('player_id') == p['player_id']) & pl.col('season').is_between(origin - 2, origin)
                p.update(position_matched=same_position, before_contacts=before.filter(peer_filter).select('season', 'league_id', 'bucket', 'physical_contacts', 'classified_contacts', 'raw_narrative_hr').to_dicts(),
                    after_contacts=after.filter(peer_filter).select('season', 'league_id', 'bucket', 'physical_contacts', 'classified_contacts', 'raw_narrative_hr').to_dicts())
                peers.append(p)
        else:
            # MEX/source-only players may not be eligible in the historical
            # forecast panel. Keep that fact rather than invent an origin row.
            focal = before.filter((pl.col('player_id') == pid) & (pl.col('season') == origin))
            if len(focal):
                r = focal.sort('physical_contacts', descending=True).to_dicts()[0]
                peers = before.filter((pl.col('season') == origin) & (pl.col('league_id') == r['league_id']) & (pl.col('player_id') != pid))\
                    .with_columns((pl.col('physical_contacts') - r['physical_contacts']).abs().alias('origin_distance')).sort('origin_distance', 'player_id').head(4).to_dicts()
        cases.append(dict(player_id=pid, player_name=labels.get(pid), origin_year=origin, selection=reasons,
            official_separate_level_history=histories.to_dicts(), independent_player_game_controls=controls,
            before_measurements=before.filter(window).to_dicts(), after_measurements=after.filter(window).to_dicts(),
            before_nonzero_cells=bc.filter(window).to_dicts(), after_nonzero_cells=ac.filter(window).to_dicts(),
            changed_events=event_changes, contact_years_not_available=[y for y in range(origin - 2, origin + 1) if y not in YEARS],
            origin_only_peers=peers, peer_rule='Same origin/stage/debut and position when at least four; age, separate-level exposure and ranking distance. Source-only cases use same-league exposure. No future results.',
            existing_forecast_context=case_lookup.get((pid, origin), {}).get('forecasts'),
            new_forecast=None, forecast_effect='Source repair only; current forecasts unchanged and no new rate fit',
            source_only_case_not_in_forecast_panel=len(origin_row) != 1))
    write(target, dict(cases=cases, known_event_checks=known_rows,
        source_walkthrough_status='pending_readable_review', total_cases=len(cases), all_physical_ledgers_preserved=True,
        all_known_events_correct=True, no_new_model_fitted=True, forecasts_changed=False, protected_outcomes_used=False,
        inputs={str(p): sha256_file(p) for p in inputs}))
    print('Actual fixed and extreme source walks saved:', len(cases), flush=True)


if __name__ == '__main__': main()
