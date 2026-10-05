"""Use an existing source overlay only to qualify descriptive training support."""
from pathlib import Path
import polars as pl
from universal_baseball.hitter_route_support import tag, counts
from universal_baseball.storage import sha256_file
from run_hitter_nonmedical_opportunity import ROOT, OUT as BASE, read, verify
from diagnose_hitter_route_support import OUT, FIXED, save


def main():
    assert not (OUT/'school-support-amendment.json').exists(), 'Preserve completed qualification'
    first=read(OUT/'execution-receipt.json'); verify(first['hashes'])
    school=ROOT/'reports/generated/hitter-cached-school-source-v65'
    source=read(school/'source-report.json'); assert source['player_walkthrough_status']=='complete'
    verify(source['input_hashes']); verify(source['output_hashes'])
    paths=[Path(__file__),ROOT/'docs/hitter-route-support-school-amendment.md',
        school/'source-report.json',school/'school-overlay.parquet',OUT/'execution-receipt.json']
    hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}
    save('school-support-source-seal.json',dict(before_support_qualification=True,new_fits=0,hashes=hashes))
    overlay=pl.read_parquet(school/'school-overlay.parquet')
    pre=read(BASE/'preflight.json'); parts=[]; case_parts=[]; changed=None
    for k in range(5):
        old=pl.read_parquet(BASE/f'features-{k}.parquet')
        j=old.join(overlay,on='row_id',how='left',validate='1:1')
        evidence=j.filter(pl.col('school_background_known')==1)
        assert (evidence['school_background_evidence_year']<=evidence['origin_year']).all()
        qualified=tag(j.with_columns(pl.when(pl.col('school_background_known')==1)
            .then(pl.col('school_background_college')).otherwise(pl.col('draft_college')).alias('draft_college')))
        if k==0:
            before=tag(old)
            changed=qualified.filter(pl.col('audit_fresh_top10_college')!=before['audit_fresh_top10_college'])
            save('school-support-source-changes.json',dict(rows=changed.select('row_id','player_id',
                'player_name','origin_year','draft_school_class','school_background','school_background_evidence_year',
                'audit_fresh_top10_college').to_dicts()))
        for c in [c for c in pre['cells'] if c['fold']==k]:
            tr=qualified.filter(pl.col('row_id').is_in(c['training_row_ids']))
            te=qualified.filter(pl.col('row_id').is_in(c['test_row_ids']))
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                support=counts(sub,te).with_columns(pl.lit(c['year']).alias('origin'),
                    pl.lit(k).alias('fold'),pl.lit(head).alias('head'))
                parts.append(support)
                for r in support.filter(pl.col('row_id').is_in(FIXED)).to_dicts():
                    query=te.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
                    match=sub
                    for n in ['audit_route','audit_age_group','on_40man','audit_major_link',
                        'audit_demonstrated_regular','audit_top20','audit_fresh_top10_college']:
                        match=match.filter(pl.col(n)==query[n])
                    assert match['player_id'].n_unique()==r['stratum_people']
                    # Preserve one row per matching person without selecting on their outcome.
                    people=match.sort(['player_id','origin_year','row_id']).unique('player_id',keep='last',maintain_order=True)
                    case_parts.append(dict(**r,matching_training_people=people.select('row_id','player_id',
                        'player_name','origin_year','next_pa','school_background','school_background_evidence_year').to_dicts()))
    detail=pl.concat(parts); assert detail.height==61038
    detail.write_parquet(OUT/'school-qualified-support.parquet')
    oldsupport=pl.read_parquet(OUT/'support.parquet')
    paired=oldsupport.join(detail,on=['row_id','head','origin','fold'],suffix='_qualified',validate='1:1')
    save('school-support-amendment.json',dict(new_fits=0,original_forecasts_unchanged=True,
        all_source_rows=63314,source_college_profile_changed_rows=changed.height,
        support_records=detail.height,support_count_changed_records=int((paired['stratum_people']!=paired['stratum_people_qualified']).sum()),
        cases=case_parts,scope='Support labeling only; V66 forecast conclusion unchanged',
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [*paths,OUT/'school-qualified-support.parquet',
            OUT/'school-support-source-changes.json',OUT/'school-support-source-seal.json']}))
    verify(hashes)
    print(__import__('json').dumps(dict(new_fits=0,source_college_profile_changed_rows=changed.height,
        support_count_changed_records=int((paired['stratum_people']!=paired['stratum_people_qualified']).sum()))),flush=True)


if __name__=='__main__': main()
