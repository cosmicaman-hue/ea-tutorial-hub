/* Only Admin-approved portraits are returned; masked ranking rows stay masked. */
(function(){
    const escape=value=>String(value||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    let rows=new Map();
    window.eaPublicPortrait=function(row){
        if(!row||row.masked||!row.roll)return '';
        const initials=String(row.name||'?').trim().split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase();
        return `<span data-ea-public-portrait="${escape(row.roll)}" class="public-avatar-initials">${escape(initials)}</span>`;
    };
    function fill(){document.querySelectorAll('[data-ea-public-portrait]').forEach(node=>{
        const media=rows.get(node.dataset.eaPublicPortrait);if(!media||node.querySelector('img')||node.dataset.failed)return;
        const initial=node.textContent,image=document.createElement('img');image.src='/api/portal/media/'+encodeURIComponent(media.media_id);image.alt='';image.loading='lazy';image.style.cssText='width:100%;height:100%;object-fit:cover;border-radius:50%';
        image.onerror=()=>{node.textContent=initial;node.dataset.failed='true';};node.textContent='';node.style.cssText='display:block;width:100%;height:100%';node.append(image);
    });}
    fetch('/api/portal/media/portraits',{credentials:'omit',cache:'no-store'}).then(response=>response.ok?response.json():null).then(data=>{if(!data?.success)return;rows=new Map(data.portraits.map(row=>[row.login_id,row]));fill();}).catch(()=>{});
    let scheduled=false;new MutationObserver(()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;fill();});}).observe(document.body,{childList:true,subtree:true});
})();
