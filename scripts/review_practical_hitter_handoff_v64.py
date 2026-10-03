"""Seal a historical research handoff, not a production promotion."""
import json
from pathlib import Path
import numpy as np
import polars as pl
import build_practical_hitter_handoff_v64 as b
from universal_baseball.storage import sha256_file


def main():
    out=b.OUT;read=lambda p:json.loads(p.read_text(encoding='utf8'))
    manifest=read(out/'handoff-manifest.json')
    for path,h in manifest['source_hashes'].items():assert sha256_file(Path(path))==h,path
    q=pl.read_parquet(b.prior.OUT/'scored-predictions.parquet').sort('row_id')
    f=pl.read_parquet(out/'candidate.parquet').sort('row_id')
    rows=read(out/'explorer/data.json');by={r['row_id']:r for r in rows}
    assert len(rows)==len(f)==30506 and len(by)==len(rows)
    for col in ['row_id','repaired_p','repaired_raw_p','repaired_conditional_pa','baseline_pa','baseline_rate','baseline_value']:
        assert f[col].equals(q[col]),col
    assert np.allclose(f['repaired_p']*f['repaired_conditional_pa'],f['baseline_pa'],atol=1e-10,rtol=0)
    source=pl.read_parquet(b.prior.OUT/'features.parquet').filter(pl.col('row_id').is_in(f['row_id'].to_list())).sort('row_id')
    for col in f.columns:
        if col=='origin_index':
            assert f[col].equals(q[col])
            assert np.allclose(f[col],source[col],atol=1e-12,rtol=0)
        elif col in source.columns and col not in ['origin_replacement_rate','next_value','next_batting_rate']:
            assert f[col].equals(source[col]),col
    for r in f.iter_rows(named=True):
        d=by[r['row_id']]
        for k in f.columns:
            if k=='player_name' and not r[k]:assert d[k]==f"Name unavailable (MLBAM {r['player_id']})"
            elif k=='next_batting_rate' and r['next_pa']==0:assert d[k] is None
            else:assert d[k]==r[k],(r['row_id'],k)
        assert d['team_context_year'] is None or d['team_context_year']<=r['origin_year']
    probability=read(out/'probability-audit.json')
    for s in probability['scopes']:
        assert sum(a['rows'] for a in s['bands'])==s['rows']
        assert sum(a['actual_appearances'] for a in s['bands'])==s['actual_appearances']
        assert abs(sum(a['expected_appearances'] for a in s['bands'])-s['expected_appearances'])<1e-8
    reviews=read(b.prior.OUT/'reviewed-case-summary.json')
    requested={(r['player_id'],r['origin_year']) for r in manifest['probability_case_ids']}
    selected=[]
    for rv in reviews:
        if (rv['player_id'],rv['origin_year']) not in requested:continue
        d=next(r for r in rows if r['player_id']==rv['player_id'] and r['origin_year']==rv['origin_year'])
        assert rv['review_note'] and rv['source_history'] and rv['peers'] and rv['saved_terms']
        assert abs(d['repaired_p']*d['repaired_conditional_pa']-d['baseline_pa'])<1e-8
        selected.append(dict(player=d['player_name'],player_id=d['player_id'],origin_year=d['origin_year'],target_year=d['target_year'],
            appearance_probability=d['repaired_p'],PA_if_active=d['repaired_conditional_pa'],expected_PA=d['baseline_pa'],actual_PA=d['next_pa'],
            hitting_per_600=d['baseline_rate'],expected_offense=d['baseline_value'],actual_offense=d['next_value'],
            support=d['support'],source_history=rv['source_history'],actual_inputs=rv['actual_inputs'],
            saved_terms=rv['saved_terms'],peers=rv['peers'],review_note=rv['review_note']))
    assert len(selected)==8
    cases={(592450,2016),(592450,2024),(665742,2024),(642715,2024),(663656,2024),(701762,2024),(665487,2022),(680574,2024)}
    affiliations=[{k:r[k] for k in ['player_id','player_name','origin_year','team_id','club','org','team_context_year','team_context_basis']}
                  for r in rows if (r['player_id'],r['origin_year']) in cases]
    assert len(affiliations)==8
    evidence=dict(player_walkthrough_status='complete',no_new_models=True,probability_cases=selected,affiliation_source_cases=affiliations,
        selection='Eight cases locked before probability audit; reuse nineteen completed source/input/saved-fit reviews and their outcome-blind peer rules.',
        conclusion='Retain reviewed means for research, not prospect readiness certification. Probability reliability and team display changes are not a forecast upgrade.')
    b.write('reviewed-handoff-cases.json',evidence)
    qa_path=b.ROOT/'reports/model-evidence/practical-hitter-handoff-v64/browser-qa.json'
    qa=read(qa_path);assert qa['status']=='complete' and qa['actual_results_hidden_by_default'] and qa['all_seven_years_checked']
    assert sha256_file(b.ROOT/'src/universal_baseball/templates/practical_hitter_handoff.html')==qa['template_sha256']
    manifest.update(player_walkthrough_status='complete',browser_verification='complete',
        next_year_research_handoff_complete=True,whole_goal_complete=False,probability_recalibrated=False,
        disposition='Retained research candidate; public PA MAE, elite prospect readiness and calibrated continuous uncertainty remain unfinished.')
    paths=[out/'candidate.parquet',out/'probability-audit.json',out/'reviewed-handoff-cases.json',qa_path,
        b.ROOT/'docs/practical-hitter-model-card.md',b.ROOT/'docs/practical-hitter-handoff-v64-result.md',Path(__file__)]
    paths+=sorted((out/'explorer').iterdir())
    manifest['handoff_hashes']={str(p):sha256_file(p) for p in paths}
    b.write('handoff-manifest.json',manifest)
    archive=b.ROOT/'reports/model-evidence/practical-hitter-handoff-v64'
    for name in ['handoff-manifest.json','probability-audit.json','reviewed-handoff-cases.json']:
        (archive/name).write_bytes((out/name).read_bytes())
    print('Research handoff sealed; eight probability and eight affiliation reviews; goal remains active.',flush=True)


if __name__=='__main__':main()
