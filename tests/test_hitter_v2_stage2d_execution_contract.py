from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_stage2d_input_result_is_target_free_and_accepted() -> None:
    result = _load("docs/hitter-v2-stage2d-input-result.json")

    assert result["accepted"] is True
    assert result["input_pa"] == 3_657_915
    assert set(result["platoon_cells"]) == {"L_vs_L", "L_vs_R", "R_vs_L", "R_vs_R"}
    assert sum(result["platoon_cells"].values()) == result["input_pa"]
    assert result["forecast_targets_loaded"] is False
    assert result["candidate_fit"] is False
    assert result["candidate_scored"] is False
    assert result["protected_2026_opened"] is False
    assert all(result["invariants"].values())


def test_stage2d_execution_contract_matches_frozen_implementation() -> None:
    contract = _load("docs/hitter-v2-stage2d-j0-fit-execution-contract.json")
    provenance = contract["provenance"]

    assert contract["status"] == "frozen_before_real_data_fit_or_score"
    assert provenance["implementation_sha256"] == _sha256(
        provenance["implementation_path"]
    )
    assert contract["nodes"] == [
        "K",
        "UBB",
        "HBP",
        "HR",
        "NON_HR_REACH",
        "HIT_COMPOSITION",
    ]
    assert contract["cohort"]["matched_contextual_and_uncontextual_rows"] is True
    assert contract["model"]["same_batter_effect_sd_used_in_both_matched_fits"] is True
    assert contract["execution_controls"] == {
        "optimizer_max_iterations": 500,
        "optimizer_tolerance": 1e-8,
        "variance_max_iterations": 20,
        "variance_relative_tolerance": 0.01,
        "random_seed": None,
        "deterministic": True,
    }


def test_stage2d_execution_boundary_remains_closed() -> None:
    contract = _load("docs/hitter-v2-stage2d-j0-fit-execution-contract.json")

    assert contract["real_data_fit_authorized"] is False
    assert contract["candidate_scoring_authorized"] is False
    assert contract["forecast_targets_loaded"] is False
    assert contract["protected_2026_opened"] is False
    assert contract["failure_policy"]["zero_or_failed_context"] == "exact_B1_prediction"
    assert contract["failure_policy"]["post_result_retuning"] is False
