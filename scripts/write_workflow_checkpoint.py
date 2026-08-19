#!/usr/bin/env python3
"""Write a small durable workflow checkpoint JSON file.

Designed for GitHub Actions jobs where the binding result should only be persisted
on success, but a lightweight artifact should survive failures/timeouts long enough
to show how far the job got.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


def _json_object(value: str | None, *, name: str) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise SystemExit(f"{name} must decode to a JSON object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument(
        "--status",
        required=True,
        choices=("started", "step_complete", "failed", "completed"),
    )
    parser.add_argument("--current-step", required=True)
    parser.add_argument("--last-completed-step", default="")
    parser.add_argument("--inputs-json")
    parser.add_argument("--outputs-json")
    parser.add_argument("--boundary-json")
    parser.add_argument("--error", default="")
    args = parser.parse_args()

    payload = {
        "schema_version": "0.1",
        "workflow": args.workflow,
        "stage": args.stage,
        "status": args.status,
        "run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]) if os.environ.get("GITHUB_RUN_ATTEMPT") else None,
        "run_sha": os.environ.get("GITHUB_SHA"),
        "ref_name": os.environ.get("GITHUB_REF_NAME"),
        "current_step": args.current_step,
        "last_completed_step": args.last_completed_step or None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": _json_object(args.inputs_json, name="inputs-json"),
        "outputs": _json_object(args.outputs_json, name="outputs-json"),
        "boundary": _json_object(args.boundary_json, name="boundary-json"),
        "error": args.error or None,
    }
    args.path.parent.mkdir(parents=True, exist_ok=True)
    args.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
