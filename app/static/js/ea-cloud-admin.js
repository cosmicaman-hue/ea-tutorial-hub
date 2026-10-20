/* Admin-only Cloudflare device review and Rules moderation, loaded on demand. */
function eaCloudAdminInit(panel) {
    const section=document.createElement('section');section.className='ea-portal-usage';
    section.innerHTML='<div class="ea-portal-usage-head"><div><p class="ea-request-kicker">Cloudflare access and Rules</p><h3>Student devices &amp; rule discussions</h3><p>Students may use two registered browsers. Approve a pending browser by replacing an old device. Signing out does not free a slot. Review cloud comments and discussions here.</p></div><button type="button" class="secondary" data-cloud-devices>Load devices</button><button type="button" class="secondary" data-cloud-rules>Load rule discussions</button></div><p data-cloud-admin-status role="status" aria-live="polite" hidden></p><div data-cloud-admin-report>Choose a report to load.</div>';
    panel.querySelector('.ea-portal-usage')?.after(section);
    const host=section.querySelector('[data-cloud-admin-report]');let generation=0;
    const esc=eaStudentRequestsEscape,attr=eaStudentRequestsEscapeAttr;
    const identity=()=>String(currentLoginId || '')+'|'+String(currentUserRole || '');
    const valid=(token,owner)=>token===generation&&eaStudentRequestsAdmin()&&owner===identity();
    function status(message,error=false){const node=section.querySelector('[data-cloud-admin-status]');node.hidden=!message;node.textContent=message;node.className=error?'profile-alert error':'';eaStudentRequestsSetStatus(message,error?'error':'');}
    async function action(path,payload,button,refresh,token,owner){
        if(!valid(token,owner))return;
        button.disabled=true;status('Saving cloud decision…');
        try{await eaPortalActivationEnsureCsrf();if(!valid(token,owner))return;const result=await eaStudentRequestsFetch('/scoreboard/api/portal-admin/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':eaStudentRequestCsrf},body:JSON.stringify(payload)});if(!valid(token,owner))return;if(path==='cloud-devices'&&(result.device_id!==payload.device_id||result.status!==(payload.action==='approve'?'allowed':'removed')))throw new Error('Device acknowledgement did not match. Reload the list before retrying.');status(path==='cloud-devices'?(payload.action==='approve'?'Browser approved. Ask the student to sign in again in that same browser.':'Browser access removed.'):'Cloud decision saved.');await refresh();}
        catch(error){if(valid(token,owner)){status('Cloud action could not be confirmed: '+error.message,true);button.disabled=false;}}
    }
    async function devices(){
        if(!eaStudentRequestsAdmin())return;
        const token=++generation,owner=identity();host.textContent='Loading registered Cloudflare devices…';
        try{const data=await eaStudentRequestsFetch('/scoreboard/api/portal-admin/cloud-devices');if(!valid(token,owner))return;const rows=data.devices || [];
            const limit=Number(data.limit)||2;
            function decision(row){if(row.status!=='pending')return '';const allowed=rows.filter(other=>other.login_id===row.login_id&&other.status==='allowed'),full=allowed.length>=limit;return '<p>'+esc(full?'Both browser slots are occupied. Choose an approved browser to replace.':'A browser slot is available.')+'</p><label>Replace <select data-replace data-replacement-required="'+(full?'true':'false')+'"><option value=""'+(full?' disabled selected':'')+'>'+esc(full?'Choose a browser to replace':'Use a free slot')+'</option>'+allowed.map((other,index)=>'<option value="'+attr(other.device_id)+'">'+esc((index+1)+'. '+(other.device_label||'Unnamed browser'))+' · registered '+esc(eaStudentRequestsDateTime(other.created_at))+' · last seen '+esc(eaStudentRequestsDateTime(other.last_seen_at))+'</option>').join('')+'</select></label><button type="button" data-approve>Approve browser</button>';}
            host.innerHTML='<div class="ea-portal-usage-scroll"><table><thead><tr><th>Student login</th><th>Browser</th><th>Status</th><th>Last login attempt</th><th>Admin decision</th></tr></thead><tbody>'+rows.map(row=>'<tr data-cloud-device="'+attr(row.device_id)+'"><td>'+esc(row.login_id)+'</td><td>'+esc(row.device_label)+'</td><td>'+esc(row.status)+'</td><td>'+esc(eaStudentRequestsDateTime(row.last_seen_at))+'</td><td>'+decision(row)+'<button type="button" class="secondary" data-remove>'+(row.status==='pending'?'Reject request':'Remove device')+'</button></td></tr>').join('')+'</tbody></table></div>'+(rows.length?'':'<p>No registered cloud devices yet.</p>');
            host.querySelectorAll('[data-approve]').forEach(button=>button.onclick=()=>{const row=button.closest('[data-cloud-device]'),select=row.querySelector('[data-replace]');if(select.dataset.replacementRequired==='true'&&!select.value){status('Choose one of this student’s approved browsers to replace. Both slots are occupied.',true);select.focus();return;}action('cloud-devices',{device_id:row.dataset.cloudDevice,action:'approve',replace_device_id:select.value || null},button,devices,token,owner);});
            host.querySelectorAll('[data-remove]').forEach(button=>button.onclick=()=>{if(!confirm('Remove this browser’s Cloudflare access? It will need Admin approval before signing in again.'))return;action('cloud-devices',{device_id:button.closest('[data-cloud-device]').dataset.cloudDevice,action:'remove'},button,devices,token,owner);});
        }catch(error){if(valid(token,owner))host.textContent='Could not load cloud devices: '+error.message;}
    }
    async function moderation(){
        if(!eaStudentRequestsAdmin())return;
        const token=++generation,owner=identity();host.textContent='Loading the latest cloud Rules comments and discussions…';
        try{const data=await eaStudentRequestsFetch('/scoreboard/api/portal-admin/cloud-rule-moderation');if(!valid(token,owner))return;const rows=data.entries || [];
            host.innerHTML='<p>Latest 100 comments and discussion titles. Hiding a discussion also hides its replies from students.</p>'+rows.map(row=>'<div class="ea-request-item" data-rule-entry="'+attr(row.id)+'" data-rule-kind="'+attr(row.kind)+'"><strong>'+esc(row.rule_id)+' · '+esc(row.kind)+' · '+esc(row.login_id)+'</strong><p style="white-space:pre-wrap">'+esc(row.text)+'</p><small>'+esc(eaStudentRequestsDateTime(row.created_at))+' · '+(row.hidden_at?'Hidden':'Visible')+'</small><label>Reason<input data-reason maxlength="500" required></label><button type="button" data-moderate="'+(row.hidden_at?'restore':'hide')+'">'+(row.hidden_at?'Restore':'Hide')+'</button></div>').join('')+(rows.length?'':'<p>No cloud Rules comments or discussions yet.</p>');
            host.querySelectorAll('[data-moderate]').forEach(button=>button.onclick=()=>{const row=button.closest('[data-rule-entry]'),reason=row.querySelector('[data-reason]').value.trim();if(!reason){eaStudentRequestsSetStatus('Enter a moderation reason first.','error');return;}action('cloud-rule-moderation',{id:row.dataset.ruleEntry,kind:row.dataset.ruleKind,action:button.dataset.moderate,reason},button,moderation,token,owner);});
        }catch(error){if(valid(token,owner))host.textContent='Could not load rule discussions: '+error.message;}
    }
    section.querySelector('[data-cloud-devices]').onclick=devices;
    section.querySelector('[data-cloud-rules]').onclick=moderation;
    window.eaCloudAdminReset=()=>{generation++;status('');host.textContent='Choose a report to load.';};
    window.addEventListener('ea-auth-changed',window.eaCloudAdminReset);
}
