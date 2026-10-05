import csv
import pytest
from universal_baseball.overseas_public_coverage import read_archive, coverage_status, REQUIRED


def record(**extra):
    return dict(system='Steamer', year=2023, label_verified=True,
                vintage_class='historical_preseason', rows=1, **extra)


def source(tmp_path, **changes):
    row = {c: '0' for c in REQUIRED}
    row.update(Name='An ordinary player', PlayerId='123', MLBAMID='456',
               PA='100', AB='85', H='20', **{'1B': '15', '2B': '3', '3B': '0', 'HR': '2'},
               BB='10', IBB='2', SO='25', HBP='2', SF='2', SH='1')
    row.update(changes)
    path = tmp_path / 'source.csv'
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row)); writer.writeheader(); writer.writerow(row)
    return path


def test_event_denominator_and_semantics(tmp_path):
    rows, note = read_archive(source(tmp_path), record())
    r = rows[456]
    assert r['event_probability'] == [.45, .25, .08, .02, .15, .03, 0, .02]
    assert sum(r['event_probability']) == pytest.approx(1)
    assert r['workload_interpretation'] == 'unconditional'
    assert not r['exact_snapshot_day_known']
    assert note['valid_ids'] == 1
    z = record(); z['system'] = 'ZiPS'
    assert read_archive(source(tmp_path), z)[0][456]['workload_interpretation'] == 'conditional'


def test_four_distinct_coverage_states():
    a = {('steamer', 2023): {1: {'PA': 0}, 2: {'PA': 150}}}
    assert coverage_status(a, 'steamer', 2022, 1)[0] == 'archive_year_unavailable'
    assert coverage_status(a, 'steamer', 2023, 3)[0] == 'identity_absent'
    assert coverage_status(a, 'steamer', 2023, 1)[0] == 'zero_projected_PA'
    assert coverage_status(a, 'steamer', 2023, 2)[0] == 'positive_projected_PA'


def test_invalid_identity_not_zero_or_fuzzy_match(tmp_path):
    rows, note = read_archive(source(tmp_path, MLBAMID=''), record())
    assert rows == {} and note['invalid_ids'][0]['Name'] == 'An ordinary player'


@pytest.mark.parametrize('changes', [{'PA': '99'}, {'H': '21'}, {'IBB': '11'},
                                      {'SO': '-1'}, {'BB': 'nan'}, {'SO': '100'}])
def test_bad_counts_stop(tmp_path, changes):
    with pytest.raises(ValueError):
        read_archive(source(tmp_path, **changes), record())


def test_duplicate_id_stops(tmp_path):
    path = source(tmp_path)
    text = path.read_text(encoding='utf-8-sig').splitlines()
    path.write_text('\n'.join([*text, text[1]]) + '\n', encoding='utf8')
    r = record(); r['rows'] = 2
    with pytest.raises(ValueError, match='Duplicate'):
        read_archive(path, r)


def test_protected_or_unverified_archive_stops(tmp_path):
    r = record(); r['year'] = 2026
    with pytest.raises(ValueError): read_archive(source(tmp_path), r)
    r = record(); r['label_verified'] = False
    with pytest.raises(ValueError): read_archive(source(tmp_path), r)
