from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_S0_scoring_authorization_is_one_shot_and_protected_safe() -> None:
    authorization = json.loads(
        (ROOT / "docs/hitter-v2-S0-scoring-authorization.json").read_text(
            encoding="utf-8"
        )
    )
    checkpoint = ROOT / authorization["fit_checkpoint_path"]
    assert authorization["fit_checkpoint_sha256"] == sha256(
        checkpoint.read_bytes()
    ).hexdigest()
    assert all(authorization["authorized"].values())
    assert not any(authorization["not_authorized"].values())
    assert "equals C0" in authorization["known_gate_consequence"]
