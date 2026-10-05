"""Seal an actually completed source walkthrough, not predictive approval."""
from pathlib import Path
import polars as pl

from prepare_hitter_shared_events import OUT,ROOT,PREVIOUS,read,save,verify
from universal_baseball.storage import sha256_file


def main():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    doc=ROOT/'docs/hitter-shared-event-source-review.md'
    body=doc.read_text(encoding='utf8')
    assert 'Source walkthrough complete' in body and '41' in body
    cases=read(OUT/'source-cases.json')['cases'];assert len(cases)==41
    assert len(pre['checks'])==70
    assert not list(OUT.glob('*.joblib')),'Source gate must precede hitter fitting'
    for c in cases:
        p=c['profile']
        assert abs(sum(p['future_shared_probability'])-1)<1e-10
        assert c['raw_profile_deployed']==(c['prior_debut']==0)
    q=pl.read_parquet(PREVIOUS/'predictions.parquet')
    new_ids=q.filter((pl.col('prior_debut')==0)|pl.col('source_addition'))['row_id'].to_list()
    save('source-review.json',dict(source_player_walkthrough_status='complete',cases=41,
        reviewed_row_ids=sorted(c['row_id'] for c in cases),approved_for_fixed_fit=True,
        actual_new_talent_evaluation_row_ids=sorted(new_ids),
        source_case_boolean_qualification='Ordinary prior-debut routing only; all thirteen additions explicitly use new raw talent, including five prior debuts',
        predictive_validation=False,deployment_approved=False,protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [doc,Path(__file__),OUT/'source-cases.json',OUT/'preflight.json']}))
    print('Source walk sealed; only the contracted seventy development rate fits are approved.',flush=True)


if __name__=='__main__':main()
