"""Team-filtered reviewed comparison; frozen forecast/deployment untouched."""
import json
import polars as pl
import prepare_practical_hitter_v31 as r
from build_practical_hitter_explorer_v31 import team_map
from universal_baseball.storage import sha256_file


def main():
    root=r.ROOT/'reports/generated';contact=root/'practical-hitter-contact-v41';games=root/'practical-hitter-v38';baseline=root/'practical-hitter-v33b'
    for p in [contact,games,baseline]:assert r.read(p/'report.json')['player_walkthrough_status']=='complete'
    f=pl.read_parquet(contact/'predictions.parquet');g=pl.read_parquet(games/'predictions.parquet').select('row_id','games_pa','games_rate','games_value')
    f=f.join(g,on='row_id',validate='1:1');assert len(f)==30506 and f['origin_year'].max()==2024 and f['target_year'].max()==2025
    mapping,hashes=team_map();rows=[]
    fields=['row_id','player_id','player_name','origin_year','target_year','age','stage','source_position','next_pa','next_value',
        'origin_replacement_rate','draft_known','draft_year','pick_number','contact_supported']
    for o in f.iter_rows(named=True):
        a={k:o[k] for k in fields};a.update(mapping.get((o['origin_year'],o['team_id']),dict(club='Unknown club',org='Unknown affiliation')))
        a['next_batting_rate']=o['next_batting_rate'] if o['next_pa']>0 else None
        for arm in ['safe_ridge','cohort','games','contact_ridge','contact_hist']:a[arm]={v:o[arm+'_'+v] for v in ['pa','rate','value']}
        rows.append(a)
    history={}
    for o in pl.read_parquet(r.OUT/'counts.parquet').select('season','player_id','bucket','plate_appearances','strike_outs','unintentional_walks','home_runs','doubles','triples').iter_rows(named=True):
        pid=o.pop('player_id');history.setdefault(str(pid),[]).append(o)
    scores=next(s for s in r.read(contact/'scores.json') if s['scope']=='public_active')['scores']
    gs=next(s for s in r.read(games/'scores.json') if s['scope']=='public_active')['scores'];scores['games']=gs['games']
    notes=r.read(r.ROOT/'config/practical_hitter_contact_v41_case_notes.json');cases=r.read(contact/'cases.json')
    reviews={str(c['origin']['player_id'])+'|'+str(c['origin']['origin_year']):notes[c['origin']['player_name']+'|'+str(c['origin']['origin_year'])] for c in cases}
    out=root/'practical-hitter-reviewed-batch';dest=out/'explorer';dest.mkdir(parents=True,exist_ok=True)
    for name,obj in [('data.json',rows),('history.json',history),('scores.json',scores),('reviews.json',reviews)]:
        (dest/name).write_text(json.dumps(obj,allow_nan=False,separators=(',',':')),encoding='utf8')
    template=r.ROOT/'src/universal_baseball/templates/practical_hitter_batch.html';(dest/'index.html').write_text(template.read_text(encoding='utf8'),encoding='utf8')
    paths=[contact/'predictions.parquet',contact/'report.json',games/'predictions.parquet',games/'report.json',baseline/'report.json',template, r.ROOT/'config/practical_hitter_contact_v41_case_notes.json']
    hashes.update({str(p):sha256_file(p) for p in paths})
    (out/'report.json').write_text(json.dumps(dict(rows=len(rows),default_model='safe_ridge',historical_only=True,target_maximum=2025,
        team_filter=True,models_have_completed_walkthroughs=True,source_hashes=hashes,frozen_forecast_changed=False),indent=2),encoding='utf8')
    print(dest,flush=True)


if __name__=='__main__':main()
