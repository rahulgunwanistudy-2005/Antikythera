import React from 'react';
import {Icon} from './Art.jsx';
import {humanize} from './data.js';
export function SourceLink({url,children='Read source'}){return /^https?:\/\//i.test(url||'')?<a href={url} target="_blank" rel="noreferrer">{children}<Icon name="external" size={12}/></a>:<span className="muted">Source unresolved</span>}
export function Banner({icon='evidence',title,children,status}){return <div className="integrity-banner"><Icon name={icon} size={24}/><div><h2>{title}</h2><p>{children}</p></div>{status&&<span className="pending-pill">{status}</span>}</div>}
export function EmptyState({title,children,action}){return <div className="workspace-empty"><h2>{title}</h2><p>{children}</p>{action}</div>}
export function Status({value}){return <span className={'neutral-pill status-'+String(value||'pending').split('_')[0]}>{humanize(value||'pending')}</span>}
export function Search({value,onChange,label='Search records',placeholder=label}){return <label className="search-field"><Icon name="search" size={16}/><input value={value} onChange={e=>onChange(e.target.value)} aria-label={label} placeholder={placeholder}/>{value&&<button aria-label={'Clear '+label.toLowerCase()} onClick={()=>onChange('')}><Icon name="close" size={13}/></button>}</label>}
export function Readiness({workspace}){const w=workspace;return <div className="readiness-strip"><div><strong>{w.proposed_claims.length.toLocaleString()}</strong><span>Extracted proposals</span></div><div><strong>{w.reviewed.claims.length.toLocaleString()}</strong><span>Eligible source claims</span></div><div><strong>{w.proposed_evidence.length.toLocaleString()}</strong><span>Collected study records</span></div><div><strong>{w.reviewed.ledger.length.toLocaleString()}</strong><span>Eligible tested pairs</span></div></div>}
