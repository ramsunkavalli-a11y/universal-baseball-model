"""Stage a provenance-preserving historical contact rebuild; no model fitting."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import time
from threading import local
import xml.etree.ElementTree as ET
import requests
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.player_game_stats import player_game_asset_from_github_payload, project_player_game_batting
from universal_baseball.player_game_controls import resolve_player_game_contact_controls
from universal_baseball.hitter_contact_identity_rebuild import FIELDS, reconcile_contacts, select_authority_games, overlay_authority, contact_cells, measurement_changes
from universal_baseball.contact_identity_overlay import project_official_sequence_authority
from universal_baseball.contact_identity_overlay import contact_identity_residuals

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/hitter-contact-identity-rebuild'
RAW = ROOT / 'data/quarantine/hitter-contact-identity-rebuild'
WORK = Path('D:/UBM-Source-Cache/hitter-contact-identity-rebuild')
YEARS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
DOWNLOAD_YEARS = (2019, 2021, 2022, 2023, 2024)
LEVELS = {'aaa', 'aa', 'a+', 'a', 'a-', 'rk'}
CONTROL_FIELDS = ['game_id', 'game_date', 'game_type', 'league_id', 'team_id', 'player_id',
                  'batting_PA', 'batting_AB', 'batting_SO', 'batting_SF', 'batting_SH']
CONTRACT = ROOT / 'docs/hitter-contact-identity-rebuild-contract.md'
STORAGE_AMENDMENT = ROOT / 'docs/hitter-contact-identity-storage-amendment.md'
CLIENTS = local()


def official_client():
    if not hasattr(CLIENTS, 'session'):
        CLIENTS.session = requests.Session()
        CLIENTS.session.headers.update({'User-Agent': 'UBM-historical-participant-audit/1.0'})
    return CLIENTS.session


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str) + '\n', encoding='utf8')
    temporary.replace(path)


def read(path): return json.loads(path.read_text(encoding='utf8'))


def inventory():
    target = OUT / 'inventory.json'
    if target.exists():
        r = read(target); assert r['contract_sha256'] == sha256_file(CONTRACT)
        print('Reusing captured inventory:', len(r['selected_assets']), 'assets', flush=True)
        return
    # gh uses the configured credential without exposing a token to logs or tool output.
    release = json.loads(subprocess.check_output(['gh', 'api',
        'repos/armstjc/milb-data-repository/releases/tags/game_player_stats']))
    pages = json.loads(subprocess.check_output(['gh', 'api', '--paginate', '--slurp',
        f"repos/armstjc/milb-data-repository/releases/{release['id']}/assets?per_page=100"]))
    assets = [x for page in pages for x in page]
    selected = []
    for payload in assets:
        a = player_game_asset_from_github_payload(payload)
        if a and a.year in DOWNLOAD_YEARS and a.filename_level in LEVELS:
            selected.append(a.as_record())
    assert selected and len({a['name'] for a in selected}) == len(selected)
    assert all(a['browser_download_url'].startswith('https://github.com/armstjc/milb-data-repository/releases/download/') for a in selected)
    assert {a['year'] for a in selected} == set(DOWNLOAD_YEARS)
    write(target, dict(captured_at=datetime.now(timezone.utc).isoformat(), release_id=release['id'],
        contract_sha256=sha256_file(CONTRACT), selected_assets=selected,
        selected_bytes=sum(a['size_bytes'] for a in selected),
        source_inventory_pages=pages, protected_2026_selected=False))
    print(json.dumps(dict(selected_assets=len(selected), selected_bytes=sum(a['size_bytes'] for a in selected),
        per_year=[dict(year=y, assets=sum(a['year'] == y for a in selected),
                      bytes=sum(a['size_bytes'] for a in selected if a['year'] == y)) for y in DOWNLOAD_YEARS]), indent=2), flush=True)


def source_fingerprint(path):
    digest = hashlib.sha256(); size = 0
    with gzip.open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            size += len(chunk); digest.update(chunk)
    return size, digest.hexdigest()


def download_project(asset):
    path = RAW / 'player-game' / (asset['name'] + '.gz')
    projected = OUT / 'projected-controls' / (asset['name'] + '.parquet')
    note = projected.with_suffix('.json')
    if projected.exists() and note.exists():
        r = read(note)
        assert r['asset_id'] == asset['asset_id'] and r['expected_source_bytes'] == asset['size_bytes']
        assert sha256_file(path) == r['archive_sha256'] and sha256_file(projected) == r['projected_sha256']
        assert source_fingerprint(path) == (asset['size_bytes'], r['source_sha256'])
        return r
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        partial = path.with_suffix('.gz.part')
        error = None
        for attempt in range(3):
            try:
                if shutil.disk_usage(ROOT).free < 1024 ** 3:
                    raise ValueError('Reserved 1 GB working space reached; preserve completed sources')
                with requests.get(asset['browser_download_url'], timeout=(20, 90), stream=True) as response:
                    response.raise_for_status()
                    size = 0; digest = hashlib.sha256()
                    with gzip.open(partial, 'wb', compresslevel=6) as handle:
                        for chunk in response.iter_content(1024 * 1024):
                            size += len(chunk); digest.update(chunk); handle.write(chunk)
                if size != asset['size_bytes']:
                    raise ValueError('Downloaded bytes differ from captured release inventory')
                if source_fingerprint(partial) != (size, digest.hexdigest()):
                    raise ValueError('Compressed archive does not reproduce downloaded bytes')
                partial.replace(path)
                break
            except (requests.RequestException, ValueError) as exc:
                error = exc
                if attempt == 2: raise RuntimeError(f"Failed source {asset['name']}: {type(error).__name__}") from exc
                time.sleep(1 + attempt)
    source_bytes, source_hash = source_fingerprint(path)
    assert source_bytes == asset['size_bytes']
    with gzip.open(path, 'rb') as handle:
        frame = pl.read_csv(handle, columns=CONTROL_FIELDS,
            schema_overrides={c: pl.String for c in CONTROL_FIELDS}, null_values=['null', 'NaN', 'nan', ''])
    result = project_player_game_batting(frame, source_asset=asset['name'], season=asset['year'], game_type='R')
    projected.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(projected)
    r = dict(name=asset['name'], asset_id=asset['asset_id'], year=asset['year'], level=asset['filename_level'],
             expected_source_bytes=asset['size_bytes'], source_path=str(path), source_sha256=source_hash,
             archive_sha256=sha256_file(path), archive_bytes=path.stat().st_size,
             projected_path=str(projected), projected_sha256=sha256_file(projected),
             raw_rows=len(frame), retained_regular_rows=len(result))
    write(note, r)
    return r


def controls():
    target = OUT / 'controls.json'
    if target.exists(): raise FileExistsError('Controls already completed; continue selection rather than overwrite')
    inv = read(OUT / 'inventory.json'); assert inv['contract_sha256'] == sha256_file(CONTRACT)
    assert shutil.disk_usage(ROOT).free > 1024 ** 3, 'Insufficient reserved working space'
    records, failures = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        future = {pool.submit(download_project, a): a for a in inv['selected_assets']}
        for job in as_completed(future):
            asset = future[job]
            try:
                r = job.result(); records.append(r)
                print(f"controls {len(records)}/{len(future)} {r['name']} rows={r['retained_regular_rows']}", flush=True)
            except Exception as exc:
                failures.append(dict(name=asset['name'], error=str(exc), kind=type(exc).__name__))
                print('CONTROL SOURCE ERROR', asset['name'], type(exc).__name__, flush=True)
    if failures:
        write(OUT / 'control-errors.json', dict(failures=failures, completed=len(records)))
        raise RuntimeError('Source capture incomplete; preserve completed assets and retry failures')
    yearly = []
    for y in YEARS:
        output = OUT / f'controls-{y}.parquet'
        if y <= 2018:
            old = ROOT / f'reports/generated/hitter-v2-{y}-game-authority'
            source = old / f'tables/hitter_v2_player_game_authority_{y}_recovered.parquet'
            receipt = read(old / 'report.json')
            # The older report keeps table hashes under artifacts; inspect exact matching grain.
            known_hashes = json.dumps(receipt)
            h = sha256_file(source)
            assert h in known_hashes, 'Recovered control artifact not certified by its captured report'
            observations = project_player_game_batting(pl.read_parquet(source), source_asset=str(source), season=y, game_type='R')
            source_hashes = {str(source): h, str(old / 'report.json'): sha256_file(old / 'report.json')}
        else:
            selected = [r for r in records if r['year'] == y]
            observations = pl.concat([pl.read_parquet(r['projected_path']) for r in selected], how='vertical_relaxed')
            source_hashes = {r['projected_path']: r['projected_sha256'] for r in selected}
        resolved, metrics = resolve_player_game_contact_controls(observations)
        resolved.write_parquet(output)
        yearly.append(dict(year=y, output_path=str(output), output_sha256=sha256_file(output),
                           source_hashes=source_hashes, observed_rows=len(observations),
                           resolved_rows=len(resolved), metrics=metrics))
        print('RESOLVED', y, len(resolved), 'player games', flush=True)
    write(target, dict(contract_sha256=sha256_file(CONTRACT), storage_amendment_sha256=sha256_file(STORAGE_AMENDMENT),
                       inventory_sha256=sha256_file(OUT / 'inventory.json'),
                       assets=records, years=yearly, no_forecast_change=True, protected_2026_used=False))


def selection():
    target = OUT / 'selection.json'
    if target.exists(): raise FileExistsError('Selection already locked; continue official capture')
    controls_report = read(OUT / 'controls.json')
    assert controls_report['contract_sha256'] == sha256_file(CONTRACT)
    WORK.mkdir(parents=True, exist_ok=True)
    yearly = []
    for y in YEARS:
        note = WORK / f'selection-{y}.json'
        inputs = sorted((ROOT / f'data/working/pbp-opportunity-foundation-v1/season={y}').glob('level=*/terminal/*.parquet'))
        assert inputs, f'No historical source for {y}'
        record = next(r for r in controls_report['years'] if r['year'] == y)
        cp = Path(record['output_path']); assert sha256_file(cp) == record['output_sha256']
        source_hashes = {str(p): sha256_file(p) for p in inputs}
        if note.exists():
            r = read(note); assert r['source_hashes'] == source_hashes and r['control_sha256'] == record['output_sha256']
            assert all(sha256_file(Path(p)) == h for p, h in r['artifact_hashes'].items())
            yearly.append(r); continue
        raw = [pl.read_parquet(p, columns=['game_pk', 'at_bat_index', 'source_asset', *FIELDS]) for p in inputs]
        contacts, quarantine = reconcile_contacts(raw)
        assert contacts['season'].unique().to_list() == [y]
        membership, residuals = select_authority_games(contacts, pl.read_parquet(cp), quarantine)
        artifacts = {name: WORK / f'{name}-{y}.parquet' for name in ['contacts', 'quarantine', 'membership', 'residuals']}
        for name, frame in [('contacts', contacts), ('quarantine', quarantine), ('membership', membership), ('residuals', residuals)]:
            frame.write_parquet(artifacts[name])
        r = dict(year=y, contact_rows=len(contacts), quarantined_keys=len(quarantine), source_partitions=len(inputs),
            contact_games=len(membership), flagged_games=membership.filter(pl.col('triggered')).height,
            unflagged_sample_games=membership.filter(pl.col('unflagged_sample')).height,
            league_counts=membership.group_by('league_id').agg(pl.len().alias('games'), pl.col('triggered').sum().alias('flagged'),
                pl.col('unflagged_sample').sum().alias('sample')).sort('league_id').to_dicts(),
            source_hashes=source_hashes, control_sha256=record['output_sha256'],
            artifact_hashes={str(p): sha256_file(p) for p in artifacts.values()})
        write(note, r); yearly.append(r)
        print('SELECTED', y, len(contacts), 'contacts;', r['flagged_games'], 'flagged;', r['unflagged_sample_games'], 'audit games', flush=True)
    members = pl.concat([pl.read_parquet(WORK / f'membership-{y}.parquet') for y in YEARS], how='vertical_relaxed')
    assert members['game_pk'].n_unique() == len(members), 'A game appeared in more than one historical year'
    chosen = members.filter(pl.col('triggered') | pl.col('unflagged_sample'))
    chosen.write_parquet(WORK / 'selected-games.parquet')
    write(target, dict(contract_sha256=sha256_file(CONTRACT), controls_sha256=sha256_file(OUT / 'controls.json'),
        years=yearly, working_root=str(WORK), selected_game_count=len(chosen),
        selected_games_sha256=sha256_file(WORK / 'selected-games.parquet'),
        sample_locked_before_official_outcomes=True, no_forecast_change=True, protected_2026_used=False))


def capture_official(row, pilot_hashes):
    game = row['game_pk']; y = row['season']
    assert y in YEARS
    directory = WORK / 'official' / str(y); directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{game}.json.gz'; note = directory / f'{game}.receipt.json'
    if note.exists():
        r = read(note); assert r['game_pk'] == game and r['season'] == y
        assert sha256_file(path) == r['capture_sha256']
        assert sha256_file(Path(r['authority_path'])) == r['authority_sha256']
        return r
    reused = ROOT / f'reports/generated/hitter-detailed-contact-compatibility/official-captures/{game}.json'
    base_url = f'https://statsapi.mlb.com/api/v1/game/{game}/playByPlay'
    url = base_url + '?fields=allPlays,about,atBatIndex,matchup,batter,id'
    if str(reused) in pilot_hashes:
        assert sha256_file(reused) == pilot_hashes[str(reused)]
        obj = read(reused); payload = obj['payload']; captured = obj['captured_at']; url = obj['url']
        reused_source = str(reused)
    elif path.exists():
        with gzip.open(path, 'rt', encoding='utf8') as handle: obj = json.load(handle)
        assert obj['game_pk'] == game and obj['season'] == y and obj['url'].split('?')[0] == base_url
        url = obj['url']
        payload = obj['payload']; captured = obj['captured_at']; reused_source = obj.get('reused_source')
    else:
        error = None
        for attempt in range(3):
            try:
                response = official_client().get(url, timeout=(15, 45)); response.raise_for_status()
                payload = response.json()
                if not isinstance(payload.get('allPlays'), list) or not payload['allPlays']:
                    raise ValueError('Official capture has no play sequences')
                break
            except (requests.RequestException, ValueError) as exc:
                error = exc
                if attempt == 2: raise RuntimeError(f'Official game {game}: {type(error).__name__}') from exc
                time.sleep(1 + attempt)
        captured = datetime.now(timezone.utc).isoformat(); reused_source = None
    if not path.exists():
        partial = path.with_suffix('.gz.part')
        with gzip.open(partial, 'wt', encoding='utf8', compresslevel=6) as handle:
            json.dump(dict(game_pk=game, season=y, url=url, captured_at=captured, payload=payload, reused_source=reused_source), handle, ensure_ascii=False)
        partial.replace(path)
    sequences = [dict(game_pk=game, at_bat_number=p.get('about', {}).get('atBatIndex'),
                      batter_id=p.get('matchup', {}).get('batter', {}).get('id')) for p in payload['allPlays']]
    authority = project_official_sequence_authority(pl.DataFrame(sequences, schema_overrides={
        'game_pk': pl.Int64, 'at_bat_number': pl.Int64, 'batter_id': pl.Int64}))
    ap = directory / f'{game}.authority.parquet'; authority.write_parquet(ap)
    r = dict(game_pk=game, season=y, url=url, captured_at=captured, capture_path=str(path), capture_sha256=sha256_file(path),
        authority_path=str(ap), authority_sha256=sha256_file(ap), official_sequences=len(authority),
        source_triggered=row['triggered'], unflagged_sample=row['unflagged_sample'], reused_source=reused_source)
    write(note, r); return r


def official():
    target = OUT / 'official.json'
    if target.exists(): raise FileExistsError('Official capture completed; continue assembly')
    selection_report = read(OUT / 'selection.json')
    assert selection_report['contract_sha256'] == sha256_file(CONTRACT)
    assert sha256_file(WORK / 'selected-games.parquet') == selection_report['selected_games_sha256']
    games = pl.read_parquet(WORK / 'selected-games.parquet').to_dicts()
    pilot = read(ROOT / 'reports/model-evidence/hitter-detailed-contact-compatibility/official-adjudication.json')
    pilot_hashes = dict(pilot['input_hashes'])
    pilot_hashes.update({r['source_capture']: r['source_sha256'] for r in pilot['rows']})
    records, failures = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {pool.submit(capture_official, row, pilot_hashes): row for row in games}
        for job in as_completed(jobs):
            row = jobs[job]
            try: records.append(job.result())
            except Exception as exc:
                failures.append(dict(game_pk=row['game_pk'], season=row['season'], error=str(exc), kind=type(exc).__name__))
                print('OFFICIAL ERROR', row['game_pk'], type(exc).__name__, flush=True)
            completed = len(records) + len(failures)
            if completed % 100 == 0 or completed == len(games):
                print(f'OFFICIAL {completed}/{len(games)} complete={len(records)} failures={len(failures)}', flush=True)
    if failures:
        write(OUT / 'official-errors.json', dict(failures=failures, completed=len(records)))
        raise RuntimeError('Official coverage incomplete; preserve successful captures')
    write(target, dict(selection_sha256=sha256_file(OUT / 'selection.json'), records=sorted(records, key=lambda r: r['game_pk']),
        retrieval_amendment_sha256=sha256_file(ROOT / 'docs/hitter-contact-identity-retrieval-amendment.md'),
        current_capture_not_historical_vintage=True, protected_2026_used=False, no_forecast_change=True))


def thin_probe():
    target = OUT / 'thin-authority-probe.json'
    if target.exists(): raise FileExistsError('Preserve first probe')
    # Compare the exact required projection against full captures, not just
    # whether the endpoint responds or returns a plausible batter name.
    receipts = sorted((WORK / 'official').glob('*/*.receipt.json'))[:3]
    assert len(receipts) == 3
    results = []
    for note in receipts:
        r = read(note); assert sha256_file(Path(r['capture_path'])) == r['capture_sha256']
        url = r['url'].split('?')[0] + '?fields=allPlays,about,atBatIndex,matchup,batter,id'
        start = time.monotonic(); response = requests.get(url, timeout=(15, 45)); response.raise_for_status()
        payload = response.json()
        rows = [dict(game_pk=r['game_pk'], at_bat_number=p.get('about', {}).get('atBatIndex'),
            batter_id=p.get('matchup', {}).get('batter', {}).get('id')) for p in payload['allPlays']]
        projected = project_official_sequence_authority(pl.DataFrame(rows, schema_overrides={
            'game_pk': pl.Int64, 'at_bat_number': pl.Int64, 'batter_id': pl.Int64}))
        full = pl.read_parquet(r['authority_path']); assert projected.equals(full)
        cp = OUT / f"thin-probe-{r['game_pk']}.json"
        write(cp, dict(url=url, payload=payload, captured_at=datetime.now(timezone.utc).isoformat()))
        results.append(dict(game_pk=r['game_pk'], seconds=time.monotonic() - start, response_bytes=len(response.content),
            sequences=len(projected), identical_authority=True, capture_sha256=sha256_file(cp), full_receipt_sha256=sha256_file(note)))
    write(target, dict(cases=results, source_only=True, forecasts_changed=False, protected_2026_used=False))
    print(json.dumps(results, indent=2), flush=True)


def assemble():
    target = OUT / 'assembly.json'
    if target.exists(): raise FileExistsError('Assembly already exists; review it instead of overwrite')
    captured = read(OUT / 'official.json')
    assert captured['selection_sha256'] == sha256_file(OUT / 'selection.json')
    yearly = []
    sample_failed = False
    for y in YEARS:
        records = [r for r in captured['records'] if r['season'] == y]
        for r in records:
            assert sha256_file(Path(r['capture_path'])) == r['capture_sha256']
            assert sha256_file(Path(r['authority_path'])) == r['authority_sha256']
        authority = pl.concat([pl.read_parquet(r['authority_path']) for r in records], how='vertical_relaxed')
        sr = read(WORK / f'selection-{y}.json')
        assert all(sha256_file(Path(p)) == h for p, h in sr['artifact_hashes'].items())
        source = pl.read_parquet(WORK / f'contacts-{y}.parquet')
        membership = pl.read_parquet(WORK / f'membership-{y}.parquet')
        repaired, mismatches = overlay_authority(source, membership, authority)
        sample_failed |= bool(len(mismatches))
        events, counts, features = contact_cells(repaired)
        changed = events.filter((pl.col('source_batter_id') != pl.col('batter_mlbam_id')).fill_null(True))
        (WORK / 'assembly').mkdir(parents=True, exist_ok=True)
        paths = {name: WORK / 'assembly' / f'{name}-{y}.parquet' for name in ['repaired', 'cell-counts', 'cell-features', 'changed', 'sample-mismatches']}
        for name, frame in [('repaired', events), ('cell-counts', counts), ('cell-features', features),
                            ('changed', changed), ('sample-mismatches', mismatches)]: frame.write_parquet(paths[name])
        r = dict(year=y, physical_contacts=len(events), classified_contacts=events['cell_eligible'].sum(),
            changed_participants=len(changed), unflagged_mismatch_contacts=len(mismatches),
            unflagged_mismatch_games=mismatches['game_pk'].n_unique(),
            coverage=events.group_by('league_id', 'bucket', 'contact_profile_status').len().sort('league_id', 'contact_profile_status').to_dicts(),
            changed_groups=changed.group_by('league_id', 'bucket', 'terminal_outcome_group').len().to_dicts(),
            all_physical_fields_preserved=True, original_batter_preserved=True,
            artifact_hashes={str(p): sha256_file(p) for p in paths.values()})
        yearly.append(r); print('ASSEMBLED', y, 'changed', len(changed), 'unflagged failures', len(mismatches), flush=True)
    write(target, dict(official_sha256=sha256_file(OUT / 'official.json'), years=yearly,
        source_gate='failed_unflagged_audit' if sample_failed else 'pending_player_review',
        player_walkthrough_status='pending', no_forecast_change=True, protected_2026_used=False,
        learned_park_adjustments_used=False, source_repair_not_model_gain=True))
    if sample_failed: raise RuntimeError('Unflagged audit found hidden identity mismatches; broader source decision required')


def review_captured():
    """Inspect a hashed partial batch; never pretend the full source gate passed."""
    selection_report = read(OUT / 'selection.json')
    assert selection_report['selected_games_sha256'] == sha256_file(WORK / 'selected-games.parquet')
    wanted = set(pl.read_parquet(WORK / 'selected-games.parquet')['game_pk'].to_list())
    records = []
    for note in sorted((WORK / 'official').glob('*/*.receipt.json')):
        try: r = read(note)
        except json.JSONDecodeError: continue  # This receipt may be being finalized by the live capture.
        assert r['game_pk'] in wanted
        assert sha256_file(Path(r['capture_path'])) == r['capture_sha256']
        assert sha256_file(Path(r['authority_path'])) == r['authority_sha256']
        records.append(dict(r, receipt_path=str(note), receipt_sha256=sha256_file(note)))
    summaries = []
    for y in YEARS:
        captured = [r for r in records if r['season'] == y]
        if not captured: continue
        game_ids = [r['game_pk'] for r in captured]
        source = pl.read_parquet(WORK / f'contacts-{y}.parquet').filter(pl.col('game_pk').is_in(game_ids))
        membership = pl.read_parquet(WORK / f'membership-{y}.parquet').filter(pl.col('game_pk').is_in(game_ids))
        authority = pl.concat([pl.read_parquet(r['authority_path']) for r in captured])
        coverage = source.select('game_pk', 'at_bat_index').join(authority, on=['game_pk', 'at_bat_index'], how='left', validate='1:1')
        missing = coverage.filter(pl.col('official_batter_id').is_null())
        mismatches = source.join(authority, on=['game_pk', 'at_bat_index'], how='left', validate='1:1').filter(
            pl.col('official_batter_id').is_not_null() & (pl.col('official_batter_id') != pl.col('source_batter_id')).fill_null(True))
        r = dict(year=y, captured_games=len(membership), contacts_reviewed=len(source), missing_authority_sequences=len(missing),
            identity_mismatch_contacts=len(mismatches), identity_mismatch_games=mismatches['game_pk'].n_unique(),
            unflagged_mismatch_contacts=mismatches.join(membership.filter(pl.col('unflagged_sample')).select('game_pk'), on='game_pk', how='semi').height,
            missing_sequence_examples=missing.head(12).to_dicts(), identity_mismatch_examples=mismatches.head(12).to_dicts())
        if not len(missing):
            repaired, failures = overlay_authority(source, membership, authority)
            eligible = set(pl.read_parquet(WORK / f'residuals-{y}.parquet')['game_id'].to_list()) & set(game_ids)
            controlled = repaired.filter(pl.col('game_pk').is_in(list(eligible)))
            controls_table = pl.read_parquet(OUT / f'controls-{y}.parquet')
            before = contact_identity_residuals(controlled.select(source.columns), controls_table)
            after = contact_identity_residuals(controlled.drop('source_batter_id').rename({'batter_mlbam_id': 'source_batter_id'}), controls_table)
            r.update(controlled_games=len(eligible), absolute_player_count_residual_before=before['contact_count_difference'].abs().sum(),
                absolute_player_count_residual_after=after['contact_count_difference'].abs().sum(), physical_fields_preserved=True,
                unflagged_sample_pass_in_this_partial_batch=not len(failures))
        summaries.append(r)
    target = OUT / ('capture-review-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '.json')
    write(target, dict(selection_sha256=sha256_file(OUT / 'selection.json'), captured_game_count=len(records),
        selected_game_count=selection_report['selected_game_count'], years=summaries, captured_receipts=records,
        source_gate='incomplete', player_walkthrough_status='pending', complete_season_repair=False,
        partial_batch_not_global_corruption_estimate=True, forecasts_changed=False, protected_2026_used=False))
    print(json.dumps([ {k: v for k, v in r.items() if not k.endswith('examples')} for r in summaries], indent=2), flush=True)
    print('Partial review saved:', target, flush=True)


def review_season(y):
    """A completed season's actual measurements; the other seasons stay pending."""
    target = OUT / f'season-review-{y}-signed.json'
    if target.exists(): raise FileExistsError('Preserve the completed season review')
    r = read(WORK / f'selection-{y}.json')
    assert all(sha256_file(Path(p)) == h for p, h in r['artifact_hashes'].items())
    source = pl.read_parquet(WORK / f'contacts-{y}.parquet')
    membership = pl.read_parquet(WORK / f'membership-{y}.parquet')
    selected = membership.filter(pl.col('triggered') | pl.col('unflagged_sample'))['game_pk'].to_list()
    records, names = [], {}
    for game in selected:
        note = WORK / 'official' / str(y) / f'{game}.receipt.json'
        if not note.exists(): raise ValueError(f'Season not complete: official game {game} pending')
        record = read(note)
        assert sha256_file(Path(record['capture_path'])) == record['capture_sha256']
        assert sha256_file(Path(record['authority_path'])) == record['authority_sha256']
        records.append(dict(record, receipt_sha256=sha256_file(note)))
        if '?' not in record['url']:
            with gzip.open(record['capture_path'], 'rt', encoding='utf8') as handle: payload = json.load(handle)['payload']
            for play in payload['allPlays']:
                player = play.get('matchup', {}).get('batter', {})
                if player.get('fullName'): names[player['id']] = player['fullName']
    authority = pl.concat([pl.read_parquet(record['authority_path']) for record in records])
    repaired, mismatches = overlay_authority(source, membership, authority)
    if len(mismatches): raise ValueError('Unflagged mismatch: broader source decision required before season review')
    after_events, after_counts, after = contact_cells(repaired)
    before_source = source.filter(pl.col('source_batter_id').is_not_null()).with_columns(
        pl.col('source_batter_id').alias('batter_mlbam_id'), pl.lit('source_default').alias('participant_authority'))
    _, before_counts, before = contact_cells(before_source)
    delta = measurement_changes(before, after)
    changed = after_events.filter((pl.col('source_batter_id') != pl.col('batter_mlbam_id')).fill_null(True))
    cases = []
    rules = [('largest_contact_gain', 'delta_physical_contacts', True), ('largest_contact_loss', 'delta_physical_contacts', False),
             ('largest_hr_gain', 'delta_raw_narrative_hr', True), ('largest_hr_loss', 'delta_raw_narrative_hr', False)]
    selected_cases = {}
    for rule, column, descending in rules:
        row = delta.sort([column, 'player_id', 'league_id'], descending=[descending, False, False]).to_dicts()[0]
        selected_cases.setdefault((row['player_id'], row['league_id']), []).append(rule)
    dsl = delta.filter(pl.col('league_id') == 130).sort(['before_physical_contacts', 'player_id'], descending=[True, False]).to_dicts()[0]
    selected_cases.setdefault((dsl['player_id'], dsl['league_id']), []).append('DSL_largest_origin_contact_exposure')
    ordinary = delta.filter((pl.col('delta_physical_contacts') == 0) & (pl.col('delta_raw_narrative_hr') == 0)
        & (pl.col('before_physical_contacts') >= 100)).sort(['before_physical_contacts', 'player_id']).to_dicts()
    ordinary = ordinary[len(ordinary) // 2]
    selected_cases.setdefault((ordinary['player_id'], ordinary['league_id']), []).append('unchanged_median_exposure_control')
    controls_table = pl.read_parquet(OUT / f'controls-{y}.parquet')
    for (pid, league), selections in selected_cases.items():
        summary = delta.filter((pl.col('player_id') == pid) & (pl.col('league_id') == league)).to_dicts()[0]
        def cells(df): return df.filter((pl.col('player_id') == pid) & (pl.col('league_id') == league)).to_dicts()
        peers = delta.filter((pl.col('league_id') == league) & (pl.col('player_id') != pid)).with_columns(
            ((pl.col('before_physical_contacts') - summary['before_physical_contacts']).abs() / max(1, summary['before_physical_contacts'])
             + (pl.col('before_raw_narrative_hr') - summary['before_raw_narrative_hr']).abs() / max(1, summary['before_raw_narrative_hr'])).alias('source_distance'))\
            .sort(['source_distance', 'player_id']).head(4).to_dicts()
        for peer in peers: peer['player_name'] = names.get(peer['player_id'])
        controls = controls_table.filter((pl.col('player_id') == pid) & (pl.col('league_id') == league))
        stat_fields = ['batting_PA', 'batting_AB', 'batting_SO', 'batting_SF', 'batting_SH', 'expected_contact_count']
        cases.append(dict(player_id=pid, player_name=names.get(pid), origin_year=y, league_id=league, selection=selections,
            measurements=summary, independent_controls=controls.select(*[pl.col(c).sum() for c in stat_fields]).to_dicts(),
            independent_control_games=len(controls), unresolved_control_games=controls.filter(pl.col('expected_contact_count').is_null()).height,
            before_nonzero_cells=cells(before_counts), after_nonzero_cells=cells(after_counts),
            changed_source_events=changed.filter((pl.col('league_id') == league) & ((pl.col('source_batter_id') == pid) | (pl.col('player_id') == pid))).to_dicts(),
            origin_only_peers=peers, peer_rule='Same actual league, nearest pre-repair contact exposure and HR; no future outcomes, age/position/pedigree not matched',
            forecast_effect='Not fitted. Current count-based forecast is unchanged; corrected contact features are not promoted.',
            interpretation='Official matchup changes participant only. Geometry, contact result and sequence remain the original source evidence.'))
    (WORK / 'season-review-signed').mkdir(parents=True, exist_ok=True)
    paths = {name: WORK / 'season-review-signed' / f'{name}-{y}.parquet' for name in ['repaired', 'cell-counts', 'cell-features', 'changed']}
    for name, frame in [('repaired', after_events), ('cell-counts', after_counts), ('cell-features', after), ('changed', changed)]: frame.write_parquet(paths[name])
    write(target, dict(year=y, contact_rows=len(source), changed_participants=len(changed), unflagged_audit_games=membership['unflagged_sample'].sum(),
        unflagged_mismatch_contacts=0, all_selected_sequences_covered=True, all_physical_fields_preserved=True,
        cases=cases, official_receipts=records, artifact_hashes={str(p): sha256_file(p) for p in paths.values()},
        full_rebuild_status='pending_other_seasons_and_fixed_cases', complete_eight_season_repair=False,
        signed_count_differences=True, supersedes_case_selection_only=str(OUT / f'season-review-{y}.json'),
        protected_2026_used=False, forecasts_changed=False, source_repair_not_model_gain=True))
    print(json.dumps(dict(year=y, changed_participants=len(changed), cases=[dict(player_id=c['player_id'], name=c['player_name'],
        selections=c['selection'], measurements=c['measurements']) for c in cases]), indent=2), flush=True)


def display_names(y):
    target = OUT / f'display-names-{y}.json'
    if target.exists(): raise FileExistsError('Preserve display registry capture')
    review_path = OUT / f'season-review-{y}-signed.json'
    review = read(review_path)
    identities = sorted({c['player_id'] for c in review['cases']} |
        {p['player_id'] for c in review['cases'] for p in c['origin_only_peers']})
    url = 'https://statsapi.mlb.com/api/v1/people?personIds=' + ','.join(map(str, identities)) + '&fields=people,id,fullName'
    response = official_client().get(url, timeout=(15, 45)); response.raise_for_status()
    people = response.json()['people']
    assert {p['id'] for p in people} == set(identities)
    write(target, dict(url=url, captured_at=datetime.now(timezone.utc).isoformat(), people=people,
        season_review_sha256=sha256_file(review_path), display_only=True,
        not_forecast_features=True, protected_outcomes_used=False))
    labels = {p['id']: p['fullName'] for p in people}
    print(json.dumps([dict(player_id=c['player_id'], name=labels[c['player_id']], measurements=c['measurements']) for c in review['cases']], indent=2), flush=True)


def checkpoint():
    dest = ROOT / 'reports/model-evidence/hitter-contact-identity-rebuild'
    if (dest / 'checkpoint.json').exists(): raise FileExistsError('Preserve source milestone')
    suites = ET.parse(OUT / 'unit-tests.xml').getroot().findall('testsuite')
    assert sum(int(s.attrib['tests']) for s in suites) == 34
    assert all(int(s.attrib['failures']) == int(s.attrib['errors']) == 0 for s in suites)
    signed = read(OUT / 'season-review-2016-signed.json')
    assert signed['changed_participants'] == 1920 and signed['unflagged_mismatch_contacts'] == 0
    assert signed['signed_count_differences'] and signed['complete_eight_season_repair'] is False
    for p, h in signed['artifact_hashes'].items(): assert sha256_file(Path(p)) == h
    controls_report = read(OUT / 'controls.json'); selected = read(OUT / 'selection.json')
    assert selected['controls_sha256'] == sha256_file(OUT / 'controls.json')
    assert controls_report['contract_sha256'] == sha256_file(CONTRACT)
    for r in controls_report['years']: assert sha256_file(Path(r['output_path'])) == r['output_sha256']
    for r in selected['years']:
        for p, h in r['artifact_hashes'].items(): assert sha256_file(Path(p)) == h
    freeze = json.loads(subprocess.check_output([str(ROOT / '.venv/Scripts/python.exe'), '-X', 'utf8',
        str(ROOT / 'scripts/verify_hitter_full_2026_freeze.py')], cwd=ROOT))
    assert freeze['status'] == 'verified' and not freeze['protected_2026_opened']
    names = ['inventory.json', 'controls.json', 'selection.json', 'thin-authority-probe.json',
             'season-review-2016-signed.json', 'display-names-2016.json']
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copy2(OUT / name, dest / name)
        assert sha256_file(OUT / name) == sha256_file(dest / name)
    sources = [CONTRACT, STORAGE_AMENDMENT, ROOT / 'docs/hitter-contact-identity-working-storage.md',
        ROOT / 'docs/hitter-contact-identity-retrieval-amendment.md', ROOT / 'docs/hitter-contact-identity-review-correction.md',
        ROOT / 'docs/hitter-contact-identity-rebuild-progress.md', Path(__file__),
        ROOT / 'src/universal_baseball/hitter_contact_identity_rebuild.py', ROOT / 'tests/test_hitter_contact_identity_rebuild.py',
        OUT / 'unit-tests.xml', OUT / 'season-review-2016.json']
    write(dest / 'checkpoint.json', dict(source_gate='incomplete', season_2016_source_walk_status='complete',
        whole_rebuild_player_walkthrough_status='pending', focused_tests=34,
        freeze_verification=freeze, forecasts_changed=False, complete_eight_season_repair=False,
        source_hashes={str(p): sha256_file(p) for p in sources},
        copied_evidence_hashes={name: sha256_file(dest / name) for name in names},
        next_action='Finish the same live official capture, review the other seasons and fixed cases before a new model fit',
        whole_goal_complete=False))
    print('Source milestone sealed; full repair and model goal remain active.', flush=True)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('stage', choices=['inventory', 'controls', 'selection', 'official', 'thin-probe', 'assemble', 'review-captured', 'review-season', 'display-names', 'checkpoint'])
    parser.add_argument('--year', type=int, choices=YEARS, default=2016)
    args = parser.parse_args()
    {'inventory': inventory, 'controls': controls, 'selection': selection, 'official': official, 'thin-probe': thin_probe,
     'assemble': assemble, 'review-captured': review_captured, 'review-season': lambda: review_season(args.year),
     'display-names': lambda: display_names(args.year), 'checkpoint': checkpoint}[args.stage]()


if __name__ == '__main__': main()
