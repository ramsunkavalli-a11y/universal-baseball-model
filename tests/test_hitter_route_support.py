import polars as pl
from universal_baseball.hitter_route_support import tag, counts


def row(**kw):
    r = dict(row_id=1, player_id=10, age=24., on_40man=0, status_major_link=0,
        status_hard_unavailable=0, status_retired=0, pa_0=0, prior_debut=0,
        evidence_foreign_source_present=0, last_first_team_known=0, last_MLB_known=0,
        AA_0_pa=0., AAA_0_pa=0., work_0=0., work_1=0., work_2=0.,
        scout_listed_0=0, scout_rank_score_0=0., draft_known=0, draft_college=0,
        draft_year=None, origin_year=2024, pick_number=None, next_pa=0)
    return r | kw


def test_foreign_source_presence_is_not_observed_participation():
    f=tag(pl.DataFrame([row(evidence_foreign_source_present=1),
        row(row_id=2,evidence_foreign_source_present=1,last_first_team_known=1)]))
    assert f['audit_route'].to_list()==['never_other','foreign_no_MLB']


def test_routes_retain_interruption_and_hard_override():
    f=tag(pl.DataFrame([row(prior_debut=1,work_1=500.),
        row(row_id=2,pa_0=500.,status_hard_unavailable=1),row(row_id=3,AAA_0_pa=20.)]))
    assert f['audit_route'].to_list()==['absent_previous_MLB','known_unavailable','never_upper']
    assert f['audit_demonstrated_regular'].to_list()==[True,False,False]


def test_labels_do_not_change_routes_and_current_draft_is_explicit():
    f=pl.DataFrame([row(draft_known=1,draft_college=1,draft_year=2024,pick_number=4)])
    a=tag(f); b=tag(f.with_columns(pl.lit(700).alias('next_pa')))
    cols=[n for n in a.columns if n.startswith('audit_')]
    assert a.select(cols).equals(b.select(cols)) and a['audit_fresh_top10_college'][0]
    assert not tag(f.with_columns(pl.lit(2023).alias('draft_year')))['audit_fresh_top10_college'][0]


def test_support_counts_people_not_rows_and_retains_missing_strata():
    tr=tag(pl.DataFrame([row(),row(row_id=2),row(row_id=3,player_id=11)]))
    te=tag(pl.DataFrame([row(row_id=4),row(row_id=5,AAA_0_pa=10.)]))
    c=counts(tr,te)
    assert c['route_people'].to_list()==[2,0]
    assert c['stratum_people'].to_list()==[2,0]
