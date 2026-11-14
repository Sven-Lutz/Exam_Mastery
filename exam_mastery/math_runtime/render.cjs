'use strict';
const path=require('path');
const base=process.env.EM_MATH_NODE_MODULES;
if(!base) throw Error('EM_MATH_NODE_MODULES missing');
const req=n=>require(path.join(base,'mathjax-full/js',n));
const {mathjax}=req('mathjax.js');
const {TeX}=req('input/tex.js');
const {SVG}=req('output/svg.js');
const {liteAdaptor}=req('adaptors/liteAdaptor.js');
const {RegisterHTMLHandler}=req('handlers/html.js');
req('input/tex/ams/AmsConfiguration.js');
req('input/tex/mhchem/MhchemConfiguration.js');
const adaptor=liteAdaptor();RegisterHTMLHandler(adaptor);
let input='';process.stdin.on('data',x=>input+=x);process.stdin.on('end',()=>{
 try {
  const item=JSON.parse(input);
  const doc=mathjax.document('',{InputJax:new TeX({packages:['base','ams','mhchem'],maxBuffer:12000}),OutputJax:new SVG({fontCache:'none'})});
  const node=doc.convert(item.tex,{display:!!item.display,em:16,ex:8,containerWidth:720});
  const svg=adaptor.outerHTML(adaptor.tags(node,'svg')[0]);
  if(svg.includes('data-mjx-error')||svg.includes('data-mml-node="merror"'))throw Error((svg.match(/data-mjx-error="([^"]+)"/)||[])[1]||'TeX syntax/render error');
  process.stdout.write(JSON.stringify({svg}));
 } catch(e){process.stderr.write(String(e));process.exitCode=1;}
});
