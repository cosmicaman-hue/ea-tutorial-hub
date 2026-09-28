(function(){
'use strict';
let account=null,generation=0;
const signal=()=>window.dispatchEvent(new CustomEvent('ea-secure-auth-changed'));
async function refresh(){
  const token=++generation;
  try{const response=await fetch('/api/portal/auth/me',{credentials:'include',cache:'no-store'});const data=await response.json();if(token!==generation)return;account=response.ok&&data.success?data.account:null;}
  catch{if(token===generation)account=null;}
  if(token===generation)signal();
}
async function load(){
  const token=generation;
  const response=await fetch('/api/portal/me/academy',{credentials:'include',cache:'no-store'});
  const data=await response.json();
  if(token!==generation)throw new Error('Account changed; refresh this view.');
  if(!response.ok||!data.success){if(response.status===401){account=null;generation++;signal();}throw new Error(data.error||'Protected academy data is unavailable.');}
  return data.academy;
}
window.EA_ACADEMY={isSignedIn:()=>!!account,load,refresh};
window.addEventListener('ea-portal-session',event=>{if(event.detail===null){generation++;account=null;signal();}else refresh();});
window.addEventListener('pageshow',refresh);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
