import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Icon,Mechanism} from './Art.jsx';
import {downloadJson,labels,normalizeWorkspace,tabs} from './data.js';
import Atlas from './Atlas.jsx';
import Corpus from './Corpus.jsx';
import Evidence from './Evidence.jsx';
import Identities from './Identities.jsx';
import Results from './Results.jsx';
import Shortlist from './Shortlist.jsx';
import Method from './Method.jsx';
import {Eras,Footer,Hero,Legends,Question,SiteNav,useReveal} from './Landing.jsx';
import './styles.css';
import './workspace.css';
import './theme.css';

async function getJson(url,required=false){const response=await fetch(url,{cache:'no-store'});if(!response.ok){if(required)throw Error('The research export could not be loaded.');return null}const type=response.headers.get('content-type')||'';if(!type.includes('json')){if(required)throw Error('The research export is not valid JSON.');return null}return response.json()}
function App(){
 const [catalog,setCatalog]=useState(null),[report,setReport]=useState(null),[workspace,setWorkspace]=useState(normalizeWorkspace()),[local,setLocal]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[refreshing,setRefreshing]=useState(false),[job,setJob]=useState(null),[tab,setTab]=useState('time'),[year,setYear]=useState(1800),[drawer,setDrawer]=useState(false),[modal,setModal]=useState(false);
 useEffect(()=>{let alive=true;Promise.all([getJson('/catalog.json',true),getJson('/report.json'),getJson('/workspace.json'),['localhost','127.0.0.1','[::1]'].includes(location.hostname)?getJson('/api/health').catch(()=>null):Promise.resolve(null)]).then(async([c,r,w,health])=>{const isLocal=health?.mode==='local'&&health?.review_enabled===true;if(isLocal){try{w=await getJson('/api/workspace',true);r=await getJson('/api/report')||r}catch(e){if(alive)setNotice('The local review service could not load. Showing the static export.');}}if(alive){setCatalog(c);setReport(r);setWorkspace(normalizeWorkspace(w||{}));setLocal(isLocal&&w?.mode==='local')}}).catch(e=>{if(alive)setError(e.message)});return()=>{alive=false}},[]);
 useEffect(()=>{const close=e=>{if(e.key==='Escape'){setModal(false);setDrawer(false)}};window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close)},[]);
 async function refresh(){setRefreshing(true);setNotice('');try{const [w,r]=await Promise.all([getJson(local?'/api/workspace':'/workspace.json',true),getJson(local?'/api/report':'/report.json')]);setWorkspace(normalizeWorkspace(w));if(r)setReport(r);setNotice('Workspace refreshed. Review decisions and analysis eligibility remain separate.')}catch(e){setNotice(e.message)}finally{setRefreshing(false)}}
 useEffect(()=>{if(!job?.poll_url||['succeeded','failed'].includes(job.status))return;let active=true,timer;const poll=async()=>{try{const state=await getJson(job.poll_url,true);if(!active)return;if(state.status==='succeeded'){setJob({...state,poll_url:job.poll_url});await refresh();setNotice('Rebuild completed. Only records passing the scientific eligibility gates entered the analysis.');return}if(state.status==='failed'){setJob({...state,poll_url:job.poll_url});setNotice('Rebuild failed: '+(state.error||state.result?.error||'Inspect the local job record for details.'));return}setJob(j=>({...j,status:state.status}));timer=setTimeout(poll,1000)}catch(e){if(active){setNotice('The rebuild status could not be read. Refresh the workspace to check the saved job.');timer=setTimeout(poll,3000)}}};timer=setTimeout(poll,1000);return()=>{active=false;clearTimeout(timer)}},[job?.poll_url,job?.status]);
 async function rebuild(){setNotice('');try{const response=await fetch('/api/rebuild',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}),data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'The local rebuild could not be started.');if(!String(data.poll_url||'').startsWith('/api/jobs/'))throw Error('The local service returned an invalid job reference.');setJob(data);setNotice('Rebuilding reviewed inputs, analysis, and static exports. This does not approve unresolved proposals.')}catch(e){setNotice(e.message)}}
 function scrollToId(id){const el=document.getElementById(id);if(el)el.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'})}
 function navigate(value){setTab(value);setDrawer(false);requestAnimationFrame(()=>scrollToId('observatory'))}
 function onSection(id){if(id==='top'){window.scrollTo({top:0,behavior:'smooth'});return}if(id==='method'||id==='shortlist'){navigate(id);return}scrollToId(id)}
 function freezeAt(y){setYear(Math.min(2026,Math.max(60,y)));navigate('time')}
 function exportData(){downloadJson({schema_version:2,exported_at:new Date().toISOString(),status:report?.status||'pending_scientific_validation',display_year:year,catalog,report,workspace},'antikythera-research-export.json')}
 useReveal();
 if(error)return <div className="loading"><Mechanism/><h1>Antikythera</h1><p role="alert">{error}</p><button className="cta" onClick={()=>location.reload()}>Try again</button></div>;
 if(!catalog)return <div className="loading"><div className="spin-slow"><Mechanism/></div><p>Opening the historical record…</p></div>;
 return <div className="site"><a className="skip-link" href="#observatory">Skip to the observatory</a>
  <SiteNav onSection={onSection} local={local}/>
  <Hero workspace={workspace} onEnter={()=>navigate('time')} onMethod={()=>navigate('method')}/>
  <Question workspace={workspace}/>
  <Eras catalog={catalog} workspace={workspace} onFreeze={freezeAt}/>
  <Legends catalog={catalog} onFreeze={freezeAt}/>
  <section id="observatory" className="band dark observatory">
   <div className="band-inner">
    <header className="center-head" data-reveal><div className="script">The observatory</div><h2>{labels[tab][0].replace(/\.$/,'')}<b>.</b></h2><p>{labels[tab][1]}</p></header>
    <div className="obs-bar" data-reveal>
     <div className="obs-tabs" role="tablist" aria-label="Observatory views">{tabs.map(([id,label])=><button key={id} role="tab" aria-selected={tab===id} className={tab===id?'active':''} onClick={()=>setTab(id)}><Icon name={id} size={16}/>{label}</button>)}</div>
     <div className="obs-actions"><span className="mode-pill"><span className="live-dot"/>{local?'Local review enabled':'Static research export'}</span>{local&&<button className="ghost small" onClick={rebuild} disabled={job&&!['succeeded','failed'].includes(job.status)}>{job&&!['succeeded','failed'].includes(job.status)?'Rebuilding…':'Rebuild exports'}</button>}<button className="ghost small icon-only" aria-label="Refresh workspace" onClick={refresh} disabled={refreshing}>↻</button><button className="cta small" onClick={exportData}><Icon name="download" size={14}/>Export record</button><button className="ghost small icon-only" onClick={()=>setModal(true)} aria-label="About the observatory">?</button></div>
    </div>
    {notice&&<div className="workspace-notice" role="status">{notice}<button className="icon-button" aria-label="Dismiss notice" onClick={()=>setNotice('')}><Icon name="close" size={14}/></button></div>}
    <div className="obs-panel" key={tab} role="tabpanel">
     {tab==='time'&&<Atlas catalog={catalog} workspace={workspace} report={report} year={year} setYear={setYear} onIdentity={()=>navigate('identity')} onResults={()=>navigate('results')} onCorpus={()=>navigate('corpus')}/>}
     {tab==='corpus'&&<Corpus workspace={workspace} categories={catalog.categories} local={local} onRefresh={refresh}/>}
     {tab==='evidence'&&<Evidence workspace={workspace} catalog={catalog} local={local} onRefresh={refresh}/>}
     {tab==='results'&&<Results report={report} workspace={workspace} categories={catalog.categories}/>}
     {tab==='identity'&&<Identities workspace={workspace} catalog={catalog} report={report} local={local} onRefresh={refresh}/>}
     {tab==='shortlist'&&<Shortlist workspace={workspace} onMethod={()=>navigate('method')}/>}
     {tab==='method'&&<Method catalog={catalog} report={report} workspace={workspace} onFreeze={freezeAt}/>}
    </div>
   </div>
  </section>
  <Footer onSection={onSection}/>
  {modal&&<AboutModal workspace={workspace} onClose={()=>setModal(false)}/>}
 </div>
}
function AboutModal({workspace,onClose}){const ref=useRef(null);useEffect(()=>{const previous=document.activeElement;ref.current?.focus();const trap=e=>{if(e.key==='Tab'){const nodes=ref.current.querySelectorAll('button,a'),first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};const element=ref.current;element?.addEventListener('keydown',trap);return()=>{element?.removeEventListener('keydown',trap);previous?.focus()}},[]);return <div className="modal-backdrop" onClick={onClose}><section ref={ref} tabIndex={-1} className="about-modal" role="dialog" aria-modal="true" aria-labelledby="about-title" onClick={e=>e.stopPropagation()}><button className="modal-close icon-button" aria-label="Close about" onClick={onClose}><Icon name="close"/></button><Mechanism small/><h2 id="about-title">A machine for asking better questions.</h2><p>Antikythera connects historical plant claims to dated pharmacology, then asks whether those claims outperform matched controls.</p><p>This snapshot contains {workspace.proposed_claims.length.toLocaleString()} extraction proposals and {workspace.reviewed.claims.length.toLocaleString()} eligible claims. Collection, review, analysis, and forward prediction keep separate status records. No pending result becomes an established effect.</p><p className="muted">Illustrations are schematic and must not be used for plant identification. This is a research tool, not medical advice.</p><button className="cta" onClick={onClose}>Return to the record</button></section></div>}
createRoot(document.getElementById('root')).render(<App/>);
