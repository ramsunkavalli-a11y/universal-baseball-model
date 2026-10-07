"""Use the published final UI receipt instead of its superseded initial build."""
from pathlib import Path
import copy
import finalize_defense_reference_history_v26 as base
from universal_baseball.storage import sha256_file


def main():
    original_read=base.read;original_write=base.write
    published=base.ROOT/'reports/model-evidence/hitter-final-2026/explorer-review.json'
    ui=original_read(published);out=base.ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    build=original_read(out/'build-review.json');assert ui['build']==build
    names=ui['name_correction'];mobile=ui['mobile_correction']
    assert names['prior_sha256']==build['output_hashes'][str(out/'index.html')]
    assert names['new_sha256']==mobile['previous_sha256']
    assert mobile['new_sha256']==ui['current_template_sha256']==sha256_file(out/'index.html')
    assert names['data_sha256']==mobile['data_sha256']==build['output_hashes'][str(out/'data.json')]==sha256_file(out/'data.json')
    assert not names['forecasts_or_outcomes_changed'] and not mobile['forecasts_changed']
    assert ui['forecasts_scores_and_membership_unchanged']
    assert sha256_file(out/'index-before-mobile-fix.html')==mobile['previous_sha256']
    assert sha256_file(Path(names['prior_template_preserved']))==names['prior_sha256']
    assert sha256_file(base.ROOT/'src/universal_baseball/templates/hitter_final_2026.html')==mobile['new_sha256']
    def current_read(path):
        note=original_read(path)
        if Path(path)==out/'build-review.json':
            note=copy.deepcopy(note)
            note['output_hashes'][str(out/'index.html')]=mobile['new_sha256']
        return note
    def sealed_write(path,note):
        note['finalizer_correction']='Initial build index hash predates the documented name/mobile UI repairs. Verified the complete published hash chain and unchanged data; no saved receipt or forecast was altered.'
        note['hashes'].update({str(p):sha256_file(p) for p in [Path(__file__),published,out/'index-before-mobile-fix.html',Path(names['prior_template_preserved']),out/'index.html',out/'data.json']})
        original_write(path,note)
    base.read=current_read;base.write=sealed_write;base.main()


if __name__=='__main__':main()
