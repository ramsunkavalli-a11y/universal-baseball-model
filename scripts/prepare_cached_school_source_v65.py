"""Source-only draft background overlay; no collection, forecasts or fitting."""
import json
from pathlib import Path
import polars as pl
from universal_baseball.cached_school_background import DatedSchoolBackground
from universal_baseball.storage import sha256_file
import prepare_practical_hitter_v31 as base

ROOT=base.ROOT
OUT=ROOT/'reports/generated/hitter-cached-school-source-v65'


def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'reports/generated/hitter-compatible-value-v63/features.parquet'
    f=pl.read_parquet(source).sort('row_id');assert len(f)==63282 and f['origin_year'].max()==2024
    hashes={str(source):sha256_file(source)};records=[];by={};identical_school_duplicates=0
    for year in range(2006,2025):
        path=base.OLD/f'draft-history/captures/draft-{year}.json'
        hashes[str(path)]=sha256_file(path)
        obj=json.loads(path.read_text(encoding='utf8'))
        for block in obj['drafts']['rounds']:
            for p in block['picks']:
                pid=(p.get('person') or {}).get('id');number=p.get('pickNumber')
                if not pid or not number:continue
                school=p.get('school') or {}
                record=dict(draft_year=int(p.get('year') or year),player_id=int(pid),pick_number=int(number),
                    school_name=school.get('name') or '',school_class=school.get('schoolClass') or '',source_path=str(path))
                assert record['draft_year']==year
                key=(year,int(pid),int(number))
                if key in by:
                    assert by[key]==record,('Conflicting school record',key)
                    identical_school_duplicates+=1
                    continue
                by[key]=record;records.append(record)
    resolver=DatedSchoolBackground(records);rows=[];evidence={}
    for r in f.iter_rows(named=True):
        record=by.get((r['draft_year'],r['player_id'],r['pick_number'])) if r['draft_known'] else None
        if r['draft_known']:
            assert record is not None,(r['player_id'],r['draft_year'],r['pick_number'])
            assert record['school_class'].strip().upper()==r['draft_school_class']
        a=resolver.resolve(record,r['origin_year']);assert all(x['year']<=r['origin_year'] for x in a['evidence'])
        evidence[r['row_id']]=dict(pick=record,**a)
        rows.append(dict(row_id=r['row_id'],school_background=a['background'],school_background_known=int(a['background']!='unknown'),
            school_source_name=record['school_name'] if record else None,
            school_background_college=int(a['background']=='college'),school_background_hs=int(a['background']=='hs'),school_background_jc=int(a['background']=='jc'),
            school_background_basis=a['basis'],school_background_evidence_year=min((v['year'] for v in a['evidence']),default=None)))
    overlay=pl.DataFrame(rows,schema_overrides={'school_background_evidence_year':pl.Int64,'school_source_name':pl.String})
    assert overlay['row_id'].equals(f['row_id'])
    overlay.write_parquet(OUT/'school-overlay.parquet')
    audit=f.join(overlay,on='row_id',validate='1:1').with_columns(
        ((pl.col('draft_class_unknown')==1)&(pl.col('school_background_known')==1)).alias('recovered_unknown_background'),
        (pl.col('draft_college')!=pl.col('school_background_college')).alias('college_flag_change'))
    audit.filter((pl.col('draft_known')==1)&(pl.col('school_background_known')==0)).select(
        'row_id','player_id','player_name','origin_year','draft_year','pick_number','draft_school_class',
        'school_source_name','school_background_basis','school_background_evidence_year').write_parquet(OUT/'unresolved-drafted-backgrounds.parquet')
    q=pl.read_parquet(ROOT/'reports/generated/hitter-compatible-value-v63/scored-predictions.parquet',columns=['row_id'])
    evaluated=audit.join(q,on='row_id',how='semi')
    def counts(g):
        return dict(rows=len(g),people=g['player_id'].n_unique(),known_background=g['school_background_known'].sum(),
            class_unknown=g['draft_class_unknown'].sum(),recovered_unknown_background=g['recovered_unknown_background'].sum(),
            college_flag_changes=g['college_flag_change'].sum(),backgrounds=g.group_by('school_background').len().sort('school_background').to_dicts())
    wanted=[('Mike Zunino',2012),('Kyle Schwarber',2014),('Michael Conforto',2014),('Dansby Swanson',2015),('Alex Bregman',2015),('Nick Kurtz',2024),('Ethan Salas',2024)]
    hs=audit.filter((pl.col('origin_year')==2016)&(pl.col('draft_year')==2016)&(pl.col('prior_debut')==0)&(pl.col('school_background_hs')==1)).sort('pick_number','player_id').head(1)
    assert len(hs)==1
    wanted.append((hs['player_name'][0],2016))
    for control in [audit.filter(pl.col('school_background_basis')=='conflicting dated institution groups').sort('origin_year','player_id').head(1),
                    audit.filter((pl.col('draft_jc')==0)&(pl.col('school_background_jc')==1)).sort('origin_year','pick_number','player_id').head(1)]:
        assert len(control)==1
        wanted.append((control['player_name'][0],int(control['origin_year'][0])))
    cases=[]
    for name,year in wanted:
        g=audit.filter((pl.col('player_name')==name)&(pl.col('origin_year')==year));assert len(g)==1,(name,year)
        r=g.row(0,named=True);a=evidence[r['row_id']]
        old={k:r[k] for k in ['draft_known','draft_year','pick_number','draft_school_class','draft_college','draft_hs','draft_jc','draft_class_unknown']}
        if a['background']=='unknown':note='No exact cutoff-known classification; background and precise class remain unknown. No college assignment inferred from player success.'
        elif r['draft_class_unknown']:
            note='Broad background recovered from the dated pick/institution evidence below. Precise class is still unknown; original source flags and forecasts are not overwritten.'
        else:note='Existing precise class supplies the same broad background. No repair is required for this own pick.'
        cases.append(dict(player=name,player_id=r['player_id'],origin_year=year,row_id=r['row_id'],old_inputs=old,
            own_pick=a['pick'],new_background=a['background'],basis=a['basis'],evidence=a['evidence'],
            new_indicators={k:r[k] for k in overlay.columns if k!='row_id'},review_note=note,
            forecast_changed=False))
    write('source-cases.json',dict(selection='Seven names/origins locked in contract, first 2016 high-school pick by cutoff-known pick order, and two source-only ambiguity/JC controls; outcomes unused.',
        cases=cases,player_walkthrough_status='complete',no_models_fitted=True))
    code=[ROOT/'docs/hitter-cached-school-source-v65-contract.md',ROOT/'docs/hitter-cached-school-source-v65-result.md',
          ROOT/'src/universal_baseball/cached_school_background.py',ROOT/'tests/test_cached_school_background.py',Path(__file__)]
    hashes.update({str(p):sha256_file(p) for p in code})
    write('source-report.json',dict(input_hashes=hashes,all=counts(audit),evaluation=counts(evaluated),
        origins=[dict(origin_year=y,**counts(audit.filter(pl.col('origin_year')==y))) for y in sorted(audit['origin_year'].unique())],
        first_year_drafted=[dict(origin_year=y,**counts(audit.filter((pl.col('origin_year')==y)&(pl.col('draft_year')==y)&(pl.col('prior_debut')==0)))) for y in sorted(audit['origin_year'].unique())],
        ambiguity_rows=audit.filter(pl.col('school_background_basis')=='conflicting dated institution groups').height,
        identical_school_duplicates=identical_school_duplicates,
        player_walkthrough_status='complete',no_models_fitted=True,new_college_information_collected=False,original_sources_and_forecasts_unchanged=True,
        output_hashes={str(OUT/p):sha256_file(OUT/p) for p in ['school-overlay.parquet','unresolved-drafted-backgrounds.parquet','source-cases.json']}))
    archive=ROOT/'reports/model-evidence/hitter-cached-school-source-v65'
    archive.mkdir(parents=True,exist_ok=True)
    for name in ['source-report.json','source-cases.json']:(archive/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps(dict(all=counts(audit),evaluation=counts(evaluated)),indent=2),flush=True)


if __name__=='__main__':main()
