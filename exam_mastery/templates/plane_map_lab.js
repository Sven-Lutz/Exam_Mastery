/* Plane transformation explorable: a 2x2 matrix morphs the plane continuously from the identity (t = 0) to A (t = 1).
   Predict first (where v lands, sign of det A), then step, scrub or play. Every number comes from EMPlaneMap, the
   parity-tested mirror of exam_mastery/labs/plane_map.py. Colours: one colour per object, used identically in the
   picture and in the equations (column 1 / Me1 amber, column 2 / Me2 violet, v teal, area blue (+) / crimson (-)). */
(()=>{'use strict';
const NS='http://www.w3.org/2000/svg',C={e1:'#c26a05',e2:'#6d3fc0',v:'#0e7490',pos:'#2563eb',neg:'#be123c',zero:'#6b7280',grid:'#9aa9bc',ghost:'#e3e8ef',kernel:'#111827',image:'#0f766e',guess:'#b45309'};
const fmt=x=>{if(!Number.isFinite(x))return '–';const r=Math.abs(x)<5e-10?0:Math.round(x*100)/100;return String(r).replace('-','−');};
const par=x=>x<-5e-10?'('+fmt(x)+')':fmt(x);
const reduce=()=>window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function node(tag,attrs){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs||{}))n.setAttribute(k,v);return n;}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function span(obj,text){const s=el('span','pl-term pl-'+obj,text);s.dataset.obj=obj;s.tabIndex=0;return s;}
for(const root of document.querySelectorAll('.plane-lab')){
 const cfg=JSON.parse(root.querySelector('.pl-parameters').textContent);
 const svg=root.querySelector('.pl-svg'),eq=root.querySelector('.pl-eq'),fb=root.querySelector('.pl-feedback');
 const tIn=root.querySelector('.pl-t'),tOut=root.querySelector('.pl-t-out'),stepBtn=root.querySelector('.pl-step'),playBtn=root.querySelector('.pl-play');
 const marks=root.querySelector('.pl-marks'),status=root.querySelector('.pl-status');
 const inputs=[...root.querySelectorAll('.pl-entry')],vin=[...root.querySelectorAll('.pl-vec')];
 const px=root.querySelector('.pl-guess-x'),py=root.querySelector('.pl-guess-y'),commit=root.querySelector('.pl-commit'),skip=root.querySelector('.pl-skip');
 let A,v,t=0,phase='predict',guess=null,raf=0,last=0,drag=null,hot=null;
 const W=400,O=200;let R=3,k=O/R;
 const X=p=>O+k*p[0],Y=p=>O-k*p[1],inv=(sx,sy)=>[(sx-O)/k,(O-sy)/k];
 function load(p){A=p.matrix.map(r=>r.slice());v=p.vector.slice();inputs.forEach(i=>{i.value=A[+i.dataset.i][+i.dataset.j];});vin.forEach(i=>{i.value=v[+i.dataset.i];});newRound();}
 function model(tt){return EMPlaneMap.compute({matrix:A,vector:v,t:tt});}
 function extent(){const m=model(1),pts=[m.e1,m.e2,m.Av,v,[m.e1[0]+m.e2[0],m.e1[1]+m.e2[1]],[1,1]];
  R=Math.min(6,Math.max(2.5,Math.ceil(Math.max(...pts.flat().map(Math.abs))+0.6)));k=O/R;}
 function newRound(){cancelAnimationFrame(raf);raf=0;phase='predict';guess=null;t=0;extent();
  px.value='';py.value='';root.querySelectorAll('.pl-sign input').forEach(r=>{r.checked=false;});
  root.querySelector('.pl-predict').hidden=false;fb.textContent='';status.textContent='Erst vorhersagen: Die Verformung ist gesperrt, bis Sie sich festgelegt haben.';
  drawMarks();render();}
 function drawMarks(){marks.replaceChildren();for(const s of model(1).singular_times){const m=el('span','pl-mark');m.style.left=(100*s)+'%';m.title='singulär bei t = '+fmt(s);marks.append(m);}}
 function line(p,q,stroke,w,extra){return node('line',Object.assign({x1:X(p),y1:Y(p),x2:X(q),y2:Y(q),stroke,'stroke-width':w},extra||{}));}
 function arrow(tip,col,key){const g=node('g',{class:'pl-obj pl-obj-'+key});
  if(Math.hypot(tip[0],tip[1])<1e-9){g.append(node('circle',{cx:X([0,0]),cy:Y([0,0]),r:6,fill:'none',stroke:col,'stroke-width':2.5}));return g;}
  const ang=Math.atan2(-(tip[1]),tip[0]),hx=X(tip),hy=Y(tip),L=11;
  g.append(line([0,0],tip,col,3.2));
  g.append(node('path',{d:`M${hx},${hy} L${hx-L*Math.cos(ang-0.4)},${hy-L*Math.sin(ang-0.4)} L${hx-L*Math.cos(ang+0.4)},${hy-L*Math.sin(ang+0.4)} Z`,fill:col}));
  return g;}
 function label(tip,text,col){const t=node('text',{x:X(tip)+(tip[0]>=0?9:-9),y:Y(tip)-8,'text-anchor':tip[0]>=0?'start':'end',fill:col,'font-weight':700,'font-size':14});t.textContent=text;return t;}
 function render(){
  const m=model(t),M=m.M,T=p=>EMPlaneMap.apply(M,p),far=4*R,n=Math.floor(R)+1;
  svg.replaceChildren();svg.setAttribute('viewBox','0 0 '+W+' '+W);
  const g=node('g');
  for(let i=-n;i<=n;i++){g.append(line([i,-far],[i,far],C.ghost,1));g.append(line([-far,i],[far,i],C.ghost,1));}
  for(let i=-3*n;i<=3*n;i++){for(const [a,b] of [[[i,-far],[i,far]],[[-far,i],[far,i]]])g.append(line(T(a),T(b),C.grid,i===0?1.7:0.8));}
  const col=m.det>1e-9?C.pos:(m.det<-1e-9?C.neg:C.zero);
  const sq=[[0,0],[1,0],[1,1],[0,1]].map(T);
  const area=node('polygon',{points:sq.map(p=>X(p)+','+Y(p)).join(' '),fill:col,'fill-opacity':0.22,stroke:col,'stroke-width':1.6,class:'pl-obj pl-obj-det'});g.append(area);
  if(m.rank===1){const u=m.kernel[0],w=m.image[0],lu=far/Math.hypot(...u),lw=far/Math.hypot(...w);
   const kl=line([-lu*u[0],-lu*u[1]],[lu*u[0],lu*u[1]],C.kernel,2);kl.setAttribute('stroke-dasharray','7 5');kl.setAttribute('class','pl-obj pl-obj-kernel');g.append(kl);
   const il=line([-lw*w[0],-lw*w[1]],[lw*w[0],lw*w[1]],C.image,2.6);il.setAttribute('class','pl-obj pl-obj-image');g.append(il);}
  g.append(arrow(m.e1,C.e1,'e1'));g.append(arrow(m.e2,C.e2,'e2'));g.append(arrow(m.Mv,C.v,'v'));
  g.append(node('circle',{cx:X(v),cy:Y(v),r:4.5,fill:'white',stroke:C.v,'stroke-width':2}));
  if(guess){const gx=X(guess),gy=Y(guess);g.append(node('path',{d:`M${gx},${gy-8} L${gx+8},${gy} L${gx},${gy+8} L${gx-8},${gy} Z`,fill:'none',stroke:C.guess,'stroke-width':2.2,class:'pl-guess'}));}
  svg.append(g);
  svg.append(label(m.e1,'Me₁',C.e1));svg.append(label(m.e2,'Me₂',C.e2));svg.append(label(m.Mv,'Mv',C.v));
  for(const key of ['e1','e2']){const h=node('circle',{cx:X(m[key]),cy:Y(m[key]),r:13,fill:'transparent',class:'pl-handle','data-key':key});
   h.setAttribute('aria-hidden','true');if(phase==='explore')h.style.cursor='grab';svg.append(h);}
  highlight();
  tIn.value=t;tOut.textContent='t = '+fmt(t);
  const locked=phase==='predict';tIn.disabled=locked;stepBtn.disabled=locked||t>=1;playBtn.disabled=locked||t>=1;
  playBtn.textContent=raf?'Pause':'Abspielen';
  equations(m,col);
  if(t>=1&&phase==='morph')finish(m);
 }
 function equations(m,col){
  const M=m.M;eq.replaceChildren();
  const p1=el('p');p1.append('M(t) = (1 − t)·I + t·A,  ',el('b','',('t = '+fmt(t))));eq.append(p1);
  const tb=el('table','pl-mat');tb.setAttribute('aria-label','Matrix M(t), Spalten farbig');
  for(let i=0;i<2;i++){const tr=el('tr');for(let j=0;j<2;j++){const td=el('td');td.append(span(j===0?'e1':'e2',fmt(M[i][j])));tr.append(td);}tb.append(tr);}
  const p2=el('p');p2.append('M = ',tb,'  ',span('e1','Spalte 1 = Me₁'),' · ',span('e2','Spalte 2 = Me₂'));eq.append(p2);
  const p3=el('p');p3.append(span('v','Mv'),' = '+par(v[0])+'·',span('e1','('+fmt(m.e1[0])+'; '+fmt(m.e1[1])+')'),' + '+par(v[1])+'·',span('e2','('+fmt(m.e2[0])+'; '+fmt(m.e2[1])+')'),' = ',span('v','('+fmt(m.Mv[0])+'; '+fmt(m.Mv[1])+')'));eq.append(p3);
  const p4=el('p');const d=span('det','det M = '+par(M[0][0])+'·'+par(M[1][1])+' − '+par(M[0][1])+'·'+par(M[1][0])+' = '+fmt(m.det));d.style.color=col;
  p4.append(d,' ',el('span','pl-note',m.det>1e-9?'(Bildquadrat, Orientierung wie vorher)':m.det<-1e-9?'(Bildquadrat gespiegelt: Orientierung umgekehrt)':'(Fläche 0: die Ebene ist kollabiert)'));eq.append(p4);
  const p5=el('p');p5.append('Rang M = '+m.rank+'. ');
  if(m.rank===1){p5.append(span('kernel','Kern = span('+m.kernel[0].map(fmt).join('; ')+')'),', ',span('image','Bild = span('+m.image[0].map(fmt).join('; ')+')'),'. Dimensionsformel: 2 = 1 + 1.');}
  else if(m.rank===0)p5.append(span('kernel','Kern = ganze Ebene'),', Bild = {0}. Dimensionsformel: 2 = 2 + 0.');
  else p5.append('Kern = {0}, Bild = ganze Ebene. Dimensionsformel: 2 = 0 + 2.');
  eq.append(p5);
 }
 function finish(m){
  phase='explore';const lines=[];
  if(guess){const dist=Math.hypot(guess[0]-m.Av[0],guess[1]-m.Av[1]);
   lines.push((dist<=0.25?'✓ Treffer: ':'✗ Nicht ganz: ')+'vorhergesagt ('+fmt(guess[0])+'; '+fmt(guess[1])+'), tatsächlich Av = ('+fmt(m.Av[0])+'; '+fmt(m.Av[1])+'). '+
    'Av ist die Kombination der Spalten mit den Koordinaten von v: '+par(v[0])+'·Spalte 1 + '+par(v[1])+'·Spalte 2.');}
  const sign=root.querySelector('.pl-sign input:checked');
  if(sign){const real=m.det_A>1e-9?'+':(m.det_A<-1e-9?'−':'0');
   lines.push((sign.value===real?'✓ ':'✗ ')+'Vorzeichen von det A: vorhergesagt '+sign.value+', tatsächlich '+real+' (det A = '+fmt(m.det_A)+').'+
    (real==='−'?' Jeder stetige Weg von I nach A muss dabei durch det = 0: Die Ebene wird auf dem Weg einmal flach gedrückt.':''));}
  if(!guess&&!sign)lines.push('Ohne Vorhersage angesehen – beim nächsten Beispiel zuerst festlegen, dann prüfen.');
  lines.push('Jetzt frei erkunden: Spitzen von Me₁ und Me₂ ziehen (Spalten der Matrix), Zeitleiste zurückschieben.');
  fb.replaceChildren(...lines.map(s=>el('p','',s)));status.textContent='Vorhersagen sind Übung, keine Bewertung; nichts wird gesendet.';
 }
 function highlight(){svg.querySelectorAll('.is-hot').forEach(x=>x.classList.remove('is-hot'));if(hot)svg.querySelectorAll('.pl-obj-'+hot).forEach(x=>x.classList.add('is-hot'));
  eq.querySelectorAll('.pl-term').forEach(x=>x.classList.toggle('is-hot',x.dataset.obj===hot));}
 function setT(nt){const s=model(1).singular_times.find(x=>Math.abs(x-nt)<0.015);t=Math.max(0,Math.min(1,s!==undefined?s:nt));render();}
 function stop(){cancelAnimationFrame(raf);raf=0;}
 function play(){if(raf){stop();render();return;}if(reduce()){setT(1);return;}last=performance.now();
  const tick=now=>{const nt=Math.min(1,t+(now-last)/2600);last=now;t=nt;if(nt>=1){raf=0;render();return;}render();raf=requestAnimationFrame(tick);};
  raf=requestAnimationFrame(tick);render();}
 commit.addEventListener('click',()=>{const x=parseFloat(px.value.replace(',','.')),y=parseFloat(py.value.replace(',','.'));
  const sign=root.querySelector('.pl-sign input:checked');
  if(!(Number.isFinite(x)&&Number.isFinite(y))||!sign){status.textContent='Bitte beide Koordinaten und ein Vorzeichen angeben (oder „Ohne Vorhersage ansehen“).';return;}
  guess=[x,y];phase='morph';root.querySelector('.pl-predict').hidden=true;status.textContent='Festgelegt. Jetzt Schritt für Schritt verformen oder abspielen.';render();});
 skip.addEventListener('click',()=>{guess=null;root.querySelectorAll('.pl-sign input').forEach(r=>{r.checked=false;});phase='morph';root.querySelector('.pl-predict').hidden=true;render();});
 stepBtn.addEventListener('click',()=>{stop();setT(Math.min(1,Math.floor(t*4+1e-9)/4+0.25));});
 playBtn.addEventListener('click',play);
 tIn.addEventListener('input',()=>{stop();setT(Number(tIn.value));});
 inputs.forEach(i=>i.addEventListener('change',()=>{const x=Number(i.value);if(!Number.isFinite(x)||Math.abs(x)>4){i.value=A[+i.dataset.i][+i.dataset.j];return;}A[+i.dataset.i][+i.dataset.j]=x;newRound();}));
 vin.forEach(i=>i.addEventListener('change',()=>{const x=Number(i.value);if(!Number.isFinite(x)||Math.abs(x)>3){i.value=v[+i.dataset.i];return;}v[+i.dataset.i]=x;newRound();}));
 const presets=root.querySelector('.pl-presets');
 for(const variant of cfg.presets){const b=el('button','secondary',variant.label);b.type='button';b.addEventListener('click',()=>load(variant.parameters));presets.append(b);}
 root.querySelector('.pl-reset').addEventListener('click',()=>load(cfg.presets[0].parameters));
 svg.addEventListener('pointerdown',e=>{const h=e.target.closest&&e.target.closest('.pl-handle');if(!h||phase!=='explore'||t<1)return;drag=h.dataset.key;svg.setPointerCapture(e.pointerId);});
 svg.addEventListener('pointermove',e=>{if(!drag)return;const r=svg.getBoundingClientRect(),p=inv((e.clientX-r.left)*W/r.width,(e.clientY-r.top)*W/r.height).map(x=>Math.max(-4,Math.min(4,Math.round(x*4)/4)));
  const j=drag==='e1'?0:1;A[0][j]=p[0];A[1][j]=p[1];inputs.forEach(i=>{i.value=A[+i.dataset.i][+i.dataset.j];});drawMarks();render();});
 svg.addEventListener('pointerup',()=>{drag=null;});
 eq.addEventListener('pointerover',e=>{const s=e.target.closest('.pl-term');hot=s?s.dataset.obj:null;highlight();});
 eq.addEventListener('focusin',e=>{const s=e.target.closest('.pl-term');hot=s?s.dataset.obj:null;highlight();});
 eq.addEventListener('pointerleave',()=>{hot=null;highlight();});
 load(cfg.presets[0].parameters);
}
})();
