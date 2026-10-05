"""Refresh only UI template after a null-name search defect, preserve builds."""
from pathlib import Path
from universal_baseball.storage import sha256_file
from score_hitter_final_2026 import ROOT,read,write


def main():
    out=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    assert not (out/'ui-correction.json').exists()
    previous=read(out/'build-review.json');oldsha=sha256_file(out/'index.html')
    assert oldsha==previous['output_hashes'][str(out/'index.html')]
    retained=ROOT/'reports/generated/hitter-final-2026-explorer/index.html'
    assert sha256_file(retained)==oldsha,'Preserved original template bytes'
    template=ROOT/'src/universal_baseball/templates/hitter_final_2026.html'
    (out/'index.html').write_text(template.read_text(encoding='utf8'),encoding='utf8')
    assert sha256_file(out/'data.json')==previous['output_hashes'][str(out/'data.json')]
    write(out/'ui-correction.json',dict(correction='136 source names are null; initial name search failed. UI now supports missing names, labels them by unchanged player ID and keeps all forecast inputs and membership unchanged.',
        prior_template_preserved=str(retained),prior_sha256=oldsha,new_sha256=sha256_file(out/'index.html'),
        data_sha256=sha256_file(out/'data.json'),template_sha256=sha256_file(template),forecasts_or_outcomes_changed=False))


if __name__=='__main__':main()
