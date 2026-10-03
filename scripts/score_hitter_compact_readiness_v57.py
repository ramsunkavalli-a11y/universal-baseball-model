"""Reuse population/replay/case checks, add explicit prior-readiness controls."""
import polars as pl
import evaluate_hitter_prospect_pooling_v54 as io
import evaluate_hitter_compact_readiness_v57 as e
import score_hitter_prospect_pooling_v54 as scoring
from score_practical_hitter_v31 import paired
from universal_baseball.practical_hitter_v30 import score


def main():
    io.OUT=e.OUT
    scoring.main()
    q=pl.read_parquet(e.OUT/"predictions.parquet")
    old=pl.read_parquet(e.ROOT/"reports/generated/practical-hitter-head-assembly-v56/predictions.parquet").select("row_id",
        *["prospect_pa_only_"+c for c in ["pa","rate","value"]],
        *["assembled_"+c for c in ["pa","rate","value"]])
    q=q.drop(["prospect_pa_only_"+c for c in ["pa","rate","value"]]).join(old,on="row_id",validate="1:1")
    comparisons=[]
    for label,g in [("all",q),("never_debut",q.filter(pl.col("prior_debut")==0)),
        ("upper_never_debut",q.filter((pl.col("prior_debut")==0)&(pl.col("stage")=="Upper minors"))),
        ("lower_never_debut",q.filter((pl.col("prior_debut")==0)&(pl.col("stage")=="Lower minors")))]:
        comparisons.append(dict(scope=label,rows=len(g),scores={a:score(g,a) for a in ["repaired","prospect_pa_only","assembled","shared"]},
            intervals=[paired(g,"shared",b,"value") for b in ["repaired","prospect_pa_only"]]))
    io.write("prior-readiness-comparison.json",comparisons)


if __name__=="__main__":main()
