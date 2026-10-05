"""Separate repaired NPB collector; old collector and KBO receipts untouched."""
from urllib.parse import urljoin
from pathlib import Path
import polars as pl
import capture_international_hitter_2025 as c
from universal_baseball.npb_hitter_2025_layout import batting_2025_rows
from universal_baseball.npb_history import roster_links,roster_names,attach_npb_ids,name_key,read_npb_crosswalk
from universal_baseball.npb_identity_overlay import reviewed_id
from universal_baseball.international_hitter_source_2025 import npb_2025_links
from universal_baseball.storage import sha256_file


def main():
    assert not (c.OUT/'npb-collection.json').exists()
    hashes=c.seal_paths()
    for p in [Path(__file__),c.ROOT/'src/universal_baseball/npb_hitter_2025_layout.py',
              c.ROOT/'docs/hitter-npb-2025-layout-amendment.md',c.ROOT/'tests/test_npb_hitter_2025_layout.py']:
        hashes[str(p)]=sha256_file(p)
    c.npb.RAW=c.RAW/'npb'
    index,meta=c.npb.capture('2025-season-index.html','https://npb.jp/bis/2025/stats/')
    ids,identity_meta=c.npb.capture('all-player-index.html','https://npb.jp/bis/players/all/index.html')
    links=npb_2025_links(index);listings=roster_links(ids,2025)
    rows=[];receipts=[meta,identity_meta];crosswalk=read_npb_crosswalk(c.REGISTER)
    for link in links:
        slug=link.rsplit('/',1)[-1].removesuffix('.html')
        body,meta=c.npb.capture(slug+'.html',urljoin('https://npb.jp',link))
        team,records=batting_2025_rows(body)
        url=urljoin('https://npb.jp',listings[name_key(team)])
        identity,identity_meta=c.npb.capture(slug+'-identities.html',url)
        listing=roster_names(identity,2025,team)
        for r in attach_npb_ids(records,listing):
            key,status=reviewed_id(r,listing);person=crosswalk.get(key,{})
            rows.append(dict(r,npb_id=key,npb_identity_status=status,
                player_id=person.get('player_id'),birth_date=person.get('birth_date'),
                chadwick_uuid=person.get('key_uuid'),table_slug=slug,
                source_url=meta['url'],source_sha256=meta['sha256'],
                identity_url=identity_meta['url'],identity_sha256=identity_meta['sha256']))
        receipts.extend([meta,identity_meta]);print('NPB 2025 verified layout',slug,len(records),flush=True)
    f=pl.DataFrame(rows,schema_overrides={'player_id':pl.Int64}).sort('table_slug','name_key')
    assert f.unique(['table_slug','name_key']).height==f.height and f['team_name'].n_unique()==12
    p=c.OUT/'npb-2025.parquet';assert not p.exists();f.write_parquet(p)
    assert all(sha256_file(Path(p))==h for p,h in hashes.items())
    c.save('npb-collection.json',dict(rows=len(f),pa=int(f['pa'].sum()),zero_pa=int((f['pa']==0).sum()),
        teams=12,unmatched_npb_rows=int(f['npb_id'].is_null().sum()),
        unmatched_mlb_rows=int(f['player_id'].is_null().sum()),residual_pa=int(f['unenumerated_pa'].sum()),
        source_hashes=hashes,captures=receipts,data_sha256=sha256_file(p),
        player_walkthrough_status='pending',source_review_status='pending',new_fits=0,forecast_changes=0,
        interrupted_capture_preserved=True,explicit_new_layout_parser=True))


if __name__=='__main__':main()
