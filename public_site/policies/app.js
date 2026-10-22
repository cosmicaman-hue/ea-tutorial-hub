/* Public read-only register; use text nodes for all catalogue content. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const dateInput = byId('policyDate'), scoreInput = byId('policyScore');
  const host = byId('policyNotices'), status = byId('policyStatus');
  const search = byId('policySearch'), stateFilter = byId('policyState');
  const topics = {all:['All topics','सभी विषय'],normal_star:['Normal Stars','नॉर्मल स्टार'],score_entry:['Point entries','अंक दर्ज करना'],punitive_waiver:['Score waivers','अंक माफ़ी'],vote_power:['Vote Power','मत शक्ति']};
  const states = {current:['In effect','लागू'],scheduled:['Upcoming','आगामी'],history:['Previous','पिछली']};
  let rows = [], topic = 'all';
  const today = () => new Date(Date.now() + 330 * 60000).toISOString().slice(0,10);
  const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase().replace(/\s+/g,' ').trim();
  const dateText = value => value ? new Date(value+'T00:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}) : 'Before 20 October 2026 / 20 अक्टूबर 2026 से पहले';
  function node(tag,text,className) { const el=document.createElement(tag);if(text!=null)el.textContent=text;if(className)el.className=className;return el; }
  function pair(tag,en,hi,className) {
    const el=node(tag,null,className);el.append(node('span',en));
    if(hi){const translated=node('span',hi,'hindi');translated.lang='hi';el.append(translated);}return el;
  }
  function stateOf(row,selected) {
    if(row.effective_date && row.effective_date>selected)return 'scheduled';
    return rows.some(next=>next.topic===row.topic && next.effective_date && (!row.effective_date || next.effective_date>row.effective_date) && next.effective_date<=selected) ? 'history' : 'current';
  }
  function renderPreview(selected) {
    const active=[...rows].reverse().find(row=>row.topic==='vote_power'&&(!row.effective_date||row.effective_date<=selected));
    const score=Number(scoreInput.value),preview=byId('policyPreview');
    if(!active){preview.textContent='No Vote Power policy available. / मत शक्ति नीति उपलब्ध नहीं है।';return;}
    if(!scoreInput.value.trim()||!Number.isFinite(score)){preview.textContent='Enter a valid monthly score. / सही मासिक स्कोर भरें।';return;}
    let power=Math.max(active.minimum,Math.floor(score/active.step)+1);if(active.maximum!=null)power=Math.min(active.maximum,power);
    preview.replaceChildren(pair('span','Vote Power: '+power+' | '+active.step+'-point steps | '+(active.maximum==null?'No maximum ceiling':'Maximum '+active.maximum),'मत शक्ति: '+power+' | प्रत्येक '+active.step+' अंक पर वृद्धि | '+(active.maximum==null?'कोई अधिकतम सीमा नहीं':'अधिकतम '+active.maximum)));
  }
  function render() {
    const selected=dateInput.value;if(!/^\d{4}-\d{2}-\d{2}$/.test(selected))return;
    renderPreview(selected);
    const terms=normalize(search.value).split(' ').filter(Boolean);
    const visible=[...rows].reverse().filter(row=>{
      const text=normalize(JSON.stringify(row));
      return (topic==='all'||row.topic===topic)&&(stateFilter.value==='all'||stateOf(row,selected)===stateFilter.value)&&terms.every(term=>text.includes(term));
    });
    host.replaceChildren();
    byId('policyCount').textContent=visible.length+' notices / सूचनाएँ';byId('policyEmpty').hidden=visible.length>0;
    visible.forEach(row=>{
      const state=stateOf(row,selected),article=node('article',null,'notice '+state);article.id=row.id;
      const meta=node('div',null,'meta');meta.append(node('span',row.notice_number||'EARLIER RULE / पिछला नियम'),node('span',states[state].join(' / '),'badge '+state));
      const heading=pair('h3',row.title,row.title_hi);
      const dates=node('p',null,'dates');dates.append(node('span','Effective / लागू: '+dateText(row.effective_date)));
      if(row.issued_date)dates.append(node('span','Issued / जारी: '+dateText(row.issued_date)));
      article.append(meta,heading,dates,pair('p',row.summary,row.summary_hi,'summary'));
      if(row.clauses?.length){
        const details=node('details'),summary=node('summary','Read full policy / पूरी नीति पढ़ें');
        const body=node('div',null,'policy-body'),list=node('ol');
        row.clauses.forEach((clause,index)=>list.append(pair('li',clause,row.clauses_hi?.[index])));body.append(list);
        if(row.examples?.length){
          const table=node('table'),caption=node('caption','Examples / उदाहरण'),thead=node('thead'),head=node('tr');
          (row.example_headers||['Before / पहले','Stars / स्टार','After / बाद','Bonus / बोनस']).forEach(label=>{const th=node('th',label);th.scope='col';head.append(th);});
          thead.append(head);const tbody=node('tbody');row.examples.forEach(values=>{const tr=node('tr');values.forEach(value=>tr.append(node('td',String(value))));tbody.append(tr);});
          table.append(caption,thead,tbody);const wrap=node('div',null,'example-wrap');wrap.append(table);body.append(wrap);
        }
        if(row.note)body.append(pair('p',row.note,row.note_hi,'policy-note'));
        details.append(summary,body);article.append(details);
      }
      if(row.notice&&/^[a-z0-9-]+\.pdf$/.test(row.notice)){
        const link=node('a','Open / download PDF notice · PDF देखें','pdf-link');link.href='./'+row.notice;link.target='_blank';link.rel='noopener';article.append(link);
      }
      host.append(article);
    });
  }
  Object.entries(topics).forEach(([key,labels])=>{
    const button=node('button',labels.join(' / '));button.type='button';button.dataset.topic=key;button.setAttribute('aria-pressed',String(key===topic));
    button.addEventListener('click',()=>{topic=key;byId('policyTopics').querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',String(el===button)));render();});byId('policyTopics').append(button);
  });
  dateInput.value=today();dateInput.addEventListener('change',render);scoreInput.addEventListener('input',()=>renderPreview(dateInput.value));search.addEventListener('input',render);stateFilter.addEventListener('change',render);
  fetch('./catalog.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('unavailable');return response.json();}).then(data=>{
    if(data.schema_version!==1||!Array.isArray(data.policies))throw new Error('invalid');rows=data.policies;status.textContent='';render();
  }).catch(()=>{status.textContent='Policies could not be loaded. Please reload when connected. / नीतियाँ लोड नहीं हुईं। कनेक्शन मिलने पर पेज दोबारा खोलें।';});
})();
