"""Independent raw-row reconciliation and source-only professional player walks."""
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys
import hashlib
import requests

from bs4 import BeautifulSoup
import polars as pl

import capture_npb_hitting_history as capture
from universal_baseball.npb_history import (
    COUNTS, history_at, name_key, read_npb_crosswalk, roster_names,
)
from universal_baseball.npb_identity_overlay import reviewed_id
from universal_baseball.storage import sha256_file

ROOT, RAW, OUT = capture.ROOT, capture.RAW, capture.OUT
EVIDENCE = ROOT/'reports/model-evidence/npb-hitting-history'
POPULATION = ROOT/'reports/generated/hitter-preseason-population-source/population.parquet'
PREDICTIONS = ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
FIXED = [(660271, 2017), (673548, 2021), (807799, 2022), (493114, 2011),
         (493120, 2007), (660294, 2019), (673451, 2019), (547887, 2012)]
FORECAST_FIELDS = ('player_id', 'origin_year', 'player_name', 'baseline_pa',
                   'baseline_p', 'baseline_conditional_pa', 'baseline_rate',
                   'combined_rate', 'combined_value')


def load_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def independent_rows(path):
    """Use positional raw counts, not the collector/validator implementation."""
    soup = BeautifulSoup(path.read_bytes(), 'html.parser')
    result = {}
    for tr in soup.find_all('tr', class_='ststats'):
        cells = tr.find_all('td', recursive=False)
        assert len(cells) == 24
        key = re.sub(r'\s+', '', cells[1].get_text())
        values = [int(c.get_text()) for c in cells[2:21]]
        assert key not in result
        assert values[8] == values[4]+values[5]+2*values[6]+3*values[7]
        assert values[1] >= values[2]+values[14]+values[16]+values[12]+values[13]
        result[key] = values
    assert result
    return result


def reconstruct_english(npb_rows, case):
    independent = []
    for row in npb_rows:
        url = row['source_url'].replace('/bis/', '/bis/eng/', 1)
        name = 'english-'+str(row['season'])+'-'+row['table_slug']+'.html'
        unavailable = RAW/(name+'.unavailable.json')
        if unavailable.exists():
            meta = load_json(unavailable)
            assert meta['url'] == url and meta['http_status'] == 404
            assert sha256_file(RAW/(name+'.404')) == meta['sha256']
            independent.append(dict(season=row['season'], status='English_rendering_unavailable_404',
                                    verified_fields=0, url=url, sha256=meta['sha256']))
            continue
        try:
            html, meta = capture.capture(name, url)
        except requests.HTTPError as error:
            response = error.response
            if response is None or response.status_code != 404:
                raise
            body = response.content
            path = RAW/(name+'.404')
            if path.exists():
                assert path.read_bytes() == body
            else:
                path.write_bytes(body)
            meta = dict(url=url, returned_url=response.url, http_status=404,
                        sha256=hashlib.sha256(body).hexdigest(), source_review_status='unavailable')
            capture.write_new(unavailable, meta)
            independent.append(dict(season=row['season'], status='English_rendering_unavailable_404',
                                    verified_fields=0, url=url, sha256=meta['sha256']))
            continue
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.get_text()
        assert str(row['season']) in title and 'Individual Batting' in title
        # Different language/name rendering; verify the full numeric stat line.
        target = [row[k] for k in COUNTS]
        candidates = []
        for tr in soup.find_all('tr', class_='ststats'):
            cells = tr.find_all('td', recursive=False)
            if len(cells) == 24 and [int(c.get_text()) for c in cells[2:21]] == target:
                candidates.append(cells[1].get_text(' ', strip=True))
        assert len(candidates) == 1, (case, row['season'], candidates)
        independent.append(dict(season=row['season'], status='English_counts_matched', english_name=candidates[0],
                                verified_fields=len(COUNTS), url=url,
                                sha256=meta['sha256']))
    return independent


def main():
    assert not (OUT/'review.json').exists(), 'Preserve completed source review'
    report = load_json(OUT/'collection.json')
    for field, path in [('contract_sha256', capture.CONTRACT),
                        ('parser_sha256', ROOT/'src/universal_baseball/npb_history.py'),
                        ('code_sha256', ROOT/'scripts/capture_npb_hitting_history.py'),
                        ('batting_sha256', OUT/'first-team-batting.parquet')]:
        assert report[field] == sha256_file(path)
    metadata_by_url = defaultdict(list)
    for p in RAW.glob('*.metadata.json'):
        metadata_by_url[load_json(p)['url']].append(p)
    for meta in report['captures']:
        # Receipts contain exact original file paths only through the cache names.
        metas = metadata_by_url[meta['url']]
        assert len(metas) == 1
        assert sha256_file(Path(str(metas[0]).removesuffix('.metadata.json'))) == meta['sha256']
    original = pl.read_parquet(OUT/'first-team-batting.parquet')
    records = original.to_dicts()
    groups = defaultdict(list)
    for row in records:
        groups[row['season'], row['table_slug']].append(row)
    checks, reviewed = [], []
    crosswalk = read_npb_crosswalk(RAW/('chadwick-'+capture.CHADWICK_SNAPSHOT_SHA+'.zip'))
    mapped_ids = [r['player_id'] for r in crosswalk.values() if r['player_id'] is not None]
    assert len(mapped_ids) == len(set(mapped_ids)), 'Conflicting NPB identities for one MLBAM'
    for (season, slug), rows in sorted(groups.items()):
        independent = independent_rows(RAW/f'{season}-{slug}.html')
        assert set(independent) == {r['name_key'] for r in rows}
        names = roster_names((RAW/f'{season}-{slug}-identities.html').read_bytes(), season, rows[0]['team_name'])
        for row in rows:
            assert independent[row['name_key']] == [row[k] for k in COUNTS]
            exact = names.get(row['name_key'], set())
            assert row['npb_id'] == (next(iter(exact)) if len(exact) == 1 else None)
            npb_id, status = reviewed_id(row, names)
            if status == 'unique_same_team_published_initial_alias':
                aliases = set()
                for key, ids in names.items():
                    if len(key) > 2 and re.fullmatch(r'[A-ZＡ-Ｚ][.．]', key[:2]) and key[2:] == row['name_key']:
                        aliases.update(ids)
                assert aliases == {npb_id}
            person = crosswalk.get(npb_id, {})
            reviewed.append(dict(row, npb_id=npb_id, npb_identity_status=status,
                                 chadwick_uuid=person.get('key_uuid'), player_id=person.get('player_id'),
                                 birth_date=person.get('birth_date'),
                                 crosswalk_status='missing_npb_identity' if npb_id is None else
                                 'missing_chadwick_npb' if not person else
                                 'npb_and_mlbam' if person.get('player_id') else 'npb_without_mlbam'))
        checks.append(dict(season=season, table=slug, reconstructed_rows=len(rows),
                           independently_reconstructed_fields=len(rows)*len(COUNTS)))
    assert len(checks) == 240 and len(reviewed) == len(records)
    reviewed_data = pl.DataFrame(reviewed).sort('season', 'table_slug', 'name_key')
    assert reviewed_data.select('season', 'table_slug', 'name_key', *COUNTS).equals(original.select('season', 'table_slug', 'name_key', *COUNTS))
    for a, b in zip(original.iter_rows(named=True), reviewed_data.iter_rows(named=True), strict=True):
        assert all(a[k] == b[k] for k in original.columns if k not in ('npb_id', 'npb_identity_status', 'chadwick_uuid', 'player_id', 'birth_date', 'crosswalk_status'))
        if a['npb_id'] is not None:
            assert b['npb_id'] == a['npb_id']
    reviewed_data.write_parquet(OUT/'reviewed-batting.parquet')
    laird = reviewed_data.filter((pl.col('season') == 2017)&(pl.col('npb_id') == '23525130'))
    assert laird.height == 1
    laird = laird.row(0, named=True)
    assert laird['player_name_ja'] == 'レアード' and laird['player_id'] == 477186
    assert laird['npb_identity_status'] == 'unique_same_team_published_initial_alias'
    assert [laird[k] for k in ('pa', 'hits', 'hr', 'bb', 'so')] == [571, 115, 32, 54, 125]
    laird_control = dict(npb_id=laird['npb_id'], player_id=laird['player_id'], season=2017,
                         source_url=laird['source_url'], identity_url=laird['identity_url'],
                         observed_counts={k:laird[k] for k in COUNTS},
                         source_name='レアード', identity_name='Ｂ．レアード',
                         rule=laird['npb_identity_status'], raw_reconstruction_passed=True)

    # Histories attach to the already sealed preseason source population, not future arrivals.
    population_hash, prediction_hash = sha256_file(POPULATION), sha256_file(PREDICTIONS)
    population = pl.read_parquet(POPULATION)
    by_mlb = defaultdict(set)
    for r in crosswalk.values():
        if r['player_id']:
            by_mlb[r['player_id']].add(r['key_npb'])
    inputs = []
    for p in population.iter_rows(named=True):
        npb_ids = by_mlb.get(p['player_id'], set())
        assert len(npb_ids) <= 1
        if not npb_ids:
            continue
        npb_id = next(iter(npb_ids))
        hist = history_at(reviewed, npb_id, p['origin_year'])
        if not hist['observed_history_pa']:
            continue
        birthday = crosswalk[npb_id]['birth_date']
        age = ((date.fromisoformat(p['information_date'])-date.fromisoformat(birthday)).days/365.2425
               if birthday else None)
        inputs.append(dict(candidate_key=p['candidate_key'], player_id=p['player_id'],
                           player_name=p['player_name'], current_model_origin=p['current_model_origin'],
                           information_date=p['information_date'], age_at_information_date=age,
                           birth_date=birthday, **hist))
    pl.DataFrame(inputs).sort('origin_year', 'player_id').write_parquet(OUT/'origin-inputs.parquet')
    # Reconstruct each input with only origin-known rows and an adversarial future mutation.
    for r in inputs:
        before = history_at(reviewed, r['npb_id'], r['origin_year'])
        truncated = [x for x in reviewed if x['season'] <= r['origin_year']]
        assert before == history_at(truncated, r['npb_id'], r['origin_year'])
        assert before == history_at(reviewed+[dict(reviewed[0], npb_id=r['npb_id'], season=2099, pa=9999, hr=999)], r['npb_id'], r['origin_year'])
    capture.write_new(OUT/'input-membership-seal.json', dict(
        population_sha256=population_hash, original_predictions_sha256=prediction_hash,
        inputs_sha256=sha256_file(OUT/'origin-inputs.parquet'),
        identities=[[r['candidate_key'], r['npb_id']] for r in inputs],
        cutoff_mutation_invariant=True, future_labels_used=False))

    # Only now inspect unchanged saved forecasts for the already fixed player review.
    # Do not read outcomes or public forecasts into this source qualification.
    predictions = pl.read_parquet(PREDICTIONS, columns=list(FORECAST_FIELDS))
    selected = list(FIXED)
    fixed_ids = {pid for pid, _ in FIXED}
    ordinary = reviewed_data.filter((pl.col('season') == 2024)&(pl.col('pa') >= 100)&
                                   pl.col('npb_id').is_not_null()&~pl.col('player_id').is_in(list(fixed_ids)).fill_null(False)).sort('npb_id')
    assert ordinary.height
    ordinary_row = ordinary.row(0, named=True)
    # NPB identity is the selection authority; it need not have an MLBAM mapping.
    cases = []
    selected_npb = [(next(k for k, p in crosswalk.items() if p['player_id'] == pid), origin, 'fixed')
                    for pid, origin in selected]
    selected_npb.append((ordinary_row['npb_id'], 2024, 'lowest_NPB_ID_100PA_ordinary'))
    for npb_id, origin, rule in selected_npb:
        person = crosswalk.get(npb_id, {})
        pid = person.get('player_id')
        history = history_at(reviewed, npb_id, origin)
        assert history['observed_history_pa'] > 0
        recent_rows = [r for r in reviewed if r['npb_id'] == npb_id and origin-2 <= r['season'] <= origin]
        origin_rows = [r for r in reviewed if r['npb_id'] == npb_id and r['season'] == origin]
        # English is an independent official rendering of the same fixed numeric seasons.
        english = reconstruct_english([r for r in recent_rows if r['pa'] > 0], (npb_id, origin))
        saved = predictions.filter((pl.col('player_id') == pid)&(pl.col('origin_year') == origin)) if pid else predictions.head(0)
        assert saved.height <= 1
        birthday = person.get('birth_date')
        age = ((date(origin, 12, 31)-date.fromisoformat(birthday)).days/365.2425 if birthday else None)
        pools = []
        for candidate_id in sorted({r['npb_id'] for r in reviewed if r['npb_id'] and r['season'] == origin and r['pa'] >= 100}):
            if candidate_id == npb_id:
                continue
            candidate = crosswalk.get(candidate_id, {})
            birth = candidate.get('birth_date')
            if not birth or age is None:
                continue
            candidate_age = (date(origin, 12, 31)-date.fromisoformat(birth)).days/365.2425
            if abs(candidate_age-age) > 5:
                continue
            h = history_at(reviewed, candidate_id, origin)
            if not h['recent_counts']['pa']:
                continue
            # Outcome-blind nearest NPB peers; league performance, not claimed MLB-quality comps.
            distance = abs(candidate_age-age)/5+abs(h['recent_counts']['pa']-history['recent_counts']['pa'])/600
            distance += abs(h['k_rate']-history['k_rate'])/.1+abs(h['hr_rate']-history['hr_rate'])/.03
            pools.append((distance, candidate_id, candidate, candidate_age, h))
        peers = [dict(npb_id=k, name=(p.get('name_first', '')+' '+p.get('name_last', '')).strip(),
                      age=round(a, 2), recent_counts=h['recent_counts'], k_rate=h['k_rate'], hr_rate=h['hr_rate'],
                      selection_distance=d, MLB_outcomes_used_for_selection=False)
                 for d, k, p, a, h in sorted(pools, key=lambda x:(x[0], x[1]))[:3]]
        source_population = population.filter((pl.col('player_id') == pid)&(pl.col('origin_year') == origin)) if pid else population.head(0)
        cases.append(dict(npb_id=npb_id, player_id=pid, origin_year=origin, selection_rule=rule,
                          name=(person.get('name_first', '')+' '+person.get('name_last', '')).strip() or origin_rows[0]['player_name_ja'],
                          birth_date=birthday, origin_end_age=age, recent_source_rows=recent_rows,
                          history=history, english_checks=english, peers=peers,
                          source_population_rows=source_population.to_dicts(),
                          unchanged_saved_forecast=saved.to_dicts(), candidate_forecast=None,
                          mlb_translation_fitted=False, pitcher_role_inferred_from_batting=False))
    capture.write_new(OUT/'player-cases.json', dict(cases=cases, future_MLB_outcomes_used=False))
    write_walkthrough(cases)
    tests = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_npb_history.py',
                            'tests/test_npb_identity_overlay.py', '-q'], cwd=ROOT, capture_output=True, text=True)
    assert tests.returncode == 0, tests.stdout+tests.stderr
    freeze = subprocess.run([sys.executable, 'scripts/verify_hitter_full_2026_freeze.py'],
                             cwd=ROOT, capture_output=True, text=True)
    assert freeze.returncode == 0, freeze.stdout+freeze.stderr
    assert sha256_file(POPULATION) == population_hash and sha256_file(PREDICTIONS) == prediction_hash
    result = dict(seasons=report['seasons'], raw_source_captures=len(report['captures']),
                  rows=reviewed_data.height, independent_checks=checks,
                  original_identity_status=report['identity_status'],
                  reviewed_identity_status=reviewed_data.group_by('npb_identity_status').len().sort('npb_identity_status').to_dicts(),
                  reviewed_crosswalk_status=reviewed_data.group_by('crosswalk_status').len().sort('crosswalk_status').to_dicts(),
                  source_population_rows=population.height, joined_origin_inputs=len(inputs),
                  joined_players=len({r['player_id'] for r in inputs}),
                  input_origin_counts=pl.DataFrame(inputs).group_by('origin_year').len().sort('origin_year').to_dicts(),
                  source_walks=len(cases), player_walkthrough_status='complete_for_source',
                  english_verified_season_rows=sum(x['verified_fields'] == 19 for c in cases for x in c['english_checks']),
                  english_unavailable_season_rows=sum(x['verified_fields'] == 0 for c in cases for x in c['english_checks']),
                  english_validation_complete=all(x['verified_fields'] == 19 for c in cases for x in c['english_checks']),
                  initial_alias_real_player_control=laird_control,
                  forecasts_changed=False, new_fits=0, kbo_collected=False,
                  mlb_translation_fitted=False, protected_2026_opened=False,
                  tests=tests.stdout, protected_freeze=freeze.stdout,
                  public_raw_or_bulk_redistribution_approved=False,
                  hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [
                      capture.CONTRACT, ROOT/'docs/hitter-foreign-history-name-amendment.md',
                      ROOT/'docs/hitter-foreign-history-language-review-amendment.md',
                      ROOT/'src/universal_baseball/npb_identity_overlay.py', Path(__file__),
                      OUT/'first-team-batting.parquet', OUT/'reviewed-batting.parquet',
                      OUT/'origin-inputs.parquet', OUT/'input-membership-seal.json', OUT/'player-cases.json',
                      OUT/'player-walkthrough.md', OUT/'collection.json', OUT/'probe.json']})
    capture.write_new(OUT/'review.json', result)
    # Only aggregate evidence and a bounded attributed player review leave private cache.
    capture.write_new(EVIDENCE/'review.json', result)
    capture.write_new(EVIDENCE/'collection-summary.json', {
        k:v for k, v in report.items() if k != 'captures'})
    summary = (OUT/'player-walkthrough.md').read_text(encoding='utf8')
    path = EVIDENCE/'player-walkthrough.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_text(encoding='utf8') == summary
    else:
        path.write_text(summary, encoding='utf8', newline='\n')
    print(json.dumps({k:v for k, v in result.items() if k not in ['hashes', 'independent_checks']}, ensure_ascii=False), flush=True)


def write_walkthrough(cases):
    lines = ['# NPB history player review', '',
             '2026-10-04. Source-only review, not a fitted MLB translation. All foreign season inputs are before the origin; existing forecasts are unchanged. Counts are from [official NPB season tables](https://npb.jp/bis/eng/2017/stats/), identities/DOB from the pinned [Chadwick register](https://github.com/chadwickbureau/register). Raw/bulk data remain private.', '',
             'Fixed eight cases plus the lowest NPB ID with 100 or more 2024 PA outside the fixed names. Peers are selected only from NPB age/exposure/K/HR distance, not future MLB success. These are NPB production comparisons, not certified MLB talent comparables. No model gain, harm or outcome category exists without a new fit.', '']
    for c in cases:
        h = c['history']
        lines += [f"## {c['name']} at the {c['origin_year']} origin", '',
                  f"NPB ID {c['npb_id']}; MLBAM {c['player_id']}; DOB {c['birth_date']}; age at year end {c['origin_end_age']}. Selection: {c['selection_rule']}.", '',
                  '| NPB season | PA | H | 2B | 3B | HR | BB | IBB | K |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for r in c['recent_source_rows']:
            lines.append('| '+ ' | '.join(str(r[k]) for k in ('season', 'pa', 'hits', 'doubles', 'triples', 'hr', 'bb', 'ibb', 'so'))+' |')
        lines += ['', f"Observed NPB history: {h['history_seasons']}; {h['observed_history_pa']} PA. Three-year UBB/PA {h['ubb_rate']:.4f}, K/PA {h['k_rate']:.4f}, HR/PA {h['hr_rate']:.4f}, BABIP {h['babip']:.4f}. These are raw NPB rates, not park-adjusted or translated MLB rates. Experience before 2005 is unavailable, so observed years are not a complete professional-career total.", '',
                  f"English official tables match all nineteen count fields for {sum(x['verified_fields'] == 19 for x in c['english_checks'])} recent positive-PA team-seasons; {sum(x['verified_fields'] == 0 for x in c['english_checks'])} English renderings return 404 and remain unavailable. Japanese raw counts are independently reconstructed in every case. Zero-PA rows remain in the source; no English identity is inferred from a shared all-zero stat line. No future MLB result is needed to recover this history.", '']
        old = c['unchanged_saved_forecast']
        if old:
            r = old[0]
            keys = [k for k in FORECAST_FIELDS if k not in ('player_id', 'origin_year', 'player_name')]
            lines.append('Unchanged saved forecast intermediates: '+str({k:r[k] for k in keys})+'. Foreign inputs are not yet consumed by this saved model.')
        else:
            lines.append('No saved forecast row in the existing research candidate. This source supplies previously missing evidence; it does not fabricate a prediction.')
        pop = c['source_population_rows']
        if pop:
            lines.append(f"The sealed preseason source has {pop[0]['recent_domestic_pa']} recent domestic PA and {pop[0]['recent_mlb_pa']} recent MLB PA. That domestic window is not the entire professional record.")
        else:
            lines.append('No row in the sealed MLB-context preseason population. NPB performance alone does not establish an MLB job or new model eligibility.')
        lines += ['', 'Origin-known NPB peers:', '']
        for p in c['peers']:
            lines.append(f"- {p['name']} (NPB {p['npb_id']}), age {p['age']}, recent PA {p['recent_counts']['pa']}, K/PA {p['k_rate']:.4f}, HR/PA {p['hr_rate']:.4f}. No MLB outcome was used to select this peer.")
        if not c['peers']:
            lines.append('- No supported age/production peers; do not manufacture a comparable.')
        lines += ['', 'Baseball interpretation: professional hitting evidence is present despite an empty or incomplete domestic window. It supports a separate league-translation input, not an automatic MLB-average prior, guaranteed workload, nationality bonus or superstar claim. Batting exposure alone does not certify fielding position or a two-way pitching role.', '']
    lines += ['## Remaining limits', '',
              'No MLB translation or model accuracy gain was estimated. NPB pitcher batting remains in raw source tables: do not use the unfiltered league average as a hitter-only talent prior. Missing identities and earlier history remain explicit. KBO inputs, park/season adjustments, mover selection bias, historical roster/employment integration and mature player-held-out training remain to be resolved. Protected forecasts and outcomes stay unchanged.']
    path = OUT/'player-walkthrough.md'
    text = '\n'.join(lines)+'\n'
    if path.exists():
        assert path.read_text(encoding='utf8') == text
    else:
        path.write_text(text, encoding='utf8', newline='\n')


if __name__ == '__main__':
    main()
