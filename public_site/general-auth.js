(function(){
'use strict';
const KEY='ea_public_auth';
let account=null,csrf='',generation=0,refreshing=null,lastAccount;
function changed(){
  const label=account?.roll || null;if(label===lastAccount)return;lastAccount=label;
  try{if(account)localStorage.setItem(KEY,JSON.stringify({roll:account.roll,ts:Date.now()}));else localStorage.removeItem(KEY);}catch{}
  window.dispatchEvent(new CustomEvent('ea-auth-changed'));
}
async function raw(path,options={}){
  const response=await fetch('/api/portal/general/auth/'+path,{...options,credentials:'include',cache:'no-store'});
  const data=await response.json();
  if(!response.ok||!data.success){const error=new Error(data.error||'General login unavailable.');error.status=response.status;error.code=data.error_code;throw error;}
  return data;
}
async function refresh(){
  if(refreshing)return refreshing;
  const token=generation;
  refreshing=(async()=>{try{const data=await raw('me');if(token===generation){account=data.account;changed();}}catch{if(token===generation){account=null;csrf='';changed();}}finally{refreshing=null;}})();
  return refreshing;
}
async function login(roll,password){
  const token=++generation;
  const data=await raw('login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({roll,password,device_label:navigator.userAgent.slice(0,120)})});
  if(token!==generation)throw new Error('Account changed. Sign in again.');
  account=data.account;csrf=data.csrf_token;changed();return account;
}
async function logout(){
  if(!csrf)csrf=(await raw('csrf')).csrf_token;
  await raw('logout',{method:'POST',headers:{'X-Portal-CSRF':csrf}});
  generation++;account=null;csrf='';changed();
}
async function request(path,options={}){
  const token=generation;
  if(!account){await refresh();if(!account)throw new Error('Please sign in with your general academy login.');}
  if(options.method&&options.method!=='GET'&&!csrf)csrf=(await raw('csrf')).csrf_token;
  if(token!==generation)throw new Error('Account changed. Refresh this view.');
  const response=await fetch('/api/portal'+path,{...options,credentials:'include',cache:'no-store',headers:{...options.headers,...(options.method&&options.method!=='GET'?{'X-Portal-CSRF':csrf}:{})}});
  const data=await response.json();
  if(token!==generation)throw new Error('Account changed. Refresh this view.');
  if(!response.ok||!data.success){if(response.status===401){generation++;account=null;csrf='';changed();}throw new Error(data.error||'Request could not be confirmed.');}
  return data;
}
window.EA_GENERAL={account:()=>account,login,logout,refresh,request};
// Local metadata never establishes an authenticated session.
changed();
window.addEventListener('pageshow',refresh);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
