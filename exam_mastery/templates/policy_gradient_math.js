/* Mirror of exam_mastery/labs/policy_gradient.py (tested for parity). No DOM access. */
var EMPolicyGradient=(function(){'use strict';
const MODES=['none','constant','expected'];
function real(v,name,lo,hi){if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)throw new Error('policy_gradient: '+name+' must be a finite number in ['+lo+', '+hi+']');return v;}
function check(p){
 if(!p||!Array.isArray(p.theta)||!Array.isArray(p.rewards)||p.theta.length<2||p.theta.length>4||p.theta.length!==p.rewards.length)
  throw new Error('policy_gradient: 2..4 arms with one logit and one mean reward each');
 const o={theta:p.theta.map(x=>real(x,'theta',-8,8)),rewards:p.rewards.map(x=>real(x,'reward',-20,20)),
  noise_sd:real(p.noise_sd===undefined?0:p.noise_sd,'noise_sd',0,10),baseline_mode:p.baseline_mode===undefined?'none':p.baseline_mode,
  baseline:real(p.baseline===undefined?0:p.baseline,'baseline',-20,20),step:real(p.step===undefined?0.5:p.step,'step',0,10)};
 if(!MODES.includes(o.baseline_mode))throw new Error('policy_gradient: baseline_mode must be none, constant or expected');
 const batch=p.batch===undefined?16:p.batch,seed=p.seed===undefined?1:p.seed;
 if(!Number.isInteger(batch)||batch<1||batch>2000)throw new Error('policy_gradient: batch must be an integer in [1, 2000]');
 if(!Number.isInteger(seed)||seed<0||seed>=4294967296)throw new Error('policy_gradient: seed must be an unsigned 32-bit integer');
 o.batch=batch;o.seed=seed;return o;
}
function fsum(xs){let s=0,c=0;for(const x of xs){const y=x-c,t=s+y;c=(t-s)-y;s=t;}return s;}
function softmax(theta){const top=Math.max(...theta),e=theta.map(x=>Math.exp(x-top)),s=fsum(e);return e.map(x=>x/s);}
function score(pi,a){return pi.map((p,j)=>(j===a?1:0)-p);}
function mulberry32(seed){let a=seed>>>0;return function(){a=(a+0x6D2B79F5)>>>0;let t=Math.imul(a^(a>>>15),a|1)>>>0;t=(((t+(Math.imul(t^(t>>>7),t|61)>>>0))>>>0)^t)>>>0;return ((t^(t>>>14))>>>0)/4294967296;};}
function exact(theta,rewards,sd){
 const pi=softmax(theta),J=fsum(pi.map((p,k)=>p*rewards[k])),grad=pi.map((p,k)=>p*(rewards[k]-J));
 const w=pi.map((_,a)=>fsum(score(pi,a).map(x=>x*x))),norm2=fsum(grad.map(g=>g*g));
 const variance=b=>fsum(pi.map((p,k)=>p*((rewards[k]-b)**2+sd*sd)*w[k]))-norm2;
 const mass=fsum(pi.map((p,k)=>p*w[k])),best=fsum(pi.map((p,k)=>p*w[k]*rewards[k]))/mass;
 return {pi,J,grad,weights:w,variance,b_opt:best};
}
function estimator(pi,actions,returns,b){const g=pi.map(()=>0),n=actions.length;
 actions.forEach((a,i)=>score(pi,a).forEach((s,j)=>{g[j]+=(returns[i]-b)*s/n;}));return g;}
function compute(params){
 const p=check(params),ex=exact(p.theta,p.rewards,p.noise_sd),pi=ex.pi,k=pi.length;
 const b={none:0,constant:p.baseline,expected:ex.J}[p.baseline_mode];
 const draw=mulberry32(p.seed),actions=[],returns=[],counts=pi.map(()=>0);
 for(let i=0;i<p.batch;i++){
  const u=draw();let a=k-1,acc=0;for(let j=0;j<k;j++){acc+=pi[j];if(u<acc){a=j;break;}}
  const u1=draw(),u2=draw(),eps=Math.sqrt(-2*Math.log(1-u1))*Math.cos(2*Math.PI*u2);
  actions.push(a);returns.push(p.rewards[a]+p.noise_sd*eps);counts[a]++;
 }
 const first=base=>fsum(pi.map((q,a)=>q*((p.rewards[a]-base)**2+p.noise_sd*p.noise_sd)*score(pi,a)[0]**2))-ex.grad[0]**2;
 const estimate=estimator(pi,actions,returns,b),updated=p.theta.map((t,j)=>t+p.step*estimate[j]),pn=softmax(updated);
 return {model:'softmax_policy_gradient',parameters:p,pi,J:ex.J,grad:ex.grad,baseline:b,b_opt:ex.b_opt,
  variance_none:ex.variance(0)/p.batch,variance_baseline:ex.variance(b)/p.batch,variance_expected:ex.variance(ex.J)/p.batch,
  variance_optimal:ex.variance(ex.b_opt)/p.batch,variance_first_none:first(0)/p.batch,variance_first_baseline:first(b)/p.batch,actions,returns,counts,estimate,
  estimate_none:estimator(pi,actions,returns,0),theta_new:updated,pi_new:pn,J_new:fsum(pn.map((q,j)=>q*p.rewards[j])),
  theta_exact_step:p.theta.map((t,j)=>t+p.step*ex.grad[j]),variance_curve:ex.variance};
}
return {compute,softmax,exact,mulberry32,check};
})();
if(typeof module!=='undefined')module.exports=EMPolicyGradient;
