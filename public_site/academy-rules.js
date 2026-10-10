(function(){
'use strict';
const host=document.getElementById('rulesRoot');if(!host)return;
let rules=[],selected=null,mode='comments',topic=null,generation=0,contribute=false;
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const api=(path,options)=>window.EA_GENERAL.request('/rules'+path,options);
const date=value=>new Date(value).toLocaleString();
const notice=message=>{const el=host.querySelector('[data-notice]');if(el)el.textContent=message;};
function gate(){host.innerHTML='<div class="login-gate"><h2>Academy Rules</h2><p>Sign in with your general academy login to read the published rules and join discussions.</p><button type="button" data-login>Login to view Rules</button></div>';host.querySelector('button').onclick=()=>openLoginModal();}
async function open(){
  const token=++generation;
  if(!window.EA_GENERAL.account()){gate();return;}
  host.innerHTML='<p role="status">Loading published Rules…</p>';
  try{const data=await api('');if(token!==generation)return;rules=data.rules||[];contribute=data.can_contribute;selected=null;
    host.innerHTML='<header><h2>Academy Rules</h2><button type="button" data-refresh>Refresh</button></header><p class="rule-meta">Published from LAN '+esc(date(data.published_at))+'. Comments and discussions do not change official rules.</p><div class="rule-toolbar"><label>Section<select data-section><option value="">All sections</option></select></label><label>Find a rule<input data-search type="search" maxlength="200"></label></div><p data-notice class="rule-notice" role="status"></p><div class="rule-list" data-list></div>';
    const sections=new Map(rules.map(row=>[row.section_key,row.section_title]));
    host.querySelector('[data-section]').innerHTML+=[...sections].map(([key,title])=>'<option value="'+esc(key)+'">'+esc(key+'. '+title)+'</option>').join('');
    host.querySelector('[data-refresh]').onclick=open;host.querySelector('[data-section]').onchange=renderList;host.querySelector('[data-search]').oninput=renderList;renderList();
  }catch(error){if(token===generation){host.innerHTML='<p role="status">'+esc(error.message)+'</p><button type="button">Retry</button>';host.querySelector('button').onclick=open;}}
}
function renderList(){
  generation++;selected=null;topic=null;
  const section=host.querySelector('[data-section]').value,query=host.querySelector('[data-search]').value.toLowerCase();
  const list=rules.filter(row=>(!section||row.section_key===section)&&(!query||[row.label,row.text,row.section_title,row.block_title].join(' ').toLowerCase().includes(query)));
  host.querySelector('[data-list]').innerHTML=list.length?list.map(row=>'<article data-rule="'+esc(row.id)+'"><p class="rule-meta">'+esc(row.label+' · '+row.section_title+' · '+row.block_title)+'</p><h3>'+esc(row.text)+'</h3><p class="rule-meta">Penalty: '+esc(row.penalty)+' · In charge: '+esc(row.in_charge)+' · For: '+esc(row.applicable_to)+' · Severity: '+esc(row.severity)+'</p><p class="rule-status">'+esc(row.status)+'</p><button type="button" data-open aria-expanded="false">Reactions, comments &amp; discussion</button><div data-detail hidden></div></article>').join(''):'<p>No matching rules.</p>';
  host.querySelectorAll('[data-open]').forEach(button=>button.onclick=()=>detail(button.closest('[data-rule]')));
}
async function detail(article){
  const token=++generation;
  if(selected===article.dataset.rule){selected=null;article.querySelector('[data-detail]').hidden=true;article.querySelector('[data-open]').setAttribute('aria-expanded','false');return;}
  host.querySelectorAll('[data-detail]').forEach(el=>{el.hidden=true;});host.querySelectorAll('[data-open]').forEach(el=>el.setAttribute('aria-expanded','false'));
  selected=article.dataset.rule;mode='comments';topic=null;const wrap=article.querySelector('[data-detail]');wrap.hidden=false;wrap.textContent='Loading…';article.querySelector('[data-open]').setAttribute('aria-expanded','true');
  try{const data=await api('/'+encodeURIComponent(selected));if(token!==generation)return;
    wrap.innerHTML='<div class="rule-buttons"><button type="button" data-vote="1" aria-pressed="'+(data.my_vote===1)+'" '+(!contribute?'disabled':'')+'>Like · '+esc(data.likes)+'</button><button type="button" data-vote="-1" aria-pressed="'+(data.my_vote===-1)+'" '+(!contribute?'disabled':'')+'>Dislike · '+esc(data.dislikes)+'</button><button type="button" data-vote="0" '+(!contribute?'disabled':'')+'>Remove my reaction</button></div><div class="rule-thread"><div class="rule-buttons" role="tablist" aria-label="Rule conversation"><button type="button" role="tab" data-mode="comments" aria-selected="true">Comments</button><button type="button" role="tab" data-mode="topics" aria-selected="false">Discussion</button></div><div data-conversation role="tabpanel"></div></div>';
    wrap.querySelectorAll('[data-vote]').forEach(button=>button.onclick=async()=>{const id=selected,ver=generation;wrap.querySelectorAll('[data-vote]').forEach(el=>el.disabled=true);try{await api('/'+encodeURIComponent(id)+'/reactions',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({vote:Number(button.dataset.vote)})});if(ver!==generation)return;selected=null;await detail(article);}catch(error){if(ver===generation){notice(error.message);wrap.querySelectorAll('[data-vote]').forEach(el=>el.disabled=false);}}});
    wrap.querySelectorAll('[data-mode]').forEach(button=>button.onclick=()=>{mode=button.dataset.mode;topic=null;wrap.querySelectorAll('[data-mode]').forEach(el=>el.setAttribute('aria-selected',String(el===button)));conversation(wrap);});
    conversation(wrap);
  }catch(error){if(token===generation)wrap.textContent=error.message;}
}
async function conversation(wrap,before=null){
  const token=++generation,id=selected,area=mode==='topics'?'topics'+(topic?'/'+topic.id:''):'comments',root=wrap.querySelector('[data-conversation]');
  root.innerHTML='<p role="status">Loading conversation…</p>';
  try{const data=await api('/'+encodeURIComponent(id)+'/'+area+(before?'?before='+encodeURIComponent(before):''));if(token!==generation)return;
    const isTopics=mode==='topics'&&!topic;
    root.innerHTML=(topic?'<button type="button" data-back>Back to discussions</button><h4>'+esc(topic.title)+'</h4>':'')+
      (isTopics?(data.topics||[]).map(row=>'<button type="button" class="rule-topic" data-topic="'+esc(row.topic_id)+'">'+esc(row.title)+'<small> · '+esc(row.display_name)+' · '+esc(date(row.created_at))+'</small></button>').join(''):
      (data.messages||[]).map(row=>'<div class="rule-message"><p>'+esc(row.message)+'</p><small>'+esc(row.display_name)+' · '+esc(date(row.created_at))+'</small></div>').join(''))+
      (!(isTopics?data.topics:data.messages)?.length?'<p>No '+(isTopics?'discussions':'messages')+' yet.</p>':'')+
      (data.next_before?'<button type="button" data-older>Older '+(isTopics?'discussions':'messages')+'</button>':'')+
      (before?'<button type="button" data-latest>Latest</button>':'')+
      (contribute?'<form data-post>'+(isTopics?'<label>Discussion title<input name="title" maxlength="160" required></label>':'')+'<label>'+ (isTopics?'Start a discussion':topic?'Reply':'Comment')+'<textarea name="message" maxlength="2000" required></textarea></label><button type="submit">'+(isTopics?'Start discussion':'Post')+'</button><p data-post-status role="status"></p></form>':'<p>Only current student accounts can contribute.</p>');
    root.querySelector('[data-back]')?.addEventListener('click',()=>{topic=null;conversation(wrap);});
    root.querySelector('[data-older]')?.addEventListener('click',()=>conversation(wrap,data.next_before));
    root.querySelector('[data-latest]')?.addEventListener('click',()=>conversation(wrap));
    root.querySelectorAll('[data-topic]').forEach(button=>button.onclick=()=>{topic={id:button.dataset.topic,title:(data.topics||[]).find(row=>row.topic_id===button.dataset.topic).title};conversation(wrap);});
    const form=root.querySelector('[data-post]');let pending=null;
    if(form)form.onsubmit=async event=>{event.preventDefault();const message=form.elements.message.value.trim(),title=form.elements.title?.value.trim();if(!message)return;const body={message,...(title?{title}:{})};const signature=JSON.stringify(body);if(!pending||pending.signature!==signature)pending={signature,client_id:crypto.randomUUID()};const button=form.querySelector('button'),status=form.querySelector('[data-post-status]');button.disabled=true;status.textContent='Saving…';try{await api('/'+encodeURIComponent(id)+'/'+area,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,client_id:pending.client_id})});if(token===generation)conversation(wrap);}catch(error){if(token===generation){status.textContent=error.message;button.disabled=false;}}};
  }catch(error){if(token===generation)root.innerHTML='<p role="status">'+esc(error.message)+'</p><button type="button" data-retry>Retry</button>';root.querySelector('[data-retry]')?.addEventListener('click',()=>conversation(wrap));}
}
window.EA_RULES={open};
window.addEventListener('ea-auth-changed',()=>{generation++;rules=[];selected=null;topic=null;if(document.getElementById('rulesPanel').classList.contains('active'))open();else host.replaceChildren();});
})();
