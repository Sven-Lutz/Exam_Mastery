/* Mirror of exam_mastery/labs/plane_map.py (parity-tested). Floats in the browser; the Python model is exact
   (rational) and is the reference for every printed number. No DOM access. */
var EMPlaneMap=(function(){'use strict';
const LIMIT=6,EPS=1e-9;
function num(x,name){if(typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>LIMIT)throw new Error('plane map: '+name+' must be a finite number with |x| <= '+LIMIT);return x;}
function parse(p){
 if(!p||!Array.isArray(p.matrix)||p.matrix.length!==2||!p.matrix.every(r=>Array.isArray(r)&&r.length===2))throw new Error('plane map: matrix must be 2x2');
 if(!Array.isArray(p.vector)||p.vector.length!==2)throw new Error('plane map: vector must have 2 components');
 const t=p.t===undefined?1:num(p.t,'t');if(t<0||t>1)throw new Error('plane map: t in [0, 1] required');
 return {A:p.matrix.map((r,i)=>r.map((x,j)=>num(x,'matrix['+i+']['+j+']'))),v:p.vector.map((x,i)=>num(x,'vector['+i+']')),t};
}
const at=(A,t)=>[[1-t+t*A[0][0],t*A[0][1]],[t*A[1][0],1-t+t*A[1][1]]];
const apply=(M,v)=>[M[0][0]*v[0]+M[0][1]*v[1],M[1][0]*v[0]+M[1][1]*v[1]];
const det=M=>M[0][0]*M[1][1]-M[0][1]*M[1][0];
function scaleNice(u){const m=Math.max(Math.abs(u[0]),Math.abs(u[1]));let w=u.map(x=>x/m);
 for(let k=1;k<=12;k++){const c=w.map(x=>x*k);if(c.every(x=>Math.abs(x-Math.round(x))<1e-7)){w=c.map(Math.round);break;}}
 const s=(w[0]!==0?w[0]:w[1])<0?-1:1;return w.map(x=>s*x+0);}
function kernelImage(M){
 const scale=Math.max(1,...M.flat().map(Math.abs));
 if(Math.abs(det(M))>EPS*scale*scale)return {rank:2,kernel:[],image:[[1,0],[0,1]]};
 if(M.flat().every(x=>Math.abs(x)<=EPS))return {rank:0,kernel:[[1,0],[0,1]],image:[]};
 const row=(Math.abs(M[0][0])>EPS||Math.abs(M[0][1])>EPS)?M[0]:M[1];
 const c1=[M[0][0],M[1][0]],col=(Math.abs(c1[0])>EPS||Math.abs(c1[1])>EPS)?c1:[M[0][1],M[1][1]];
 return {rank:1,kernel:[scaleNice([row[1],-row[0]])],image:[scaleNice(col)]};
}
function singularTimes(A){
 const tr=A[0][0]+A[1][1],D=det(A),a=1-tr+D,b=tr-2,c=1;
 if(Math.abs(a)<1e-15){if(Math.abs(b)<1e-15)return [];const r=-c/b;return r>=0&&r<=1?[r]:[];}
 const disc=b*b-4*a*c;if(disc<0)return [];const q=Math.sqrt(disc);
 const rs=[...new Set([(-b-q)/(2*a),(-b+q)/(2*a)])].sort((x,y)=>x-y);
 return rs.filter(r=>r>=-1e-12&&r<=1+1e-12);
}
function compute(p){
 const {A,v,t}=parse(p),M=at(A,t),ki=kernelImage(M),kA=kernelImage(A),d=det(M);
 return {t,M,A,e1:[M[0][0],M[1][0]],e2:[M[0][1],M[1][1]],v,Mv:apply(M,v),Av:apply(A,v),det:d,det_A:det(A),
  orientation:d>EPS?'positiv':(d<-EPS?'negativ':'kollabiert'),rank:ki.rank,kernel:ki.kernel,image:ki.image,
  rank_A:kA.rank,kernel_A:kA.kernel,image_A:kA.image,singular_times:singularTimes(A)};
}
return {compute,at,apply,det,kernelImage,singularTimes,parse,LIMIT};
})();
if(typeof module!=='undefined')module.exports=EMPlaneMap;
