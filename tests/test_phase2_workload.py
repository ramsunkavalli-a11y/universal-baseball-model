import polars as pl

from universal_baseball.phase2_workload import anchor_workload_paths


def test_workload_anchor_corrects_established_tail_and_fades() -> None:
    paths = pl.DataFrame(
        {
            "player_id": [1, 1, 2],
            "horizon": [1, 2, 1],
            "mlb_active_probability": [0.9, 0.8, 0.1],
            "conditional": [400.0, 380.0, 100.0],
            "expected": [360.0, 304.0, 10.0],
            "variance": [10_000.0, 9_000.0, 2_500.0],
        }
    )
    current = pl.DataFrame({"player_id": [1, 2], "current": [700.0, 0.0]})
    result = anchor_workload_paths(
        paths,
        current,
        conditional_column="conditional",
        expected_column="expected",
        current_column="current",
        variance_column="variance",
        workload_cap=800.0,
        reliability_exposure=250.0,
    )
    veteran = result.filter(pl.col("player_id") == 1).sort("horizon")
    assert veteran.item(0, "conditional") > 550.0
    assert veteran.item(1, "conditional") > 480.0
    assert veteran.item(0, "workload_anchor_weight") > veteran.item(
        1, "workload_anchor_weight"
    )
    prospect = result.filter(pl.col("player_id") == 2)
    assert prospect.item(0, "conditional") == 100.0
    assert prospect.item(0, "expected") == 10.0


def test_workload_anchor_rejects_invalid_strength() -> None:
    empty = pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "horizon": pl.Int64,
            "mlb_active_probability": pl.Float64,
            "conditional": pl.Float64,
            "expected": pl.Float64,
            "variance": pl.Float64,
        }
    )
    current = pl.DataFrame(schema={"player_id": pl.Int64, "current": pl.Float64})
    try:
        anchor_workload_paths(
            empty,
            current,
            conditional_column="conditional",
            expected_column="expected",
            current_column="current",
            variance_column="variance",
            workload_cap=800.0,
            reliability_exposure=250.0,
            anchor_strength=1.1,
        )
    except ValueError as error:
        assert "between zero and one" in str(error)
    else:
        raise AssertionError("invalid strength should fail")
