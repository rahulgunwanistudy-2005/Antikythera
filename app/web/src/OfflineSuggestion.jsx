import React from 'react';
import {asArray,humanize} from './data.js';
export default function OfflineSuggestion({suggestion,compact=false,onCopy}){
 if(!suggestion||typeof suggestion!=='object')return null;
 return <div className={'offline-suggestion '+(compact?'compact':'')}><strong>Offline cue suggestion; unreviewed</strong><p>{suggestion.abstain?'Abstains from a verdict':suggestion.verdict?humanize(suggestion.verdict):'No verdict suggested'}{suggestion.evidence_tier?' · '+humanize(suggestion.evidence_tier):''}</p><p className="suggestion-scope">{humanize(suggestion.preparation_scope||'scope unresolved')} · {humanize(suggestion.study_type||'study type unresolved')}</p>{suggestion.rationale&&<p>{suggestion.rationale}</p>}{!compact&&<><small>Method: {humanize(suggestion.method||'offline cue rules')}. Cue matches do not establish study relevance or a pharmacological effect.</small>{asArray(suggestion.caveats).length>0&&<ul>{suggestion.caveats.map((c,i)=><li key={i}>{c}</li>)}</ul>}{onCopy&&<button type="button" className="secondary-button" disabled={suggestion.abstain===true||!suggestion.verdict} onClick={onCopy}>Copy suggested fields to the form</button>}</>}</div>
}
