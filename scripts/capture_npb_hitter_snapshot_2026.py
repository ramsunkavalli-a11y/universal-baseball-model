"""Current-listing recovery, preserving the stopped historical-listing reader."""
from pathlib import Path
from urllib.parse import urljoin
import polars as pl

import capture_international_hitter_snapshot_2026 as c
from universal_baseball.international_hitter_snapshot_2026 import npb_links, batting_rows, snapshot_date
from universal_baseball.npb_hitter_2026_identity import listings, names
from universal_baseball.npb_history import name_key, read_npb_crosswalk, attach_npb_ids
from universal_baseball.npb_identity_overlay import reviewed_id
from universal_baseball.storage import sha256_file


def main():
    assert not (c.OUT / 'npb-collection.json').exists()
    hashes = c.seals()
    for p in [Path(__file__), c.ROOT / 'src/universal_baseball/npb_hitter_2026_identity.py',
              c.ROOT / 'docs/hitter-npb-2026-identity-amendment.md']:
        hashes[str(p)] = sha256_file(p)
    c.npb.RAW = c.RAW / 'npb'
    body, im = c.npb.capture('index.html', 'https://npb.jp/bis/2026/stats/')
    roster, rm = c.npb.capture('current-roster-index.html', 'https://npb.jp/bis/teams/')
    clubs = listings(roster); crosswalk = read_npb_crosswalk(c.REGISTER)
    rows = []; receipts = [im, rm]; dates = []
    for link in npb_links(body):
        slug = Path(link).stem
        raw, meta = c.npb.capture(slug + '.html', urljoin('https://npb.jp', link))
        team, records = batting_rows(raw); asof = snapshot_date(raw); dates.append(asof)
        raw_id, identity_meta = c.npb.capture(slug + '-current-identity.html', urljoin('https://npb.jp', clubs[name_key(team)]))
        listing, birth_dates = names(raw_id, team)
        for r in attach_npb_ids(records, listing):
            key, status = reviewed_id(r, listing); person = crosswalk.get(key, {})
            dob = birth_dates.get(key); conflict = bool(dob and person.get('birth_date') and dob != person['birth_date'])
            rows.append(dict(r, npb_id=key, npb_identity_status=status, player_id=person.get('player_id'),
                birth_date=None if conflict else dob or person.get('birth_date'), static_DOB_conflict=conflict,
                register_birth_date=person.get('birth_date'), listing_birth_date=dob, table_slug=slug,
                provider_asof=asof, source_url=meta['url'], source_sha256=meta['sha256'],
                identity_url=identity_meta['url'], identity_sha256=identity_meta['sha256'],
                current_role_rights_status_used=False))
        receipts += [meta, identity_meta]
        print(f'NPB {slug}: {len(records)} snapshot rows, exact static identity links retained.', flush=True)
    assert len({d for d in dates if d}) <= 1, 'Moving snapshot dates'
    f = pl.DataFrame(rows, schema_overrides={'player_id': pl.Int64}).sort('table_slug', 'name_key')
    assert f['team_name'].n_unique() == 12 and f.unique(['table_slug', 'name_key']).height == len(f)
    c.OUT.mkdir(parents=True, exist_ok=True); p = c.OUT / 'npb.parquet'; assert not p.exists(); f.write_parquet(p)
    c.save('npb-collection.json', dict(league='NPB', source_year=2026, rows=len(f), teams=12, PA=int(f['pa'].sum()),
        zero_PA_rows=int((f['pa'] == 0).sum()), missing_source_key_rows=int(f['npb_id'].is_null().sum()),
        missing_MLB_key_rows=int(f['player_id'].is_null().sum()), DOB_conflict_rows=int(f['static_DOB_conflict'].sum()),
        provider_index_asof=snapshot_date(body), provider_table_dates=dates,
        season_complete=False, season_completion_status='unproven_snapshot_only', captures=receipts,
        source_hashes=hashes, data_sha256=sha256_file(p), player_walkthrough_status='pending',
        interrupted_collector_preserved=True, current_identity_used_only_for_static_keys=True, new_fits=0, forecast_changes=0))


if __name__ == '__main__': main()
