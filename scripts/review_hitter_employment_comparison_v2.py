"""Explicitly reuse the matched review and retain every earlier diagnostic origin."""
from pathlib import Path
import run_hitter_employment_comparison as base
import review_hitter_employment_comparison as review

FIRST=base.OUT
OUT=base.GEN/'hitter-employment-comparison-v2'
original_read=base.read


def read_retained(path):
    if Path(path)==base.OLD/'reviewed-cases.json':
        earlier=original_read(FIRST/'player-walks.json')
        return dict(cases=[dict(origin=c['origin']) for c in earlier['cases']])
    return original_read(path)


if __name__=='__main__':
    completed=original_read(FIRST/'final-review.json')
    assert completed['player_walkthrough_status']=='complete'
    base.verify(completed['hashes'])
    base.OUT=OUT;review.OUT=OUT;review.read=read_retained
    review.main()
