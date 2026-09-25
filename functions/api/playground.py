"""GET /playground — OpenRouter-style chat playground (LTR, mobile-first). NO Fly."""
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import usage

PAGE = """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
<title>AYAI-VPX Playground</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#08080d;--panel:#0d0d15;--card:#14141f;--line:#212130;--txt:#e9e9f2;--mut:#8e8ea6;--acc:#7c5cf0;--acc2:#b18cff}
html,body{height:100%}
body{background:radial-gradient(1200px 500px at 80% -10%,#1b1440 0%,var(--bg) 55%) fixed,var(--bg);color:var(--txt);font-family:Inter,-apple-system,Segoe UI,Roboto,sans-serif;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid var(--line);background:rgba(13,13,21,.85);backdrop-filter:blur(8px);flex-shrink:0}
#burger{display:none;background:var(--card);color:#fff;border:1px solid var(--line);border-radius:10px;font-size:18px;padding:7px 13px}
.logo{font-weight:800;font-size:18px;background:linear-gradient(90deg,#a78bfa,#f0abfc);-webkit-background-clip:text;background-clip:text;color:transparent;white-space:nowrap}
nav a{color:var(--mut);text-decoration:none;font-size:13px;margin-right:14px}
nav a:hover{color:#fff}
.hstat{margin-left:auto;font-size:12px;color:var(--mut);background:var(--card);border:1px solid var(--line);border-radius:20px;padding:5px 13px;white-space:nowrap}
.hstat b{color:#7cf5c4}
button{cursor:pointer;border:none;border-radius:10px;font-size:13px;padding:9px 15px;min-height:40px;font-weight:600}
.btn{background:linear-gradient(135deg,#7c5cf0,#9d6bff);color:#fff;box-shadow:0 4px 18px rgba(124,92,240,.35)}
.btn:hover{filter:brightness(1.1)}
.btn:disabled{opacity:.5}
.ghost{background:var(--card);color:#cfcfe0;border:1px solid var(--line)}
.ghost:hover{border-color:var(--acc)}
main{flex:1;display:flex;min-height:0;position:relative}
aside{width:320px;border-right:1px solid var(--line);background:rgba(13,13,21,.92);display:flex;flex-direction:column;min-height:0;z-index:5}
aside .tools{padding:10px;border-bottom:1px solid var(--line);display:flex;gap:6px;flex-shrink:0}
aside .tools input{flex:1;background:var(--card);border:1px solid var(--line);color:#fff;border-radius:10px;padding:10px;font-size:13px;min-width:0}
aside .tools input:focus{outline:none;border-color:var(--acc)}
#list{flex:1;overflow-y:auto;padding:8px;-webkit-overflow-scrolling:touch}
.grp{margin-bottom:4px}
.grp>h4{font-size:11px;color:var(--mut);padding:9px 8px 5px;cursor:pointer;text-transform:uppercase;letter-spacing:1px;position:sticky;top:-8px;background:var(--panel);z-index:2}
.grp>h4:hover{color:#fff}
.mrow{display:flex;align-items:center;gap:8px;padding:11px 9px;border-radius:12px;font-size:13px;cursor:pointer;color:#c6c6d8;border:1px solid transparent;min-height:48px}
.mrow:hover{background:var(--card)}
.mrow.sel{background:linear-gradient(135deg,#241a4d,#1a1440);color:#fff;border-color:var(--acc)}
.mrow .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;pointer-events:none}
.tbtn{background:var(--card);color:#ffd88a;border:1px solid var(--line);border-radius:9px;font-size:12px;padding:7px 11px;min-height:36px;flex-shrink:0}
.tbtn:hover{border-color:#ffd88a}
.tok{font-size:11px;white-space:nowrap}
#overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:4}
section{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0}
#cur{display:flex;align-items:center;gap:8px;padding:9px 14px;border-bottom:1px solid var(--line);font-size:14px;flex-wrap:wrap;flex-shrink:0;background:rgba(13,13,21,.6)}
#cur .pill{background:linear-gradient(135deg,#241a4d,#1a1440);border:1px solid var(--acc);color:#d9ccff;border-radius:20px;padding:5px 15px;font-size:12px;font-weight:700;max-width:58vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#msgs{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;-webkit-overflow-scrolling:touch;min-height:0}
.hero{text-align:center;margin:auto;color:var(--mut);padding:20px}
.hero .big{font-size:44px;margin-bottom:10px}
.hero h2{color:var(--txt);font-size:20px;margin-bottom:6px}
.hero p{font-size:13px;line-height:1.7}
.hero .hint{display:inline-block;margin-top:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px 16px;font-size:12px;color:#b9a8ff}
.msg{max-width:82%;padding:11px 15px;border-radius:16px;font-size:14px;line-height:1.6;white-space:pre-wrap;word-break:break-word;animation:pop .18s ease}
@keyframes pop{from{transform:translateY(6px);opacity:.4}to{transform:none;opacity:1}}
.u{align-self:flex-end;background:linear-gradient(135deg,#7c5cf0,#9d6bff);color:#fff;border-bottom-right-radius:5px;box-shadow:0 4px 16px rgba(124,92,240,.25)}
.a{align-self:flex-start;background:var(--card);border:1px solid var(--line);border-bottom-left-radius:5px}
.meta{font-size:11px;color:var(--mut);margin-top:7px}
#box{padding:10px 14px calc(12px + env(safe-area-inset-bottom));border-top:1px solid var(--line);flex-shrink:0;background:rgba(13,13,21,.85)}
#sysrow{display:none;margin-bottom:8px}
#sysrow.show{display:block}
#sys{width:100%;background:#0f0f18;border:1px solid var(--line);color:#c9c9da;border-radius:10px;padding:9px;font-size:12px;resize:vertical}
#row{display:flex;gap:8px;align-items:flex-end}
#inp{flex:1;background:var(--card);border:1px solid var(--line);color:#fff;border-radius:14px;padding:12px 14px;font-size:16px;resize:none;height:50px;min-width:0;line-height:1.4}
#inp:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px rgba(124,92,240,.18)}
#send{height:50px;padding:0 22px;font-size:15px}
.iconbtn{background:var(--card);color:#b9a8ff;border:1px solid var(--line);border-radius:10px;height:50px;width:50px;font-size:18px;flex-shrink:0}
.typ{color:var(--mut);font-size:13px}
@media(max-width:820px){
 #burger{display:block}
 nav{display:none}
 .hstat{display:none}
 aside{position:fixed;top:0;bottom:0;left:0;transform:translateX(-105%);transition:transform .25s ease;width:min(330px,88vw);box-shadow:0 0 50px #000}
 aside.open{transform:none}
 #overlay.show{display:block}
 .msg{max-width:94%}
 #cur .pill{max-width:50vw}
 .logo{font-size:16px}
}
</style>
</head>
<body>
<header>
<button id="burger" onclick="toggleDrawer()">☰</button>
<div class="logo">▲ AYAI-VPX</div>
<nav><a href="/playground">Playground</a><a href="/">Dashboard</a><a href="/v1/models">Models API</a><a href="/api/status">Status</a></nav>
<div class="hstat"><b id="mcount">…</b> models • free, no key needed</div>
</header>
<div id="overlay" onclick="toggleDrawer(false)"></div>
<main>
<aside id="side">
<div class="tools"><input id="q" placeholder="🔍 Search models…"><button class="ghost" id="rf" onclick="refreshModels()" title="Fetch newest models">🔄</button></div>
<div id="mstat" style="padding:8px 12px;font-size:12px;color:var(--mut);border-bottom:1px solid var(--line)">…</div>
<div id="list"></div>
</aside>
<section>
<div id="cur"><span style="color:var(--mut);font-size:13px">Model:</span><span class="pill" id="curm">—</span><button class="ghost" onclick="testCurrent()" style="margin-left:auto">⚡ Test</button><button class="ghost" onclick="clearChat()">Clear</button></div>
<div id="msgs"><div class="hero" id="hero"><div class="big">💬</div><h2>Pick a model & start chatting</h2><p>190+ free AI models, no login, no API key.<br>Tap ☰ to browse models, ⚡ to test if one answers.</p><div class="hint">⚡ = test model directly &nbsp;•&nbsp; 🔄 = fetch newest models</div></div></div>
<div id="box">
<div id="sysrow"><textarea id="sys" rows="2" placeholder="System prompt (optional personality)…"></textarea></div>
<div id="row"><button class="iconbtn" onclick="document.getElementById('sysrow').classList.toggle('show')" title="System prompt">⚙</button><textarea id="inp" placeholder="Message the model…" rows="1"></textarea><button class="btn" id="send" onclick="send()">➤</button></div>
</div>
</section>
</main>
<script>
let MODELS=[],CUR="",HIST=[];
const $=id=>document.getElementById(id);
function toggleDrawer(force){
 let s=$("side"),o=$("overlay");
 let open=(force!==undefined)?force:!s.classList.contains("open");
 s.classList.toggle("open",open);o.classList.toggle("show",open);
}
let NEWSET={},TESTRES={};
try{TESTRES=JSON.parse(localStorage.vpx_test||"{}");}catch(e){TESTRES={};}
function saveTest(){try{localStorage.vpx_test=JSON.stringify(TESTRES);}catch(e){}}
async function loadModels(){
 try{
  let d=await (await fetch("/v1/models")).json();
  MODELS=(d.data||[]).map(x=>x.id).sort();
 }catch(e){MODELS=[];}
 $("mcount").textContent=MODELS.length;
 let seen=null;
 try{seen=JSON.parse(localStorage.vpx_seen||"null");}catch(e){seen=null;}
 NEWSET={};
 if(seen===null){try{localStorage.vpx_seen=JSON.stringify(MODELS);}catch(e){}}
 else{for(let id of MODELS)if(seen.indexOf(id)<0)NEWSET[id]=1;
  try{localStorage.vpx_seen=JSON.stringify(MODELS);}catch(e){}}
 if(!CUR&&MODELS.length)CUR=MODELS[0];
 $("curm").textContent=CUR||"—";
 updStat();renderList("");
}
function updStat(){
 let ok=0,bad=0;
 for(let k in TESTRES){if(TESTRES[k]&&TESTRES[k].ok)ok++;else bad++;}
 let nw=Object.keys(NEWSET).length;
 $("mstat").textContent=MODELS.length+" models • ✅ "+ok+" live • ❌ "+bad+(nw?" • ✨ "+nw+" new":"");
}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function renderList(q){
 q=(q||"").toLowerCase();
 let g={};
 for(let i=0;i<MODELS.length;i++){
  let id=MODELS[i];
  if(q&&id.toLowerCase().indexOf(q)<0)continue;
  let s=id.split("-")[0];(g[s]=g[s]||[]).push(i);
 }
 let h="";
 let ni=[];for(let i=0;i<MODELS.length;i++){let id=MODELS[i];if(NEWSET[id]&&(!q||id.toLowerCase().indexOf(q)>=0))ni.push(i);}
 if(ni.length){
  h+="<div class='grp'><h4>✨ New · "+ni.length+"</h4>";
  for(let i of ni){let id=MODELS[i];let tr=TESTRES[id];h+="<div class='mrow"+(id===CUR?" sel":"")+"' data-i='"+i+"'><span class='nm'>🆕 "+esc(id)+"</span><span class='tok' id='t"+i+"'>"+(tr?(tr.ok?"✅":"❌"):"")+"</span><button class='tbtn' data-t='"+i+"'>⚡</button></div>";}
  h+="</div>";
 }
 for(let s of Object.keys(g).sort()){
  h+="<div class='grp'><h4>"+esc(s)+" · "+g[s].length+"</h4>";
  for(let i of g[s]){
   let id=MODELS[i];let tr=TESTRES[id];
   h+="<div class='mrow"+(id===CUR?" sel":"")+"' data-i='"+i+"'><span class='nm'>"+(NEWSET[id]?"🆕 ":"")+esc(id)+"</span><span class='tok' id='t"+i+"'>"+(tr?(tr.ok?"✅":"❌"):"")+"</span><button class='tbtn' data-t='"+i+"'>⚡</button></div>";
  }
  h+="</div>";
 }
 $("list").innerHTML=h||"No models";
}
$("list").addEventListener("click",e=>{
 let t=e.target;
 if(t.dataset&&t.dataset.t!==undefined){e.stopPropagation();testModel(MODELS[+t.dataset.t],+t.dataset.t);return;}
 let row=t.closest?t.closest(".mrow"):null;
 if(row&&row.dataset.i!==undefined)pick(MODELS[+row.dataset.i]);
});
function pick(id){CUR=id;$("curm").textContent=id;HIST=[];$("msgs").innerHTML="";renderList($("q").value);toggleDrawer(false);}
function bubble(who,text,meta){
 let h=$("hero");if(h)h.remove();
 let d=document.createElement("div");d.className="msg "+who;d.textContent=text;
 if(meta){let m=document.createElement("div");m.className="meta";m.textContent=meta;d.appendChild(m);}
 $("msgs").appendChild(d);$("msgs").scrollTop=1e9;return d;
}
function clearChat(){HIST=[];$("msgs").innerHTML="";}
async function send(){
 let t=$("inp").value.trim();if(!t||!CUR)return;
 $("inp").value="";bubble("u",t);
 HIST.push({role:"user",content:t});
 let sys=$("sys").value.trim();
 let msgs=(sys?[{role:"system",content:sys}]:[]).concat(HIST.slice(-6));
 let ty=bubble("a","● ● ●");ty.classList.add("typ");
 $("send").disabled=true;
 try{
  let r=await fetch("/api/play",{method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({model:CUR,messages:msgs})});
  let d=await r.json();
  ty.classList.remove("typ");
  if(!r.ok){ty.textContent="⚠️ "+(d.error||r.status);}
  else{HIST.push({role:"assistant",content:d.text});stream(ty,d.text,"via "+d.used+" · "+d.seconds+"s");}
 }catch(e){ty.textContent="⚠️ "+e;}
 $("send").disabled=false;
}
function stream(el,full,meta){
 let i=0;el.textContent="";
 let iv=setInterval(()=>{i+=16;el.textContent=full.slice(0,i);
  if(i>=full.length){clearInterval(iv);let m=document.createElement("div");m.className="meta";m.textContent=meta;el.appendChild(m);}},25);
}
async function testModel(id,idx){
 let sl=document.querySelectorAll('[id="t'+idx+'"]');
 sl.forEach(s=>{s.textContent="…";s.style.color="";});
 try{
  let r=await fetch("/api/play",{method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({model:id,direct:true,messages:[{role:"user",content:"reply with exactly: OK-KURD"}]})});
  let d=await r.json();
  let ok=r.ok&&(d.text||"").indexOf("OK-KURD")>=0;
  TESTRES[id]={ok:ok?1:0,t:Date.now()};saveTest();updStat();
  sl.forEach(s=>{s.textContent=(ok?"✅ ":"❌ ")+(d.seconds||"")+"s";s.style.color=ok?"#7cf5c4":"#ff9d9d";});
 }catch(e){TESTRES[id]={ok:0,t:Date.now()};saveTest();updStat();sl.forEach(s=>{s.textContent="❌";s.style.color="#ff9d9d";});}
}
function testCurrent(){let i=MODELS.indexOf(CUR);if(i>=0)testModel(CUR,i);}
async function refreshModels(){
 $("rf").disabled=true;$("rf").textContent="⏳";
 try{
  let r=await fetch("/api/refresh",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({})});
  let d=await r.json();
  if(!r.ok)alert("Refresh failed: "+(d.error||r.status));
  else{alert("Synced "+d.sync_ok+"/"+d.sync_total+" sources · "+d.models+" models");await loadModels();}
 }catch(e){alert("Refresh error: "+e);}
 $("rf").disabled=false;$("rf").textContent="🔄";
}
$("q").addEventListener("input",e=>renderList(e.target.value));
$("inp").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}});
loadModels();
</script>
</body>
</html>
"""


class handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        raw = body.encode("utf-8")
        try:
            usage.hit(len(raw))
        except Exception:
            pass
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        return self._send(200, PAGE, "text/html; charset=utf-8")
