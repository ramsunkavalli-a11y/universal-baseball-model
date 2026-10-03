"""Origin-profile diagnostics of missing roster listing and missed-year regulars."""
import polars as pl
from universal_baseball.practical_hitter_v30 import score
from score_hitter_readiness_v49 import probability_score
import evaluate_hitter_readiness_v49 as e


def main():
    verified=e.old.r.read(e.OUT/'verification.json');assert verified['replayed_heads']==140
    f=pl.read_parquet(e.OUT/'predictions.parquet');out=[]
    for label,g in [('current_MLB_not40man',f.filter((pl.col('pa_0')>0)&(pl.col('on_40man')==0))),
        ('current_400PA_not40man',f.filter((pl.col('pa_0')>=400)&(pl.col('on_40man')==0))),
        ('current_400PA_listed',f.filter((pl.col('pa_0')>=400)&(pl.col('on_40man')==1))),
        ('absent_prior_regular',f.filter((pl.col('pa_0')==0)&(pl.col('regular_window')>0)))]:
        out.append(dict(scope=label,diagnostic_origin_only_group=True,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ['binary_count','binary_scout','retired_games','retired_safe_ridge']},
            probabilities={a:probability_score(g,a) for a in ['binary_count','binary_scout']},
            interpretation='Roster absence is not certified free agency, injury, release or permanent unavailability; no causes assigned from this diagnostic.'))
    e.write('origin-profile-diagnostics.json',out)
    for s in out:print(s['scope'],s['rows'],'actual PA',round(s['actual_pa']),s['probabilities']['binary_scout'],'expected PA',round(s['scores']['binary_scout']['pa_total']),flush=True)


if __name__=='__main__':main()
