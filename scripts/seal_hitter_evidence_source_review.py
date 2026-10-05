"""Seal the explicitly performed source review; not automatic model approval."""
from pathlib import Path
from prepare_hitter_evidence_representation import ROOT, OUT, read, save
from universal_baseball.storage import sha256_file


def main():
    pre=read(OUT/'preflight.json')
    for p,h in pre['source_hashes'].items(): assert sha256_file(Path(p))==h,p
    cases=read(OUT/'source-cases.json')
    assert len(cases)==len({r['row_id'] for r in cases})==38
    assert not (OUT/'fit-seal.json').exists()
    doc=ROOT/'docs/hitter-evidence-representation-source-review.md'
    assert doc.exists()
    save('source-review.json',dict(source_player_walkthrough_status='complete',
        manual_review_scope='All 38 retained source cases, actual production shares, source levels, job inputs and profile counts read before fitting',
        reviewed_row_ids=[r['row_id'] for r in cases],approved_for_fixed_development_fit=True,
        predictive_validation=False,deployment_approved=False,protected_outcomes_used=False,
        unresolved=['Sparse or absent training profiles','Selected-mover translation and park gaps',
                    'Chosen prior mass is not an estimated stabilization point','Participation and conditional production factorization'],
        hashes={str(p):sha256_file(p) for p in [Path(__file__),doc,OUT/'preflight.json',OUT/'source-cases.json']}))
    print('All 38 source walks sealed; two fixed development arms permitted, no promotion.')


if __name__=='__main__':main()
