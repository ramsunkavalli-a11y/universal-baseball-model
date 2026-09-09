import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "model_artifacts" / "playing-time-v1-confirmation-2025"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_preserved_confirmation_artifact_matches_manifest() -> None:
    manifest = json.loads((ARTIFACT_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["run_id"] == 32146445795
    assert manifest["source_sha"] == "5ac0456d20741c240ab8acad962707b6dbdae925"
    for relative_path, record in manifest["files"].items():
        path = ARTIFACT_ROOT / relative_path
        assert path.stat().st_size == record["bytes"]
        assert _sha256(path) == record["sha256"]


def test_preserved_scores_match_committed_confirmation_report() -> None:
    manifest = json.loads((ARTIFACT_ROOT / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads(
        (ROOT / "docs" / "playing-time-v1-confirmation-result.json").read_text(
            encoding="utf-8"
        )
    )

    mapping = {
        "baseline0_scores": "tables/baseline0_scores.parquet",
        "candidate_scores": "tables/candidate_scores.parquet",
        "diagnostic_strata": "tables/diagnostic_level_strata.parquet",
    }
    for report_key, relative_path in mapping.items():
        assert report["storage"][report_key]["file_sha256"] == manifest["files"][
            relative_path
        ]["sha256"]


def test_preserved_report_matches_committed_confirmation_results() -> None:
    preserved = json.loads((ARTIFACT_ROOT / "report.json").read_text(encoding="utf-8"))
    committed = json.loads(
        (ROOT / "docs" / "playing-time-v1-confirmation-result.json").read_text(
            encoding="utf-8"
        )
    )

    # The committed report later added source identifiers; the original artifact
    # carries those identifiers in its durable manifest instead.
    assert committed.pop("source_run_id") == 32146445795
    assert committed.pop("source_sha") == "5ac0456d20741c240ab8acad962707b6dbdae925"
    assert preserved == committed
