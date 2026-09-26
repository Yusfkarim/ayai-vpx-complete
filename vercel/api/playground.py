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
.msg h1,.msg h2,.msg h3,.msg h4{font-weight:800;line-height:1.3;margin:12px 0 6px;text-align:start}
.msg h1:first-child,.msg h2:first-child,.msg h3:first-child,.msg h4:first-child{margin-top:0}
.msg h1{font-size:22px;border-bottom:1px solid var(--line);padding-bottom:6px}
.msg h2{font-size:19px}
.msg h3{font-size:16px}
.msg h4{font-size:14px}
.msg p{margin:4px 0}
.msg ul,.msg ol{margin:6px 0;padding-inline-start:22px}
.msg li{margin:3px 0}
.msg hr{border:none;border-top:1px solid var(--line);margin:12px 0}
.msg blockquote{border-inline-start:3px solid var(--acc);padding:6px 12px;margin:8px 0;color:#c9c9da;background:rgba(124,92,240,.08);border-radius:8px}
.msg code{background:#0a0a12;border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:12.5px;font-family:ui-monospace,Menlo,Consolas,monospace}
.cb{margin:8px 0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#0a0a12}
.cbl{font-size:11px;color:#b9a8ff;background:#14141f;padding:5px 12px;border-bottom:1px solid var(--line);font-weight:700}
.cb pre{margin:0;padding:10px 12px;overflow-x:auto;font-size:12.5px;line-height:1.55;font-family:ui-monospace,Menlo,Consolas,monospace;white-space:pre;text-align:left}
.cbl{display:flex;align-items:center;justify-content:space-between}
.cpb{background:#241a4d;color:#d9ccff;border:1px solid var(--acc);border-radius:8px;font-size:11px;padding:4px 10px;min-height:0;font-weight:700}
.cpb:hover{background:var(--acc);color:#fff}
.cpb2{display:inline-block;margin-top:8px;background:var(--card);color:#b9a8ff;border:1px solid var(--line);border-radius:9px;font-size:12px;padding:7px 14px;font-weight:700}
.cpb2:hover{border-color:var(--acc);color:#fff}
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
.msg.a{max-width:100%;background:linear-gradient(180deg,rgba(124,92,240,.09),rgba(124,92,240,.02));border:1px solid rgba(124,92,240,.25);border-radius:18px;padding:15px 18px;font-size:15px;line-height:1.8;box-shadow:0 6px 28px rgba(0,0,0,.3)}
.who{font-size:11px;font-weight:800;color:#b9a8ff;letter-spacing:.6px;margin-bottom:8px;text-transform:uppercase}
.msg.u{max-width:85%;padding:11px 16px;border-radius:20px 20px 6px 20px;font-size:14.5px;line-height:1.65}
.caret{display:inline-block;width:9px;height:17px;background:linear-gradient(180deg,#b18cff,#7c5cf0);border-radius:2px;animation:blink 1s steps(1) infinite;vertical-align:-3px;margin-left:2px}
@keyframes blink{50%{opacity:0}}
.msg h1{font-size:23px;border-bottom:2px solid rgba(124,92,240,.5);padding-bottom:8px;margin:16px 0 10px}
.msg h2{font-size:20px;border-inline-start:4px solid var(--acc);padding-inline-start:12px;margin:14px 0 8px}
.msg h3{font-size:17px;color:#e6dcff;margin:12px 0 6px}
.msg h4{font-size:14px;color:#c9c2e8;text-transform:uppercase;letter-spacing:.6px;margin:10px 0 6px}
.msg p{margin:7px 0}
.msg li{margin:5px 0}
.msg li::marker{color:var(--acc2);font-weight:800}
.msg li.td{list-style:none;margin-inline-start:-22px}
.msg a{color:#9ec5ff;text-decoration:none;border-bottom:1px dotted #9ec5ff}
.msg a:hover{border-bottom-style:solid}
.msg del{color:var(--mut)}
.msg code{background:rgba(124,92,240,.13);border:1px solid rgba(124,92,240,.3);color:#ffc98a;border-radius:7px;padding:2px 7px;font-size:13px}
.msg table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.5px}
.msg th{background:rgba(124,92,240,.18);color:#fff;padding:9px 12px;border:1px solid var(--line);text-align:start;font-weight:800}
.msg td{padding:8px 12px;border:1px solid var(--line)}
.msg tr:nth-child(even) td{background:rgba(255,255,255,.025)}
.tbl{overflow-x:auto;margin:4px 0;border-radius:12px}
.msg blockquote{border-inline-start:4px solid var(--acc);padding:10px 14px;margin:10px 0;background:rgba(124,92,240,.07);border-radius:10px;font-size:14.5px}
.msg hr{border:none;height:2px;background:linear-gradient(90deg,transparent,rgba(124,92,240,.6),transparent);margin:16px 0}
.cb{margin:12px 0;border:1px solid rgba(124,92,240,.32);border-radius:14px;background:#0a0a13;box-shadow:0 8px 30px rgba(0,0,0,.4)}
.cbl{background:linear-gradient(90deg,#1e1548,#14141f);padding:8px 8px 8px 14px;font-size:12px;color:#d9ccff;font-weight:800;display:flex;align-items:center;justify-content:space-between}
.cb pre{padding:14px 16px;font-size:13px;line-height:1.7}
.cpb{background:rgba(124,92,240,.14);color:#d9ccff;border:1px solid rgba(124,92,240,.45);border-radius:9px;font-size:11.5px;padding:5px 13px;min-height:0;font-weight:800}
.cpb:hover{background:var(--acc);color:#fff;box-shadow:0 0 14px rgba(124,92,240,.6)}
.cpb2{margin-top:12px;background:rgba(124,92,240,.1);color:#c9b8ff;border:1px solid rgba(124,92,240,.4);border-radius:12px;font-size:12.5px;padding:9px 20px;font-weight:800}
.cpb2:hover{background:rgba(124,92,240,.25);color:#fff;border-color:var(--acc)}
.meta{font-size:11px;color:#6f6f8a;margin-top:10px}
.mrow{-webkit-tap-highlight-color:transparent}
.mrow:active{background:#2a2156}
#msgs{max-width:900px;margin:0 auto;width:100%}
#inp{border-radius:18px}
.hero h2{background:linear-gradient(90deg,#c4b5fd,#f0abfc);-webkit-background-clip:text;background-clip:text;color:transparent;font-size:24px}
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
<div id="sysrow"><textarea id="sys" rows="8" placeholder="System prompt…"># 🎨 SYSTEM INSTRUCTION: ABSOLUTE MARKDOWN &amp; VISUAL FORMATTING PROTOCOL

You are an advanced AI context decorator. Your primary mission is to format ALL generated text with strict Markdown compliance, exceptional typography, visual hierarchy, and precise RTL/LTR text alignment.

---

## 🚨 MANDATORY FORMATTING RULES (STRICT COMPLIANCE)

### 1. HEADINGS &amp; TITLES (LARGE &amp; BOLD FONTS)
- EVERY heading (`#`, `##`, `###`, `####`) MUST be placed at the VERY START OF THE LINE (the absolute leftmost position).
- NEVER attach Markdown heading syntax to the end or middle of a sentence in Arabic, Kurdish, or Hebrew.
- ALWAYS leave an empty line BEFORE and AFTER every heading.
- ✅ CORRECT:
  ## ٤. إنشاء الصفحات الأساسية
- ❌ INCORRECT (NEVER DO THIS):
  ٤. إنشاء الصفحات الأساسية ##

### 2. CODE BLOCKS &amp; COPY CONTAINERS
- ALL code snippets, HTML/CSS, JSON, command-line scripts, or raw queries MUST be enclosed within standard fenced code blocks using triple backticks (```) with the specified language name.
- NEVER mix inline code with normal sentences unless it is a single keyword.
- Format structure:
  ```html
  &lt;div class="card"&gt;
    &lt;p&gt;Sample Code&lt;/p&gt;
  &lt;/div&gt;
  ```</textarea></div>
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
 let d=document.createElement("div");d.className="msg "+who;d.setAttribute("dir","auto");d.textContent=text;
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
function cpText(t,btn){
 const done=()=>{if(!btn)return;let o=btn.textContent;btn.textContent="\u2713 \u0643\u0648\u067e\u0649 \u06a9\u0631\u0627";setTimeout(()=>{btn.textContent=o;},1500);};
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done).catch(()=>fallbackCp(t,done));}
 else fallbackCp(t,done);
}
function fallbackCp(t,done){try{let ta=document.createElement("textarea");ta.value=t;ta.style.position="fixed";ta.style.opacity="0";document.body.appendChild(ta);ta.select();document.execCommand("copy");ta.remove();done();}catch(e){}}
function cpCode(btn){let cb=btn.closest?btn.closest(".cb"):null;let pre=cb?cb.querySelector("pre"):null;if(pre)cpText(pre.textContent,btn);}
function cpMsg(btn){let b=btn.closest?btn.closest(".msg"):null;if(b&&b._raw!==undefined)cpText(b._raw,btn);else if(b)cpText(b.textContent,btn);}
function renderMd(t){
 let e=esc(t),code=[];
 e=e.replace(/```(\\w*)\\n([\\s\\S]*?)```/g,(m,l,c)=>{code.push({l:l||"code",c:c.replace(/\\n$/,"")});return "\\x00"+(code.length-1)+"\\x00";});
 const linkify=s=>s.replace(/\\[([^\\]]+)\\]\\((https?:[^)\\s]+)\\)/g,"<a href=\\"$2\\" target=\\"_blank\\" rel=\\"noopener\\">$1</a>").replace(/(^|[\\s(])(https?:\\/\\/[^\\s<]+)/g,"$1<a href=\\"$2\\" target=\\"_blank\\" rel=\\"noopener\\">$2</a>");
 const inline=s=>linkify(s).replace(/`([^`\\n]+)`/g,"<code>$1</code>").replace(/~~([^~]+)~~/g,"<del>$1</del>").replace(/\\*\\*([^*]+)\\*\\*/g,"<b>$1</b>").replace(/(^|[\\s(])\\*([^\\*\\n]+)\\*/g,"$1<i>$2</i>");
 const rowCells=s=>s.replace(/^\\||\\|$/g,"").split("|").map(c=>inline(c.trim()));
 let html="",inul=false,inol=false,intbl=false;
 const closeLists=()=>{if(inul){html+="</ul>";inul=false;}if(inol){html+="</ol>";inol=false;}};
 const closeTbl=()=>{if(intbl){html+="</table></div>";intbl=false;}};
 for(let ln of e.split("\\n")){
  let m,trim=ln.trim();
  if(/^\\x00\\d+\\x00$/.test(trim)){closeLists();closeTbl();let b=code[+trim.slice(1,-1)];html+="<div class='cb'><div class='cbl'><span>"+b.l+"</span><button class='cpb' onclick='cpCode(this)'>⧉ کوپی</button></div><pre>"+b.c+"</pre></div>";continue;}
  if(/^\\|.*\\|$/.test(trim)&&!intbl){closeLists();html+="<div class='tbl'><table>";intbl=true;}
  if(intbl){
   if(!/^\\|.*\\|$/.test(trim)){closeTbl();}
   else{
    if(/^\\|[\\s:|\\-]+\\|$/.test(trim))continue;
    let th=html.endsWith("<table>");
    html+="<tr>"+rowCells(trim).map(c=>th?"<th>"+c+"</th>":"<td>"+c+"</td>").join("")+"</tr>";continue;
   }
  }
  if(m=ln.match(/^(#{1,4})\\s+(.*)$/)){closeLists();html+="<h"+m[1].length+">"+inline(m[2].replace(/\\s+#$/,""))+"</h"+m[1].length+">";continue;}
  if(/^([-*_])\\1{2,}$/.test(trim.replace(/\\s/g,""))){closeLists();html+="<hr>";continue;}
  if(m=ln.match(/^&gt;\\s?(.*)$/)){closeLists();html+="<blockquote>"+inline(m[1])+"</blockquote>";continue;}
  if(m=ln.match(/^(\\d+)[.)]\\s+(.*)$/)){if(inul){html+="</ul>";inul=false;}if(!inol){html+="<ol>";inol=true;}html+="<li>"+inline(m[2])+"</li>";continue;}
  if(m=ln.match(/^[-*]\\s+\\[([ xX])\\]\\s+(.*)$/)){if(inol){html+="</ol>";inol=false;}if(!inul){html+="<ul>";inul=true;}html+="<li class='td'>"+(m[1]===" "?"☐":"☑")+" "+inline(m[2])+"</li>";continue;}
  if(m=ln.match(/^[-*]\\s+(.*)$/)){if(inol){html+="</ol>";inol=false;}if(!inul){html+="<ul>";inul=true;}html+="<li>"+inline(m[1])+"</li>";continue;}
  if(!trim){closeLists();continue;}
  html+="<p>"+inline(ln)+"</p>";
 }
 closeLists();closeTbl();
 return html;
}
function stream(el,full,meta){
 let i=0;el.textContent="";
 let car=document.createElement("span");car.className="caret";
 let iv=setInterval(()=>{i+=24;el.textContent=full.slice(0,i);el.appendChild(car);
  try{$("msgs").scrollTop=1e9;}catch(e){}
  if(i>=full.length){clearInterval(iv);el._raw=full;el.innerHTML="";
   let who=document.createElement("div");who.className="who";who.textContent="▲ "+(CUR||"assistant");el.appendChild(who);
   let bd=document.createElement("div");bd.innerHTML=renderMd(full);while(bd.firstChild)el.appendChild(bd.firstChild);
   let m=document.createElement("div");m.className="meta";m.textContent=meta;el.appendChild(m);
   let cb=document.createElement("button");cb.className="cpb2";cb.textContent="⧉ کوپی نامە";cb.onclick=function(){cpMsg(this);};el.appendChild(cb);
   try{$("msgs").scrollTop=1e9;}catch(e){}}},25);
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
