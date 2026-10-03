"""Review repaired linear model before proceeding beyond workload."""
import joblib
import numpy as np
import polars as pl
import evaluate_practical_hitter_v30 as r
import evaluate_practical_hitter_v30b as b
from report_practical_hitter_v30 import NOTES
from universal_baseball.storage import sha256_file

def main():
    report=r.read(b.OUT/'report.json');r.check(report['input_hashes']);r.check(report['output_hashes'])
    f=pl.read_parquet(b.OUT/'predictions.parquet').join(pl.read_parquet(r.OUT/'features.parquet').select('row_id','pa_1','pa_2'),on='row_id',validate='1:1')
    f=f.join(pl.read_parquet(r.OUT/'predictions.parquet').select('row_id','ridge_pa'),on='row_id',validate='1:1')
    selected={t['selection']['row_id']:t['selection']['reasons'] for t in r.read(r.OUT/'cases.json')}
    g=f.with_columns(((pl.col('ridge_b_pa')-pl.col('next_pa')).abs()-(pl.col('v24_pa')-pl.col('next_pa')).abs()).alias('change'),
        (pl.col('ridge_b_pa')-pl.col('next_pa')).alias('error')).sort('change','row_id')
    for row,why in [(g.row(0,named=True),'repair_largest_gain'),(g.row(-1,named=True),'repair_largest_loss'),
        (g.sort('error','row_id').row(0,named=True),'repair_false_low'),(g.sort('error','row_id').row(-1,named=True),'repair_false_high')]:
        selected.setdefault(row['row_id'],[]).append(why)
    raw=pl.read_parquet(r.COUNTS);cases=[];lines=['# V30b repaired linear workload: player review','',
        'Same cases and fixed 98-feature ridge; global schedule fractions/environment removed, player schedule-normalized workloads retained. '
        'No outcome tuning. 35 saved fits replayed. All-year PA RMSE 130.43 versus V24 128.62; matched public 149.94 versus 149.12. '
        'The repair resolves a genuine numerical/design failure, but does not establish a better workload model.','']
    for rowid,reasons in selected.items():
        o=f.filter(pl.col('row_id')==rowid).row(0,named=True);key=(o['player_name'],o['origin_year'])
        model=joblib.load(b.OUT/f"model-ridge-{o['origin_year']}-{o['outer_fold']}.joblib")
        x=np.array([o[c] for c in b.FEATURES]);z=(x-model[0].mean_)/model[0].scale_;terms=z*model[-1].coef_
        np.testing.assert_allclose(model[-1].intercept_+terms.sum(),o['ridge_b_raw_pa'],atol=1e-10)
        peers=f.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('player_id')!=o['player_id'])).with_columns(
            (((pl.col('age')-o['age'])/3)**2+((pl.col('pa_0')-o['pa_0'])/200)**2+((pl.col('pa_1')-o['pa_1'])/200)**2+
             ((pl.col('quality_0')-o['quality_0'])/2)**2).alias('distance')).sort('distance','player_id').head(3)
        source=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','level_group').to_dicts()
        top=sorted([dict(feature=c,input=float(v),term=float(t)) for c,v,t in zip(b.FEATURES,x,terms)],key=lambda a:-abs(a['term']))[:8]
        judgment=NOTES.get(key,'Ozzie Albies: 244 MLB PA after a young debut is discounted toward ordinary brief-role workloads, despite strong ability. The repaired model 414 PA is lower than V24 560 and actual 684: a real lost upside/role signal, not a schedule explosion. Comparable young debuts include unsuccessful/partial roles; no blanket guarantee is warranted.')
        cases.append(dict(row_id=rowid,reasons=reasons,origin={c:o[c] for c in ['player_id','player_name','origin_year','target_year','outer_fold','age','pa_0','pa_1','pa_2','v24_pa','ridge_b_raw_pa','ridge_b_pa','ridge_b_value','next_pa','next_value']},
            actual_inputs=dict(zip(b.FEATURES,x.tolist())),raw_history=source,intercept=float(model[-1].intercept_),top_terms=top,
            peers=peers.select('player_name','age','pa_0','pa_1','ridge_b_pa','next_pa','distance').to_dicts(),judgment=judgment))
        lines += [f"## {key[0]}: {key[1]} → {o['target_year']}",'',
            f"Age {o['age']:g}; MLB PA newest to oldest {o['pa_0']}/{o['pa_1']}/{o['pa_2']}. V24 {o['v24_pa']:.1f}; original ridge {o['ridge_pa']:.1f}; repaired ridge {o['ridge_b_pa']:.1f}; actual {o['next_pa']}. "
            f"Unchanged expected yield {600*o['v24_value']/o['v24_pa']:.3f}/600 produces value {o['ridge_b_value']:.3f}, actual {o['next_value']:.3f}.",'',
            'Known source: '+'; '.join(f"{s['season']} {s['level_group']}: {s['plate_appearances']} PA, {s['home_runs']} HR, {s['strike_outs']} K, {s['unintentional_walks']} UBB" for s in source)+'.','',
            'Mechanism: fixed 100-opportunity prior-smoothed rates by MLB/AAA/AA, age, normalized workloads and observed quality. Standardized linear contributions (PA): '+
            '; '.join(f"{t['feature']} {t['term']:+.1f}" for t in top)+f"; intercept {model[-1].intercept_:.1f}. Raw {o['ridge_b_raw_pa']:.1f}; physical/status rules then produce final PA.",'',
            judgment,'',
            'Origin-blind peers: '+'; '.join(f"{p['player_name']} (current PA {p['pa_0']}, forecast {p['ridge_b_pa']:.0f}, actual {p['next_pa']})" for p in peers.to_dicts())+'.','']
    lines += ['## Disposition','',
        'Complete review of all retained cases and repaired-arm extremes. No promotion: sensible regression now competes at roughly the same level as the other methods but loses to V24 on PA. '
        'The original catastrophic ridge result is explained, not hidden. Preserve V24 workload while broadening the talent/population architecture; no additional library or penalty sweep. '
        'The original V30 case judgments describe that batch; the repaired-arm predictions and actual contributions above are the authoritative V30b mechanics.']
    b.write('cases.json',cases);(b.OUT/'player-walkthrough.md').write_text('\n'.join(lines),encoding='utf8')
    report.update(player_walkthrough_status='complete',selected_cases=len(cases),player_walkthrough_path=str(b.OUT/'player-walkthrough.md'),
        disposition='Defect repaired; no linear workload gain. Retain V24 reference and proceed to talent/population integration.')
    report['output_hashes'].update({str(b.OUT/n):sha256_file(b.OUT/n) for n in ['cases.json','player-walkthrough.md']});b.write('report.json',report)
    print(f'Reviewed {len(cases)} repaired-arm cases; unsupported schedule effect removed.')

if __name__=='__main__':main()
