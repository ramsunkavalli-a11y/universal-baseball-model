#!/usr/bin/env python3
"""Materialize the private 2025 Cot's contract bridge and MLBAM identity audit."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.historical_contract_bridge import (
    match_cots_players_to_opening_day,
    parse_cots_team_csv,
)
from universal_baseball.storage import write_canonical_parquet


GIST_ID = "0baaa3c47c409ed38b7f1e0cde41d5cc"
GIST_API = f"https://api.github.com/gists/{GIST_ID}"
TEAM_BY_NAME = {
    "angels": "LAA", "astros": "HOU", "athletics": "ATH", "bluejays": "TOR",
    "braves": "ATL", "brewers": "MIL", "cardinals": "STL", "cubs": "CHC",
    "diamondbacks": "ARI", "dodgers": "LAD", "giants": "SFG", "guardians": "CLE",
    "mariners": "SEA", "marlins": "MIA", "mets": "NYM", "nationals": "WSN",
    "orioles": "BAL", "padres": "SDP", "phillies": "PHI", "pirates": "PIT",
    "rangers": "TEX", "rays": "TBR", "redsox": "BOS", "reds": "CIN",
    "rockies": "COL", "royals": "KCR", "tigers": "DET", "twins": "MIN",
    "whitesox": "CHW", "yankees": "NYY",
}


def _team(filename: str) -> str:
    compact = "".join(character for character in filename.lower() if character.isalpha())
    matches = [abbr for name, abbr in TEAM_BY_NAME.items() if compact.endswith(f"{name}csv")]
    if len(matches) != 1:
        raise ValueError(f"cannot resolve one team from {filename!r}")
    return matches[0]


def main() -> int:
    output = Path("reports/generated/historical-contract-bridge/2025")
    opening_path = Path(
        "reports/generated/fangraphs-opening-day-control/2025/"
        "opening-day-control-baseline.parquet"
    )
    if not opening_path.is_file():
        raise FileNotFoundError(opening_path)
    metadata_response = requests.get(GIST_API, timeout=60)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    files = metadata.get("files", {})
    if len(files) != 30:
        raise ValueError(f"expected 30 Cot's team files, observed {len(files)}")
    revision = str(metadata["history"][0]["version"])
    raw_dir = output / "raw-private"
    raw_dir.mkdir(parents=True, exist_ok=True)
    player_frames = []
    term_frames = []
    manifest = []
    for filename in sorted(files):
        record = files[filename]
        response = requests.get(record["raw_url"], timeout=60)
        response.raise_for_status()
        content = response.content
        digest = sha256(content).hexdigest()
        team = _team(filename)
        safe_name = f"{team}.csv"
        (raw_dir / safe_name).write_bytes(content)
        source_id = f"cots-derived-gist:{revision}:{team}:{digest}"
        players, terms = parse_cots_team_csv(
            response.text,
            season=2025,
            team_abbreviation=team,
            source_snapshot_id=source_id,
        )
        player_frames.append(players)
        term_frames.append(terms)
        manifest.append(
            {
                "team_abbreviation": team,
                "upstream_filename": filename,
                "private_file": safe_name,
                "sha256": digest,
                "size_bytes": len(content),
                "source_snapshot_id": source_id,
            }
        )
    players = pl.concat(player_frames).sort(["team_abbreviation", "player_name"])
    terms = pl.concat(term_frames).sort(["source_record_id", "payroll_year"])
    opening = pl.read_parquet(opening_path)
    identities = match_cots_players_to_opening_day(players, opening)
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "players": write_canonical_parquet(
            players, output / "contract-players.parquet", table_name="historical_contract_players"
        ).as_record(),
        "terms": write_canonical_parquet(
            terms, output / "contract-year-terms.parquet", table_name="historical_contract_year_terms"
        ).as_record(),
        "identity": write_canonical_parquet(
            identities, output / "identity-audit.parquet", table_name="historical_contract_identity_audit"
        ).as_record(),
    }
    status_counts = {
        str(row["match_status"]): int(row["len"])
        for row in identities.group_by("match_status").len().sort("match_status").iter_rows(named=True)
    }
    report = {
        "report_schema_version": "0.1",
        "season": 2025,
        "source": "private_retrospective_cots_derived_gist",
        "gist_id": GIST_ID,
        "gist_revision": revision,
        "source_created_at": metadata.get("created_at"),
        "source_updated_at": metadata.get("updated_at"),
        "team_files": len(manifest),
        "player_rows": players.height,
        "annual_term_rows": terms.height,
        "identity_status": status_counts,
        "accepted_identity_rows": status_counts.get("accepted_team_name_exact_service", 0),
        "available_amount_rows": terms.filter(pl.col("term_status") == "available").height,
        "control_state_rows": terms.filter(pl.col("term_status") == "control_state").height,
        "unparsed_term_rows": terms.filter(pl.col("term_status") == "review_unparsed").height,
        "replay_mode_boundary": "retrospective_event_cutoff_not_vintage_information_set",
        "authority_boundary": "secondary_private_bridge_not_primary_contract_authority",
        "raw_manifest": manifest,
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key not in {"raw_manifest", "storage"}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
