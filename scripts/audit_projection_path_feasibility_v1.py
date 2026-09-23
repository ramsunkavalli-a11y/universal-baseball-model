"""Inventory vintage forecasts, not a new development model or outcome score."""
from pathlib import Path
import polars as pl
from audit_player_path_population_v1 import OUT, FOLDS, ANCHORS, eligible, panel_data, support
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file

SOURCES={
    'conditional_h1_anchor':ANCHORS,
    'anchored_h2':Path('model_artifacts/hitter-anchored-development-v1-2026-09-22/historical-predictions.parquet'),
    'three_year_opportunity':Path('model_artifacts/hitter-three-year-opportunity-v1-2026-09-22/predictions.parquet'),
    'established_opportunity':Path('model_artifacts/multiyear-hitter-followup-v2-2026-09-22/opportunity-predictions.parquet'),
    'unconditional_quantiles':Path('model_artifacts/multiyear-hitter-followup-v2-2026-09-22/raw-quantile-predictions.parquet'),
    'six_year_totals':Path('model_artifacts/six-year-hitter-v1-2026-09-22/cumulative-predictions.parquet')}


def main():
    panel=panel_data();inventory={};frames={}
    for name,path in SOURCES.items():
        f=pl.read_parquet(path);frames[name]=f
        inventory[name]={'path':str(path),'sha256':sha256_file(path),'rows':f.height,
            'columns':f.columns,'origins':sorted(f['origin_year'].unique().to_list()),
            'horizons':sorted(f['horizon'].unique().to_list()) if 'horizon' in f.columns else None}
    opportunities=frames['three_year_opportunity'].group_by('origin_year','player_id').agg(
        pl.col('horizon').n_unique().alias('horizons')).filter(pl.col('horizons')==3).select('origin_year','player_id')
    anchors=frames['conditional_h1_anchor'].select('origin_year','player_id')
    folds=[]
    for year,h,cold in FOLDS:
        test=panel.filter(pl.col('origin_year')==year)
        train=eligible(panel,year,h,test['player_id'].to_list() if cold else ())
        both=train.join(anchors,on=['origin_year','player_id'],how='inner').join(
            opportunities,on=['origin_year','player_id'],how='inner')
        folds.append({'cutoff':year,'horizon':h,'cold':cold,
            'h1_anchor_and_h1_h3_opportunity':support(both),
            'supported_donor_origins':sorted(both['origin_year'].unique().to_list())})
    save(OUT/'c1-feasibility.json',{'status':'not_ready_for_c1_fit','inventory':inventory,'folds':folds,
        'what_exists':'Cutoff-safe H1 conditional batting/replacement-rate anchors from 2012; H2 development challenger; H1-H3 opportunity replays from 2016; unconditional H1-H3 quantiles from 2012.',
        'why_not_fit':'The conditional anchors are selected-MLB rate estimates, not universal latent ability. No accepted joint rate/opportunity path is archived at early donor cutoffs. The earliest normal outer fold has zero donors with both existing H1 anchor and complete H1-H3 opportunity replay. H6 2016/2017 has no eligible H1 anchors at all. Unconditional quantiles cannot be divided by expected PA and called talent, or independently sampled into coherent careers.',
        'not_a_claim_of_impossibility':'The raw annual panel is available. Earlier vintage models and a coherent transition design can be rebuilt in a separately specified follow-up. This is an archive/readiness gate, not proof that anchoring cannot work.',
        'next_prerequisites':['Rebuild cutoff-specific conditional-rate and opportunity baseline states at donor origins, starting with H3. Preserve inactive and never-debuted rows and unknown rates.',
            'Freeze how baseline ability, development and availability interact before residual-path scoring; do not use a failed H2 challenger as an accepted anchor.',
            'Verify vintage training cutoffs and predictive support for young brief-MLB and never-debuted states, then freeze one C1 experiment.',
            'Keep six-year calibration explicitly pandemic-limited; do not synthesize a normal H6 test or full control tail.'],
        'direct_benchmarks_reviewed':{'positive_tail':'docs/prospect-broad-history-positive-tail-result.md: rejected basic tail family.',
            'skill_tail':'docs/prospect-broad-history-skill-tail-result.md: rejected aggregate skill-tail increment.',
            'reuse_limit':'Different previously exposed targets/cohorts; not new matched distribution benchmarks. No threshold sweep added.'},
        'protected_outcomes_used':False,'new_models_fitted':False})
    print('C1 readiness inventory saved; no C1 fit authorized by the feasibility gate.')


if __name__=='__main__':main()
