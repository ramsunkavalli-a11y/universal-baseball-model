"""Separate read-only frozen-versus-realized view; no model or score changes."""
from pathlib import Path
import gzip
import json
import math
import polars as pl
from universal_baseball.storage import sha256_file
from score_hitter_final_2026 import ROOT,OUT,read,write

OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
DEST=ROOT/'reports/generated/hitter-final-2026-explorer'


def clean(v):
    if isinstance(v,float) and not math.isfinite(v):return None
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    return v


def main():
    assert not DEST.exists(),'Keep separate explorer build immutable'
    review=read(OUT/'review-completion.json');score=read(OUT/'score-report.json')
    assert review['player_walkthrough_status']=='complete' and review['no_post_result_forecast_change']
    for path,sha in review['input_hashes'].items():assert sha256_file(Path(path))==sha,path
    paths=[OLD/'opportunity-history-sources-v2/captures/2025/teams.json.gz',ROOT/'reports/generated/hitter-rosters-2025-source/captures/teams-2025.json.gz']
    mapping={}
    for path in paths:
        data=json.load(gzip.open(path,'rt',encoding='utf8'));data=data.get('payload',data)
        for t in data['teams']:
            assert int(t['season'])==2025
            mapping[t['id']]=dict(club=t['name'],org=t['name'] if t['sport']['id']==1 else t.get('parentOrgName') or 'Unknown organization')
    q=pl.read_parquet(OUT/'scored-fixed-cohort.parquet')
    fields=['player_id','player_name','row_id','outer_fold','age','age_unknown','stage','source_position','team_id','on_40man',
        'pa_0','pa_1','pa_2','minor_pa_0','minor_pa_1','minor_pa_2','career_mlb_observed_pa','translated_missing',
        'translation_supported_pa','translation_total_pa','translation_buckets','translated_reliability','sc_tracked',
        'scout_listed_0','scout_rank_score_0','draft_known','draft_rank','reported_retired','hard_unavailable',
        'participation_probability','conditional_pa','expected_pa','hitting_wins_per_600','batting_contribution','talent_route',
        'actual_pa','actual_relative_rate','actual_relative_value','actual_common_value','contribution_error','pa_error',
        'sparse_profile','unseen_profile','other','K','UBB','HBP','1B','2B','3B','HR']
    rows=[]
    for r in q.select(fields).iter_rows(named=True):
        r.update(mapping.get(r['team_id'],dict(club='Unknown source club',org='Unknown organization')))
        rows.append(clean(r))
    source_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    counts=pl.read_parquet(source_path).filter(pl.col('season').is_between(2023,2025));history={}
    for r in counts.iter_rows(named=True):
        pid=r.pop('player_id');history.setdefault(str(pid),[]).append(r)
    walks={}
    for w in read(OUT/'player-walks.json')['walks']:
        walks[str(w['player_id'])]={k:w[k] for k in ['selection','origin_peers','support','rate_intercept','rate_terms','error_accounting','baseball_review_notes']}
        walks[str(w['player_id'])]['pa_paths']=w['conditional_pa_trace']['feature_effects'][:8]
        walks[str(w['player_id'])]['participation_paths']=w['participation_trace']['feature_effects'][:8]
    outside=pl.read_parquet(OUT/'unmodeled-actual-participants.parquet').to_dicts()
    template=ROOT/'src/universal_baseball/templates/hitter_final_2026.html'
    DEST.mkdir(parents=True)
    write(DEST/'data.json',dict(players=rows,history=history,walks=walks,score=score,review=review,outside=outside))
    (DEST/'index.html').write_text(template.read_text(encoding='utf8'),encoding='utf8')
    published=read(DEST/'data.json');assert len(published['players'])==4030
    for a,b in zip(rows,published['players']):assert a==b
    assert sum(r['actual_pa'] for r in rows)==182453
    assert math.isclose(sum(r['expected_pa'] for r in rows),score['headline']['pa']['predicted_total'],abs_tol=1e-8)
    write(DEST/'build-review.json',dict(players=4030,team_filter='2025 captured source organization, not future destinations or team roster capacity.',
        unknown_organizations=sum(r['org']=='Unknown organization' for r in rows),forecasts_and_scores_unchanged=True,public_2026_benchmark=False,
        original_explorer_untouched=True,UI_validation='pending',
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),template,source_path,OUT/'scored-fixed-cohort.parquet',OUT/'review-completion.json',*paths]},
        output_hashes={str(p):sha256_file(p) for p in [DEST/'index.html',DEST/'data.json']}))
    print(json.dumps(dict(explorer=str(DEST),players=4030,unknown_organizations=sum(r['org']=='Unknown organization' for r in rows))),flush=True)


if __name__=='__main__':main()
