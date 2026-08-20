from __future__ import annotations

import json
import math
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LOCAL_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def _load_result(filename: str) -> dict[str, object]:
    return json.loads((ROOT / "docs" / filename).read_text(encoding="utf-8"))


def test_all_documented_json_is_parseable() -> None:
    json_paths = sorted((ROOT / "docs").rglob("*.json"))
    assert json_paths
    for path in json_paths:
        json.loads(path.read_text(encoding="utf-8"))


def test_all_local_markdown_links_resolve() -> None:
    failures: list[str] = []
    markdown_paths = sorted(
        {
            *ROOT.glob("*.md"),
            *(ROOT / ".github").glob("*.md"),
            *(ROOT / "docs").rglob("*.md"),
        }
    )
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        for match in LOCAL_LINK.finditer(text):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split(maxsplit=1)[0]
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_part = unquote(target.split("#", 1)[0])
            if not (path.parent / local_part).resolve().exists():
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{path.relative_to(ROOT)}:{line}: {target}")
    assert failures == []


def test_workflow_names_are_present_and_unique() -> None:
    names: dict[str, Path] = {}
    for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"(?m)^name:\s*(.+?)\s*$", text)
        assert match is not None, path.relative_to(ROOT)
        name = match.group(1).strip('"\'')
        assert name not in names, (name, names.get(name), path)
        names[name] = path
    assert names


def test_only_integration_and_security_checks_have_automatic_triggers() -> None:
    automatic_workflows = {"ci.yml", "codeql.yml"}
    for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        has_push = re.search(r"(?m)^  push:\s*$", text) is not None
        has_pull_request = re.search(r"(?m)^  pull_request:\s*$", text) is not None
        has_dispatch = re.search(r"(?m)^  workflow_dispatch:\s*$", text) is not None
        if path.name in automatic_workflows:
            assert has_push and has_pull_request and has_dispatch
        else:
            assert not has_push and not has_pull_request, path.relative_to(ROOT)
            assert has_dispatch, path.relative_to(ROOT)


def test_public_release_files_are_present() -> None:
    required = (
        "LICENSE",
        "NOTICE.md",
        "CONTRIBUTING.md",
        ".github/SECURITY.md",
        ".github/dependabot.yml",
        ".github/workflows/codeql.yml",
    )
    for relative_path in required:
        assert (ROOT / relative_path).is_file(), relative_path


def test_dev_extra_covers_every_imported_model_runtime() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = project["project"]["optional-dependencies"]
    dev_names = {requirement.split("<", 1)[0].split(">", 1)[0] for requirement in extras["dev"]}
    playing_time_names = {
        requirement.split("<", 1)[0].split(">", 1)[0]
        for requirement in extras["playing-time"]
    }
    assert {"scikit-learn", "statsmodels"} <= dev_names
    assert playing_time_names == {"scikit-learn", "statsmodels"}


def test_frozen_player_value_summaries_reconcile() -> None:
    final = _load_result("player-value-v1-final-2024.json")
    uncertainty = _load_result("player-value-v1-uncertainty-2024.json")
    centering = _load_result("player-value-v1-mlb-centering-2024.json")

    aggregate = final["aggregate"]
    assert isinstance(aggregate, dict)
    component_sum = sum(
        float(aggregate[key])
        for key in (
            "batting_runs",
            "baserunning_runs",
            "defense_runs",
            "positional_runs",
            "centering_runs",
            "park_runs",
            "replacement_runs",
        )
    )
    assert math.isclose(
        component_sum,
        float(aggregate["runs_above_replacement"]),
        rel_tol=0.0,
        abs_tol=1e-10,
    )
    assert math.isclose(
        float(uncertainty["aggregate"]["point_war"]),
        float(aggregate["war"]),
        rel_tol=0.0,
        abs_tol=1e-10,
    )
    assert abs(float(centering["reference"]["post_centering_residual_runs"])) <= float(
        centering["reference"]["tolerance_runs"]
    )
    assert final["population"]["final_player_count"] == uncertainty["population"][
        "player_count"
    ]
