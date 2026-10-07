"""Public immutable biography only; no performance or 2026 results request."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl
import requests

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/generated/defensive-talent-position-v2"


def capture(task):
    index, ids = task
    path = OUT / f"identity-{index:03d}.response"
    query = {"personIds": ",".join(map(str, ids)), "fields": "people,id,birthDate,fullName"}
    if not path.exists():
        r = requests.get("https://statsapi.mlb.com/api/v1/people", params=query, timeout=45)
        r.raise_for_status()
        path.write_bytes(r.content)
    people = json.loads(path.read_text(encoding="utf8"))["people"]
    assert all(set(p).issubset({"id", "birthDate", "fullName"}) for p in people)
    assert {p["id"] for p in people}.issubset(ids)
    return people, dict(params=query, response_path=str(path), sha256=sha256_file(path))


def main():
    protections()
    assert not (OUT / "identity-report.json").exists()
    cohort_path = ROOT / "reports/generated/defensive-talent-support/origins.parquet"
    ids = sorted(pl.read_parquet(cohort_path, columns=["player_id"])["player_id"].unique())
    with ThreadPoolExecutor(max_workers=3) as pool:
        captured = list(pool.map(capture, [(i // 150, ids[i:i + 150]) for i in range(0, len(ids), 150)]))
    people = [p for batch, note in captured for p in batch]
    assert len({p["id"] for p in people}) == len(people)
    rows = [{"player_id": p["id"], "birth_date": p.get("birthDate"), "captured_name": p.get("fullName")} for p in people]
    target = OUT / "identity.parquet"
    pl.DataFrame(rows).write_parquet(target)
    report = dict(requested_people=len(ids), returned_people=len(people), missing_ids=sorted(set(ids) - {p["id"] for p in people}),
                  missing_birthdates=sum(not p.get("birthDate") for p in people), source="MLB StatsAPI immutable biography reconstructed today",
                  captures=[note for batch, note in captured], additional_2026_data_ingested_or_used=False,
                  hashes={str(p): sha256_file(p) for p in [Path(__file__), target, cohort_path]})
    save(OUT / "identity-report.json", report)
    protections()
    print(json.dumps({k: v for k, v in report.items() if k not in ("captures", "hashes")}, indent=2))


if __name__ == "__main__":
    main()
