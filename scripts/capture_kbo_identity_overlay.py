"""Qualify exact static KBO joins, retaining every unmatched batting row."""
import json
from pathlib import Path

import polars as pl
import requests

import probe_kbo_hitting_source as probe
from universal_baseball.kbo_identity import profile_identity, register_index, match_identity
from universal_baseball.storage import sha256_file

ROOT = probe.ROOT
OUT = ROOT / 'reports/generated/kbo-identity-overlay'
SOURCE = ROOT / 'reports/generated/kbo-hitting-history'
NPB = ROOT / 'data/quarantine/npb-hitting-history'
CONTRACT = ROOT / 'docs/hitter-foreign-integration-readiness-contract.md'
REGISTER = NPB / 'chadwick-2e8e73355f9c77b963115377bd98c784cfeec10f.zip'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    assert not (OUT / 'collection.json').exists(), 'Preserve completed collection'
    review = read(SOURCE / 'review.json')
    for path, expected in review['hashes'].items():
        assert sha256_file(ROOT / path) == expected, path
    source = pl.read_parquet(SOURCE / 'first-team-batting.parquet')
    keys = source.filter(pl.col('pa') >= 100)['kbo_id'].unique().sort().to_list()
    assert len(keys) == 584
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in [
        CONTRACT, Path(__file__), ROOT / 'src/universal_baseball/kbo_identity.py',
        ROOT / 'scripts/probe_kbo_hitting_source.py', REGISTER,
        SOURCE / 'review.json', SOURCE / 'first-team-batting.parquet']}
    seal = dict(kbo_ids=keys, selection='at_least_one_100_PA_season_2005_2024',
                collection_priority_only=True, forecast_eligibility_changed=False,
                original_source_rows=source.height, hashes=hashes)
    probe.write_new(OUT / 'membership-seal.json', seal)
    index = register_index(REGISTER)
    session = requests.Session()
    results = []
    for i, key in enumerate(keys):
        path = OUT / 'identities' / (key + '.json')
        if path.exists():
            r = read(path)
            assert r['kbo_id'] == key and r['source_code_hashes'] == hashes
            raw = probe.RAW / ('review-english-identity-' + key + '.html')
            assert sha256_file(raw) == r['source_meta']['sha256']
            assert match_identity(profile_identity(raw.read_bytes(), key), index) == r['identity']
        else:
            url = 'https://eng.koreabaseball.com/Teams/PlayerInfoHitter/Summary.aspx?pcode=' + key
            _, meta = probe.request(session, 'review-english-identity-' + key, url)
            raw = probe.RAW / ('review-english-identity-' + key + '.html')
            identity = match_identity(profile_identity(raw.read_bytes(), key), index)
            r = dict(kbo_id=key, identity=identity, source_meta=meta,
                     source_code_hashes=hashes, current_salary_role_status_used=False)
            probe.write_new(path, r)
        results.append(r)
        if (i + 1) % 20 == 0 or i + 1 == len(keys):
            print(f'Identity records {i + 1}/{len(keys)}; exact MLBAM joins '
                  f'{sum(r["identity"]["player_id"] is not None for r in results)}', flush=True)
    identities = pl.DataFrame([r['identity'] for r in results],
                              schema_overrides={'player_id': pl.Int64, 'key_uuid': pl.String,
                                                'register_name': pl.String})
    matched = identities.filter(pl.col('player_id').is_not_null())
    assert matched['player_id'].n_unique() == matched.height, 'Conflicting KBO identities for MLBAM'
    assert not (OUT / 'identities.parquet').exists()
    identities.write_parquet(OUT / 'identities.parquet')
    joined = source.join(identities, on='kbo_id', how='left', validate='m:1')
    assert joined.select(source.columns).equals(source) and len(joined) == len(source)
    assert not (OUT / 'reviewed-batting.parquet').exists()
    joined.write_parquet(OUT / 'reviewed-batting.parquet')
    probe.write_new(OUT / 'collection.json', dict(
        collected_identities=len(results), original_source_rows=source.height,
        match_status=identities.group_by('match_status').len().sort('match_status').to_dicts(),
        MLBAM_joined_identities=matched.height,
        uncollected_source_ids=source['kbo_id'].n_unique() - identities.height,
        all_source_rows_preserved=True, forecasts_changed=False, new_fits=0,
        source_walkthrough_status='pending', historical_role_qualified=False,
        all_league_crosswalk_qualified=False, protected_2026_opened=False,
        hashes=hashes, identity_capture_hashes={r['kbo_id']: sha256_file(OUT / 'identities' / (r['kbo_id'] + '.json')) for r in results},
        output_hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in [
            OUT / 'membership-seal.json', OUT / 'identities.parquet', OUT / 'reviewed-batting.parquet']}))
    print('Static KBO identity collection complete', flush=True)


if __name__ == '__main__':
    main()
