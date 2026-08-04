"""Global busy-modal ("Realify is working") — one reusable, self-contained block shared by the tester
hub (Python-rendered) and frontend.html (static). Injected verbatim into both so the markup, styles,
and JS API are identical. Pure-CSS animated Realify mark (no GIFs/spinners), action title, human
sub-line, elapsed-time counter, and a real focus trap: while open, Escape / backdrop click / the
underlying UI are inert — the anti-"click five other buttons" device.

JS API (window.RealifyBusy):
  run(btn, {title, sub, refresh}, doFetch)   -> synchronous action: modal up until the response; on
                                                success shows ✓ then closes + calls refresh(); on error
                                                shows the reason + Close and re-enables btn.
  runJob(btn, {title, sub}, startFetch, statusUrl, {refresh})
                                             -> backgrounded job: modal up only until ACCEPTED, then
                                                converts to a persistent non-blocking progress chip
                                                that polls statusUrl until done (async-job honesty).
Both reject a double-fire on the client (button disabled in-flight); the server enforces the other half."""

SNIPPET = r"""
<style>
#realifyBusyModal{position:fixed;inset:0;z-index:9000;display:none;align-items:center;justify-content:center;
  background:rgba(26,26,26,.55);backdrop-filter:blur(2px)}
#realifyBusyModal.open{display:flex}
#realifyBusyModal .rb-card{background:#FFFFFF;color:#1A1A1A;border-radius:16px;padding:34px 40px;max-width:380px;
  width:calc(100% - 40px);text-align:center;box-shadow:0 24px 70px rgba(26,26,26,.3);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
#realifyBusyModal .rb-mark{width:56px;height:56px;margin:0 auto 16px;position:relative}
#realifyBusyModal .rb-mark span{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-size:34px;color:#C4785B;animation:rbpulse 1.3s ease-in-out infinite}
#realifyBusyModal .rb-mark::after{content:"";position:absolute;inset:0;border-radius:50%;
  border:3px solid #EFE1D9;border-top-color:#C4785B;animation:rbspin 1.1s linear infinite}
@keyframes rbpulse{0%,100%{transform:scale(.82);opacity:.6}50%{transform:scale(1.05);opacity:1}}
@keyframes rbspin{to{transform:rotate(360deg)}}
#realifyBusyModal .rb-title{font-size:18px;font-weight:700;margin-bottom:4px}
#realifyBusyModal .rb-sub{font-size:13px;color:#6E675C;margin-bottom:12px}
#realifyBusyModal .rb-elapsed{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#9C9483}
#realifyBusyModal.done .rb-mark span{animation:none;color:#7A9E7E}
#realifyBusyModal.done .rb-mark::after{animation:none;border:3px solid #DDEAD9;border-top-color:#7A9E7E}
#realifyBusyModal.err .rb-mark span{animation:none;color:#B3402E}
#realifyBusyModal.err .rb-mark::after{display:none}
#realifyBusyModal .rb-actions{margin-top:16px}
#realifyBusyModal .rb-actions button{background:#C4785B;color:#fff;border:none;border-radius:9px;padding:9px 18px;font-size:14px;font-weight:600;cursor:pointer}
#realifyJobChips{position:fixed;right:16px;bottom:16px;z-index:8500;display:flex;flex-direction:column;gap:8px}
.rb-chip{background:#1A1A1A;color:#EDE7DB;border-radius:100px;padding:9px 16px;font-size:12.5px;
  box-shadow:0 8px 24px rgba(26,26,26,.25);display:flex;align-items:center;gap:8px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.rb-chip .rb-dot{width:9px;height:9px;border-radius:50%;background:#C4785B;animation:rbpulse 1.1s infinite}
.rb-chip.done .rb-dot{background:#7A9E7E;animation:none}
</style>
<div id="realifyBusyModal" role="dialog" aria-modal="true" aria-hidden="true" aria-labelledby="rbTitle">
  <div class="rb-card" tabindex="-1">
    <div class="rb-mark"><span>&#10022;</span></div>
    <div class="rb-title" id="rbTitle">Realify is working</div>
    <div class="rb-sub" id="rbSub">usually under a minute</div>
    <div class="rb-elapsed" id="rbElapsed">0s</div>
    <div class="rb-actions" id="rbActions"></div>
  </div>
</div>
<div id="realifyJobChips"></div>
<script>
window.RealifyBusy=(function(){
  var el,card,titleEl,subEl,elEl,actEl,timer,t0,curBtn,keyH;
  function grab(){el=document.getElementById('realifyBusyModal');card=el.querySelector('.rb-card');
    titleEl=document.getElementById('rbTitle');subEl=document.getElementById('rbSub');
    elEl=document.getElementById('rbElapsed');actEl=document.getElementById('rbActions');}
  function tick(){elEl.textContent=Math.round((Date.now()-t0)/1000)+'s';}
  function trap(e){if(e.key==='Escape'){e.preventDefault();e.stopPropagation();}
    if(e.key==='Tab'){e.preventDefault();card.focus();}}
  function open(title,sub,btn){grab();curBtn=btn||null;if(curBtn)curBtn.disabled=true;
    el.classList.remove('done','err');titleEl.textContent=title||'Realify is working';
    subEl.textContent=sub||'usually under a minute';actEl.innerHTML='';el.classList.add('open');
    el.setAttribute('aria-hidden','false');t0=Date.now();elEl.textContent='0s';
    clearInterval(timer);timer=setInterval(tick,250);card.focus();
    keyH=trap;document.addEventListener('keydown',keyH,true);}
  function close(){grab();el.classList.remove('open');el.setAttribute('aria-hidden','true');
    clearInterval(timer);if(keyH){document.removeEventListener('keydown',keyH,true);keyH=null;}
    if(curBtn)curBtn.disabled=false;curBtn=null;}
  function success(msg,cb){grab();el.classList.add('done');titleEl.textContent='✓ '+(msg||'Done');
    subEl.textContent='';clearInterval(timer);setTimeout(function(){close();if(cb)cb();},900);}
  function error(msg){grab();el.classList.add('err');titleEl.textContent='Something went wrong';
    subEl.textContent=msg||'Please try again.';clearInterval(timer);
    var b=document.createElement('button');b.textContent='Close';b.onclick=close;actEl.innerHTML='';actEl.appendChild(b);
    if(curBtn){curBtn.disabled=false;}}
  async function run(btn,opts,doFetch){opts=opts||{};open(opts.title,opts.sub,btn);
    try{var r=await doFetch();var d={};try{d=await r.json();}catch(e){}
      if(r.ok&&(d.ok===undefined||d.ok)){success(d.message||opts.title||'Done',opts.refresh);return d;}
      error((d&&(d.error||d.message))||('Request failed ('+r.status+').'));return d;}
    catch(e){error(String(e&&e.message||e));}}
  function chip(title){grab();var w=document.getElementById('realifyJobChips');
    var c=document.createElement('div');c.className='rb-chip';
    c.innerHTML='<span class="rb-dot"></span><span class="rb-lbl"></span>';
    c.querySelector('.rb-lbl').textContent=title||'Working…';w.appendChild(c);return c;}
  async function runJob(btn,opts,startFetch,statusUrl,done){opts=opts||{};open(opts.title,opts.sub,btn);
    try{var r=await startFetch();var d={};try{d=await r.json();}catch(e){}
      if(!(r.ok&&(d.started||d.ok!==false))){error((d&&(d.error||d.message))||'Could not start.');return;}
      // ACCEPTED -> release the blocking modal, convert to a non-blocking progress chip; the main thread
      // is now free (backdrop gone) while the backgrounded job runs. DO NOT claim completion yet.
      var c=chip(opts.title||'Working…');close();
      var poll=setInterval(async function(){try{var s=await (await fetch(statusUrl)).json();
        if(s.done){clearInterval(poll);var errd=(s.state==='error');c.classList.add('done');
          c.querySelector('.rb-lbl').textContent=errd?('✗ '+(s.error||'Failed')):('✓ '+(opts.title||'Done'));
          setTimeout(function(){c.remove();if(done&&done.refresh)done.refresh();},errd?4500:2000);}}catch(e){}},1500);}
    catch(e){error(String(e&&e.message||e));}}
  return {open:open,close:close,success:success,error:error,run:run,runJob:runJob,chip:chip};
})();
</script>
"""
