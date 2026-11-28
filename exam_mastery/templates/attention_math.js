/* Pure bounded model; adapted after inspection of local lab_math.js attendOne/
   max-shift softmax. Stronger finite/shape/mask validation; no local pilot changed.
   Paired with labs.models.scaled_attention, tested against independent Decimal. */
(function(root){'use strict';
function attention(p){
  if(!p || typeof p!=='object' || Array.isArray(p) || Object.keys(p).some(k=>!['Q','K','V','mask','temperature','scaled'].includes(k))) throw Error('Unbekannte Modellfelder');
  function matrix(name){
    const m=p[name];
    if(!Array.isArray(m)||m.length<1||m.length>8||!Array.isArray(m[0])||m[0].length<1||m[0].length>8) throw Error('Ungültige Matrix '+name);
    const d=m[0].length;
    if(m.some(r=>!Array.isArray(r)||r.length!==d||r.some(x=>typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>10000))) throw Error('Endliche rechteckige Matrix benötigt');
    return m;
  }
  const Q=matrix('Q'),K=matrix('K'),V=matrix('V');
  if(Q[0].length!==K[0].length||K.length!==V.length) throw Error('Dimensionen von Q/K/V passen nicht');
  const temperature=p.temperature===undefined?1:p.temperature,scaled=p.scaled===undefined?true:p.scaled;
  if(typeof temperature!=='number'||!Number.isFinite(temperature)||temperature<.05||temperature>20||typeof scaled!=='boolean') throw Error('Temperatur/Skalierung ungültig');
  const mask=p.mask===undefined?Q.map(()=>K.map(()=>true)):p.mask;
  if(!Array.isArray(mask)||mask.length!==Q.length||mask.some(r=>!Array.isArray(r)||r.length!==K.length||r.some(x=>typeof x!=='boolean'))) throw Error('Boolesche Maske mit Score-Dimension benötigt');
  if(mask.some(r=>!r.some(Boolean))) throw Error('Vollständig maskierte Zeile: Softmax ist undefiniert');
  const divisor=scaled?Math.sqrt(Q[0].length):1;
  const raw=Q.map(q=>K.map(k=>q.reduce((s,x,i)=>s+x*k[i],0)));
  const scores=raw.map(r=>r.map(x=>x/divisor/temperature));
  const weights=scores.map((r,i)=>{const m=Math.max(...r.filter((_,j)=>mask[i][j]));const e=r.map((x,j)=>mask[i][j]?Math.exp(x-m):0);const z=e.reduce((a,b)=>a+b,0);return e.map(x=>x/z);});
  const contributions=weights.map(r=>r.map((w,j)=>V[j].map(v=>w*v)));
  const output=contributions.map(r=>V[0].map((_,j)=>r.reduce((s,c)=>s+c[j],0)));
  return {Q,K,V,mask,raw,scores,weights,contributions,output,divisor,temperature,scaled};
}
root.EMAttention={compute:attention};
})(globalThis);
