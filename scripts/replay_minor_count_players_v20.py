"""Replay the sealed player trace with an explicitly hashed archive access helper."""
from pathlib import Path
import sys

import minor_count_archive_access_v20 as storage
from universal_baseball.storage import sha256_file

# The initial trace imported digest from a temporary storage helper extension.
# Keep its executed source unchanged; supply the same storage-only function here.
sys.modules['archive_minor_count_fits_v20']=storage
import review_minor_count_players_v20 as original

original_write=original.write


def write(path,value):
    assert path.name=='player-walkthrough.json.gz'
    value=dict(value,storage_replay_of_sealed_player_trace=True,model_refits=0,
        execution_note='Archive access moved to a dedicated helper after the initial trace. This sibling replay hashes all current execution dependencies; source counts and forecasts are unchanged.')
    value['hashes'].update({str(p):sha256_file(p) for p in [Path(__file__).resolve(),Path(storage.__file__).resolve(),
        original.PUBLIC/'archive-index.json.gz',original.PUBLIC/'reference-fits.zip',original.PUBLIC/'player-walkthrough.json.gz']})
    original_write(path.with_name('player-walkthrough-replayed.json.gz'),value)


if __name__=='__main__':
    original.write=write
    original.main()
