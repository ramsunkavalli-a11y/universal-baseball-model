"""Keep mobile tables inside their own scroll area; forecast bytes unchanged."""
from universal_baseball.storage import sha256_file
from score_hitter_final_2026 import ROOT,write


def main():
    out=ROOT/'reports/generated/hitter-final-2026-reviewed-explorer'
    assert not (out/'mobile-correction.json').exists()
    old=(out/'index.html').read_text(encoding='utf8');sha=sha256_file(out/'index.html')
    needle='@media(max-width:1100px){.grid{grid-template-columns:1fr}'
    replacement='@media(max-width:1100px){.grid{grid-template-columns:minmax(0,1fr)}.grid>section,aside{min-width:0}'
    assert old.count(needle)==1
    template=ROOT/'src/universal_baseball/templates/hitter_final_2026.html'
    assert template.read_text(encoding='utf8')==old
    (out/'index-before-mobile-fix.html').write_text(old,encoding='utf8')
    for p in [template,out/'index.html']:p.write_text(old.replace(needle,replacement),encoding='utf8')
    write(out/'mobile-correction.json',dict(correction='A rendered 430-pixel viewport exposed a table minimum-width overflow; mobile grid now permits internal table scrolling instead of widening the whole page.',
        previous_sha256=sha,previous_file='index-before-mobile-fix.html',new_sha256=sha256_file(out/'index.html'),
        data_sha256=sha256_file(out/'data.json'),forecasts_changed=False))


if __name__=='__main__':main()
