"""Publish compact verified source evidence without private raw captures."""
import json
from pathlib import Path
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/model-evidence/hitter-2025-source-extension'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    assert not (OUT/'report.json').exists(), 'Preserve public evidence'
    out_tracking = ROOT/'reports/generated/hitter-tracking-2025-audit'
    out_roster = ROOT/'reports/generated/hitter-rosters-2025-source'
    out_rank = ROOT/'reports/generated/hitter-preseason-2026-archive-probe'
    tracking = read(out_tracking/'final-source-review.json')
    roster = read(out_roster/'review.json')
    rank = read(out_rank/'transport-and-player-review.json')
    for group in ['input_hashes', 'output_hashes']:
        for p, h in tracking[group].items():
            assert sha256_file(Path(p)) == h
    for p, h in roster['input_hashes'].items():
        assert sha256_file(Path(p)) == h
    for p, h in rank['source_hashes'].items():
        assert sha256_file(Path(p)) == h
    assert tracking['source_approved_for_existing_tracking_inputs'] and roster['approved_for_membership_feature'] and rank['rank_source_approved']
    walks = read(out_tracking/'completed-player-review.json')['cases']
    public_walks = []
    for c in walks:
        public_walks.append({k: c[k] for k in ['player_id', 'player_name', 'official_2025', 'raw_rows', 'measured_annual',
            'independently_reconstructed', 'input_row', 'corrections', 'judgment']} | dict(
            peers=[dict(player_id=p['player_id'], player_name=p['player_name'],
                        terminal_contacts=p['annual']['terminal_nonbunt_contacts'], mean_ev=p['annual']['mean_ev']) for p in c['peers']]))
    report = dict(tracking=tracking, rosters=roster, preseason_ranks=rank,
        all_three_source_families_verified=True, new_model_fits=0, candidate_frozen=False,
        source_player_reviews=public_walks, protected_outcomes_used=False,
        next_step='Construct origin-known 2025 membership and all matching inputs, audit training support, assemble and replay selected candidate, then freeze before final 2026 evaluation')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf8', newline='\n')
    print('Three completed source gates and case evidence published; no forecast or 2026 outcome', flush=True)


if __name__ == '__main__':
    main()
