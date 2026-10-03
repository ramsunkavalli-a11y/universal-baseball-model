"""Sufficient AB graduation evidence, not a complete rookie-eligibility label."""
import polars as pl

FEATURES=['scout_ab_graduated','scout_graduated_absent','scout_graduated_prior_score']


def overlay(frame, stints):
    raw=stints.filter((pl.col('sport_id')==1)&(pl.col('season')<=int(frame['origin_year'].max())))
    if raw.unique(['player_id','season']).height!=raw.height:
        raise ValueError('Duplicate MLB season totals')
    if raw.filter(pl.col('at_bats').is_null()|(pl.col('at_bats')<0)|(pl.col('at_bats')>pl.col('plate_appearances'))).height:
        raise ValueError('Invalid or missing MLB AB')
    lookup={}
    for r in raw.sort('player_id','season').iter_rows(named=True):
        lookup.setdefault(r['player_id'],[]).append((r['season'],r['at_bats']))
    rows=[]
    for r in frame.iter_rows(named=True):
        ab=sum(n for y,n in lookup.get(r['player_id'],[]) if y<=r['origin_year'])
        grad=int(ab>130)
        absent=(-1 if r['scout_listed_0']<0 else int(r['scout_listed_0']==0)) if grad else 0
        history=0.0
        if absent==1:
            for lag in (1,2):
                if r[f'scout_listed_{lag}']==1:
                    history=float(r[f'scout_rank_score_{lag}']);break
            else:
                if any(r[f'scout_listed_{lag}']<0 for lag in (1,2)):history=-1.0
        elif absent<0:history=-1.0
        rows.append(dict(row_id=r['row_id'],observed_mlb_ab_lower_bound=ab,
            scout_ab_graduated=grad,scout_graduated_absent=absent,scout_graduated_prior_score=history))
    return frame.join(pl.DataFrame(rows),on='row_id',validate='1:1')
