import polars as pl
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

from review_hitter_direct_events import clean_foreign_precision,scope


def test_tiny_inverse_log_residue_is_not_foreign_evidence():
    q=pl.DataFrame(dict(source_addition=[False]*3,prior_debut=[0]*3,
        foreign_supported_PA=[1e-12,0.,70.8],US_supported_PA=[600.]*3))
    cleaned=clean_foreign_precision(q)
    assert cleaned['foreign_supported_PA'].to_list()==[0.,0.,70.8]
    assert scope(cleaned,'foreign_never_debut').height==1
    assert q['foreign_supported_PA'][0]==1e-12
