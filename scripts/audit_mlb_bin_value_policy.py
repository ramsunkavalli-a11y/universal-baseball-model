#!/usr/bin/env python
"""Primary 2024 MLB Performance-bin value policy audit.

This is the MLB analogue of the affiliated bin-value stability/pooling gates.
It deliberately keeps the universal contextual value definition fixed:

    runs + RE(after) - RE(before)

with one independently estimated full-season 2024 Retrosheet 24-state matrix.
Savant ``delta_run_exp`` is not used (ADR 022).

Design:
- fetch official 2024 MLB schedule and season-specific team->AL/NL authority;
- select 45 deterministic spread intraleague games in the AL and NL;
- fetch each selected game's official PBP once;
- classify the same screened 12 Performance bins from official outcomes/hitData;
- value terminal transitions with the full-2024 Retrosheet matrix;
- compare direct league means with same-bin peer-league shrinkage over a fixed
  prior-strength grid using both bidirectional split halves and five held-out
  folds.

The script nominates a confirmation strength only if one positive strength
matches or improves the direct baseline on every primary split-half and
cross-validation error metric. A separate season must confirm that nominated
strength before production policy is changed.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import date
import json
from math import sqrt
from pathlib import Path
from typing import Any, Mapping
from zipfile import ZipFile

import polars as pl
import requests

from audit_retrosheet_run_expectancy import _find_csv, _load_transitions
from universal_baseball.bin_value_pooling import DEFAULT_PRIOR_STRENGTHS, shrink_mean
from universal_baseball.certification import download_file
from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.mlb_season_stats import fetch_mlb_team_leagues
from universal_baseball.official import project_official_play_by_play
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.performance_events import BB_HBP_EVENT_TYPES, STRIKEOUT_EVENT_TYPES
from universal_baseball.run_expectancy import attach_re24, estimate_run_expectancy
from universal_baseball.state_transitions_v2 import build_official_state_transitions_v2


SEASON = 2024
GAMES_PER_LEAGUE = 45
FOLD_COUNT = 5
LEAGUES = {103: "AL", 104: "NL"}
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
RETROSHEET_URL = f"https://www.retrosheet.org/downloads/plays/{SEASON}plays.zip"
WORK_DIR = Path("data/quarantine/mlb-bin-value-policy")
REPORT_DIR = Path("reports/generated/mlb-bin-value-policy")
PRIMARY_METRICS = (
    "cell_mae",
    "cell_rmse",
    "event_mae",
    "event_rmse",
)


def _spread_sample(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (row["game_date"], row["game_pk"]))
    if len(ordered) < n:
        raise RuntimeError(f"requested {n} games from only {len(ordered)} candidates")
    if n == 1:
        return [ordered[len(ordered) // 2]]
    indices = [round(i * (len(ordered) - 1) / (n - 1)) for i in range(n)]
    if len(set(indices)) != n:
        raise RuntimeError("deterministic spread sample produced duplicate indices")
    return [ordered[index] for index in indices]


def _load_retrosheet_matrix() -> tuple[pl.DataFrame, dict[str, Any]]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = WORK_DIR / f"{SEASON}plays.zip"
    metadata = download_file(RETROSHEET_URL, archive_path, timeout_seconds=240)
    with ZipFile(archive_path) as archive:
        member = _find_csv(archive)
        csv_path = WORK_DIR / Path(member).name
        with archive.open(member) as source, csv_path.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
    transitions = _load_transitions(csv_path)
    matrix = estimate_run_expectancy(transitions)
    if matrix.height != 24:
        raise RuntimeError(f"Retrosheet matrix has {matrix.height} states instead of 24")
    return matrix, {
        "url": RETROSHEET_URL,
        "archive_sha256": metadata["sha256"],
        "game_count": transitions.get_column("game_pk").n_unique(),
        "candidate_transition_count": transitions.height,
        "state_count": matrix.height,
    }


def _schedule_candidates() -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    teams, team_bytes = fetch_mlb_team_leagues(SEASON)
    team_to_league = {int(row.team_id): int(row.league_id) for row in teams}
    response = requests.get(
        SCHEDULE_URL,
        params={"sportId": 1, "season": SEASON, "gameType": "R"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    candidates: dict[int, list[dict[str, Any]]] = defaultdict(list)
    total_regular = 0
    for date_row in payload.get("dates") or []:
        game_date = str(date_row.get("date") or "")
        for game in date_row.get("games") or []:
            if str(game.get("gameType") or "") != "R":
                continue
            status = game.get("status") or {}
            if str(status.get("abstractGameState") or "") != "Final":
                continue
            total_regular += 1
            home = int(((game.get("teams") or {}).get("home") or {}).get("team", {}).get("id"))
            away = int(((game.get("teams") or {}).get("away") or {}).get("team", {}).get("id"))
            home_league = team_to_league.get(home)
            away_league = team_to_league.get(away)
            if home_league is None or away_league is None:
                raise RuntimeError(f"schedule game has team absent from league authority: {game.get('gamePk')}")
            if home_league != away_league or home_league not in LEAGUES:
                continue
            candidates[home_league].append(
                {
                    "game_pk": int(game["gamePk"]),
                    "game_date": game_date,
                    "home_team_id": home,
                    "away_team_id": away,
                    "league_id": int(home_league),
                }
            )
    if set(candidates) != set(LEAGUES):
        raise RuntimeError(f"missing intraleague schedule candidates: {sorted(candidates)}")
    return dict(candidates), {
        "team_authority_sha256": __import__("hashlib").sha256(team_bytes).hexdigest(),
        "regular_final_game_count": total_regular,
        "intraleague_candidate_counts": {
            LEAGUES[league_id]: len(rows) for league_id, rows in candidates.items()
        },
    }


def _performance_core_from_official(
    pa: pl.DataFrame,
    pitch: pl.DataFrame,
    *,
    league_id: int,
) -> pl.DataFrame:
    pa_work = pa.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
        pl.col("batter_id").cast(pl.Int64).alias("batter_mlbam_id"),
        pl.col("batter_side").cast(pl.String),
        pl.col("event_type").cast(pl.String),
        pl.col("description").cast(pl.String).alias("result_description"),
    )
    duplicate_pa = pa_work.group_by(["game_pk", "at_bat_index"]).len().filter(pl.col("len") > 1)
    if not duplicate_pa.is_empty():
        raise RuntimeError("official calibration PA frame contains duplicate play sequences")

    contact_pitch = (
        pitch.filter(pl.col("is_in_play") == True)  # noqa: E712
        .select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
            pl.col("pitch_number").cast(pl.Int64),
            pl.col("hit_trajectory").cast(pl.String).alias("bb_type"),
            pl.col("hit_coord_x").cast(pl.Float64, strict=False).alias("hc_x"),
            pl.col("hit_coord_y").cast(pl.Float64, strict=False).alias("hc_y"),
        )
    )
    duplicate_contacts = (
        contact_pitch.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_contacts.is_empty():
        raise RuntimeError(
            "MLB calibration sample contains multiple official in-play pitches in one true PA"
        )

    contact_input = (
        contact_pitch.join(
            pa_work.select(
                "game_pk",
                "at_bat_index",
                "batter_mlbam_id",
                "batter_side",
                "result_description",
            ),
            on=["game_pk", "at_bat_index"],
            how="inner",
        )
        .with_columns(
            pl.lit(SEASON).alias("season"),
            pl.lit(int(league_id)).alias("league_id"),
            pl.lit("official_calibration").alias("participant_authority"),
            pl.lit("official_calibration").alias("result_description_authority"),
        )
    )
    classified = classify_contact_profile_events(contact_input) if not contact_input.is_empty() else pl.DataFrame()
    if classified.is_empty():
        contact_bins = pl.DataFrame(
            schema={"game_pk": pl.Int64, "at_bat_index": pl.Int64, "contact_core_bin": pl.String}
        )
    else:
        contact_bins = classified.select(
            "game_pk",
            "at_bat_index",
            pl.col("core_bin").alias("contact_core_bin"),
        )

    return (
        pa_work.join(contact_bins, on=["game_pk", "at_bat_index"], how="left")
        .with_columns(
            pl.when(pl.col("event_type").is_in(sorted(BB_HBP_EVENT_TYPES)))
            .then(pl.lit("BB_HBP"))
            .when(pl.col("event_type").is_in(sorted(STRIKEOUT_EVENT_TYPES)))
            .then(pl.lit("K"))
            .otherwise(pl.col("contact_core_bin"))
            .alias("core_bin"),
            pl.lit(int(league_id)).alias("league_id"),
        )
        .select("game_pk", "at_bat_index", "league_id", "core_bin")
    )


def _process_game(
    game: Mapping[str, Any],
    matrix: pl.DataFrame,
    *,
    session: requests.Session,
) -> pl.DataFrame:
    game_pk = int(game["game_pk"])
    league_id = int(game["league_id"])
    capture = capture_official_json(f"game/{game_pk}/playByPlay", session=session)
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official game {game_pk} PBP is not an object")
    pa, pitch = project_official_play_by_play(game_pk, capture.data)
    core = _performance_core_from_official(pa, pitch, league_id=league_id)
    transitions = build_official_state_transitions_v2(
        game_pk,
        capture.data,
        source_snapshot_id=f"audit:{capture.content_sha256}",
        normalization_id="audit:mlb-bin-value-policy-v1",
    )
    valued = attach_re24(transitions, matrix)
    terminal = valued.filter(
        pl.col("is_plate_appearance_result") & pl.col("re24_available")
    ).select("game_pk", "at_bat_index", "re24")
    joined = core.filter(pl.col("core_bin").is_not_null()).join(
        terminal, on=["game_pk", "at_bat_index"], how="left"
    )
    if joined.filter(pl.col("re24").is_null()).height:
        raise RuntimeError(f"core Performance PA lacks RE24 in game {game_pk}")
    return joined.with_columns(
        pl.lit(str(game["game_date"])).alias("game_date")
    )


def _bin_map(frame: pl.DataFrame) -> dict[str, dict[str, float | int]]:
    if frame.is_empty():
        return {}
    return {
        str(row["core_bin"]): {"mean": float(row["mean"]), "n": int(row["n"])}
        for row in frame.group_by("core_bin")
        .agg(pl.len().alias("n"), pl.col("re24").mean().alias("mean"))
        .to_dicts()
    }


def _score_predictions(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    if not rows:
        raise RuntimeError("cannot score empty prediction rows")
    cell_errors = [float(row["prediction"]) - float(row["holdout_mean"]) for row in rows]
    cell_n = sum(int(row["holdout_n"]) for row in rows)
    event_abs = sum(float(row["event_abs_error_sum"]) for row in rows)
    event_sq = sum(float(row["event_sq_error_sum"]) for row in rows)
    return {
        "cell_count": len(rows),
        "cell_mae": sum(abs(error) for error in cell_errors) / len(cell_errors),
        "cell_rmse": sqrt(sum(error * error for error in cell_errors) / len(cell_errors)),
        "occurrence_weighted_cell_mae": sum(
            abs(float(row["prediction"]) - float(row["holdout_mean"])) * int(row["holdout_n"])
            for row in rows
        ) / cell_n,
        "event_count": cell_n,
        "event_mae": event_abs / cell_n,
        "event_rmse": sqrt(event_sq / cell_n),
    }


def _score_holdout(
    target_training: pl.DataFrame,
    peer_training: pl.DataFrame,
    holdout: pl.DataFrame,
    *,
    strength: int,
    label: str,
) -> list[dict[str, Any]]:
    target = _bin_map(target_training)
    peer = _bin_map(peer_training)
    rows: list[dict[str, Any]] = []
    for bin_name, group in holdout.group_by("core_bin", maintain_order=True):
        bin_key = str(bin_name[0] if isinstance(bin_name, tuple) else bin_name)
        values = [float(value) for value in group.get_column("re24").to_list()]
        if bin_key not in target:
            raise RuntimeError(f"target training lacks held-out bin {bin_key} in {label}")
        if strength > 0 and bin_key not in peer:
            raise RuntimeError(f"peer training lacks held-out bin {bin_key} in {label}")
        target_row = target[bin_key]
        if strength == 0:
            prediction = float(target_row["mean"])
            prior_mean = None
            prior_n = 0
        else:
            peer_row = peer[bin_key]
            prior_mean = float(peer_row["mean"])
            prior_n = int(peer_row["n"])
            prediction = shrink_mean(
                float(target_row["mean"]),
                int(target_row["n"]),
                prior_mean,
                int(strength),
            )
        holdout_mean = sum(values) / len(values)
        rows.append(
            {
                "label": label,
                "core_bin": bin_key,
                "strength": int(strength),
                "training_mean": float(target_row["mean"]),
                "training_n": int(target_row["n"]),
                "prior_mean": prior_mean,
                "prior_n": prior_n,
                "holdout_mean": holdout_mean,
                "holdout_n": len(values),
                "prediction": prediction,
                "event_abs_error_sum": sum(abs(prediction - value) for value in values),
                "event_sq_error_sum": sum((prediction - value) ** 2 for value in values),
            }
        )
    return rows


def _evaluate(
    frames: dict[int, list[pl.DataFrame]],
    strengths: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    split_rows: list[dict[str, Any]] = []
    cv_rows: list[dict[str, Any]] = []
    league_ids = sorted(LEAGUES)

    # Bidirectional split halves: every selected game appears once as candidate
    # and once as reference across the two orientations.
    for target_league in league_ids:
        peer_league = next(value for value in league_ids if value != target_league)
        target_frames = frames[target_league]
        peer_frames = frames[peer_league]
        for orientation in (0, 1):
            target_train = pl.concat(target_frames[orientation::2], how="vertical_relaxed")
            target_holdout = pl.concat(target_frames[1 - orientation :: 2], how="vertical_relaxed")
            peer_train = pl.concat(peer_frames[orientation::2], how="vertical_relaxed")
            for strength in strengths:
                split_rows.extend(
                    _score_holdout(
                        target_train,
                        peer_train,
                        target_holdout,
                        strength=strength,
                        label=f"split:{LEAGUES[target_league]}:{orientation}",
                    )
                )

    for fold in range(FOLD_COUNT):
        for target_league in league_ids:
            peer_league = next(value for value in league_ids if value != target_league)
            target_frames = frames[target_league]
            peer_frames = frames[peer_league]
            target_train = pl.concat(
                [frame for index, frame in enumerate(target_frames) if index % FOLD_COUNT != fold],
                how="vertical_relaxed",
            )
            target_holdout = pl.concat(
                [frame for index, frame in enumerate(target_frames) if index % FOLD_COUNT == fold],
                how="vertical_relaxed",
            )
            peer_train = pl.concat(
                [frame for index, frame in enumerate(peer_frames) if index % FOLD_COUNT != fold],
                how="vertical_relaxed",
            )
            for strength in strengths:
                cv_rows.extend(
                    _score_holdout(
                        target_train,
                        peer_train,
                        target_holdout,
                        strength=strength,
                        label=f"cv:{LEAGUES[target_league]}:{fold}",
                    )
                )
    return split_rows, cv_rows


def _evaluation_table(rows: list[dict[str, Any]], strengths: list[int]) -> list[dict[str, Any]]:
    return [
        {"prior_strength": strength, **_score_predictions([row for row in rows if int(row["strength"]) == strength])}
        for strength in strengths
    ]


def _robust_strengths(
    split_eval: list[dict[str, Any]],
    cv_eval: list[dict[str, Any]],
) -> list[int]:
    split_direct = next(row for row in split_eval if int(row["prior_strength"]) == 0)
    cv_direct = next(row for row in cv_eval if int(row["prior_strength"]) == 0)
    robust: list[int] = []
    for split_row in split_eval:
        strength = int(split_row["prior_strength"])
        if strength <= 0:
            continue
        cv_row = next(row for row in cv_eval if int(row["prior_strength"]) == strength)
        split_ok = all(
            float(split_row[metric]) <= float(split_direct[metric])
            for metric in (*PRIMARY_METRICS, "occurrence_weighted_cell_mae")
        )
        cv_ok = all(
            float(cv_row[metric]) <= float(cv_direct[metric])
            for metric in (*PRIMARY_METRICS, "occurrence_weighted_cell_mae")
        )
        if split_ok and cv_ok:
            robust.append(strength)
    return robust


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    matrix, retrosheet_meta = _load_retrosheet_matrix()
    candidates, schedule_meta = _schedule_candidates()
    selected = {
        league_id: _spread_sample(rows, GAMES_PER_LEAGUE)
        for league_id, rows in candidates.items()
    }

    frames: dict[int, list[pl.DataFrame]] = {league_id: [] for league_id in LEAGUES}
    session = new_official_session()
    try:
        for league_id in sorted(selected):
            for game in selected[league_id]:
                frames[league_id].append(_process_game(game, matrix, session=session))
    finally:
        session.close()

    strengths = sorted(set(int(value) for value in DEFAULT_PRIOR_STRENGTHS))
    split_rows, cv_rows = _evaluate(frames, strengths)
    split_eval = _evaluation_table(split_rows, strengths)
    cv_eval = _evaluation_table(cv_rows, strengths)
    robust = _robust_strengths(split_eval, cv_eval)
    nominated = min(robust) if robust else 0

    payload = {
        "report_schema_version": 1,
        "status": "primary_mlb_bin_value_policy_audit_not_yet_production_policy",
        "season": SEASON,
        "games_per_league": GAMES_PER_LEAGUE,
        "fold_count": FOLD_COUNT,
        "retrosheet": retrosheet_meta,
        "schedule": schedule_meta,
        "selected_games": {
            LEAGUES[league_id]: selected[league_id] for league_id in sorted(selected)
        },
        "event_counts": {
            LEAGUES[league_id]: sum(frame.height for frame in frames[league_id])
            for league_id in sorted(frames)
        },
        "split_half_evaluations": split_eval,
        "cross_validation_evaluations": cv_eval,
        "robust_positive_strengths": robust,
        "nominated_independent_confirmation_strength": nominated,
        "decision_rule": (
            "A positive strength is robust only if it matches or improves the direct "
            "baseline on cell MAE, cell RMSE, occurrence-weighted cell MAE, event MAE, "
            "and event RMSE in both bidirectional split-half and five-fold tests. The "
            "smallest robust positive strength is nominated for independent-season "
            "confirmation; if none qualify, direct is nominated."
        ),
    }
    (REPORT_DIR / "mlb_bin_value_policy.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    pl.DataFrame(split_rows).write_csv(REPORT_DIR / "split_half_prediction_cells.csv")
    pl.DataFrame(cv_rows).write_csv(REPORT_DIR / "cross_validation_prediction_cells.csv")

    direct_split = next(row for row in split_eval if int(row["prior_strength"]) == 0)
    direct_cv = next(row for row in cv_eval if int(row["prior_strength"]) == 0)
    nominated_split = next(row for row in split_eval if int(row["prior_strength"]) == nominated)
    nominated_cv = next(row for row in cv_eval if int(row["prior_strength"]) == nominated)
    lines = [
        "# MLB Performance-bin value policy audit — 2024",
        "",
        f"- Intraleague games per AL/NL environment: {GAMES_PER_LEAGUE}",
        f"- Core events — AL / NL: {payload['event_counts']['AL']:,} / {payload['event_counts']['NL']:,}",
        f"- Full Retrosheet matrix: {retrosheet_meta['game_count']:,} games / {retrosheet_meta['state_count']} states",
        f"- Robust positive strengths: {robust}",
        f"- Nominated independent-season confirmation strength: **{nominated}**",
        "",
        "## Direct vs nominated",
        "",
        f"- Split direct: cell MAE={direct_split['cell_mae']:.5f}, RMSE={direct_split['cell_rmse']:.5f}, event MAE={direct_split['event_mae']:.5f}, event RMSE={direct_split['event_rmse']:.5f}",
        f"- Split nominated: cell MAE={nominated_split['cell_mae']:.5f}, RMSE={nominated_split['cell_rmse']:.5f}, event MAE={nominated_split['event_mae']:.5f}, event RMSE={nominated_split['event_rmse']:.5f}",
        f"- CV direct: cell MAE={direct_cv['cell_mae']:.5f}, RMSE={direct_cv['cell_rmse']:.5f}, event MAE={direct_cv['event_mae']:.5f}, event RMSE={direct_cv['event_rmse']:.5f}",
        f"- CV nominated: cell MAE={nominated_cv['cell_mae']:.5f}, RMSE={nominated_cv['cell_rmse']:.5f}, event MAE={nominated_cv['event_mae']:.5f}, event RMSE={nominated_cv['event_rmse']:.5f}",
        "",
        "No MLB production pooling rule is accepted by this primary audit alone. A positive nominated strength must survive an independent season unchanged.",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "mlb_bin_value_policy.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
