export const tabs=[['time','Time machine'],['corpus','Corpus & review'],['evidence','Evidence ledger'],['results','Backtest results'],['identity','Plant identities'],['shortlist','Research shortlist'],['method','The method']];
export const freezeYears=[1900,1950,1980,2000,2010];
export const labels={time:['A long memory. A fair test.','Did Mediterranean medicine point toward effects that science later found?'],corpus:['Read the record. Check the claim.','Exact source spans, dated editions, and decisions that can be audited.'],evidence:['Follow the evidence.','A dated paper becomes an outcome only after its botanical evidence is reviewed.'],results:['The past, against its controls.','Temporal comparisons, with uncertainty and explicit limits.'],identity:['One name, many possibilities.','Historical names carry uncertainty. The analysis should carry it, too.'],shortlist:['The next question to test.','Research prioritisation for laboratory testing, with a hazard trail.'],method:['Let the past face a fair test.','Freeze the record. Match the controls. Measure what survives.']};
export const humanize=value=>String(value??'Unspecified').replaceAll('_',' ');
export const yearLabel=value=>Number.isInteger(value)?`${value} CE`:'Date unresolved';
export const number=value=>typeof value==='number'&&Number.isFinite(value)?value.toLocaleString(undefined,{maximumFractionDigits:2}):'Pending';
export const percent=value=>typeof value==='number'&&Number.isFinite(value)?`${(value*100).toFixed(1)}%`:'Pending';
export function asArray(value){return Array.isArray(value)?value:[]}
export function normalizeWorkspace(raw={}){
 const reviewed=raw.reviewed||{},dataset=raw.dataset||{};
 return {...raw,sources:asArray(raw.sources),proposed_claims:asArray(raw.proposed_claims),proposed_evidence:asArray(raw.proposed_evidence),proposed_taxa:asArray(raw.proposed_taxa),proposed_identities:asArray(raw.proposed_identities),forward:raw.forward||raw.ranker?.forward||{},collection:raw.collection||{},reviewed:{...reviewed,claims:asArray(reviewed.claims||dataset.claims),identities:asArray(reviewed.identities),ledger:asArray(reviewed.ledger||dataset.ledger),taxa:asArray(reviewed.taxa||dataset.taxa),grades:asArray(reviewed.grades)},ranker:raw.ranker||{status:'pending',shortlist:[]},audits:raw.audits||{},stats:raw.stats||{}};
}
export function reviewedAtlas(workspace,catalog){
 const data=normalizeWorkspace(workspace),taxa=new Map(data.reviewed.taxa.map(t=>[t.species||t.species_id,t])),provenance=new Map(asArray(data.dataset?.claim_provenance).map(p=>[p.claim_id,p]));
 const plants=new Map();
 for(const claim of data.reviewed.claims){
  if(!Number.isInteger(claim.year)||!Number.isInteger(claim.identity_available_year))continue;
  const all=asArray(claim.candidates);
  if(!all.length||all.some(c=>!Number.isFinite(c.probability)||c.probability<0||c.probability>1)||Math.abs(all.reduce((sum,c)=>sum+c.probability,0)-1)>1e-7)continue;
  const candidates=all.filter(c=>c.probability>0);
  if(!candidates.length)continue;
  for(const c of candidates){
   const species=c.species||c.species_id;if(!species)continue;
   if(!plants.has(species)){
    const known=asArray(catalog?.plants).find(p=>p.scientific_name===species),taxon=taxa.get(species)||{};
    plants.set(species,{id:species,common_name:taxon.common_name||known?.common_name||species,scientific_name:species,family:taxon.family||known?.family||'Family unresolved',summary:'An accepted species linked to source-grounded claims through reviewed identity distributions.',hazard:taxon.hazard||known?.hazard||'Hazard review is incomplete. No botanical use is implied.',candidates:[],claims:[],milestones:[],sources:[]});
   }
   const p=plants.get(species),source={...provenance.get(claim.id),...claim};
   p.claims.push({...source,era:claim.layer||claim.era,text:claim.source_span||claim.text||claim.ailment_as_written||'Reviewed source claim',source_url:source.source_url,candidate_probability:c.probability,identity_available_year:claim.identity_available_year});
  }
 }
 return [...plants.values()].sort((a,b)=>a.common_name.localeCompare(b.common_name));
}
export function isConfirmed(ledger,species,category,year){return asArray(ledger).some(row=>(row.species||row.species_id)===species&&row.category===category&&Number.isInteger(row.confirmed_year)&&row.confirmed_year<=year)}
export function matchingMethods(report,freeze){return asArray(report?.analysis?.[String(freeze)]?.primary?.methods)}
export function analysisAt(report,freeze){return report?.analysis?.[String(freeze)]?.primary||{status:'pending',reason:'No analysis export is available at this freeze.',methods:[]}}
export function reviewPayload({reviewer,decision,note,record,fields,attested}){
 if(!reviewer?.trim())throw Error('Enter your reviewer name.');
 if(!attested)throw Error('Confirm that you personally checked the displayed source.');
 if(!['accept','reject','defer'].includes(decision))throw Error('Choose a review decision.');
 if(!note?.trim())throw Error('Record a reason for this decision.');
 return {reviewer:reviewer.trim(),decision,note:note.trim(),expected_revision:Number.isInteger(record.revision)?record.revision:0,attested:true,fields};
}
export function downloadJson(value,name){const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
export function offlineSuggestedFields(suggestion){
 if(!suggestion||suggestion.abstain===true||!['supports','refutes','irrelevant'].includes(suggestion.verdict))return {};
 const fields={verdict:suggestion.verdict};
 if(['in_vitro','in_vivo','clinical','not_applicable'].includes(suggestion.evidence_tier))fields.evidence_tier=suggestion.evidence_tier;
 if(['botanical','compound_only','unclear'].includes(suggestion.preparation_scope))fields.preparation_scope=suggestion.preparation_scope;
 if(['original','review','other','unclassified'].includes(suggestion.study_type))fields.study_type=suggestion.study_type;
 return fields;
}
