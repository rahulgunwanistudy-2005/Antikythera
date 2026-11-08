import React,{useEffect,useRef,useState} from 'react';
import {Botanical,Icon,Mechanism} from './Art.jsx';

/* Scroll-reveal: adds .in once an element enters the viewport. */
export function useReveal(){
 useEffect(()=>{
  const nodes=[...document.querySelectorAll('[data-reveal]:not(.in)')];
  if(!('IntersectionObserver' in window)){nodes.forEach(n=>n.classList.add('in'));return}
  const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.18,rootMargin:'0px 0px -6% 0px'});
  nodes.forEach(n=>io.observe(n));
  return()=>io.disconnect();
 });
}

/* Writes scroll progress (0..1) of an element into a CSS variable for parallax and line-draw effects. */
function useScrollVar(ref,name='--p'){
 useEffect(()=>{
  let frame=0;
  const update=()=>{frame=0;const el=ref.current;if(!el)return;const r=el.getBoundingClientRect(),vh=window.innerHeight;const p=Math.min(1,Math.max(0,(vh*.55-r.top)/(r.height)));el.style.setProperty(name,p.toFixed(4));el.style.setProperty('--y',String(Math.round(-r.top)))};
  const onScroll=()=>{if(!frame)frame=requestAnimationFrame(update)};
  update();window.addEventListener('scroll',onScroll,{passive:true});window.addEventListener('resize',onScroll);
  return()=>{window.removeEventListener('scroll',onScroll);window.removeEventListener('resize',onScroll);cancelAnimationFrame(frame)};
 },[ref,name]);
}

export function CountUp({value,duration=1600}){
 const ref=useRef(null),[shown,setShown]=useState(0);
 useEffect(()=>{
  const el=ref.current;if(!el||!Number.isFinite(value))return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){setShown(value);return}
  let raf=0,start=0;
  const run=t=>{if(!start)start=t;const k=Math.min(1,(t-start)/duration),e=1-Math.pow(1-k,3);setShown(Math.round(value*e));if(k<1)raf=requestAnimationFrame(run)};
  const io=new IntersectionObserver(([entry])=>{if(entry.isIntersecting){raf=requestAnimationFrame(run);io.disconnect()}},{threshold:.4});
  io.observe(el);return()=>{io.disconnect();cancelAnimationFrame(raf)};
 },[value,duration]);
 return <span ref={ref}>{Number.isFinite(value)?shown.toLocaleString():'—'}</span>;
}

/* Procedural leaf spray: a curved stem with paired lanceolate leaves (olive / bay silhouette). */
export function Sprig({leaves=9,className='',tone='leaf',flip=false}){
 const id=React.useId().replace(/:/g,'');
 const items=Array.from({length:leaves},(_,i)=>{const t=(i+1)/(leaves+1),x=60+Math.sin(t*2.6)*34,y=380-t*340,side=i%2?1:-1,len=58-t*22,angle=side*(48-t*18);return {x,y,len,angle,side,i}});
 return <svg className={'sprig '+tone+' '+className} viewBox="0 0 200 400" aria-hidden="true"><g transform={flip?'translate(200 0) scale(-1 1)':undefined}>
  <defs><linearGradient id={'lg'+id} x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="var(--leaf-a)"/><stop offset="1" stopColor="var(--leaf-b)"/></linearGradient></defs>
  <path d={`M60 392 ${items.map(l=>`L${l.x.toFixed(1)} ${l.y.toFixed(1)}`).join(' ')} L${(60+Math.sin(2.6)*34).toFixed(1)} 30`} fill="none" stroke="var(--stem)" strokeWidth="2.2" strokeLinecap="round"/>
  {items.map(l=><g key={l.i} transform={`translate(${l.x} ${l.y}) rotate(${l.angle-90})`}><g className="sprig-leaf" style={{'--d':`${l.i*90}ms`}}><path d={`M0 0 C ${l.len*.3} ${-l.len*.22} ${l.len*.75} ${-l.len*.18} ${l.len} 0 C ${l.len*.75} ${l.len*.18} ${l.len*.3} ${l.len*.22} 0 0Z`} fill={`url(#lg${id})`}/><path d={`M2 0 L${l.len*.92} 0`} stroke="var(--vein)" strokeWidth=".8"/></g></g>)}
 </g></svg>;
}

/* Palmate leaf silhouette used for watermarks (fern-like, deliberately generic). */
export function Frond({className=''}){
 const lobes=[-62,-31,0,31,62];
 return <svg className={'frond '+className} viewBox="-120 -150 240 260" aria-hidden="true"><g fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round">
  {lobes.map((a,i)=>{const len=i===2?132:i===1||i===3?108:76,w=len*.3;return <g key={a} transform={`rotate(${a})`}><path d={`M0 0 C ${w} ${-len*.2} ${w*1.2} ${-len*.7} 0 ${-len} C ${-w*1.2} ${-len*.7} ${-w} ${-len*.2} 0 0Z`}/><path d={`M0 0 L0 ${-len*.94}`}/>{Array.from({length:4},(_,k)=><path key={k} d={`M0 ${-len*(k+1)/5.2} q${w*.45} ${-len*.06} ${w*.8} ${-len*.16} M0 ${-len*(k+1)/5.2} q${-w*.45} ${-len*.06} ${-w*.8} ${-len*.16}`}/>)}</g>})}
  <path d="M0 0 C 2 40 -4 70 -10 100"/></g></svg>;
}

const NAV=[['question','The question'],['eras','Four layers'],['legends','Legends']],NAV2=[['observatory','Observatory'],['method','Method'],['shortlist','Shortlist']];

export function SiteNav({onSection,local}){
 const [solid,setSolid]=useState(false),[open,setOpen]=useState(false);
 useEffect(()=>{const on=()=>setSolid(window.scrollY>40);on();window.addEventListener('scroll',on,{passive:true});return()=>window.removeEventListener('scroll',on)},[]);
 const go=id=>{setOpen(false);onSection(id)};
 const link=([id,label])=><button key={id} className="nav-link" onClick={()=>go(id)}>{label}</button>;
 return <header className={'site-nav '+(solid?'solid ':'')+(open?'open':'')}>
  <div className="nav-inner">
   <div className="nav-social"><span className="live-dot"/>{local?'Local workbench':'Research snapshot'}</div>
   <div className="nav-links left">{NAV.map(link)}</div>
   <button className="nav-logo" onClick={()=>go('top')} aria-label="Antikythera, back to top"><Mechanism small/><span>Antikythera<small>est. 60 CE</small></span></button>
   <div className="nav-links right">{NAV2.map(link)}</div>
   <button className="cta small" onClick={()=>go('observatory')}>Open observatory</button>
   <button className="nav-burger" aria-label="Menu" aria-expanded={open} onClick={()=>setOpen(!open)}><span/><span/><span/></button>
  </div>
  <div className="nav-drawer">{[...NAV,...NAV2].map(link)}</div>
 </header>;
}

export function Hero({workspace,onEnter,onMethod}){
 const ref=useRef(null),[year,setYear]=useState(60);
 useScrollVar(ref);
 useEffect(()=>{
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){setYear(2026);return}
  let raf=0,start=0;const run=t=>{if(!start)start=t+500;const k=Math.min(1,Math.max(0,(t-start)/5200)),e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;setYear(Math.round(60+(2026-60)*e));if(k<1)raf=requestAnimationFrame(run)};
  raf=requestAnimationFrame(run);return()=>cancelAnimationFrame(raf);
 },[]);
 const onMove=e=>{const el=ref.current;if(!el)return;const r=el.getBoundingClientRect();el.style.setProperty('--mx',((e.clientX-r.left)/r.width-.5).toFixed(3));el.style.setProperty('--my',((e.clientY-r.top)/r.height-.5).toFixed(3))};
 const words=['Did','two','thousand','years','of','medicine','beat','a','coin','flip?'];
 return <section id="top" className="hero dark" ref={ref} onMouseMove={onMove}>
  <div className="hero-glow"/><div className="hero-grain"/>
  <div className="hero-layer far"><Sprig leaves={13} className="hs1" flip/><Sprig leaves={11} className="hs2"/></div>
  <div className="hero-layer near"><Sprig leaves={9} className="hs3"/><Sprig leaves={10} className="hs4" flip/><Frond className="hf1"/></div>
  <div className="hero-content">
   <div className="script" data-reveal>Since 60 CE</div>
   <h1 className="hero-title" aria-label="Did two thousand years of medicine beat a coin flip?">{words.map((w,i)=><span key={i} className={'word'+(['thousand','years','coin','flip?'].includes(w)?' strong':'')} style={{'--i':i}} aria-hidden="true">{w}</span>)}</h1>
   <p className="hero-lede" data-reveal>Mediterranean medicine wrote down which plant treats what for two millennia. Antikythera freezes that record at each century, lets science happen, and scores the past against matched controls.</p>
   <div className="hero-actions" data-reveal><button className="cta" onClick={onEnter}>Enter the time machine <Icon name="arrow" size={14}/></button><button className="ghost" onClick={onMethod}>How the test works</button></div>
   <dl className="hero-stats" data-reveal>
    <div><dt><CountUp value={workspace.proposed_claims.length}/></dt><dd>Source-grounded claim proposals</dd></div>
    <div><dt><CountUp value={workspace.sources.filter(s=>s.layer).length}/></dt><dd>Era layers acquired</dd></div>
    <div><dt><CountUp value={new Set(workspace.proposed_evidence.map(e=>e.pmid).filter(Boolean)).size}/></dt><dd>Dated PubMed records</dd></div>
   </dl>
  </div>
  <div className="hero-dial" aria-hidden="true"><div className="dial-ring"><Mechanism year={year}/></div><div className="dial-year"><strong>{year}</strong><span>CE</span></div><div className="dial-caption">Freezing the record…</div></div>
  <button className="scroll-cue" onClick={()=>document.getElementById('question')?.scrollIntoView({behavior:'smooth'})} aria-label="Scroll to the question"><span/></button>
 </section>;
}

export function Question({workspace}){
 return <section id="question" className="band light question">
  <Frond className="watermark wm-right"/>
  <div className="band-inner q-split">
   <div className="tilt-card" data-reveal="left"><div className="tilt-face specimen-face"><div className="spin-slow"><Mechanism year={1800}/></div><Botanical id="colchicum" large/><span className="face-label">Hermodactyl · <i>Colchicum</i> spp.</span></div></div>
   <div className="copy" data-reveal="right">
    <div className="script">Our question</div>
    <h2>Tradition, against <b>chance</b></h2>
    <p>Earlier studies counted how many historical remedies were later “confirmed”. Yarnell &amp; Touwaide found 56 of 67 studied Dioscoridean diuretic genera confirmed — but with no baseline. Famous plants simply get studied more.</p>
    <p>Antikythera asks the conditional question: among species × indication pairs first tested after a freeze year, are traditionally claimed pairs confirmed more often than matched unclaimed controls?</p>
    <ul className="perks"><li>Every claim keeps its exact source span</li><li>Plant identity stays a probability distribution</li><li>Confirmation needs reviewed in-vivo or clinical evidence</li></ul>
   </div>
  </div>
 </section>;
}

const ERA_COPY={
 dioscorides:{n:'01',title:'Dioscorides',when:'c. 60 CE',text:['De Materia Medica — Berendes’ 1902 German translation','Translator commentary separated from the ancient text'],tone:'amber'},
 byzantine:{n:'02',title:'Byzantine',when:'5th–7th c.',text:['Paul of Aegina, Book VII (Adams, 1844–47)','Does this layer add anything Dioscorides did not?'],tone:'green'},
 renaissance:{n:'03',title:'Culpeper',when:'1653 →',text:['The Complete Herbal (Project Gutenberg)','Later edition additions never back-dated to 1653'],tone:'violet'},
 balkan:{n:'04',title:'Balkan folk',when:'1990–2026',text:['Open-access Pieroni et al. medicinal tables (CC BY)','Dated by publication; no community-identifying detail'],tone:'rose'},
};

export function Eras({catalog,workspace,onFreeze}){
 const ref=useRef(null);useScrollVar(ref);
 const counts=workspace.proposed_claims.reduce((m,c)=>{const k=c.era||c.layer;m[k]=(m[k]||0)+1;return m},{});
 return <section id="eras" className="band dark eras" ref={ref}>
  <Frond className="watermark wm-left"/><Frond className="watermark wm-right2"/>
  <div className="band-inner">
   <header className="center-head" data-reveal><div className="script">Four layers</div><h2>The record, <b>layer by layer</b></h2><p>Each era is ablated in turn. Inherited claims are scored apart from claims that are new in their layer.</p></header>
   <ol className="roadmap">
    <div className="road-line"><span/></div>
    {catalog.eras.map((era,i)=>{const c=ERA_COPY[era.id]||{n:String(i+1).padStart(2,'0'),title:era.label,when:era.year,text:[],tone:'green'};return <li key={era.id} className={'road-step '+(i%2?'flip':'')} data-reveal>
     <div className="road-art"><div className={'orb '+c.tone}><div className="orb-ring"/><Sprig leaves={7} className="orb-sprig"/><div className="orb-count"><strong><CountUp value={counts[era.id]||0}/></strong><span>proposals</span></div></div></div>
     <div className={'road-node '+c.tone}>{c.n}</div>
     <div className="road-copy"><span className="road-when">{c.when}</span><h3>{c.title}</h3><ul>{c.text.map(t=><li key={t}>{t}</li>)}</ul><button className="text-link" onClick={()=>onFreeze(era.year)}>Freeze the record at {era.year} CE <Icon name="arrow" size={12}/></button></div>
    </li>})}
   </ol>
  </div>
 </section>;
}

const FREEZE={colchicum:1800,galanthus:1950,galega:1900,papaver:1800,taxus:1960,catharanthus:1950};
const TAG={colchicum:'Byzantine lift?',galanthus:'Balkan nerve remedy',galega:'Road to metformin',papaver:'Sanity check',taxus:'Honest miss',catharanthus:'Right plant, wrong reason'};

export function Legends({catalog,onFreeze}){
 return <section id="legends" className="band light legends">
  <Frond className="watermark wm-center"/>
  <div className="band-inner">
   <header className="center-head" data-reveal><div className="script">Legends</div><h2>Case studies, <b>not evidence</b></h2><p>Freeze the record the year before each discovery. Misses are shown alongside hits, and every lead carries its hazard trail.</p></header>
   <div className="lg-grid">
    {catalog.plants.map((p,i)=>{const m=(p.milestones||[])[0];return <article key={p.id} className="lg-card" data-reveal style={{'--d':`${i*80}ms`}}>
     <div className={'lg-avatar a'+(i%6)}><Botanical id={p.id}/></div>
     <h3>{p.common_name}</h3><span className="lg-role">{TAG[p.id]||p.family}</span>
     <p className="lg-latin"><i>{p.scientific_name}</i> · {p.family}</p>
     <p className="lg-summary">{p.summary}</p>
     {m&&<p className="lg-milestone"><strong>{m.year}</strong> {m.label}</p>}
     <div className={'lg-hazard '+(p.hazard?.severity||'')}><span>Hazard</span>{p.hazard?.text}</div>
     <button className="text-link" onClick={()=>onFreeze(FREEZE[p.id]||1800)}>Freeze at {FREEZE[p.id]||1800} <Icon name="arrow" size={12}/></button>
    </article>})}
   </div>
  </div>
 </section>;
}

export function Footer({onSection}){
 return <footer className="site-footer">
  <Frond className="watermark wm-footer"/>
  <div className="band-inner">
   <div className="footer-logo"><Mechanism small/><span>Antikythera</span></div>
   <div className="footer-grid">
    <div><h4>About Antikythera</h4><p>A 2,000-year backtest of Mediterranean medicine, built for EthnoHack 2026 — Track T1, Traditional Knowledge Mining.</p><p className="fine">Research prioritisation for laboratory testing, not medical advice. Illustrations are schematic and must not be used for plant identification.</p></div>
    <div><h4>Explore</h4>{[['question','The question'],['eras','Four layers'],['legends','Legends'],['observatory','Observatory']].map(([id,l])=><button key={id} onClick={()=>onSection(id)}>{l}</button>)}</div>
    <div><h4>Sources</h4><a href="https://www.gutenberg.org/ebooks/49513" target="_blank" rel="noreferrer">Culpeper, Gutenberg</a><a href="https://archive.org/details/despedaniosdios00pedagoog" target="_blank" rel="noreferrer">Dioscorides, Berendes</a><a href="https://archive.org/details/sevenbooksofpaul03pauluoft" target="_blank" rel="noreferrer">Paul of Aegina, Adams</a><a href="https://europepmc.org/articles/PMC3998745" target="_blank" rel="noreferrer">Pieroni et al. 2014</a></div>
    <div><h4>Project</h4><a href="https://ethnohack2026.devpost.com" target="_blank" rel="noreferrer">EthnoHack 2026</a><a href="https://github.com/rahulgunwanistudy-2005/Antikythera" target="_blank" rel="noreferrer">Source code</a><button onClick={()=>onSection('method')}>The method</button></div>
   </div>
   <div className="footer-base">Antikythera · Open research software · Sources open in a new tab</div>
  </div>
 </footer>;
}
