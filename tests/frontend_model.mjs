import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeWorkspace,reviewedAtlas,isConfirmed,reviewPayload,analysisAt,offlineSuggestedFields} from '../app/web/src/data.js';
const catalog={plants:[{id:'case',scientific_name:'Species alpha',common_name:'Alpha',family:'Family'}]};
test('proposals and historical narratives never become a reviewed cohort',()=>{
 const w=normalizeWorkspace({proposed_claims:[{id:'unreviewed',year:60,candidates:[{species:'Species alpha',probability:1}]}]});
 assert.deepEqual(reviewedAtlas(w,catalog),[]);
});
test('reviewed identity candidates retain source and availability provenance',()=>{
 const w=normalizeWorkspace({reviewed:{taxa:[{species:'Species alpha',family:'Family'}],claims:[{id:'claim',year:60,identity_available_year:1800,layer:'dioscorides',category:'neuro',source_span:'Exact source',source_url:'https://example.org/source',candidates:[{species:'Species alpha',probability:.6},{species:'Species beta',probability:.4}]}]}});
 const p=reviewedAtlas(w,catalog);assert.equal(p.length,2);assert.equal(p[0].claims[0].identity_available_year,1800);assert.equal(p[0].claims[0].candidate_probability,.6);assert.equal(p[0].claims[0].text,'Exact source');
});
test('unresolved identity priors cannot enter the atlas',()=>{
 const w=normalizeWorkspace({reviewed:{claims:[{id:'bad',year:60,candidates:[{species:'Species alpha',probability:null}]}]}});
 assert.deepEqual(reviewedAtlas(w,catalog),[]);
});
test('only dated eligible ledger support produces green confirmation',()=>{
 const ledger=[{species:'Species alpha',category:'neuro',tested_year:1950,confirmed_year:1970}];
 assert.equal(isConfirmed(ledger,'Species alpha','neuro',1969),false);assert.equal(isConfirmed(ledger,'Species alpha','neuro',1970),true);
 assert.equal(isConfirmed([{species:'Species alpha',category:'neuro',year:1804,label:'Discovery'}],'Species alpha','neuro',2026),false);
});
test('review requires a named person, decision reason, and explicit attestation',()=>{
 const base={reviewer:'Reviewer',decision:'defer',note:'Date unresolved',record:{id:'c',revision:3},fields:{category:'neuro'},attested:true};
 assert.equal(reviewPayload(base).expected_revision,3);
 assert.throws(()=>reviewPayload({...base,attested:false}),/personally checked/);
 assert.throws(()=>reviewPayload({...base,reviewer:''}),/reviewer name/);
 assert.throws(()=>reviewPayload({...base,note:''}),/reason/);
});
test('absent analysis stays pending instead of manufacturing a ratio',()=>{
 const result=analysisAt({},2000);assert.equal(result.status,'pending');assert.equal(result.methods.length,0);
});

test('offline cue copying cannot create a review or override an abstention',()=>{
 const suggestion={method:'synthetic-cue-test',abstain:false,verdict:'supports',evidence_tier:'in_vivo',preparation_scope:'botanical',study_type:'original',reviewed:true,attested:true,decision:'accept'};
 assert.deepEqual(offlineSuggestedFields(suggestion),{verdict:'supports',evidence_tier:'in_vivo',preparation_scope:'botanical',study_type:'original'});
 assert.deepEqual(offlineSuggestedFields({...suggestion,abstain:true}),{});
 assert.deepEqual(offlineSuggestedFields({...suggestion,verdict:null}),{});
});
