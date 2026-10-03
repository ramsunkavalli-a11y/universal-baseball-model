"""Expose reviewed corrected historical candidates without production mutation."""
import json
import polars as pl
import prepare_practical_hitter_v31 as r
from build_practical_hitter_explorer_v31 import team_map
from universal_baseball.storage import sha256_file

def main():
    out=r.ROOT/'reports/generated/practical-hitter-v33b';report=r.read(out/'report.json')
    assert report['player_walkthrough_status']=='complete'
    f=pl.read_parquet(out/'scored-predictions.parquet');mapping,hashes=team_map()
    support=pl.read_parquet(out/'support.parquet').filter(pl.col('head')=='active')
    supportmap={s['row_id']:s['profile_players'] for s in support.iter_rows(named=True)}
    rows=[]
    fields=['row_id','player_id','player_name','origin_year','target_year','age','stage','source_position','on_40man',
        'pa_0','pa_1','pa_2','quality_0','DSL_0_pa','AAA_0_pa','AA_0_pa','career_mlb_observed_pa','career_mlb_left_truncated',
        'age_unknown','last_stat_gap','next_pa','next_value','v24_pa','v24_value','steamer_pa','steamer_value','legacy_n_pa',
        'legacy_n_value','hard_unavailable','needs_availability_scenario','draft_known','draft_year','pick_number','draft_school_class']
    for o in f.iter_rows(named=True):
        row={c:o[c] for c in fields};row.update(mapping.get((o['origin_year'],o['team_id']),dict(club='Unknown club',org='Unknown affiliation')))
        row['support']={'active_rate':supportmap[o['row_id']]};row['contribution_rate']=o['safe_ridge_rate']
        row['origin_replacement_rate']=o['origin_replacement_rate']
        for arm in ['safe_ridge','pooled','pedigree','repaired_direct']:
            row[arm]=dict(pa=o[arm+'_pa'],value=o[arm+'_value'])
            if arm!='repaired_direct':row[arm]['rate']=o[arm+'_rate']
        rows.append(row)
    history={}
    for o in pl.read_parquet(r.OUT/'counts.parquet').select('season','player_id','bucket','plate_appearances','strike_outs','unintentional_walks','home_runs','doubles','triples','babip_hits','babip_opportunities').iter_rows(named=True):
        pid=o.pop('player_id');history.setdefault(str(pid),[]).append(o)
    dest=out/'explorer';dest.mkdir(exist_ok=True)
    for name,obj in [('data.json',rows),('history.json',history),('scores.json',r.read(out/'scores.json'))]:
        (dest/name).write_text(json.dumps(obj,allow_nan=False,separators=(',',':')),encoding='utf8')
    template=r.ROOT/'src/universal_baseball/templates/practical_hitter_explorer_v31.html'
    (dest/'index.html').write_text(template.read_text(encoding='utf8'),encoding='utf8')
    (out/'explorer-report.json').write_text(json.dumps(dict(rows=len(rows),target_years=sorted(f['target_year'].unique()),
        source_hashes=hashes,template_sha256=sha256_file(template),default_model='safe_ridge',origin_2020_training_excluded=True,protected_2026_unchanged=True,
        research_only=True),indent=2),encoding='utf8')
    print(dest)

if __name__=='__main__':main()
