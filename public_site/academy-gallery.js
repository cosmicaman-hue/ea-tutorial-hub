(function(){
'use strict';
const host=document.getElementById('academyGallery');
const h=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let generation=0,photos=[],shown=0,filtered=[],lastGroup='';
const style=document.createElement('style');style.textContent=`
.academy-gallery-controls{display:flex;gap:12px;flex-wrap:wrap;align-items:end;margin:20px 0}
.academy-gallery-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.academy-gallery-grid figure{margin:0;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--surface)}
.academy-gallery-grid img{width:100%;height:200px;object-fit:cover;display:block}
.academy-gallery-grid figcaption{padding:12px}.academy-gallery-grid button{border:0;padding:0;width:100%;background:none;cursor:zoom-in}
.academy-gallery-lightbox{max-width:95vw;max-height:95vh;border:0;border-radius:12px;background:var(--surface);color:var(--text)}
.academy-gallery-lightbox::backdrop{background:rgba(0,0,0,.82)}.academy-gallery-lightbox img{display:block;max-width:85vw;max-height:75vh;object-fit:contain}
`;document.head.append(style);
function allowed(){return typeof isLoggedIn==='function'&&isLoggedIn();}
function gate(){host.innerHTML='<div class="login-gate"><div class="login-gate-icon">📷</div><h2>Academy Gallery</h2><p>Log in with your general academy password to view approved photographs.</p><button data-gallery-login class="cta-button">Login to View Gallery</button></div>';host.querySelector('button').onclick=()=>openLoginModal();}
function append(){
 if(!allowed())return gate();
 const batch=filtered.slice(shown,shown+30);shown+=batch.length;
 const grid=host.querySelector('[data-gallery-grid]');
 for(const row of batch){
  const group=row.month+' · '+row.folder;
  if(group!==lastGroup){const heading=document.createElement('h3');heading.textContent=group;heading.style.gridColumn='1 / -1';grid.append(heading);lastGroup=group;}
  const figure=document.createElement('figure');
  figure.innerHTML=`<button type="button" aria-label="Enlarge ${h(row.caption)}"><img src="${h(row.photo_path)}" alt="${h(row.caption)}" loading="lazy" decoding="async"></button><figcaption><strong>${h(row.caption)}</strong><p>${h(row.month)} · ${h(row.folder)}</p></figcaption>`;
  figure.querySelector('button').onclick=()=>{
   if(!allowed())return;document.querySelector('.academy-gallery-lightbox')?.remove();
   const dialog=document.createElement('dialog');dialog.className='academy-gallery-lightbox';
   dialog.innerHTML=`<button type="button" aria-label="Close photograph">Close ×</button><img src="${h(row.photo_path)}" alt="${h(row.caption)}"><p>${h(row.caption)}</p>`;
   document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();dialog.onclick=e=>{if(e.target===dialog)dialog.close();};dialog.onclose=()=>dialog.remove();dialog.showModal();
  };grid.append(figure);
 }
 host.querySelector('[data-gallery-more]').hidden=shown>=filtered.length;
 host.querySelector('[data-gallery-count]').textContent=`${filtered.length} approved photos · showing ${shown}`;
 if(!filtered.length)grid.textContent='No approved photos in this album yet.';
}
function filter(){
 const month=host.querySelector('[data-gallery-month]').value,folder=host.querySelector('[data-gallery-folder]').value;
 filtered=photos.filter(p=>(!month||p.month===month)&&(!folder||p.folder===folder));shown=0;lastGroup='';
 host.querySelector('[data-gallery-grid]').replaceChildren();append();
}
function submissionForm(){
 if(!allowed())return gate();
 host.querySelector('[data-gallery-submission]')?.remove();
 const form=document.createElement('form');form.dataset.gallerySubmission='true';form.className='academy-gallery-controls';
 form.innerHTML=`<h3>Submit photographs</h3><label>General login<input name="roll" maxlength="100" autocomplete="username" required></label><label>General password<input name="password" type="password" maxlength="128" autocomplete="current-password" required></label><label>Month<input name="month" type="month" value="${new Date().toISOString().slice(0,7)}" required></label><label>Folder<input name="folder" maxlength="100" placeholder="Annual Day / Classes / Sports"></label><label>Caption<input name="caption" maxlength="500" required></label><label>Photos<input name="photos" type="file" accept="image/jpeg,image/png,image/webp" multiple required></label><button type="submit">Send for Admin approval</button><button type="button" data-cancel>Cancel</button><p role="status" data-status></p>`;
 host.querySelector('.academy-gallery-controls').after(form);form.querySelector('[data-cancel]').onclick=()=>form.remove();
 form.onsubmit=async event=>{
  event.preventDefault();const button=form.querySelector('[type=submit]'),status=form.querySelector('[data-status]');button.disabled=true;
  const files=[...form.elements.photos.files];let saved=0;
  try{
   if(files.length>10)throw new Error('Choose up to ten photos per submission batch.');
   for(const file of files){
    if(!allowed()||!form.isConnected)break;status.textContent=`Preparing ${saved+1} of ${files.length}…`;
    file.galleryId ||= crypto.randomUUID();
    const image_data=await prepare(file);
    const response=await fetch('/api/portal/gallery/submissions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({media_id:file.galleryId,roll:form.elements.roll.value,password:form.elements.password.value,album_month:form.elements.month.value,folder:form.elements.folder.value,caption:form.elements.caption.value,image_data})});
    const data=await response.json();if(!response.ok||!data.success)throw new Error(data.error||'Submission failed.');saved++;
   }
   status.textContent=`${saved} photographs saved for Admin approval.`;
   form.elements.photos.value='';form.elements.password.value='';
  }catch(error){status.textContent=`${saved} saved. ${error.message}`;}finally{button.disabled=false;}
 };
}
async function prepare(file){
 if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>8*1024*1024)throw new Error('Choose JPG, PNG or WebP photos up to 8 MB each.');
 const bitmap=await createImageBitmap(file);
 try{
  if(bitmap.width*bitmap.height>24000000)throw new Error('Choose a smaller photo.');
  const canvas=document.createElement('canvas'),scale=Math.min(1,1024/Math.max(bitmap.width,bitmap.height));canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));
  const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
  for(const quality of [.8,.65,.5,.35]){const data=canvas.toDataURL('image/jpeg',quality);if(data.length<=192*1024*4/3+30)return data;}
  throw new Error('Photo is too detailed; choose a smaller image.');
 }finally{bitmap.close();}
}
async function open(){
 const token=++generation;if(!allowed())return gate();
 host.innerHTML='<h2>Academy Gallery</h2><p role="status">Loading approved photographs…</p>';
 try{
  const response=await fetch('./gallery/catalog.json',{cache:'no-store'});if(!response.ok)throw new Error('Gallery publication is not available yet.');
  const data=await response.json();if(token!==generation||!allowed())return;
  photos=(data.photos||[]).filter(p=>/^gallery\/[0-9a-f-]{36}\.jpg$/i.test(p.photo_path)&&/^\d{4}-\d{2}$/.test(p.month));
  photos.sort((a,b)=>b.month.localeCompare(a.month)||a.folder.localeCompare(b.folder)||String(b.created_at).localeCompare(String(a.created_at)));
  const months=[...new Set(photos.map(p=>p.month))].sort().reverse(),folders=[...new Set(photos.map(p=>p.folder))].sort();
  host.innerHTML=`<h2>Academy Gallery</h2><p>Academy memories, reviewed by Admin.</p><div class="academy-gallery-controls"><label>Month <select data-gallery-month><option value="">All months</option>${months.map(m=>`<option>${h(m)}</option>`).join('')}</select></label><label>Folder <select data-gallery-folder><option value="">All folders</option>${folders.map(f=>`<option>${h(f)}</option>`).join('')}</select></label><button type="button" data-gallery-upload>Submit photos for Admin approval</button></div><p role="status" data-gallery-count></p><div class="academy-gallery-grid" data-gallery-grid></div><button type="button" data-gallery-more>Load more photos</button>`;
  host.querySelector('[data-gallery-month]').onchange=filter;host.querySelector('[data-gallery-folder]').onchange=filter;
  host.querySelector('[data-gallery-more]').onclick=append;
  host.querySelector('[data-gallery-upload]').onclick=submissionForm;filter();
 }catch(error){if(token===generation&&allowed()){host.innerHTML=`<h2>Academy Gallery</h2><p role="status">${h(error.message)}</p><button type="button">Retry</button>`;host.querySelector('button').onclick=open;}}
}
window.EA_GALLERY={open};
window.addEventListener('ea-auth-changed',()=>{generation++;document.querySelector('.academy-gallery-lightbox')?.remove();if(document.getElementById('galleryPanel').classList.contains('active'))open();else if(!allowed())host.replaceChildren();});
if(location.hash.toLowerCase()==='#gallery')open();
})();
