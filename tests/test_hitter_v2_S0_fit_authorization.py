from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_S0_fit_authorization_preserves_scoring_boundary() -> None:
    authorization = json.loads(
        (ROOT / "docs/hitter-v2-S0-fit-authorization.json").read_text(
            encoding="utf-8"
        )
    )
    preregistration = ROOT / authorization["preregistration_path"]
    assert authorization["preregistration_sha256"] == sha256(
        preregistration.read_bytes()
    ).hexdigest()
    assert all(authorization["authorized"].values())
    assert not any(authorization["not_authorized"].values())
    assert authorization["stop_boundary"] == (
        "freeze_S0_fit_artifacts_and_report_without_loading_disclosed_target_tables"
    )
