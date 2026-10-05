"""Publish checked display receipts, never bulk source data or new forecasts."""
from universal_baseball.storage import sha256_file
from score_hitter_final_2026 import ROOT,read,write


def main():
    out=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    public=ROOT/'reports/model-evidence/hitter-final-2026/explorer-review.json'
    assert not public.exists()
    browser=read(out/'browser-review-mobile-verified.json');assert browser['status']=='passed'
    mobile=read(out/'mobile-correction.json');build=read(out/'build-review.json')
    assert sha256_file(out/'index.html')==mobile['new_sha256']
    assert sha256_file(out/'data.json')==mobile['data_sha256']==build['output_hashes'][str(out/'data.json')]
    template=ROOT/'src/universal_baseball/templates/hitter_final_2026.html'
    assert sha256_file(template)==sha256_file(out/'index.html')
    write(public,dict(build=build,name_correction=read(out/'ui-correction.json'),mobile_correction=mobile,browser=browser,
        url='http://127.0.0.1:8810/',visual_review='Desktop Judge details and final 430-pixel mobile render inspected; internal table scrolling, no whole-page overflow.',
        current_template_sha256=sha256_file(template),forecasts_scores_and_membership_unchanged=True,
        source_hashes={str(p):sha256_file(p) for p in [ROOT/'scripts/build_hitter_final_2026_explorer.py',ROOT/'scripts/complete_hitter_final_2026_explorer.py',
            ROOT/'scripts/repair_hitter_final_2026_explorer_names.py',ROOT/'scripts/repair_hitter_final_2026_explorer_mobile.py',
            ROOT/'scripts/test_hitter_final_2026_explorer.mjs',ROOT/'docs/hitter-final-2026-explorer.md',ROOT/'scripts/publish_hitter_final_2026_explorer_review.py']}))


if __name__=='__main__':main()
