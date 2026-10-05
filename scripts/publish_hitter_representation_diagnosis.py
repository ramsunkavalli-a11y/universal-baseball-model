"""Publish bounded numerical diagnosis with its readable-review provenance."""
from pathlib import Path
import json
from prepare_hitter_evidence_representation import ROOT, OUT, read
from universal_baseball.storage import sha256_file


def main():
    source=OUT/'regularization-audit.json';audit=read(source)
    assert audit['new_fits']==0 and audit['all_35_Ridge_coefficients_independently_reconstructed']
    target=ROOT/'reports/model-evidence/hitter-evidence-representation/regularization-audit.json'
    assert not target.exists()
    doc=ROOT/'docs/hitter-evidence-learning-diagnosis.md'
    value=dict(audit,readable_diagnosis=str(doc.relative_to(ROOT)),
               publication_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),doc,source]})
    target.write_text(json.dumps(value,indent=2,allow_nan=False,ensure_ascii=False,default=str)+'\n',encoding='utf8',newline='\n')
    print('No-fit diagnosis published; source, completed review and original forecast preserved.')


if __name__=='__main__':main()
