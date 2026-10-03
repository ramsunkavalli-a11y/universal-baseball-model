"""Seal the completed manual source review before any model fitting."""
from pathlib import Path
from universal_baseball.storage import sha256_file
import evaluate_hitter_compatible_value_v63 as e


def main():
    assert not list(e.OUT.glob('*.joblib'))
    p=e.ROOT/'docs/hitter-compatible-value-v63-source-review.md'
    assert 'Source/reference review complete' in p.read_text(encoding='utf8')
    r=e.read(e.OUT/'source-reconciliation.json');r['source_case_review_status']='complete'
    r['manual_review_path']=str(p);r['manual_review_sha256']=sha256_file(p)
    e.write('source-reconciliation.json',r)
    pre=e.read(e.OUT/'preflight.json')
    for path,h in pre['input_hashes'].items():assert sha256_file(Path(path))==h
    for path in [p,Path(__file__),e.OUT/'source-reconciliation.json']:
        pre['input_hashes'][str(path)]=sha256_file(path)
    e.write('preflight.json',pre)
    print('Eight actual source/reference cases reviewed; hashes sealed before fits.')


if __name__=='__main__':main()
