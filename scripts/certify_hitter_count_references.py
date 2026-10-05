"""Reconstruct cached past foreign league environments from actual source rows."""
from pathlib import Path
import numpy as np
from universal_baseball.storage import sha256_file
from prepare_foreign_component_translation import sources,NPB,KBO,DOMESTIC
from universal_baseball.foreign_component_translation import References
from run_hitter_count_baseline import OUT,read,save,source_data


def main():
    assert not (OUT/'reference-review.json').exists()
    refs=References(sources());_,_,inputs,profiles=source_data();n=0;cache={}
    for p in profiles.values():
        origin=p['origin_year'];excluded=tuple(p['excluded_folds'])
        for league in p['leagues']:
            for season in league['observed_seasons']:
                y=season['season'];assert y<=origin
                key=league['league'],y,excluded
                if key not in cache:cache[key]=refs.get(*key)
                assert np.allclose(cache[key],season['reference'],atol=1e-12)
                n+=1
    save('reference-review.json',dict(past_foreign_references_reconstructed=n,unique_references=len(cache),
        own_and_outer_player_folds_excluded=True,protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),NPB,KBO,DOMESTIC,
            OUT.parent/'foreign-borrowed-stability/profiles.json']}))
    print(f'Rebuilt {n} cached foreign seasonal references from actual source rows with held folds removed.')


if __name__=='__main__':main()
