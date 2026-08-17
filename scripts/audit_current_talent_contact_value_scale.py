#!/usr/bin/env python3
"""Audit the frozen challenger-2 MLB contact-value scale on 2021 Retrosheet.

This is a source/target feasibility gate only. It uses regular-season state
transitions strictly before 2021-07-15, builds the canonical 24-state run
expectancy matrix from that same pre-cutoff sample, attaches RE24, and freezes an
event-weighted mean RE24 for each predeclared terminal contact group.

It does not consume 2022 or 2023 evidence and does not score a player model.
"""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from zipfile import ZipFile

import polars as pl

from universal_baseball.certification import download_file
from universal_baseball.retrosheet import (
    RETROSHEET_CONTACT_VALUE_GROUPS,
    find_plays_csv_member,
    load_plays_contact_value_transitions,
)
from universal_baseball.run_expectancy import attach_re24, estimate_run_expectancy


RETROSHEET_2021_PLAYS_URL = "https://www.retrosheet.org/downloads/plays/2021plays.zip"
VALUE_SCALE_CUTOFF = date(2021, 7, 15)


def main() -> int:
    work_dir = Path("data/quarantine/current-talent-contact-value-scale")
    output_dir = Path("reports/generated/current-talent-contact-value-scale")
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_path = work_dir / "2021plays.zip"
    metadata = download_file(RETROSHEET_2021_PLAYS_URL, archive_path, timeout_seconds=240)
    with ZipFile(archive_path) as archive:
        member = find_plays_csv_member(archive.namelist())
        csv_path = work_dir / Path(member).name
        with archive.open(member) as source, csv_path.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)

    transitions = load_plays_contact_value_transitions(
        csv_path,
        cutoff_date=VALUE_SCALE_CUTOFF,
    )
    if transitions.get_column("game_date").max() >= VALUE_SCALE_CUTOFF:
        raise RuntimeError("Retrosheet contact-value audit contains post-cutoff event")

    matrix = estimate_run_expectancy(transitions)
    if matrix.height != 24:
        raise RuntimeError(f"expected 24 pre-cutoff MLB base/out states, found {matrix.height}")
    valued = attach_re24(transitions, matrix)

    target = valued.filter(pl.col("contact_value_target_candidate"))
    if target.is_empty():
        raise RuntimeError("pre-cutoff Retrosheet sample contains no contact-value targets")
    unsupported = target.filter(~pl.col("contact_value_mapping_supported"))
    if not unsupported.is_empty():
        examples = unsupported.select(
            "game_pk", "game_date", "inning", "half_inning", "at_bat_index"
        ).head(20).to_dicts()
        raise RuntimeError(
            f"frozen terminal mapping is incomplete for {unsupported.height} target contacts: {examples}"
        )

    missing_re24 = target.filter(~pl.col("re24_available"))
    if not missing_re24.is_empty():
        raise RuntimeError(
            f"RE24 unavailable for {missing_re24.height} supported pre-cutoff target contacts"
        )

    by_group = (
        target.group_by("terminal_outcome_group")
        .agg(
            pl.len().cast(pl.Int64).alias("event_count"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("game_count"),
            pl.col("re24").mean().alias("terminal_value"),
            pl.col("re24").std().alias("re24_std"),
        )
        .sort("terminal_outcome_group")
    )
    observed_groups = set(by_group.get_column("terminal_outcome_group").to_list())
    expected_groups = set(RETROSHEET_CONTACT_VALUE_GROUPS)
    if observed_groups != expected_groups:
        raise RuntimeError(
            f"terminal outcome groups mismatch: missing={sorted(expected_groups-observed_groups)} "
            f"extra={sorted(observed_groups-expected_groups)}"
        )

    values = {
        str(row["terminal_outcome_group"]): float(row["terminal_value"])
        for row in by_group.to_dicts()
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_scale_source_feasibility",
        "model_scoring_performed": False,
        "development_or_confirmation_data_used": False,
        "retrosheet_url": RETROSHEET_2021_PLAYS_URL,
        "retrosheet_archive_sha256": metadata["sha256"],
        "cutoff_date_exclusive": VALUE_SCALE_CUTOFF.isoformat(),
        "game_types": ["regular", "playoff"],
        "transition_count": transitions.height,
        "game_count": transitions.get_column("game_pk").n_unique(),
        "observed_state_count": matrix.height,
        "contact_target_count": target.height,
        "unsupported_contact_target_count": unsupported.height,
        "missing_re24_target_count": missing_re24.height,
        "terminal_outcome_values": values,
        "terminal_outcome_diagnostics": by_group.to_dicts(),
        "value_definition": (
            "Event-weighted mean contextual RE24 within frozen parsed terminal outcome group, "
            "using a run-expectancy matrix estimated only from regular-season 2021 MLB "
            "state transitions with event date strictly before 2021-07-15."
        ),
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    by_group.write_csv(output_dir / "terminal_outcome_values.csv")
    matrix.write_csv(output_dir / "run_expectancy_matrix.csv")

    lines = [
        "# Current Talent challenger-2 contact-value scale audit",
        "",
        f"- Cutoff: `< {VALUE_SCALE_CUTOFF.isoformat()}`",
        f"- Pre-cutoff state transitions: {transitions.height:,}",
        f"- Games: {report['game_count']:,}",
        f"- Observed base/out states: {matrix.height}/24",
        f"- Supported non-bunt contact targets: {target.height:,}",
        f"- Unsupported target contacts: {unsupported.height:,}",
        f"- Target contacts missing RE24: {missing_re24.height:,}",
        "",
        "Frozen terminal values:",
        "",
    ]
    for group in RETROSHEET_CONTACT_VALUE_GROUPS:
        lines.append(f"- `{group}`: {values[group]:.6f}")
    lines.extend(
        [
            "",
            "This is a source/value-scale feasibility gate only; no 2022 player-model score was computed.",
            "",
            "Retrosheet attribution: The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at 20 Sunset Rd., Newark, DE 19711.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (output_dir / "checkpoint.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
