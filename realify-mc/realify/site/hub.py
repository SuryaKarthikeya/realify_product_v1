"""R9 reimagined tester hub — LIFTED from docs/mockups/realify-hub-reimagined.html (its <style> + element
markup are the source of truth). Two steps (Data + Role) with the order toggle, the parametric generator
form, pick-existing seeds, a loaded state header, role cards with impersonation pickers, and the global
email short-circuit toggle. Only DATA is dynamic — chrome/layout/CSS are the mockup's. Long ops use the
shared busy modal (accept-then-poll)."""
import html as _h

from .busy_modal import SNIPPET as _BUSY_MODAL

from .hubkit import CSS as _CSS   # warm component sheet (shared w/ agency fleet grid + drill-in)

# R15 Part G.4 — full-screen GENERATING lock: greys the whole hub, only Cancel is clickable while a
# world is being created. Dedicated overlay (hubkit.CSS is shared with fleet/drill-in, so keep it local).
_GENLOCK_CSS = ("#genLock{position:fixed;inset:0;z-index:9600;background:rgba(26,26,26,.6);"
    "backdrop-filter:blur(3px);display:none;align-items:center;justify-content:center}"
    "#genLock.on{display:flex}"
    "#genLock .gl-card{background:#fff;border-radius:14px;padding:30px 34px;text-align:center;"
    "box-shadow:0 12px 40px rgba(0,0,0,.3);max-width:340px}"
    "#genLock .gl-spin{width:34px;height:34px;border:3px solid #E4DDD0;border-top-color:#C4785B;"
    "border-radius:50%;margin:0 auto 16px;animation:glspin .8s linear infinite}"
    "@keyframes glspin{to{transform:rotate(360deg)}}"
    "#genLock .gl-title{font-weight:600;font-size:16px;color:#1A1A1A}"
    "#genLock .gl-sub{font-size:12.5px;color:#6E675C;margin-top:6px;line-height:1.5}"
    "#genLock .gl-cancel{margin-top:18px;padding:8px 20px;border:1px solid #E4DDD0;background:#fff;"
    "border-radius:9px;font-size:13px;font-weight:500;cursor:pointer;color:#1A1A1A}"
    "#genLock .gl-cancel:hover{border-color:#C4785B;color:#A9603F}")
_GENLOCK_HTML = ("<div id=genLock><div class=gl-card><div class=gl-spin></div>"
    "<div class=gl-title>Generating your world…</div>"
    "<div class=gl-sub>Synthesizing SKUs, ads, channels and decisions — usually under a minute. "
    "Everything else stays locked until it finishes.</div>"
    "<button class=gl-cancel id=genCancel>Cancel</button></div></div>")
_LOCALE_CHANNELS = {"US": ["Amazon US", "Walmart", "Shopify"], "IN": ["Amazon.in", "Flipkart", "Shopzee"]}
_CATS = {"US": ["Home & Kitchen", "Pet Supplies", "Outdoor", "Electronics", "Beauty", "Grocery", "Toys"],
         "IN": ["Car cover", "Dashcam", "Phone mount", "Seat organizer", "Tyre inflator", "LED kit"]}


def _captured_block(seeds):
    """R17 Part D — 'Seed from a real catalog' pick: catalogs rescued on brand deletion (server-rendered
    so the world's REAL brand/SKU count/country show without a round-trip)."""
    rows = "".join(
        f'<div class=seedrow><span><b>{_h.escape(s.get("brand_name") or s.get("name") or "brand")}</b> · '
        f'{int(s.get("sku_count") or 0)} SKUs · {_h.escape(s.get("country") or "US")} '
        f'<span class=tag>rescued</span></span>'
        f'<button class="btn p sm" data-seed="{int(s["id"])}">Provision &amp; enter →</button></div>'
        for s in (seeds or []))
    return ('<div class=field style="margin-top:16px"><label>Seed from a real catalog</label>'
            '<div class=hint>Catalogs rescued when a brand was deleted (R17). Provisions a fresh sandbox '
            'world from the real ASINs/titles/categories, then drops you in as that brand.</div>'
            f'<div id=capturedSeeds>{rows or "<p class=note-s>No rescued catalogs yet.</p>"}</div></div>')


def hub_html(email, captured_seeds=None):
    e = _h.escape(email)
    captured = _captured_block(captured_seeds)
    us_cats = "".join(f'<span class="chip{" sel" if i < 3 else ""}" data-cat>{_h.escape(c)}</span>'
                      for i, c in enumerate(_CATS["US"]))
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><link rel='icon' type='image/png' href='/assets/Final-logo-VF-white-3.png'>
<meta name=viewport content="width=device-width,initial-scale=1"><meta name=robots content="noindex, nofollow">
<title>Realify · Reimagined Tester Hub</title><style>{_CSS}</style><style>{_GENLOCK_CSS}</style></head><body>{_BUSY_MODAL}{_GENLOCK_HTML}<div id=stage>
<div class=frame>
<div class=sandbar><span><b>SANDBOX</b> · synthetic data · writes go to mock marketplaces · signed in as {e}</span><span><a href="/platform" style="color:inherit;text-decoration:underline">← Home</a> · env: staging</span></div>
<div class=pad>
<h2 class=htitle>Tester &amp; sandbox hub</h2>
<p class=hsub>Generate or pick a world, then step into any role in it.</p>
<div id=stateHead><div class=emptyhead>Nothing loaded yet. Generate a world or pick the <b>US Pilot</b>/<b>India Pilot</b> below — that unlocks the roles.</div></div>
<div class=ordertoggle><span id=ordData class=on onclick="setOrder('data')">▷ Data first</span><span id=ordRole onclick="setOrder('role')">Role first</span></div>

<div class=step done id=stepData>
  <div class=step-h><span class=step-n>1</span><h3>Data — build or pick a world</h3><span class=st-note>start here</span></div>
  <div class=step-body>
    <div class=subtabs><span class="subtab on" data-dtab=gen onclick="dtab('gen')">✦ Generate new</span><span class=subtab data-dtab=pick onclick="dtab('pick')">◷ Pick existing seed</span><span class=subtab data-dtab=resyn onclick="dtab('resyn')">↻ Resynthesize current</span></div>

    <div id=paneGen>
      <div class=field><label>Categories</label><div class=chips id=catChips>{us_cats}</div><div class=hint>Drives product names, COGS bands, seasonality.</div></div>
      <div class=field><label>Number of SKUs (across the world)</label>
        <div class=rangewrap><input type=range id=skuRange min=20 max=2000 value=480 oninput="document.getElementById('skuVal').textContent=this.value"><span class=rangeval id=skuVal>480</span></div>
        <div class=hint>Up to 2000. Distributed across brands.</div></div>
      <div class=cols3>
        <div class=field><label>Agencies</label><input type=number id=nAgencies value=1 min=1></div>
        <div class=field><label>Brands per agency</label><input type=number id=nBrands value=8 min=1></div>
        <div class=field><label>+ Direct brands</label><input type=number id=nDirect value=1 min=0></div>
      </div>
      <div class=field><label>Country <span style="color:var(--terra)">*</span> — one world = one country</label>
        <div class=chips id=countryChips><span class="chip sel" data-country=US onclick="setCountry('US')">🇺🇸 United States · USD</span><span class=chip data-country=IN onclick="setCountry('IN')">🇮🇳 India · ₹</span></div>
        <div class=hint>Drives currency &amp; formatting ($1,234 vs ₹1,23,456), COGS/margin bands, product selection, and channels.</div></div>
      <div class=cols2>
        <div class=field><label>Channels</label><div class=chips id=chanChips></div><div class=hint id=chanHint></div></div>
        <div class=field><label>Synthesis depth</label><div class=chips id=depthChips><span class="chip sel" data-depth=rich onclick="pickOne(this,'depth')">Rich (demo — full cross-channel)</span><span class=chip data-depth=fast onclick="pickOne(this,'depth')">Fast (volume/perf)</span></div><div class=hint>Rich = orders, ads, competitors, economics. Fast = catalog + light signals.</div></div>
      </div>
      <div class=cols2>
        <div class=field><label>Planted moments</label><div class=chips id=momChips><span class="chip sel" data-mom=stockout>Stockout-ready SKU</span><span class="chip sel" data-mom=acos_over_breakeven>ACOS over break-even</span><span class="chip sel" data-mom=competitor_undercut>Competitor undercut</span><span class="chip sel" data-mom=expired_conn>1–2 expired connections</span></div></div>
        <div class=field><label>Seed (determinism)</label><input type=text id=seed value="demo-2026Q3-v4"><div class=hint>Same country+params+seed → byte-identical world.</div></div>
      </div>
      <div class=cols2>
        <div class=field><label>Brand name <span class=note-s>(a DIRECT brand — leave Agency blank; billed as a seller, no agency)</span></label><input type=text id=brandName placeholder="e.g. Cedar &amp; Co"></div>
        <div class=field><label>Agency name <span class=note-s>(leave blank if direct — fill to make the brand MANAGED under this agency)</span></label><input type=text id=agencyName placeholder="e.g. BrightPeak Commerce"></div></div>
      <div style="display:none"><!--keep grid balanced-->
      </div>
      <button class="btn p" id=btnGen>✦ Generate &amp; load world →</button>
      <button class="btn g" id=btnSave style="margin-left:8px">Generate &amp; save as…</button>
    </div>

    <div id=panePick style="display:none">
      <div id=seedList><p class=note-s>Loading worlds…</p></div>
    </div>

    <div id=paneResyn style="display:none">
      <p class=note-s>Re-roll the currently-loaded world in place (reset to its seed) — same shape, fresh economics.</p>
      <button class="btn g" id=btnResyn>↻ Reset current world to seed</button>
      <button class="btn g" id=btnClock style="margin-left:8px">⏩ Advance clock 30 days</button>
    </div>
    {captured}
  </div>
</div>

<div class=settingbar id=scBar><div class=toggle id=scToggle onclick="toggleSC()"></div><div><b>Email short-circuit: <span id=scLabel>…</span>.</b> Consent &amp; invite emails still send — and show an inline "✓ approve as if clicked" control so you never leave the test. Sandbox only.</div></div>

<div class="step locked" id=stepRole>
  <div class=step-h><span class=step-n>2</span><h3>Role — become someone in this world</h3><span class=st-note id=roleNote>🔒 load a dataset first</span></div>
  <div class=step-body>
    <div class=roles>
      <div class="role dis" data-role=direct><div class=r-role>Direct brand · $20/mo</div><h4>Direct Brand Owner</h4><p>The classic five-lens seller product — a paying direct customer.</p><div class=pick><label>Impersonate which direct brand</label><select id=selDirect></select></div><button class="btn p sm ent" data-kind=direct disabled>Enter as this brand →</button></div>
      <div class="role dis" data-role=agency><div class=r-role>Agency · paying</div><h4>Agency operator</h4><p>Fleet grid; onboard &amp; manage client brands.</p><div class=pick><label>Impersonate which agency</label><select id=selAgency></select></div><button class="btn p sm ent" data-kind=agency disabled>Enter as agency →</button></div>
      <div class="role dis" data-role=managed_brand><div class=r-role>Agency-managed brand</div><h4>Managed Brand Owner</h4><p>The brand portal — how a managed client sees Realify.</p><div class=pick><label>Brand</label><select id=selManaged></select></div><button class="btn p sm ent" data-kind=managed_brand disabled>Enter as this brand →</button></div>
      <div class="role dis" data-role=admin><div class=r-role>Realify · internal</div><h4>Realify Admin</h4><p>Fleet ops console — agencies, gates, provisioning.</p><div class=pick><label>Scope</label><select><option>All agencies (fleet)</option></select></div><button class="btn p sm ent" data-kind=admin disabled>Enter as admin →</button></div>
    </div>
    <div style="margin-top:16px"><div class=stepbody id=stepBody>Pick a walkthrough — a guided bar then rides across the REAL surfaces (fleet → scope-switched brand → portal), each Next navigating + flipping persona live.</div>
      <div style="margin-top:10px"><button class="btn p sm gr-start" data-run=customer disabled>▶ Customer walkthrough · ~15m</button> <button class="btn g sm gr-start" data-run=vc disabled>▶ Investor walkthrough · ~8m</button></div></div>
  </div>
</div>

<details class=op><summary>Operator actions (advanced)</summary>
  <p class=note-s style="margin-top:10px">Create an internal tenant (paid access synthesized, auto-tagged <b>is_internal</b>). Uses this superlogin session.</p>
  <label>New tenant email (@realify.ai)</label><input id=oe type=email placeholder="tester@realify.ai">
  <label>Password</label><input id=op type=password><label>Account / org name</label><input id=oa type=text placeholder="HQ">
  <div style="margin-top:12px"><button class="btn g sm" id=btnCreate>Create internal tenant</button></div><div id=omsg class=note-s></div></details>
</div></div></div>
<script>{_JS}</script></body></html>"""


_JS = r"""
var STATE=null, STEPS=[], STEPI=0, WORLD=null;
function esc(s){var d=document.createElement('div');d.textContent=(s==null?'':s);return d.innerHTML;}
function jpost(u,b){return fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})});}
function pickOne(el,grp){document.querySelectorAll('[data-'+grp+']').forEach(function(c){c.classList.remove('sel');});el.classList.add('sel');}
document.querySelectorAll('#catChips [data-cat],#momChips [data-mom]').forEach(function(c){c.addEventListener('click',function(){c.classList.toggle('sel');});});
var LOCALE_CHAN={US:['Amazon US','Walmart','Shopify'],IN:['Amazon.in','Flipkart','Shopzee']};
var LOCALE_CATS={US:['Home & Kitchen','Pet Supplies','Outdoor','Electronics','Beauty','Grocery','Toys'],IN:['Car cover','Dashcam','Phone mount','Seat organizer','Tyre inflator','LED kit']};
function setCountry(c){document.querySelectorAll('#countryChips [data-country]').forEach(function(x){x.classList.toggle('sel',x.dataset.country===c);});renderChan(c);renderCats(c);}
function renderChan(c){var h='';LOCALE_CHAN[c].forEach(function(ch,i){h+='<span class="chip'+(i<2?' sel':'')+'" data-chan onclick="this.classList.toggle(\'sel\')">'+esc(ch)+'</span>';});document.getElementById('chanChips').innerHTML=h;document.getElementById('chanHint').textContent=(c==='US'?'India would offer Amazon.in · Flipkart · Shopzee.':'US would offer Amazon US · Walmart · Shopify.');}
function renderCats(c){var h='';LOCALE_CATS[c].forEach(function(ct,i){h+='<span class="chip'+(i<3?' sel':'')+'" data-cat onclick="this.classList.toggle(\'sel\')">'+esc(ct)+'</span>';});document.getElementById('catChips').innerHTML=h;}
function country(){var s=document.querySelector('#countryChips .sel');return s?s.dataset.country:'US';}
function genParams(){var cats=[];document.querySelectorAll('#catChips .sel').forEach(function(c){cats.push(c.textContent);});
  var moms=[];document.querySelectorAll('#momChips .sel').forEach(function(c){moms.push(c.dataset.mom);});
  var depth=(document.querySelector('#depthChips .sel')||{}).dataset?document.querySelector('#depthChips .sel').dataset.depth:'rich';
  return {country:country(),categories:cats,sku_count:+document.getElementById('skuRange').value,
    brands_per_agency:+document.getElementById('nBrands').value,direct_brands:+document.getElementById('nDirect').value,
    depth:depth,moments:moms,seed:document.getElementById('seed').value.trim(),
    agency_name:(document.getElementById('agencyName')||{}).value,
    brand_name:(document.getElementById('brandName')||{}).value};}
function dtab(t){['gen','pick','resyn'].forEach(function(x){document.getElementById('pane'+x.charAt(0).toUpperCase()+x.slice(1)).style.display=(x===t?'block':'none');document.querySelector('[data-dtab='+x+']').classList.toggle('on',x===t);});if(t==='pick')loadWorlds();}
// R14 Part A: the hub is a TWO-STATE machine — exactly one step active. Data-loaded LOCKS the Data
// controls (greyed + disabled) and activates Role; not-loaded activates Data and locks Role. There is
// no path where Data + a live role are both active.
function _setDataLocked(lock){var sd=document.getElementById('stepData');sd.classList.toggle('collapsed',lock);sd.classList.toggle('done',lock);sd.classList.toggle('locked',lock);
  var sdb=sd.querySelector('.step-body');if(sdb)sdb.style.display=lock?'none':'block';
  sd.querySelectorAll('.step-body button,.step-body input,.step-body select').forEach(function(el){el.disabled=lock;});}
function _setRoleLocked(lock){document.getElementById('stepRole').classList.toggle('locked',lock);
  document.querySelectorAll('.role').forEach(function(r){r.classList.toggle('dis',lock);});
  document.querySelectorAll('.ent,.gr-start').forEach(function(b){b.disabled=lock;});
  document.getElementById('roleNote').textContent=lock?'🔒 load a dataset first':'ready';}
// "↻ Change world" = explicit ordered reset: clear the assumed grant (log out of the role) → unlock
// Data → re-lock Role. Changing data always resets the role; no swapping data under a live role.
function changeWorld(){jpost('/api/ops/sandbox/return',{}).then(function(){},function(){}).then(function(){
  _setDataLocked(false);_setRoleLocked(true);dtab('gen');
  document.getElementById('stepData').scrollIntoView({behavior:'smooth',block:'start'});});}
function setOrder(o){document.getElementById('ordData').classList.toggle('on',o==='data');document.getElementById('ordRole').classList.toggle('on',o==='role');
  var sd=document.getElementById('stepData'),sr=document.getElementById('stepRole'),p=sd.parentNode;
  if(o==='role')p.insertBefore(sr,sd);else p.insertBefore(sd,sr);}
var JOB='/api/ops/sandbox/job';
function afterLoad(){loadState();dtab('gen');}
// R15 Part G.4 — full-screen GENERATING lock: only Cancel is clickable while a world is being created;
// Cancel restores the prior unlocked hub. World-creating ops (generate/save/preset/saved) run through it.
function showGenLock(){var g=document.getElementById('genLock');if(g)g.classList.add('on');}
function hideGenLock(){var g=document.getElementById('genLock');if(g)g.classList.remove('on');}
function afterCreate(){hideGenLock();afterLoad();}
function genRun(btn,opts,start){showGenLock();return RealifyBusy.runJob(btn,opts,start,JOB,{refresh:afterCreate});}
(function(){var gc=document.getElementById('genCancel');if(gc)gc.addEventListener('click',function(){hideGenLock();});})();
document.getElementById('btnGen').addEventListener('click',function(ev){var p=genParams();if(!p.categories.length){alert('Pick at least one category.');return;}
  genRun(ev.currentTarget,{title:'Synthesizing world',sub:p.sku_count+' SKUs — usually under a minute'},function(){return jpost('/api/ops/sandbox/generate',p);});});
document.getElementById('btnSave').addEventListener('click',function(ev){var name=prompt('Save this world as (name):');if(!name)return;var p=genParams();p.save_as=name;
  genRun(ev.currentTarget,{title:'Synthesizing & saving world'},function(){return jpost('/api/ops/sandbox/generate',p);});});
document.getElementById('btnResyn').addEventListener('click',function(ev){RealifyBusy.runJob(ev.currentTarget,{title:'Resetting current world to seed'},function(){return jpost('/api/ops/sandbox/reset',{});},JOB,{refresh:afterLoad});});
document.getElementById('btnClock').addEventListener('click',function(ev){RealifyBusy.runJob(ev.currentTarget,{title:'Advancing the clock 30 days'},function(){return jpost('/api/ops/sandbox/clock',{days:30});},JOB,{refresh:afterLoad});});
async function loadWorlds(){var d=await (await fetch('/api/ops/sandbox/worlds')).json();var h='';
  (d.presets||[]).forEach(function(w){h+='<div class=seedrow><span><b>'+esc(w.name)+'</b> '+(w.country==='IN'?'🇮🇳':'🇺🇸')+' — '+w.brands+' brands <span class="tag live">preset</span><div class=meta>seed '+esc(w.seed)+'</div></span><button class="btn p sm" data-preset="'+esc(w.key)+'">Load</button></div>';});
  (d.saved||[]).forEach(function(w){h+='<div class=seedrow><span><b>'+esc(w.name)+'</b> '+(w.country==='IN'?'🇮🇳':'🇺🇸')+' <span class=tag>yours</span><div class=meta>seed '+esc(w.seed)+'</div></span><button class="btn g sm" data-saved=\''+esc(JSON.stringify(w.params))+'\'>Load</button></div>';});
  document.getElementById('seedList').innerHTML=h||'<p class=note-s>No worlds yet — generate one.</p>';
  document.querySelectorAll('[data-preset]').forEach(function(b){b.addEventListener('click',function(ev){genRun(ev.currentTarget,{title:'Loading preset'},function(){return jpost('/api/ops/sandbox/preset',{scenario:ev.currentTarget.dataset.preset});});});});
  document.querySelectorAll('[data-saved]').forEach(function(b){b.addEventListener('click',function(ev){var p=JSON.parse(ev.currentTarget.dataset.saved);genRun(ev.currentTarget,{title:'Loading saved world'},function(){return jpost('/api/ops/sandbox/generate',p);});});});}
function renderState(st){STATE=st;var h=document.getElementById('stateHead');
  var loading=(st&&st.loading&&st.loading.in_progress);
  var lb=loading?'<div class=emptyhead style="border-style:solid">A sandbox '+esc(st.loading.action)+' is in progress since '+esc(st.loading.since)+' — updates when done.</div>':'';
  if(!st||!st.loaded){h.innerHTML=lb+'<div class=emptyhead>Nothing loaded yet. Generate a world or pick a preset below — that unlocks the roles.</div>';}
  else{h.innerHTML=lb+'<div class=shead><div class=cell><div class=k>Scenario</div><div class=v>'+esc(st.scenario)+'</div></div>'
    +'<div class=cell><div class=k>Seed</div><div class=v>'+esc(st.seed)+'</div></div>'
    +'<div class=cell><div class=k>Country</div><div class=v>'+esc(({US:"United States",IN:"India"})[st.country]||st.country)+' · '+esc(st.currency==='USD'?'USD':(st.symbol||st.currency))+'</div></div>'   /* R15.1: world's real country/currency */
    +'<div class=cell><div class=k>Brands</div><div class=v>'+esc(st.brand_count)+'</div></div>'
    +'<div class=cell><div class=k>Last loaded</div><div class=v>'+esc(st.loaded_at||'—')+'</div></div>'
    +'<div class=cell><div class=k>Next reset</div><div class=v>Manual</div></div></div>'
    +'<button class="btn g sm" onclick="changeWorld()" style="margin-top:4px">↻ Change world</button>';}
  var on=!!(st&&st.loaded);
  _setDataLocked(on);      // R14: loaded → Data controls LOCK (greyed + disabled)
  _setRoleLocked(!on);     // ...and Role becomes the only active step (or stays locked until a world loads)
  var note=document.querySelector('#stepData .st-note'); if(note)note.textContent=on?('✓ '+esc(st.scenario)+' loaded'):'start here';
  // currency↔world sync: the form country reflects the LOADED world until you Change world.
  if(on&&st.country)setCountry(st.country);
  if(on&&st.personas){fillPickers(st);document.getElementById('stepRole').scrollIntoView({behavior:'smooth',block:'start'});}}
function fillPickers(st){var p=st.personas||{};var brands=st.brands||[];var directs=st.directs||[];
  var da=document.getElementById('selAgency');da.innerHTML='<option value="agency">'+esc(st.agency_name||'Agency')+' ('+brands.length+' brands)</option>';
  var dm=document.getElementById('selManaged');dm.innerHTML=brands.map(function(b){return '<option value="'+b.tenant_id+'">'+esc(b.name)+' (managed · '+esc(b.symbol||b.currency)+')</option>';}).join('');   // R15.1: real currency symbol
  var dd=document.getElementById('selDirect');dd.innerHTML=directs.map(function(d){return '<option value="'+d.tenant_id+'">'+esc(d.name)+' (direct · '+esc(d.symbol||(st.symbol||'$'))+')</option>';}).join('')||'<option value="">(none — set + Direct brands)</option>';}
document.querySelectorAll('.ent').forEach(function(b){b.addEventListener('click',async function(){if(b.disabled)return;var kind=b.dataset.kind;var body={kind:kind};
  if(kind==='agency')body.tenant_id=+document.getElementById('selManaged').value;   // enter agency via any of its brands
  if(kind==='managed_brand')body.tenant_id=+document.getElementById('selManaged').value;
  if(kind==='direct')body.tenant_id=+document.getElementById('selDirect').value;
  if(kind==='agency'){var pr=STATE.personas||{};body.tenant_id=(STATE.brands&&STATE.brands[0]&&STATE.brands[0].tenant_id);}
  var r=await jpost('/api/ops/sandbox/impersonate',body);var d=await r.json().catch(function(){return{};});
  if(r.ok&&d.redirect)location.href=d.redirect;else alert((d&&d.error)||'Could not impersonate.');});});
async function loadState(){try{var d=await (await fetch('/api/ops/sandbox/state')).json();renderState(d);WORLD=d.scenario;}catch(e){renderState(null);}}
async function loadSC(){try{var d=await (await fetch('/api/ops/sandbox/shortcircuit')).json();setSC(d.on);}catch(e){}}
function setSC(on){document.getElementById('scToggle').classList.toggle('off',!on);document.getElementById('scLabel').textContent=on?'ON':'OFF';}
async function toggleSC(){var on=!document.getElementById('scToggle').classList.contains('off')?false:true;/*flip*/
  var cur=document.getElementById('scLabel').textContent==='ON';var r=await jpost('/api/ops/sandbox/shortcircuit',{on:!cur});var d=await r.json();setSC(d.on);}
// R11.1: start a guided-run TELEPROMPTER — the bar then rides the real surfaces; Next navigates live.
document.querySelectorAll('.gr-start').forEach(function(b){b.addEventListener('click',function(){if(b.disabled)return;
  jpost('/api/ops/sandbox/guided-run/start',{name:b.dataset.run}).then(function(r){return r.json();}).then(function(d){
    if(d.ok&&d.redirect)location.href=d.redirect;else alert((d&&d.error)||'Load a world first.');});});});
document.getElementById('btnCreate').addEventListener('click',async function(){var r=await jpost('/superlogin/operator/create-tenant',{email:oe.value,password:op.value,account:oa.value});var d=await r.json().catch(function(){return{};});document.getElementById('omsg').textContent=r.ok?('Created internal tenant #'+d.tenant_id):((d&&d.error)||'Failed.');});
// R17 Part D: provision a sandbox world from a rescued catalog, then drop into the real app.
document.querySelectorAll('#capturedSeeds [data-seed]').forEach(function(b){b.addEventListener('click',function(ev){
  if(ev.currentTarget.disabled)return;showGenLock();
  jpost('/api/ops/sandbox/generate-from-seed',{seed_id:+ev.currentTarget.dataset.seed}).then(function(r){return r.json();}).then(function(d){
    if(d.ok&&d.redirect)location.href=d.redirect;else{hideGenLock();alert((d&&d.error)||'Could not provision from that seed.');}});});});
setCountry('US');loadState();loadSC();
"""
