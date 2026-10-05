"""Preserve failed review and use annual count checks for every KBO player."""
from pathlib import Path
from datetime import date
import json
import review_international_hitter_2025 as r
from universal_baseball.kbo_identity import profile_identity
from universal_baseball.kbo_english_annual_counts import annual_counts
from universal_baseball.storage import sha256_file


def english_case(session,row,mlb_id):
    assert mlb_id is None, 'No outcome or current MLB status in this source review'
    key=row['kbo_id'];url='https://eng.koreabaseball.com/Teams/PlayerInfoHitter/Summary.aspx?pcode='+key
    _,meta=r.c.probe.request(session,'review-english-identity-'+key,url)
    raw=r.c.probe.RAW/('review-english-identity-'+key+'.html')
    identity=profile_identity(raw.read_bytes(),key)
    check=annual_counts(raw.read_bytes(),row['season'])
    for k,v in check['counts'].items():assert v==row[k],(key,row['season'],k,v,row[k])
    return dict(kbo_english_name=identity['english_name'],birth_date=identity['birth_date'],
        english_meta=meta,english_origin_count_fields_checked=13,annual_count_review=check,
        static_identity_only=True,same_provider_rendering=True,MLB_outcomes_used=False)


def main():
    original_save=r.c.save
    def preserve_selection(name,o):
        path=r.OUT/name
        if name=='walk-selection.json' and path.exists():
            assert json.loads(path.read_text(encoding='utf8'))==o,'Selection changed'
            return
        original_save(name,o)
    r.c.save=preserve_selection
    r.kr.english_case=english_case # Only this process; sealed old source unchanged.
    r.walks()
    paths=[Path(__file__),r.ROOT/'src/universal_baseball/kbo_english_annual_counts.py',
        r.ROOT/'tests/test_kbo_english_annual_counts.py',
        r.ROOT/'docs/hitter-kbo-2025-traded-player-review-amendment.md',
        r.OUT/'walk-selection.json',r.OUT/'player-walks.json']
    r.c.save('completed-walk-execution.json',dict(original_selection_unchanged=True,
        ordinary_traded_player_retained=True,earlier_execution_stop_documented=True,
        mechanical_source_walks_complete=True,readable_review_pending=True,new_fits=0,forecast_changes=0,
        hashes={str(p):sha256_file(p) for p in paths}))


if __name__=='__main__':main()
