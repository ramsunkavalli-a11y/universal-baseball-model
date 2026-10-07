"""Independent completed-state calendar replay of the corrected sibling audit."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import gzip
import json

import verify_defense_role_population_v16 as original
import repair_defense_role_calendar_v16 as current
from run_hitter_finite_return_baseline import save, protections
from universal_baseball.storage import sha256_file


def independent_calendar():
    # A log can exist while this saved schedule has no completed listing.
    # Such dates stay unknown; lack of a calendar key is not zero exposure.
    result=defaultdict(lambda:dict(dates=[],period=None))
    for year in range(2021,2025):
        for sport in (1,11,12,13,14,16):
            if sport==1:
                p=current.ROOT/'reports/generated/hitter-injury-history-v2/source/captures'/f'schedule-{year}.json'
                payload=json.loads(p.read_text(encoding='utf8'))
            else:
                p=current.ROOT/'reports/generated/hitter-minor-statcast-capture/official-context'/f'schedule-{year}-{sport}.json.gz'
                payload=json.loads(gzip.decompress(p.read_bytes()))
            grouped=defaultdict(list)
            assert sum(len(d['games']) for d in payload['dates'])==payload['totalGames']
            for d in payload['dates']:
                for g in d['games']:
                    detail=g['status']['detailedState']
                    if detail[:5]!='Final' and not detail.startswith('Completed Early'):continue
                    grouped[g['gamePk']].append((d['date'],g))
            for pk,entries in grouped.items():
                all_dates={d for d,g in entries}|{g['officialDate'] for d,g in entries}
                all_dates|={g[k] for d,g in entries for k in ('resumeGameDate','resumedFromDate') if g.get(k)}
                periods={'before_August' if date.fromisoformat(d).month<8 else 'August_onward' for d in all_dates}
                teams={tuple(sorted(g['teams'][s]['team']['id'] for s in ('home','away'))) for d,g in entries}
                originals={g['officialDate'] for d,g in entries}
                valid=len(teams)==len(originals)==1 and all(g['status']['abstractGameState']=='Final' for d,g in entries)
                result[year,sport,pk]=dict(dates=sorted(all_dates),
                    period=next(iter(periods)) if valid and len(periods)==1 else None)
    return result


def main():
    protections()
    seal=current.DEST/'calendar-execution-seal.json'
    for path,digest in json.loads(seal.read_text(encoding='utf8'))['input_hashes'].items():
        assert sha256_file(Path(path))==digest,path
    original.DEST=current.DEST;original.write=current.write
    original.independent_calendar=independent_calendar
    original.main()
    current.write('calendar-verifier-receipt.json',dict(
        verifier_sha256=sha256_file(Path(__file__)),
        original_verifier_sha256=sha256_file(Path(original.__file__)),
        independent_calendar_uses_detailed_played_states=True,
        original_source_and_verification_preserved=True,
        verification_sha256=sha256_file(current.DEST/'independent-verification.json'),no_fits=True))
    protections()


if __name__=='__main__':main()
