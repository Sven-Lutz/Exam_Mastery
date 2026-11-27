/* Policy-gradient explorable. All numbers come from EMPolicyGradient (parity-tested with the Python model).
   Controls change the parameters of the displayed equations; nothing is decorative. */
(()=>{'use strict';
const NS='http://www.w3.org/2000/svg';
const fmt=(x,d=3)=>Number.isFinite(x)?(Math.abs(x)<1e-12?'0':Number(x.toFixed(d)).toString()):'–';
const vec=(v,d=3)=>'('+v.map(x=>fmt(x,d)).join('; ')+')';
function node(tag,attrs,text){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs||{}))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
for(const root of document.querySelectorAll('.pg-lab')){
 const initial=JSON.parse(root.querySelector('.pg-parameters').textContent);
 let p=structuredClone(initial),predicted=false,history=[],draws=[],learning=[];
 const controls=root.querySelector('.pg-controls'),eq=root.querySelector('.pg-equations'),status=root.querySelector('.pg-status');
 const predictBox=root.querySelector('.pg-predict'),feedback=root.querySelector('.pg-feedback');
 const sampleBtn=root.querySelector('.pg-sample'),updateBtn=root.querySelector('.pg-update'),runBtn=root.querySelector('.pg-run');
 const plot=root.querySelector('.pg-plot');
 const K=p.theta.length;
 function slider(label,min,max,step,get,set,help){
  const wrap=el('label','pg-control');const span=el('span','',label);const out=el('output','',fmt(get(),2));
  const input=el('input');input.type='range';input.min=min;input.max=max;input.step=step;input.value=get();
  input.setAttribute('aria-label',label+(help?' – '+help:''));
  input.addEventListener('input',()=>{set(Number(input.value));out.textContent=fmt(get(),2);changed(true);});
  wrap.append(span,input,out);controls.append(wrap);return input;
 }
 const inputs=[];
 function buildControls(){
  controls.replaceChildren();inputs.length=0;
  for(let k=0;k<K;k++){
   inputs.push(slider('θ'+(k+1)+' (Logit von a'+(k+1)+')',-4,4,0.1,()=>p.theta[k],v=>{p.theta[k]=v;}));
   inputs.push(slider('r(a'+(k+1)+') (mittlere Belohnung)',-5,10,0.5,()=>p.rewards[k],v=>{p.rewards[k]=v;}));
  }
  inputs.push(slider('σ (Rauschen der Belohnung)',0,3,0.1,()=>p.noise_sd||0,v=>{p.noise_sd=v;}));
  const modeWrap=el('label','pg-control');modeWrap.append(el('span','','Baseline'));
  const mode=el('select');for(const [v,t] of [['none','keine (b = 0)'],['constant','konstant b (Regler)'],['expected','b = J(θ)']]){const o=el('option','',t);o.value=v;mode.append(o);}
  mode.value=p.baseline_mode||'none';mode.addEventListener('change',()=>{p.baseline_mode=mode.value;changed(false);});modeWrap.append(mode);controls.append(modeWrap);
  inputs.push(slider('b (konstante Baseline)',-5,10,0.25,()=>p.baseline||0,v=>{p.baseline=v;}));
  const nWrap=el('label','pg-control');nWrap.append(el('span','','N (Episoden je Schätzung)'));
  const n=el('select');for(const v of [1,4,16,64,256]){const o=el('option','',String(v));o.value=v;n.append(o);}n.value=String(p.batch||16);
  n.addEventListener('change',()=>{p.batch=Number(n.value);changed(false);});nWrap.append(n);controls.append(nWrap);
  inputs.push(slider('α (Schrittweite)',0.05,2,0.05,()=>p.step,v=>{p.step=v;}));
 }
 function buildPrediction(){
  predictBox.replaceChildren();
  predictBox.append(el('p','pg-q','Vorhersage vor jeder Stichprobe: Steigt oder sinkt das Logit θₖ beim exakten Gradientenschritt?'));
  for(let k=0;k<K;k++){
   const row=el('fieldset','pg-choice');row.append(el('legend','','Arm a'+(k+1)));
   for(const [v,t] of [['up','θ'+(k+1)+' steigt'],['down','θ'+(k+1)+' sinkt']]){
    const l=el('label');const r=el('input');r.type='radio';r.name=root.id+'-pred-'+k;r.value=v;l.append(r,document.createTextNode(' '+t));row.append(l);
   }
   predictBox.append(row);
  }
  const b=el('button','','Vorhersage prüfen');b.type='button';b.addEventListener('click',checkPrediction);predictBox.append(b);
 }
 function model(){return EMPolicyGradient.compute(p);}
 function checkPrediction(){
  let m;try{m=model();}catch(e){status.textContent=e.message;return;}
  const answers=[];for(let k=0;k<K;k++){const c=predictBox.querySelector('input[name="'+root.id+'-pred-'+k+'"]:checked');answers.push(c?c.value:null);}
  if(answers.includes(null)){feedback.textContent='Bitte für jeden Arm eine Richtung wählen.';return;}
  const lines=answers.map((a,k)=>{const g=m.grad[k],truth=Math.abs(g)<1e-12?'flat':(g>0?'up':'down');
   const ok=truth==='flat'||truth===a;
   return 'a'+(k+1)+': ∂J/∂θ'+(k+1)+' = π'+(k+1)+'·(r'+(k+1)+' − J) = '+fmt(m.pi[k])+'·('+fmt(p.rewards[k],2)+' − '+fmt(m.J)+') = '+fmt(g)+(ok?' ✓':' ✗ – das Vorzeichen folgt aus r(a) − J, nicht aus r(a) allein');});
  feedback.replaceChildren(...lines.map(t=>el('div','',t)));
  predicted=true;sampleBtn.disabled=false;updateBtn.disabled=!history.length;runBtn.disabled=false;
  status.textContent='Vorhersage geprüft. Jetzt Episoden ziehen und die Schätzung ĝ mit ∇J vergleichen.';
 }
 function changed(keepPrediction){
  draws=[];history=[];
  {predicted=false;sampleBtn.disabled=true;updateBtn.disabled=true;runBtn.disabled=true;feedback.textContent='';
   predictBox.querySelectorAll('input[type=radio]').forEach(r=>{r.checked=false;});}
  render();
 }
 function sample(){
  p.seed=((p.seed||1)+1)>>>0;let m;try{m=model();}catch(e){status.textContent=e.message;return null;}
  history=[m];draws.push({none:m.estimate_none[0],base:m.estimate[0]});if(draws.length>300)draws.shift();
  updateBtn.disabled=false;render();return m;
 }
 function update(){
  const m=history[history.length-1];if(!m)return;
  learning.push(m.J);p.theta=m.theta_new.map(x=>Math.max(-8,Math.min(8,x)));
  learning.push(EMPolicyGradient.compute(p).J);if(learning.length>400)learning=learning.slice(-400);
  draws=[];history=[];buildControls();updateBtn.disabled=true;render();
  status.textContent='Update θ ← θ + α·ĝ angewandt. Neue Stichprobe ziehen (die Vorhersage gilt weiter, da Sie die Regler nicht verändert haben).';
 }
 function run(){for(let i=0;i<20;i++){if(!sample())return;update();}status.textContent='20 Updates mit je N = '+p.batch+' Episoden ausgeführt; die Kurve zeigt J(θ) nach jedem Schritt.';}
 function axisText(svg,x,y,t,anchor,cls){svg.append(node('text',{x,y,'text-anchor':anchor||'start','class':cls||'pg-ax'},t));}
 function render(){
  let m;try{m=model();status.classList.remove('pg-error');}catch(e){status.textContent=e.message;status.classList.add('pg-error');return;}
  const last=history[history.length-1];
  const b=m.baseline;
  eq.replaceChildren(
   el('div','','π = softmax(θ) = '+vec(m.pi)),
   el('div','','J(θ) = Σₐ π(a)·r(a) = '+fmt(m.J,4)),
   el('div','','∇J = π ⊙ (r − J) = '+vec(m.grad)+'   (Komponentensumme '+fmt(m.grad.reduce((s,x)=>s+x,0),6)+')'),
   el('div','','ĝ = (1/N) Σᵢ (Rᵢ − b)(e_{Aᵢ} − π),  b = '+fmt(b,3)+(last?'  →  ĝ = '+vec(last.estimate):'  (noch keine Stichprobe)')),
   el('div','','Var[ĝ] (Spur, exakt) = ['+'Σₐ π(a)((r(a) − b)² + σ²)‖e_a − π‖² − ‖∇J‖²]/N = '+fmt(m.variance_baseline,4)+'   ohne Baseline: '+fmt(m.variance_none,4)+'   b*: '+fmt(m.variance_optimal,4)+' (b* = '+fmt(m.b_opt,3)+')'),
   el('div','','Update: θ ← θ + α·ĝ'+(last?' = '+vec(last.theta_new)+'  ⇒  J = '+fmt(last.J_new,4):''))
  );
  plot.replaceChildren();
  const W=680,H=250,svg=node('svg',{viewBox:'0 0 '+W+' '+H,role:'img','aria-label':'Exakter Gradient, Schätzungen und Lernkurve'});
  // Panel 1: exact gradient vs latest estimate per arm
  axisText(svg,10,18,'∇J (Strich) · ĝ (Balken)','start','pg-title');
  const gmax=Math.max(1e-9,...m.grad.map(Math.abs),...(last?last.estimate.map(Math.abs):[]));
  for(let k=0;k<K;k++){
   const y=45+k*45,x0=140,s=70/gmax;
   axisText(svg,10,y+5,'a'+(k+1)+'  π='+fmt(m.pi[k],2));
   svg.append(node('line',{x1:x0,y1:y-16,x2:x0,y2:y+16,stroke:'#9aa6b2'}));
   if(last){const g=last.estimate[k];svg.append(node('rect',{x:g>=0?x0:x0+g*s,y:y-8,width:Math.abs(g*s),height:16,fill:g>=0?'#4e7d6b':'#8a5a44',opacity:.8}));}
   svg.append(node('line',{x1:x0+m.grad[k]*s,y1:y-14,x2:x0+m.grad[k]*s,y2:y+14,stroke:'#1d2a3a','stroke-width':3}));
  }
  // Panel 2: spread of the first component across draws, without and with baseline
  axisText(svg,260,18,'Streuung von ĝ₁ über Stichproben','start','pg-title');
  const vals=draws.flatMap(d=>[d.none,d.base]).concat([m.grad[0]]);const lo=Math.min(...vals),hi=Math.max(...vals),span=Math.max(1e-9,hi-lo);
  const X=v=>260+170*(v-lo)/span;
  [['ohne b','none',70],['mit b','base',130]].forEach(([t,key,y])=>{
   axisText(svg,254,y+4,t,'end');
   svg.append(node('line',{x1:258,y1:y,x2:432,y2:y,stroke:'#d5dce4'}));
   draws.forEach(d=>svg.append(node('circle',{cx:X(d[key]),cy:y,r:3,fill:key==='none'?'#8a5a44':'#4e7d6b','fill-opacity':.35})));
   if(draws.length>1){const xs=draws.map(d=>d[key]),mu=xs.reduce((a,c)=>a+c,0)/xs.length,v=xs.reduce((a,c)=>a+(c-mu)**2,0)/(xs.length-1);
    axisText(svg,432,y+22,'emp. Var '+fmt(v,4)+' · exakt '+fmt(key==='none'?m.variance_first_none:m.variance_first_baseline,4),'end');}
  });
  svg.append(node('line',{x1:X(m.grad[0]),y1:45,x2:X(m.grad[0]),y2:140,stroke:'#1d2a3a','stroke-width':2,'stroke-dasharray':'4 3'}));
  axisText(svg,X(m.grad[0]),158,'∂J/∂θ₁ = '+fmt(m.grad[0]),'middle');
  // Panel 3: learning curve J
  axisText(svg,460,18,'J(θ) nach Updates','start','pg-title');
  const rmin=Math.min(...p.rewards),rmax=Math.max(...p.rewards),rs=Math.max(1e-9,rmax-rmin);
  svg.append(node('rect',{x:460,y:30,width:210,height:130,fill:'none',stroke:'#d5dce4'}));
  axisText(svg,456,36,fmt(rmax,1),'end');axisText(svg,456,160,fmt(rmin,1),'end');
  if(learning.length>1){const pts=learning.map((j,i)=>(460+210*i/(learning.length-1)).toFixed(1)+','+(160-130*(j-rmin)/rs).toFixed(1)).join(' ');
   svg.append(node('polyline',{points:pts,fill:'none',stroke:'#2f5d8a','stroke-width':2}));}
  else axisText(svg,565,100,'noch keine Updates','middle');
  axisText(svg,10,200,'Exakt: Var[ĝ] ohne b = '+fmt(m.variance_none,4)+' · mit gewählter b = '+fmt(m.variance_baseline,4)+' · b = J: '+fmt(m.variance_expected,4)+' · b* = '+fmt(m.b_opt,3)+': '+fmt(m.variance_optimal,4));
  axisText(svg,10,222,'Mittelpunkt beider Punktwolken: ∂J/∂θ₁ (gestrichelt) – die Baseline verschiebt nicht den Erwartungswert, nur die Streuung.');
  plot.append(svg);
  root.dataset.model=JSON.stringify({pi:m.pi,J:m.J,grad:m.grad,variance_none:m.variance_none,variance_baseline:m.variance_baseline,b_opt:m.b_opt,estimate:last?last.estimate:null});
 }
 sampleBtn.addEventListener('click',()=>{if(predicted)sample();});
 updateBtn.addEventListener('click',update);runBtn.addEventListener('click',()=>{if(predicted)run();});
 root.querySelector('.pg-reset').addEventListener('click',()=>{p=structuredClone(initial);learning=[];buildControls();changed(false);});
 buildControls();buildPrediction();changed(false);
}
})();
