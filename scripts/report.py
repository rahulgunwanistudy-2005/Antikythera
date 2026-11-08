"""Compute every report figure from provenance-validated inputs and audit records."""
import hashlib
import json
from pathlib import Path
from scripts.build_dataset import ROOT,build,read_json
from timemachine import analyze,era_ablation
from timemachine.engine import file_drawer_sensitivity,analysis_slices
from timemachine.ranker import fit_temporal,rank_forward
from audit.scoring import score
from identity.calibrate_prior import fit_identity_calibration
from timemachine.external_checks import yarnell_overlap


def load(path,default):return read_json(path) if path.exists() else default

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def generate(root=ROOT):
    root=Path(root);reviewed=root/'data/reviewed';out=root/'data/derived';public=root/'app/web/public'
    dataset=build(reviewed,root)
    catalog=load(root/'data/seed/catalog.json',{'plants':[],'categories':[]})
    collection=load(out/'collection.json',{'counts':{},'source_status':[],'status':'not_collected'})
    audit_rows=load(reviewed/'audits.json',[])
    db_path=root/'data/local/antikythera.duckdb'
    if db_path.exists():
        from storage.repository import Repository
        audit_rows+=Repository(db_path).valid_audits()
    audits=score(audit_rows)
    gold=load(reviewed/'identity_calibration.json',{'calibration_rows':[],'evaluation_rows':[]})
    identity_model=fit_identity_calibration(gold.get('calibration_rows',[]),gold.get('evaluation_rows',[]))
    write(out/'identity_calibration.json',identity_model)
    audits['identity_calibration']=identity_model
    reference=load(root/'data/external/yarnell_reference.json',{})
    extracted=[r.get('plant_name_as_written','') for r in load(reviewed/'claims.json',[]) if r.get('era')=='dioscorides' and r.get('category')=='urinary']
    external_check=yarnell_overlap(extracted,reference.get('names'),reference_verified=reference.get('verified') is True,reference_source=reference.get('source_url'))
    readiness={'reviewed_claims':len(dataset['claims']),'reviewed_tested_pairs':len(dataset['ledger']),'reviewed_identity_groups':len(load(reviewed/'identities.json',[])),'search_complete':dataset['coverage'].get('search_complete') is True,'effort_coverage_complete':dataset['coverage'].get('effort_coverage_complete') is True,'human_audit_rows':audits['completed'],'audit_targets_met':audits['targets_met']}
    analysis={};categories=[c['id'] for c in catalog['categories']]
    for freeze in (1900,1950,1980,2000,2010):
        settings={'freeze_year':freeze,'seed':1729}
        slices=analysis_slices(dataset,categories=categories,**settings)
        analysis[str(freeze)]={'primary':analyze(dataset,**settings),'era_ablation':slices['era'],'by_category':slices['category'],'novel_in_layer':slices['novel_in_layer'],'in_vitro_sensitivity':analyze(dataset,allow_in_vitro=True,**settings),'refutation_sensitivity':analyze(dataset,count_refuted_as_failure=True,**settings),'rematched_sensitivity':analyze(dataset,resample_matching=True,**settings),'file_drawer':file_drawer_sensitivity(dataset,**settings)}
        if freeze+20>dataset['observation_end'] and freeze<dataset['observation_end']:
            analysis[str(freeze)]['available_followup_sensitivity']=analyze(dataset,follow_up=dataset['observation_end']-freeze,**settings)
    model=fit_temporal(dataset,train_freeze=1950,calibration_freeze=1980,evaluation_freeze=2000,seed=1729)
    shortlist=rank_forward(dataset,model,as_of=dataset['observation_end'])
    validated=bool(readiness['reviewed_claims'] and readiness['reviewed_tested_pairs'] and readiness['search_complete'] and readiness['effort_coverage_complete'] and readiness['audit_targets_met'])
    primary=analysis['2000']['primary'];headline=None
    if validated:
        method=next((m for m in primary.get('methods',[]) if m['method']=='research_effort' and m.get('risk_ratio') is not None and m.get('ci95') is not None),None)
        if method:headline={'freeze_year':2000,'method':method['method'],'risk_ratio':method['risk_ratio'],'ci95':method['ci95'],'estimand':primary['estimand']}
    status='audited_analysis_available' if headline else 'exploratory_analysis' if dataset['claims'] and dataset['ledger'] else 'pending_scientific_validation'
    limitations=['Model probabilities condition on future first testing and are not clinical efficacy or the chance of a future study.','Claim dates and identity prior availability must both precede a temporal freeze.','Whole-plant preparations and compound-only evidence are kept distinct.','Complete 20-year follow-up for freeze 2010 ends in 2030; shorter follow-up is a labelled sensitivity.','PubMed/EuropePMC coverage is insufficient to establish exhaustive pre-1900 pharmacology.','Publication-bias grids assume hypothetical unseen negative pairs; they do not estimate actual missing-study rates.','Identity/family fit-ensemble intervals are not confidence intervals for an established medicinal effect.']
    if not validated:limitations.insert(0,'Independent human audits, historical-date/identity review and complete evidence coverage remain release gates.')
    report={'schema_version':2,'status':status,'dataset_sha256':hashlib.sha256(json.dumps(dataset,sort_keys=True).encode()).hexdigest(),'observation_end':dataset['observation_end'],'case_study_count':len(catalog['plants']),'category_count':len(categories),'collection':collection,'external_check':external_check,'readiness':readiness,'headline':headline,'audits':audits,'analysis':analysis,'ranker':{k:v for k,v in model.items() if k not in ('model_strings','calibrators')},'shortlist':shortlist,'limitations':limitations,'software':{'collection':'implemented','source_span_validation':'implemented','harmonisation':'offline_baseline_and_optional_model','identity_candidates':'implemented','evidence_acquisition':'implemented','database_and_review':'implemented','temporal_analysis':'implemented','lightgbm_ranker':'implemented','static_and_api_workspace':'implemented'}}
    write(out/'dataset.json',dataset);write(out/'report.json',report);write(out/'ranker.json',model);write(out/'shortlist.json',shortlist)
    write(public/'catalog.json',catalog);write(public/'report.json',report)
    from scripts.export_tables import export_tables
    export_tables(dataset,root)
    counts=collection.get('counts',{})
    lines=['# Antikythera research report','','Generated by `make report`. All counts and results below come from project records.','','## Build and collection','','The source-to-review pipeline, DuckDB storage, human review API, temporal matching, calibrated temporal LightGBM training, ranking comparisons and static workspace are implemented. A completed software build does not imply a completed scientific audit.','','| Record | Count |','| --- | --- |']
    lines += [f'| {k.replace("_"," ")} | {v} |' for k,v in counts.items()]
    lines += ['','## Scientific readiness','','| Gate | Current state |','| --- | --- |']+[f'| {k.replace("_"," ")} | {v} |' for k,v in readiness.items() if not isinstance(v,dict)]
    lines += ['','### Independent audits','','| Task | Completed | Target |','| --- | --- | --- |']+[f'| {k} | {audits["completed"].get(k,0)} | {v} |' for k,v in audits['targets'].items()]
    lines += ['','Audit counts include only explicitly attested, independent gold labels with an available prediction. Empty sample templates and AI proposals do not count. Precision/recall use Wilson intervals. Extraction recall requires independently annotated complete passages. Identity ECE requires expert identity outcomes.','','## Primary result','',f'Current status: **{status}**.']
    if headline:lines.append(f'At freeze 2000, research-effort-matched RR = {headline["risk_ratio"]:.3f}, 95% CI [{headline["ci95"][0]:.3f}, {headline["ci95"][1]:.3f}].')
    else:lines.append('No audited headline effect size is released. Computed exploratory outputs, if eligible data exists, remain separated from audited results. The curated legends never become empirical outcomes.')
    lines += ['','Among species/indication pairs first tested inside the fully observed 20 years after each freeze, the analysis compares earlier claims against tested unclaimed controls. Confirmation needs an original, reviewed botanical in-vivo or clinical supporting study. Missing records remain unknown. Evidence for a purified compound does not automatically confirm a botanical preparation.','','Three matched comparisons use the same species, the same family/indication, or similar pre-freeze research effort. Publication volume is a ranking baseline. Identity sampling and family bootstrap propagate uncertainty. A separate sensitivity resamples families and refits matching. Era, category and novel/inherited layers are computed independently.','','The 2010 primary window matures in 2030. A separately named available-followup sensitivity ends at the declared observation year. It must not be compared as if it were another complete 20-year window.','','## Temporal ranker','',f'Model status: **{model["status"]}**. {model.get("reason", "A calendar-separated training, calibration and test run is available in the JSON report.")}','', 'The configured train/calibration/evaluation freezes are 1950, 1980 and 2000, with mature, nonoverlapping 20-year labels. Features use information available at each freeze. Reported performance includes precision at k and family-bootstrap comparisons, held-out reliability and ECE. Model text and calibration parameters persist as JSON, without executable pickle files.','','Forward probabilities mean confirmation conditional on a pair being first tested in the next window. They do not estimate whether a plant will be tested. Candidate release requires explicit search coverage, Mediterranean/Balkan regional provenance and a hazard trail. The interval represents identity and family-bootstrap model ensemble spread, not a clinical confidence interval.','',f'Forward status: **{shortlist["status"]}**. {shortlist.get("reason", "See the machine-readable shortlist for qualified research leads.")}','','## Source provenance','','| Source | State | Edition note |','| --- | --- | --- |']
    for source in collection.get('source_status',[]):lines.append(f'| {source.get("source_id")} | {source.get("status")} | {source.get("edition_warning",source.get("reason",""))} |')
    lines += ['','The downloaded Culpeper text identifies its edition as 1850 and includes later additions. Proposed source dates stay unresolved until review. Berendes and Adams commentary must be separated from ancient text. Modern records retain article-specific attribution and omit community columns from public exports. GBIF modern-name candidate snapshots do not substitute for expert historical identity calibration.','','## Limitations','']+['- '+s for s in limitations]
    lines += ['','## Reproduction','','`make all` runs offline cached collection, proposal synchronization, audited-input promotion, analysis/model evaluation, typed Parquet export, static JSON export, tests and the React production build. `make collect` explicitly runs network acquisition. Paid model calls require a separately enabled model command. Missing inputs return a precise pending reason.','',f'Dataset SHA-256: `{report["dataset_sha256"]}`. Full figures, sensitivity grids and audit metrics: [data/derived/report.json](data/derived/report.json).']
    (root/'REPORT.md').write_text('\n'.join(lines)+'\n')
    from scripts.workspace import export
    repository=None
    if db_path.exists():
        from storage.repository import Repository
        repository=Repository(db_path)
    export(root,repository)
    print(f'Report regenerated: {counts.get("proposed_claims",0)} proposals, {len(dataset["claims"])} eligible reviewed claims; {status}')
    return report

if __name__=='__main__':generate()
