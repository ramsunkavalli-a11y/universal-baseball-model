"""One bounded reliability model, all fold support checks saved before fitting."""
import json

import numpy as np
import polars as pl

from build_defense_native_range_v3 import OUT, PUBLIC, ROOT, write
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections
from universal_baseball.defense_native_range import preflight, fit, predict, matrix, score, paired_interval
from universal_baseball.storage import sha256_file

ARMS = ("neutral", "history", "calibrated")


def report_group(rows):
    return dict(scores={a:score(rows,a) for a in ARMS},
                calibrated_minus_history=paired_interval(rows,"calibrated","history"),
                history_minus_neutral=paired_interval(rows,"history","neutral"),
                calibrated_minus_neutral=paired_interval(rows,"calibrated","neutral"),
                sparse_rows=sum(r["profile_people"] < 20 for r in rows),
                fallback_rows=sum(not r["fit_allowed"] for r in rows))


def main():
    protected = protections()
    audit = json.loads((OUT / "source-review.json").read_text(encoding="utf8"))
    assert audit["player_walkthrough_status"] == "complete"
    assert (ROOT / "docs/defense-native-range-v3-source-review.md").exists()
    verify(audit["hashes"])
    assert not (OUT / "fit-preflight.json").exists()
    rows = pl.read_parquet(OUT / "labels.parquet").to_dicts()
    checks, folds = [], []
    for origin in sorted({r["origin_year"] for r in rows}):
        for fold in range(5):
            train = [r for r in rows if r["quality_rate"] is not None and r["window_end"] <= origin
                     and r["origin_year"] < origin and r["player_id"] % 5 != fold]
            test = [r for r in rows if r["origin_year"] == origin and r["player_id"] % 5 == fold]
            check, counts = preflight(train,test,origin,fold)
            checks.append(check)
            folds.append((origin,fold,train,test,check,counts))
    code_paths = [ROOT / "src/universal_baseball/defense_native_range.py",
                  ROOT / "scripts/fit_defense_native_range_v3.py",
                  ROOT / "docs/defense-native-range-v3-contract.md"]
    write("fit-preflight.json", dict(checks=checks, protections=protected,
                                    hashes={str(p):sha256_file(p) for p in code_paths},
                                    training_windows_with_2020_retained=True))
    predictions, models = [], []
    for origin,fold,train,test,check,counts in folds:
        model = fit(train) if check["fit_allowed"] else None
        values = predict(model,test) if model else np.array([r["history_rate"] for r in test])
        if model:
            x = matrix(train)
            outside = ((matrix(test) < x.min(axis=0)) | (matrix(test) > x.max(axis=0))).sum(axis=1)
        else:
            outside = [None] * len(test)
        models.append(dict(origin=origin, fold=fold, model=model))
        for row,value,count,outside_n in zip(test,values,counts,outside):
            predictions.append({**row, "fold":fold, "neutral":0., "history":row["history_rate"],
                                "calibrated":float(value), "profile_people":count,
                                "fit_allowed":check["fit_allowed"],
                                "features_outside_training_range":int(outside_n) if outside_n is not None else None})
    assert len(predictions) == len(rows)
    pl.DataFrame(predictions).write_parquet(OUT / "predictions.parquet")
    write("models.json",dict(models=models))
    measured = [r for r in predictions if r["quality_rate"] is not None]
    primary = [r for r in measured if r["origin_year"] >= 2022]
    groups = {}
    for p in range(3,10):
        group = [r for r in primary if r["position"] == p]
        if group:
            groups[str(p)] = report_group(group)
    by_origin = {str(y):report_group([r for r in measured if r["origin_year"] == y])
                 for y in sorted({r["origin_year"] for r in measured})}
    result = dict(player_walkthrough_status="pending", disposition="provisional",
                  primary=report_group(primary), by_origin=by_origin, primary_by_position=groups,
                  all_eligible_rows=len(rows), all_predicted_rows=len(predictions),
                  primary_age_groups={}, primary_exposure_groups={},
                  protections=protected, no_value_forecast=True,
                  hashes={str(p):sha256_file(p) for p in (OUT/"predictions.parquet",OUT/"models.json",OUT/"fit-preflight.json")})
    for name, fn in [("primary_age_groups",lambda r:"unknown" if r["age"] is None else "<=24" if r["age"] <= 24 else "25-29" if r["age"] <=29 else "30+"),
                     ("primary_exposure_groups",lambda r:"<1500" if r["history_outs"] <1500 else "1500-4499" if r["history_outs"] <4500 else "4500+")]:
        for g in sorted({fn(r) for r in primary}):
            result[name][g] = report_group([r for r in primary if fn(r) ==g])
    write("report.json",result)
    print(json.dumps(result["primary"],indent=2))


if __name__ == "__main__":
    main()
