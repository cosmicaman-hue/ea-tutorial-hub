'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require(path.join(process.argv[2],'lib/api.js'));
const source=fs.readFileSync(path.join(__dirname,'../app/static/js/ea-cloud-admin.js'),'utf8');
const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
const uuid=n=>'00000000-0000-4000-8000-'+String(n).padStart(12,'0');
async function fixture(count=2){
 const dom=new JSDOM('<div id="panel"><div class="ea-portal-usage"></div></div>',{runScripts:'outside-only'}),w=dom.window,decisions=[];
 w.currentLoginId='ADMIN';w.currentUserRole='admin';w.eaStudentRequestsAdmin=()=>w.currentUserRole==='admin';
 w.eaStudentRequestsEscape=w.eaStudentRequestsEscapeAttr=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 w.eaStudentRequestsDateTime=value=>value;w.eaStudentRequestsSetStatus=()=>{};w.eaStudentRequestCsrf='fixture-csrf';w.eaPortalActivationEnsureCsrf=async()=>{};w.confirm=()=>true;
 let rows=Array.from({length:count},(_,i)=>({device_id:uuid(i+1),login_id:'EA25D22',device_label:i?'Linux armv81':'Win32',status:'allowed',created_at:'2026-10-17',last_seen_at:'2026-10-19'}));
 rows.push({device_id:uuid(3),login_id:'EA25D22',device_label:'<img src=x onerror=evil()>',status:'pending'});
 rows.push({device_id:uuid(4),login_id:'EA26A01',device_label:'Other student',status:'allowed'});
 let failure=null,ackMismatch=false;
 w.eaStudentRequestsFetch=async(url,options)=>{if(options?.method==='POST'){const body=JSON.parse(options.body);decisions.push(body);if(failure)throw Error(failure);if(ackMismatch)return{success:true};rows=rows.filter(row=>row.device_id!==body.replace_device_id).map(row=>row.device_id===body.device_id?{...row,status:body.action==='approve'?'allowed':'removed'}:row);return{success:true,device_id:body.device_id,status:body.action==='approve'?'allowed':'removed'};}return{success:true,devices:rows,limit:2};};
 w.eval(source);w.eaCloudAdminInit(w.document.querySelector('#panel'));w.document.querySelector('[data-cloud-devices]').click();await tick();
 return{dom,w,decisions,fail(message){failure=message;},mismatch(){ackMismatch=true;},status:()=>w.document.querySelector('[data-cloud-admin-status]').textContent};
}
(async()=>{
 const f=await fixture();try{
  const select=f.w.document.querySelector('[data-replace]');assert.equal(select.options.length,3);assert(select.options[0].disabled);assert.match(select.options[0].textContent,/Choose a browser/);assert(!f.w.document.querySelector('[data-cloud-admin-report] img'));
  f.w.document.querySelector('[data-approve]').click();await tick();assert.equal(f.decisions.length,0);assert.match(f.status(),/Both slots are occupied/);
  select.value=uuid(1);f.w.document.querySelector('[data-approve]').click();await tick();await tick();assert.equal(f.decisions[0].replace_device_id,uuid(1));assert.match(f.status(),/Browser approved/);assert.equal(f.w.document.querySelectorAll('[data-approve]').length,0);
  f.w.currentUserRole='teacher';f.w.eaCloudAdminReset();assert.equal(f.w.document.querySelectorAll('[data-cloud-device]').length,0);assert.equal(f.status(),'');
 }finally{f.dom.window.close();}
 for(const failure of ['network failure','mismatch']){const f=await fixture(1);try{
  const select=f.w.document.querySelector('[data-replace]');assert.equal(select.options[0].textContent,'Use a free slot');assert(!select.options[0].disabled);
  if(failure==='mismatch')f.mismatch();else f.fail(failure);f.w.document.querySelector('[data-approve]').click();await tick();await tick();assert.equal(f.decisions[0].replace_device_id,null);assert.match(f.status(),/could not be confirmed/);assert(!f.w.document.querySelector('[data-approve]').disabled);
 }finally{f.dom.window.close();}}
 console.log('Admin browser checks passed: full/free slots, explicit replacement, student boundary, safe text, success acknowledgement, failures, retry and sign-out.');
})().catch(error=>{console.error(error);process.exitCode=1;});
