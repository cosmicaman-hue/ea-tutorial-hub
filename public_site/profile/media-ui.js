// This fragment is embedded in app.js so the isolated portal keeps one entry point.
let portraitMap=new Map();
function profileMediaUUID(){
  const source=globalThis.crypto;
  if(typeof source?.randomUUID==='function')return source.randomUUID();
  if(typeof source?.getRandomValues!=='function')throw new Error('This browser cannot prepare an upload ID. Please use an updated browser.');
  const bytes=source.getRandomValues(new Uint8Array(16));
  bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
  const hex=Array.from(bytes,value=>value.toString(16).padStart(2,'0')).join('');
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
function portraitHtml(studentId, name, broad=false){
  const id=portraitMap.get(String(studentId));
  const initials=String(name||'?').trim().split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase();
  return `<span class="ea-portrait ${broad?'ea-portrait-broad':''}" aria-hidden="true">${id?`<img src="${API}/media/${h(id)}" alt="" loading="lazy">`:h(initials)}</span>`;
}
async function loadPortraits(){
  try{const data=await api('/media/portraits');portraitMap=new Map((data.portraits||[]).map(row=>[String(row.student_id),row.media_id]));}catch{portraitMap=new Map();}
}
async function preparePhoto(file, kind){
  if(!file||!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>8*1024*1024)throw new Error('Choose a JPG, PNG or WebP photo up to 8 MB.');
  const bitmap=await createImageBitmap(file);
  try{
    if(bitmap.width*bitmap.height>24000000)throw new Error('Choose a smaller photo.');
    const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
    const size=kind==='portrait'?512:1024, scale=Math.min(1,size/Math.max(bitmap.width,bitmap.height));
    canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));
    ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
    let encoded=canvas.toDataURL('image/jpeg',.8);
    for(const quality of [.65,.5,.35]){if(encoded.length<=192*1024*4/3+30)break;encoded=canvas.toDataURL('image/jpeg',quality);}
    if(encoded.length>192*1024*4/3+30)throw new Error('This photo is too detailed. Try a smaller image.');
    return encoded;
  }finally{bitmap.close();}
}
function photoForm(kind){return `<form class="profile-form" data-photo-upload="${kind}"><label>${kind==='portrait'?'New profile picture':'Photo'}<input type="file" name="photo" accept="image/jpeg,image/png,image/webp" required></label>${kind==='gallery'?'<label>Caption<textarea name="caption" maxlength="500" required></textarea></label>':'<input type="hidden" name="caption" value="">'}<p class="profile-photo-help">${kind==='gallery'?'Visible to signed-in academy users after Admin approval.':'Your profile picture appears across student displays after Admin approval.'}</p><button class="profile-btn" type="submit">Send photo for approval</button><p role="status" data-upload-status></p></form>`;}
function bindPhotoForms(){
  view().querySelectorAll('[data-photo-upload]').forEach(form=>{
    form.onchange=()=>{delete form.dataset.mediaId;};
    form.onsubmit=async event=>{
      event.preventDefault();const button=form.querySelector('button[type=submit]'),status=form.querySelector('[data-upload-status]');button.disabled=true;
      try{
        form.dataset.mediaId ||= profileMediaUUID();
        status.textContent='Preparing your photo…';
        const image_data=await preparePhoto(form.querySelector('[name=photo]').files[0],form.dataset.photoUpload);
        await api('/me/media',{method:'POST',body:JSON.stringify({media_id:form.dataset.mediaId,kind:form.dataset.photoUpload,caption:form.querySelector('[name=caption]').value,image_data})});
        status.textContent='Saved. Awaiting Admin approval.';form.reset();delete form.dataset.mediaId;
      }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
    };
  });
}
function renderPhotoSettings(){
  const o=state.profile.overview||{};
  view().innerHTML=`<h3>My profile picture</h3><section class="profile-card"><div class="profile-person">${portraitHtml(state.account.student_id,o.name,true)}<div><strong>${h(o.name)}</strong><p>Use a clear photo of yourself. Portraits have a circular frame and a soft depth effect.</p></div></div>${photoForm('portrait')}</section><h3>My submissions</h3><div data-photo-submissions>Loading…</div>`;
  bindPhotoForms();loadMyPhotos();
}
async function loadMyPhotos(){
  try{const data=await api('/me/media');const target=view()?.querySelector('[data-photo-submissions]');if(!target)return;
    target.innerHTML=(data.media||[]).map(row=>`<article class="profile-card"><div class="profile-person"><img class="profile-submission-photo" src="${API}/media/${h(row.media_id)}" alt="Your submitted photo" loading="lazy"><div><strong>${h(label(row.kind))} · ${h(label(row.status))}</strong><p>${h(row.caption)}</p>${row.review_reason?`<small>Admin: ${h(row.review_reason)}</small>`:''}</div></div></article>`).join('')||'<p>No photos submitted yet.</p>';
  }catch(error){const target=view()?.querySelector('[data-photo-submissions]');if(target)target.textContent=error.message;}
}
async function renderGallery(){
  view().innerHTML=`<h3>Student gallery</h3><p>Academy memories shared with signed-in students and staff.</p>${state.account?.kind!=='staff'?`<details class="profile-duty-compose"><summary>Post a photo with a caption</summary>${photoForm('gallery')}</details>`:''}<div class="profile-media-grid" data-gallery-list>Loading approved photos…</div><button class="profile-btn secondary" data-gallery-more hidden>Load more</button>${state.account?.kind!=='staff'?'<details class="profile-duty-compose"><summary>My submissions and review status</summary><div data-photo-submissions></div></details>':''}`;
  bindPhotoForms();loadMyPhotos();
  let before='',busy=false;const list=view().querySelector('[data-gallery-list]'),more=view().querySelector('[data-gallery-more]');
  const load=async()=>{if(busy)return;busy=true;more.disabled=true;try{const data=await api('/gallery'+(before?'?before='+encodeURIComponent(before):''));if(!list.isConnected)return;if(!before)list.innerHTML='';for(const row of data.media||[]){list.insertAdjacentHTML('beforeend',`<figure class="profile-card"><img src="${API}/media/${h(row.media_id)}" alt="${h(row.caption)}" loading="lazy"><figcaption><strong>${h(row.name||row.login_id||'Student')}</strong><p>${h(row.caption)}</p><small>${h(new Date(row.created_at).toLocaleDateString())}</small></figcaption></figure>`);}if(!list.childElementCount)list.textContent='No approved photos yet.';before=data.next_before;more.hidden=!before;}catch(error){if(list.isConnected)notice(error.message,true);}finally{busy=false;more.disabled=false;}};
  more.onclick=load;await load();
}
