"""Independent source totals and missingness; no projection fits or source waiver."""
import gzip
import hashlib
import json
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
import capture_hitter_statcast_history as first
import capture_hitter_statcast_history_v2 as second

ROOT, OUT = first.ROOT, first.OUT
RESULT = ROOT/'reports/generated/hitter-statcast-historical-capture-audit'


def main():
    assert not (RESULT/'report.json').exists(), 'Preserve completed audit'
    RESULT.mkdir(parents=True,exist_ok=True)
    counts_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    dates_path=ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    counts=pl.read_parquet(counts_path).filter(pl.col('bucket')=='MLB').with_columns(
        (pl.col('babip_hits')-pl.col('doubles')-pl.col('triples')).alias('singles'))
    dated=pl.read_parquet(dates_path).filter(pl.col('bucket')=='MLB')
    hashes={str(p):sha256_file(p) for p in [Path(__file__),Path(first.__file__),Path(second.__file__),
        first.CONTRACT,second.AMENDMENT,counts_path,dates_path]}
    years=[]
    for year in range(2015,2023):
        frames=[]
        for month in range(3,11):
            receipt_path=OUT/f'{year}-{month:02}.json'
            r=json.loads(receipt_path.read_text(encoding='utf8'))
            assert r['season']==year and r['month']==month
            assert r['contract_sha256']==hashes[str(first.CONTRACT)]
            assert r['collector_sha256'] in [hashes[str(Path(first.__file__))],hashes[str(Path(second.__file__))]]
            if 'amendment_sha256' in r: assert r['amendment_sha256']==hashes[str(second.AMENDMENT)]
            hashes[str(receipt_path)]=sha256_file(receipt_path)
            for path,digest in r['outputs'].items():
                assert sha256_file(Path(path))==digest
                hashes[path]=digest
            zipped=receipt_path.with_suffix('.csv.gz')
            # Independently confirm that retained compression recovers exact response bytes.
            with gzip.open(zipped,'rb') as stream:
                digest=hashlib.sha256(); byte_count=0
                while block:=stream.read(1_000_000): digest.update(block); byte_count+=len(block)
            assert digest.hexdigest()==r['response_sha256'] and byte_count==r['response_bytes']
            q=pl.read_parquet(receipt_path.with_suffix('.parquet')); assert len(q)==r['raw_rows']
            frames.append(q)
        raw=pl.concat(frames)
        assert raw.unique(['game_pk','batter','at_bat_number','pitch_number']).height==len(raw)
        assert raw.unique(['game_pk','batter','at_bat_number']).height==len(raw)
        assert set(raw['game_year'].cast(pl.Int64).unique())=={year} and set(raw['game_type'].unique())=={'R'}
        hit=raw.group_by(pl.col('batter').cast(pl.Int64).alias('player_id')).agg(
            *[(pl.col('events')==event).sum().alias(name) for event,name in
            [('single','singles'),('double','doubles'),('triple','triples'),('home_run','home_runs')]],
            pl.len().alias('all_source_results'),(pl.col('events')=='catcher_interf').sum().alias('catcher_interference'))
        expected=counts.filter(pl.col('season')==year).select('player_id','singles','doubles','triples','home_runs')
        official=dated.filter(pl.col('season')==year).group_by('player_id').agg(
            (pl.col('at_bats')-pl.col('strike_outs')+pl.col('sac_flies')+pl.col('sac_bunts')).sum().alias('official_contact_denominator'))
        joined=expected.join(hit,on='player_id',how='full',coalesce=True,suffix='_raw').join(official,on='player_id',how='full',coalesce=True).fill_null(0)
        cols=['singles','doubles','triples','home_runs']
        assert joined.select(pl.all_horizontal([pl.col(c)==pl.col(c+'_raw') for c in cols]).all()).item(), 'Hit reconciliation failed'
        joined=joined.with_columns((pl.col('all_source_results')-pl.col('catcher_interference')).alias('source_without_catcher_interference'))
        joined=joined.with_columns((pl.col('source_without_catcher_interference')-pl.col('official_contact_denominator')).alias('contact_denominator_residual'))
        errors=joined.filter(pl.col('contact_denominator_residual')!=0)
        name_map=dated.filter(pl.col('season')==year).select('player_id','player_name').unique()
        assert name_map.unique('player_id').height==len(name_map)
        errors=errors.join(name_map,on='player_id',how='left',validate='1:1')
        errors.write_parquet(RESULT/f'contact-denominator-residuals-{year}.parquet')
        uncommon=raw.filter(pl.col('type').fill_null('')!='X').select('game_pk','batter','type','events','description','des')
        assert uncommon.filter(pl.col('events')!='catcher_interf').is_empty(), 'Inspect non-X source result other than catcher interference'
        nonbunt=raw.filter((pl.col('type')=='X')&~pl.col('des').fill_null('').str.to_lowercase().str.contains(r'\bbunt\b'))
        complete=nonbunt.filter(pl.col('launch_speed').is_not_null()&pl.col('launch_angle').is_not_null())
        years.append(dict(season=year,source_results=len(raw),complete_nonbunt_pairs=len(complete),
            terminal_nonbunt_results=len(nonbunt),missing_pair_results=len(nonbunt)-len(complete),
            complete_pair_share=len(complete)/len(nonbunt),source_people=raw['batter'].n_unique(),
            exact_all_player_hit_counts=True,catcher_interference_results=uncommon.to_dicts(),
            contact_denominator_residual_people=len(errors),contact_denominator_residual_total=int(errors['contact_denominator_residual'].sum()),
            contact_denominator_residual_absolute=int(errors['contact_denominator_residual'].abs().sum()),
            contact_denominator_residuals=errors.select('player_id','player_name','official_contact_denominator',
                'source_without_catcher_interference','contact_denominator_residual').to_dicts(),
            approved_for_modeling=False))
        print(f'{year}: all hit counts exact; {len(complete)} measured pairs; {len(errors)} unresolved denominator profiles.',flush=True)
    first.write(RESULT/'report.json',dict(source_only=True,new_model_fits=0,protected_outcomes_used=False,
        source_walkthrough_status='pending',approved_for_modeling=False,source_hashes=hashes,years=years,
        unchanged_query_scope=True,source_years=list(range(2015,2023)),
        no_source_waiver=True,output_hashes={str(p):sha256_file(p) for p in RESULT.glob('*.parquet')}))


if __name__=='__main__':main()
