"""Collect historical context only, then audit every forecast-time source join."""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sys

import polars as pl
import requests
from universal_baseball.hitter_team_record import context, record_rows, team_rows, rights_events, latest_rights
from universal_baseball.storage import sha256_file
import evaluate_hitter_preseason_readiness_v68 as previous

ROOT = previous.ROOT
OUT = ROOT / 'reports/generated/hitter-team-record-v75'
YEARS = list(range(2011, 2025))
FIXED = [(701762, 2024), (694671, 2023), (677594, 2021), (624413, 2018),
         (641355, 2016), (702616, 2023), (670867, 2017), (592450, 2024)]


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, default=str)+'\n', encoding='utf8')


def capture(item):
    year, kind = item
    path = OUT/'captures'/f'{kind}-{year}.json'
    if path.exists():
        old = json.loads(path.read_text(encoding='utf8'))
        assert old['year'] == year and old['kind'] == kind
        return
    sports = [1] if year == 2020 else [1, 11, 12, 13, 14, 16] + ([15] if year < 2021 else [])
    params = ([{'season': year, 'sportId': sport} for sport in sports] if kind == 'teams' else
              [{'season': year, 'leagueId': league, 'standingsTypes': 'regularSeason'} for league in [103, 104]])
    url = f'https://statsapi.mlb.com/api/v1/{kind}'
    captures = []
    for query in params:
        response = requests.get(url, params=query, timeout=45)
        response.raise_for_status()
        captures.append(dict(url=response.url, params=query, payload=response.json()))
    payload = ({'teams': [t for c in captures for t in c['payload']['teams']]} if kind == 'teams' else
               {'records': [r for c in captures for r in c['payload']['records']]})
    (team_rows if kind == 'teams' else record_rows)(payload, year)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Raw public source capture, not an authored code/document edit.
    path.write_text(json.dumps(dict(year=year, kind=kind, captures=captures,
        retrieved_at=datetime.now(timezone.utc).isoformat(), params=params, payload=payload),
        ensure_ascii=False, allow_nan=False)+'\n', encoding='utf8')
    print(kind, year, 'captured', flush=True)


def source():
    assert not (OUT/'preflight.json').exists(), 'Preserve sealed source'
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(capture, [(y, k) for y in YEARS for k in ['teams', 'standings']]))
    teams, records, hashes = {}, {}, {}
    for year in YEARS:
        for kind, fn, lookup in [('teams', team_rows, teams), ('standings', record_rows, records)]:
            path = OUT/'captures'/f'{kind}-{year}.json'
            raw = json.loads(path.read_text(encoding='utf8'))
            lookup.update({(year, k): v for k, v in fn(raw['payload'], year).items()})
            hashes[str(path)] = sha256_file(path)
    # Independently sourced dated affiliate changes; not current metadata.
    expected = {(2018, 556): 133, (2019, 556): 140, (2021, 556): 158}
    for key, parent in expected.items():
        assert teams[key]['parent_id'] == parent, (key, teams[key])
    transactions = {}
    for year in range(2015, 2025):
        path = ROOT/'reports/generated/hitter-injury-history-v2'/('source-2015' if year == 2015 else 'source')/'captures'/f'transactions-{year}.json'
        obj = json.loads(path.read_text(encoding='utf8'))
        hashes[str(path)] = sha256_file(path)
        for event in rights_events(obj.get('payload', obj), year, teams):
            transactions.setdefault(event['player_id'], []).append(event)
    f = pl.read_parquet(previous.OUT/'features.parquet').sort('row_id')
    rp = ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet'
    sp = ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    roster = pl.read_parquet(rp)
    extra_roster_path = ROOT/'reports/generated/hitter-2020-cohort/40man.parquet'
    extra_full_path = ROOT/'reports/generated/hitter-2020-cohort/full-roster.parquet'
    extra_roster = pl.read_parquet(extra_roster_path)
    extra_full = pl.read_parquet(extra_full_path).sort('team_id', 'position')
    stints = pl.read_parquet(sp).filter((pl.col('season') <= 2024) & (pl.col('plate_appearances') > 0))
    listings = {(r['season'], r['player_id']): r['team_id'] for r in roster.iter_rows(named=True)}
    listings.update({(r['season'], r['player_id']): r['team_id'] for r in extra_roster.iter_rows(named=True)})
    raw_2020 = {}
    for r in extra_full.iter_rows(named=True):
        raw_2020.setdefault(r['player_id'], r['team_id'])
    primary = stints.sort(['season', 'player_id', 'plate_appearances', 'team_id'],
                         descending=[False, False, True, False]).unique(['season', 'player_id'], keep='first').sort('season')
    histories = {}
    for r in primary.iter_rows(named=True):
        histories.setdefault(r['player_id'], []).append(r)
    rows = []
    for r in f.iter_rows(named=True):
        year, pid = r['origin_year'], r['player_id']
        assert year in YEARS
        rostered = (year, pid) in listings
        if rostered:
            club_year, club = year, listings[(year, pid)]
        else:
            past = [x for x in histories.get(pid, []) if x['season'] <= year]
            last = past[-1] if past else None
            club_year, club = (last['season'], last['team_id']) if last else (None, None)
            if year == 2020 and last is None and pid in raw_2020:
                club_year, club = 2020, raw_2020[pid]
        assert club == r['team_id'], r['row_id']
        ctx = context(origin=year, club_year=club_year, club_id=club,
                      rostered=rostered, teams=teams, records=records)
        if year == 2020 and not rostered and club_year == year and pid in raw_2020:
            ctx['context_basis'] = 'Historical full roster proxy for unobserved 2020 entrant'
        event = latest_rights(transactions.get(pid, []), year)
        # A source-season acquisition/release supersedes batting-club ownership,
        # but does not replace a later dated December 31 roster listing.
        use_event = bool(not rostered and event and
                         int(event['known_date'][:4]) >= (club_year or 0))
        ctx['context_rights_override'] = int(use_event)
        ctx['context_rights_date'] = event['known_date'] if use_event else None
        ctx['context_rights_code'] = event['code'] if use_event else None
        ctx['context_rights_ids'] = event['transaction_ids'] if use_event else []
        if use_event:
            owner = event['parent_id']
            rec = records.get((year, owner))
            ctx.update(context_parent_id=owner,
                       context_parent=teams.get((year, owner), {}).get('parent_name'),
                       context_basis='Dated acquisition or release in or after last club source season',
                       context_reason='known' if rec else 'No resolved MLB owner after rights event',
                       org_record_known=int(rec is not None),
                       org_record_centered=rec['win_pct']-.5 if rec else 0.,
                       context_wins=rec['wins'] if rec else None,
                       context_losses=rec['losses'] if rec else None)
        rows.append(dict(row_id=r['row_id'], **ctx))
    new = f.join(pl.DataFrame(rows, infer_schema_length=None), on='row_id', validate='1:1').sort('row_id')
    assert new.select(f.columns).equals(f) and len(new) == 63282
    new.write_parquet(OUT/'features.parquet')
    coverage = new.group_by('origin_year', 'stage', 'prior_debut').agg(pl.len().alias('rows'),
        pl.col('org_record_known').sum().alias('known'), pl.col('player_id').n_unique().alias('people')).sort('origin_year', 'stage', 'prior_debut')
    cases = []
    context_columns = [c for c in new.columns if c.startswith('context_') or c.startswith('org_record_')]
    for pid, year in FIXED:
        row = new.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year)).row(0, named=True)
        peers = new.filter((pl.col('origin_year') == year) & (pl.col('stage') == row['stage']) &
                          (pl.col('prior_debut') == row['prior_debut']) & (pl.col('player_id') != pid)).with_columns(
            (((pl.col('age')-row['age'])/3)**2 + ((pl.col('minor_pa_0')-row['minor_pa_0'])/250)**2 +
             4*(pl.col('scout_rank_score_0')-row['scout_rank_score_0'])**2).alias('distance')).sort('distance', 'player_id').head(4)
        cases.append(dict(player_id=pid, origin_year=year, player_name=row['player_name'],
                          context={k: row[k] for k in context_columns},
                          peers=peers.select('player_id', 'player_name', 'age', 'stage', 'minor_pa_0',
                                             'scout_rank_score_0', *context_columns, 'next_pa').to_dicts()))
    inputs = [rp, sp, extra_roster_path, extra_full_path, previous.OUT/'features.parquet', previous.OUT/'preflight.json', Path(__file__),
              ROOT/'src/universal_baseball/hitter_team_record.py', ROOT/'docs/hitter-team-record-v75-contract.md']
    inputs.append(ROOT/'docs/hitter-team-record-v75-source-amendment.md')
    hashes.update({str(p): sha256_file(p) for p in inputs})
    write('source-report.json', dict(input_hashes=hashes, output_sha256=sha256_file(OUT/'features.parquet'),
        coverage=coverage.to_dicts(), source_cases=cases, checked_affiliate_changes=[dict(season=y, club_id=t, **teams[y,t]) for y,t in expected],
        historical_source_retrospectively_retrieved=True, player_walkthrough_status='source_review_pending',
        no_models_fitted=True, protected_outcomes_used=False, stale_club_not_used_as_current_owner=True,
        rights_coverage_qualification='2015–24 captured explicit events; incomplete minor-league rights coverage and earlier proxy affiliations remain qualified',
        rights_override_rows=int(new['context_rights_override'].sum()),
        no_resolved_owner_rows=int((new['context_reason']=='No resolved MLB owner after rights event').sum())))
    print('Source coverage', len(new), int(new['org_record_known'].sum()), flush=True)
    for c in cases:
        print(c['player_name'], c['origin_year'], c['context'], flush=True)


if __name__ == '__main__':
    source()
