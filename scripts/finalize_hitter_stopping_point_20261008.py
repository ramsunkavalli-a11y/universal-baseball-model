"""Add review seals without overwriting evidence or changing any forecast.

Replays the immutable independent checkers in disposable evidence directories;
only tiny additive receipts persist. No fitting or new outcome collection.
"""
from contextlib import redirect_stdout
import gzip
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from universal_baseball.storage import sha256_file
from audit_defense_component_bias_v27 import protected

EVIDENCE = ROOT / "reports/model-evidence"
FINAL = EVIDENCE / "hitter-stopping-point-2026-10-08"


def read(path):
    with gzip.open(path, "rt", encoding="utf8") as stream:
        return json.load(stream)


def write(path, obj):
    assert not path.exists(), f"Never overwrite a review: {path}"
    with gzip.open(path, "wt", encoding="utf8") as stream:
        json.dump(obj, stream, allow_nan=False, separators=(",", ":"))


def verify_hashes(note):
    checked = {}
    for field in ("hashes", "source_hashes", "raw_source_hashes", "protected_hashes"):
        for name, expected in note.get(field, {}).items():
            path = Path(name)
            assert path.is_file(), name
            observed = sha256_file(path)
            assert observed == expected, f"Changed evidence: {name}"
            checked[name] = observed
    return checked


def replay(folder, checker, inputs):
    old = read(folder / "independent-review.json.gz")
    checked = verify_hashes(old)
    # The original script remains unchanged; PUBLIC alone points to disposable
    # copies so its deliberate no-overwrite assertion remains effective.
    with tempfile.TemporaryDirectory(prefix="ubm-stopping-point-") as temporary:
        scratch = Path(temporary)
        for name in inputs:
            shutil.copyfile(folder / (name + ".json.gz"), scratch / (name + ".json.gz"))
        spec = importlib.util.spec_from_file_location("stopping_point_replay", ROOT / "scripts" / checker)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PUBLIC = scratch
        with redirect_stdout(io.StringIO()):
            module.main()
        fresh = read(scratch / "independent-review.json.gz")
        for key, value in old.items():
            if key not in ("hashes", "source_hashes", "raw_source_hashes"):
                assert fresh[key] == value, f"Replay changed {key}"
        assert fresh["execution_integrity_pass"]
    return checked, {k: v for k, v in fresh.items() if "hash" not in k}


def check_xml(path, expected):
    suites = ET.parse(path).getroot().findall("testsuite")
    assert sum(int(s.get("tests", "0")) for s in suites) == expected
    assert all(int(s.get(x, "0")) == 0 for s in suites for x in ("failures", "errors", "skipped"))


def check_links(path):
    text = path.read_text(encoding="utf8")
    verified = []
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            continue
        target = (path.parent / link.split("#")[0]).resolve()
        # Completion receipt is this script's eventual output, checked after save.
        if target == FINAL / "completion-audit.json.gz":
            continue
        assert target.is_file(), f"Broken handoff link: {link}"
        verified.append(str(target.relative_to(ROOT)))
    return verified


def main():
    destinations = [EVIDENCE / f / "final-review.json.gz" for f in
                    ("defense-component-bias-v27", "defense-first-base-prior-v28")]
    destinations.append(FINAL / "completion-audit.json.gz")
    assert all(not p.exists() for p in destinations), "Completion receipts already exist"
    initial = protected()
    v27 = EVIDENCE / "defense-component-bias-v27"
    v28 = EVIDENCE / "defense-first-base-prior-v28"
    pre27 = read(v27 / "preflight.json.gz")
    pre28 = read(v28 / "preflight.json.gz")
    verified = {**verify_hashes(pre27), **verify_hashes(pre28)}
    context = read(v27 / "player-value-context.json.gz")
    verified.update(verify_hashes(context))
    assert context["records"] == 56 and context["whole_value_arithmetic_verified"]
    assert context["fits"] == 0 and not context["forecasts_changed"]
    checks27, replay27 = replay(v27, "verify_defense_component_bias_v27.py",
                              ["preflight", "report", "player-walks"])
    checks28, replay28 = replay(v28, "verify_defense_first_base_prior_v28.py",
                              ["preflight", "report", "quality-predictions", "value-predictions", "player-walks"])
    verified.update(checks27)
    verified.update(checks28)
    assert replay27["player_records_replayed"] == 56
    assert replay28["quality_rows_replayed"] == 1741
    assert replay28["value_rows_replayed"] == 12432
    assert replay28["references_replayed"] == 40
    assert replay28["player_records_replayed"] == 44
    assert pre28["reconstruction"]["byte_identity"]
    assert pre28["missing_quality_is_unknown"] and pre28["unchanged_quality_membership"]
    report28 = read(v28 / "report.json.gz")
    assert report28["model_fits"] == 0 and report28["unknown_value_rows"] == 318
    assert not report28["deployment_approved"] and report28["no_2026_access"]
    # Preserve the original pending review. This additive seal completes it.
    assert report28["player_walkthrough_status"] == "pending"
    walks28 = read(v28 / "player-walks.json.gz")["groups"]
    assert len(walks28) == 11
    assert len({(w["origin"], w["player_id"]) for g in walks28 for w in g["records"]}) == 38
    check_xml(v27 / "unit-tests.xml", 5)
    check_xml(v28 / "unit-tests.xml", 6)
    check_xml(FINAL / "unit-tests.xml", 17)
    docs = [ROOT / "docs" / name for name in (
        "hitter-stopping-point-2026-10-08.md", "hitter-stopping-point-execution.md",
        "defense-first-base-prior-v28-contract.md", "defense-first-base-prior-v28-result.md",
        "defense-first-base-prior-v28-player-review.md", "defense-component-bias-v27-result.md",
        "project-status.md", "prospect-model-execution-plan.md")]
    links = {str(p.relative_to(ROOT)): check_links(p) for p in docs[:6]}
    handoff = docs[0].read_text(encoding="utf8")
    for heading in ("What actually drives", "What the evidence", "Baseball checks",
                    "What is not settled", "The next bounded milestone", "Verified stopping point"):
        assert heading in handoff
    narrative = (ROOT / "docs/defense-first-base-prior-v28-player-review.md").read_text(encoding="utf8")
    for name in ("Freeman", "Olson", "Goldschmidt", "Guerrero", "Santana", "Wilson",
                 "Toglia", "O'Hearn", "Kirilloff", "Pasquantino"):
        assert name in narrative
    assert protected() == initial
    audit = dict(
        objective="Locked first-base test, independent review, component reconciliation and honest hitter handoff",
        bounded_goal_complete=True, full_war_complete=False, minor_talent_identified=False,
        club_control_value_complete=False, deployment_approved=False,
        requirements={
            "locked_main_stress_and_earlier_quality_tests": str(v28 / "report.json.gz"),
            "fixed_opportunities_other_components_targets_and_membership": str(v28 / "independent-review.json.gz"),
            "person_bootstrap_scores_and_subgroups": str(v28 / "independent-review.json.gz"),
            "full_source_to_outcome_focal_peer_review": str(docs[4]),
            "preceding_bias_review_completed": str(docs[5]),
            "independent_source_rate_value_and_selection_replay": replay28,
            "byte_identical_archived_baseline_reconstruction": pre28["reconstruction"],
            "actual_frozen_vs_research_component_map": str(docs[0]),
            "specific_remaining_limits_and_one_next_milestone": str(docs[0]),
            "start_here_and_plan_reconciled": [str(docs[6]), str(docs[7])],
            "frozen_forecasts_and_explorer_preserved": initial,
            "no_new_2026_outcomes_or_promotion": True,
        },
        original_reports_preserved=True, player_walkthrough_status="complete",
        unit_checks=17, local_links_verified=links,
        verified_source_and_prior_review_hashes=verified,
        handoff_hashes={str(p): sha256_file(p) for p in docs},
        finalizer_hash=sha256_file(Path(__file__)),
        interpretation="Completion of review and handoff; not statistical certification of every legacy component.")
    for folder, replayed, narratives in (
        (v27, replay27, [docs[5]]), (v28, replay28, [docs[3], docs[4]])):
        receipt = dict(player_walkthrough_status="complete", replayed=replayed,
                       deployment_approved=False, protected_hashes=initial,
                       review_hashes={str(p): sha256_file(p) for p in narratives},
                       evidence_hashes={str(p): sha256_file(p) for p in folder.iterdir() if p.is_file()},
                       original_machine_reports_preserved=True,
                       finalizer_hash=sha256_file(Path(__file__)))
        write(folder / "final-review.json.gz", receipt)
    audit["final_seal_hashes"] = {str(p): sha256_file(p) for p in destinations[:2]}
    write(FINAL / "completion-audit.json.gz", audit)
    assert (FINAL / "completion-audit.json.gz").is_file()
    print(json.dumps({"completion_audit": str(FINAL / "completion-audit.json.gz"),
                      "unit_checks": 17, "first_base_player_records": 44,
                      "bias_player_records": 56, "forecast_changed": False}))


if __name__ == "__main__":
    main()
