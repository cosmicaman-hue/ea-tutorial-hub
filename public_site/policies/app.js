/* Public, read-only register. All content comes from the versioned catalogue. */
(() => {
  'use strict';
  const dateInput=document.getElementById('policyDate'),scoreInput=document.getElementById('policyScore');
  const host=document.getElementById('policyNotices'),status=document.getElementById('policyStatus');
  let rows=[];
  const today=()=>new Date(Date.now()+330*60000).toISOString().slice(0,10);
  const dateText=value=>value?new Date(value+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}):'Previous rule (before 20 October 2026)';
  function node(tag,text,className){const el=document.createElement(tag);if(text!=null)el.textContent=text;if(className)el.className=className;return el;}
  function render(){
    const selected=dateInput.value;if(!/^\d{4}-\d{2}-\d{2}$/.test(selected))return;
    const active=[...rows].reverse().find(row=>row.topic==='vote_power'&&(!row.effective_date||row.effective_date<=selected));
    const score=Number(scoreInput.value),preview=document.getElementById('policyPreview');
    if(!active)preview.textContent='No Vote Power policy is available for this date.';
    else if(!scoreInput.value.trim()||!Number.isFinite(score))preview.textContent='Enter a finite monthly score to preview Vote Power.';
    else{
      let power=Math.max(active.minimum,Math.floor(score/active.step)+1);if(active.maximum!=null)power=Math.min(active.maximum,power);
      preview.textContent='Vote Power: '+power+' | '+active.step+'-point steps | '+(active.maximum==null?'No maximum ceiling':'Maximum '+active.maximum);
    }
    host.replaceChildren();
    [...rows].reverse().forEach(row=>{
      const article=node('article',null,'notice'+(!row.notice?' baseline':''));
      const meta=node('div',null,'meta');meta.append(node('span',row.notice_number||'PRIOR POLICY RECORD'),node('span',row.issued_date?'Issued: '+dateText(row.issued_date):'Historical reference'));
      const newer=rows.find(next=>next.topic===row.topic&&next.effective_date&&(!row.effective_date||next.effective_date>row.effective_date)&&next.effective_date<=selected);
      const state=row.effective_date&&row.effective_date>selected?'SCHEDULED':newer?'SUPERSEDED':'IN EFFECT';
      article.append(meta,node('h2',row.title),node('span',state,'badge'),node('p','Effective: '+dateText(row.effective_date)),node('p',row.summary));
      if(row.clauses){const list=node('ol');row.clauses.forEach(text=>list.append(node('li',text)));article.append(list);}
      if(row.notice&&/^[a-z0-9-]+\.pdf$/.test(row.notice)){
        const link=node('a','Open / download PDF notice');link.href='./'+row.notice;link.target='_blank';link.rel='noopener';article.append(link);
        article.append(node('p','Academy Administration','signature'));
      }
      host.append(article);
    });
  }
  dateInput.value=today();dateInput.addEventListener('change',render);scoreInput.addEventListener('input',render);
  fetch('./catalog.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('Policy register unavailable.');return response.json();}).then(data=>{
    if(data.schema_version!==1||!Array.isArray(data.policies))throw new Error('Unrecognized policy register.');
    rows=data.policies;status.textContent='';render();
  }).catch(()=>{status.textContent='The policy register could not be loaded. Please reload this page when connected. No policy preview is available.';});
})();
