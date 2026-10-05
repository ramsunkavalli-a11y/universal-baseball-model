"""Check one contradictory historical IL span against dated official game logs."""

import json
from pathlib import Path

import requests

from universal_baseball.role_health_separation import medical_span_audit
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/model-evidence/hitter-role-health-separation"
URL = "https://statsapi.mlb.com/api/v1/people/581527/stats?stats=gameLog&group=hitting&season=2016&sportIds=1&gameType=R"


def save(path, value):
    assert not path.exists(), "Preserve source capture"
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n",
        encoding="utf8",
        newline="\n",
    )


def main():
    assert OUT.exists() and not (OUT / "travis-source-audit.json").exists()
    response = requests.get(URL, timeout=45)
    response.raise_for_status()
    payload = response.json()
    assert len(payload["stats"]) == 1
    block = payload["stats"][0]
    assert block["type"]["displayName"] == "gameLog"
    assert block["group"]["displayName"] == "hitting"
    splits = block["splits"]
    windows = []
    for s in splits:
        assert s["season"] == "2016" and s["sport"]["id"] == 1
        assert s["player"]["id"] == 581527 and s["isHome"] in [True, False]
        day, pa = s["date"], s["stat"]["plateAppearances"]
        assert day.startswith("2016-") and pa >= 0
        windows.append(
            dict(
                start=day,
                end=day,
                available_date=day,
                pa=pa,
                game_pk=s["game"]["gamePk"],
                source_url=URL,
            )
        )
    assert sum(w["pa"] for w in windows) == 432
    assert len({w["game_pk"] for w in windows}) == len(windows)
    walks = json.loads((OUT / "player-walks.json").read_text(encoding="utf8"))["cases"]
    walk = next(
        w
        for w in walks
        if w["forecast"]["player_id"] == 581527 and w["forecast"]["origin_year"] == 2016
    )
    audit = medical_span_audit(
        walk["context"]["clinical_spells"],
        windows,
        walk["forecast"]["ctx_information_date"],
    )
    captured = OUT / "travis-2016-official-gamelog.json"
    save(captured, payload)
    conflicts = [
        w
        for a in audit
        if a["continuous_absence_contradicted"]
        for w in a["positive_contained_windows"]
    ]
    assert conflicts, "Do not assert a contradiction without a positive game"
    report = dict(
        player_id=581527,
        origin=2016,
        target=2017,
        source_url=URL,
        historical_publication_vintage_verified=False,
        source_capture_sha256=sha256_file(captured),
        captured_pa=432,
        first_positive_MLB_game=min(w["start"] for w in windows if w["pa"] > 0),
        games_inside_recorded_absence=len(conflicts),
        pa_inside_recorded_absence=sum(w["pa"] for w in conflicts),
        medical_span_audit=audit,
        exact_medical_recovery_date_known=False,
        corrected_medical_days=None,
        medical_inputs_used_in_repaired_role_heads=False,
        no_additional_model_fit=True,
        protected_2026_outcomes_used=False,
    )
    save(OUT / "travis-source-audit.json", report)
    print(
        {
            k: report[k]
            for k in [
                "first_positive_MLB_game",
                "games_inside_recorded_absence",
                "pa_inside_recorded_absence",
            ]
        }
    )


if __name__ == "__main__":
    main()
