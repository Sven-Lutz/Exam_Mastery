/* Existing semantic SVG is updated, never replaced with authored HTML. */
(()=>{'use strict';
for(const root of document.querySelectorAll('.attention-lab')){
 const initial=JSON.parse(root.querySelector('.attention-parameters').textContent);
 let p=structuredClone(initial); const inputs=[];
 const editor=root.querySelector('.attention-editors'), output=root.querySelector('.attention-readout');
 const svg=root.querySelector('svg'), status=root.querySelector('.attention-status');
 const fmt=x=>Number(x.toPrecision(6)).toString();
 function render(){
   try{
    const m=EMAttention.compute(p);svg.style.display='';svg.removeAttribute('aria-hidden');status.textContent='Berechnung gültig. Beobachtung ist kein Nachweis von Lernkompetenz.';
    const set=(id,value)=>{const n=svg.querySelector('[data-field="'+id+'"]');if(n)n.textContent=value;};
    for(let j=0;j<m.K.length;j++){
      set('raw-'+j,fmt(m.raw[0][j]));set('score-'+j,fmt(m.scores[0][j]));set('weight-'+j,fmt(m.weights[0][j]));
      set('value-'+j,m.V[j].map(fmt).join(', '));set('contribution-'+j,m.contributions[0][j].map(fmt).join(', '));
      svg.querySelector('[data-bar="'+j+'"]').setAttribute('width',125*m.weights[0][j]);
    }
    set('output',m.output[0].map(fmt).join(', '));
    svg.setAttribute('aria-label','Aktuelle erste Gewichtszeile '+m.weights[0].map(fmt).join(', ')+'. Erste Ausgabe '+m.output[0].map(fmt).join(', '));
    output.textContent=m.output.map((r,i)=>'Ausgabe o'+(i+1)+' = ('+r.map(fmt).join('; ')+')').join(' · ');
    const alternative=root.querySelector('.attention-alternative');alternative.replaceChildren();
    for(let j=0;j<m.K.length;j++){
     const list=document.createElement('dl');
     for(const [label,value] of [['Key',j+1],['Rohscore',fmt(m.raw[0][j])],['Logit',fmt(m.scores[0][j])],['Gewicht',fmt(m.weights[0][j])],['Value',m.V[j].map(fmt).join('; ')],['Beitrag',m.contributions[0][j].map(fmt).join('; ')]]){
      const term=document.createElement('dt'),detail=document.createElement('dd');term.textContent=label;detail.textContent=value;list.append(term,detail);
     }alternative.append(list);
    }
    root.dataset.model=JSON.stringify(m);
   }catch(e){svg.style.display='none';svg.setAttribute('aria-hidden','true');status.textContent=e.message;output.textContent='Keine Ausgabe: Eingaben korrigieren.';root.querySelector('.attention-alternative').replaceChildren();root.dataset.model='';}
 }
 for(const name of ['Q','K','V']){
  const field=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent=name+' · Zeilen sind Vektoren';field.append(legend);
  p[name].forEach((row,i)=>row.forEach((value,j)=>{
   const label=document.createElement('label');label.textContent=name+'['+(i+1)+','+(j+1)+']';
   const input=document.createElement('input');input.type='number';input.step='.1';input.min='-10000';input.max='10000';input.value=value;
   input.setAttribute('aria-label',label.textContent);input.dataset.matrix=name;input.dataset.row=i;input.dataset.column=j;
   input.addEventListener('input',()=>{p[name][i][j]=input.value.trim()===''?NaN:Number(input.value);render();});
   inputs.push(input);label.append(input);field.append(label);
  }));editor.append(field);
 }
 const mask=root.querySelector('.attention-masks');
 p.Q.forEach((_,i)=>p.K.forEach((_,j)=>{
  const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=!p.mask||p.mask[i][j];
  label.append(input,document.createTextNode('Query '+(i+1)+' darf Key '+(j+1)+' sehen'));
  input.addEventListener('change',()=>{if(!p.mask)p.mask=p.Q.map(()=>p.K.map(()=>true));p.mask[i][j]=input.checked;render();});mask.append(label);
 }));
 const temp=root.querySelector('.attention-temperature'),scale=root.querySelector('.attention-scale');
 temp.value=p.temperature||1;scale.checked=p.scaled!==false;
 temp.addEventListener('input',()=>{p.temperature=Number(temp.value);render();});scale.addEventListener('change',()=>{p.scaled=scale.checked;render();});
 root.querySelector('.attention-reset').addEventListener('click',()=>{
  p=structuredClone(initial);inputs.forEach(n=>n.value=p[n.dataset.matrix][Number(n.dataset.row)][Number(n.dataset.column)]);
  mask.querySelectorAll('input').forEach((n,index)=>n.checked=!p.mask||p.mask[Math.floor(index/p.K.length)][index%p.K.length]);
  temp.value=p.temperature||1;scale.checked=p.scaled!==false;render();
 });
 root.querySelector('.attention-export').addEventListener('click',()=>{
  try{EMAttention.compute(p);}catch(e){svg.style.display='none';svg.setAttribute('aria-hidden','true');status.textContent=e.message;return;}
  const link=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify({schema:'em-attention-experiment-v1',parameters:p},null,2)],{type:'application/json'}));
  link.href=url;link.download='attention-experiment.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),0);
 });
 render();
}
})();
