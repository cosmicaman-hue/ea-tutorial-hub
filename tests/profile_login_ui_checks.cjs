'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require(path.join(process.argv[2],'lib/api.js'));
const source=fs.readFileSync(path.join(__dirname,'../public_site/profile/app.js'),'utf8');
const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
async function fixture({status=401,error='Invalid login or account unavailable.',code,staff=false}={}){
 const dom=new JSDOM('<div id="myProfileRoot"></div>',{url:'https://portal.example/#home',runScripts:'outside-only'}),w=dom.window,calls=[];
 Object.defineProperty(w.navigator,'userAgent',{value:'Mozilla/5.0 (Linux; Android 13) Chrome/120.0 Mobile Safari/537.36'});
 w.Headers=Headers;w.fetch=async(url,options)=>{calls.push({url,body:JSON.parse(options.body)});return{status,ok:status<400,json:async()=>({success:false,error,error_code:code})};};
 w.eval(source);if(staff)w.document.querySelector('[data-auth-mode="staff-login"]').click();
 const form=w.document.querySelector('[data-login]');form.elements.login_id.value='EA26A01';form.elements.password.value='valid123';
 const submit=async()=>{form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await tick();await tick();return calls.at(-1);};
 return{dom,w,form,calls,submit,mode(value){const select=form.querySelector('[data-device-name-mode]');select.value=value;select.dispatchEvent(new w.Event('change'));}};
}
(async()=>{
 for(const staff of [false,true]){
  const f=await fixture({staff});try{
   assert.equal(f.form.querySelector('[name="device_label"]').required,false);
   assert.equal(f.form.querySelector('[name="device_label"]').disabled,true);
   assert.equal((await f.submit()).body.device_label,'Android · Chrome');
   assert.match(f.calls.at(-1).url,staff?/staff\/login$/:/auth\/login$/);
   assert(!f.form.querySelector('button[type="submit"]').disabled);
   f.mode('none');assert.equal((await f.submit()).body.device_label,'Unnamed browser');
   f.mode('custom');assert(!f.form.querySelector('[data-device-name-custom]').hidden);
   f.form.elements.device_label.value='  My phone  ';assert.equal((await f.submit()).body.device_label,'My phone');
   f.form.elements.device_label.value=' ';assert.equal((await f.submit()).body.device_label,'Android · Chrome');
   f.mode('auto');assert(f.form.elements.device_label.disabled);assert.equal((await f.submit()).body.device_label,'Android · Chrome');
   assert.match(f.w.document.querySelector('[data-profile-alert]').textContent,/wait 15 minutes/);
  }finally{f.dom.window.close();}
 }
 for(const row of [{status:403,code:'device_admin_approval_required',error:'Two devices are already registered.',expected:/waiting for LAN Admin approval/},{status:429,error:'rate limited',expected:/Too many sign-in attempts/},{status:403,error:'Account access is blocked. Contact Admin.',expected:/Account access is blocked/},{status:503,error:'database_daily_quota_exceeded',expected:/Daily cloud database allowance reached/},{status:503,error:'unavailable',expected:/hosted separately/}]){
  const f=await fixture(row);try{await f.submit();assert.match(f.w.document.body.textContent,row.expected);}finally{f.dom.window.close();}
 }
 console.log('Profile sign-in checks passed: student/staff, automatic/unnamed/custom/blank names, device approval, failed sign-in, throttling, block and quota messages.');
})().catch(error=>{console.error(error);process.exitCode=1;});
