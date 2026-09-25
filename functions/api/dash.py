"""GET / — AYAI-VPX dashboard (RTL Arabic, self-contained). NO Fly."""
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import providers
import usage

PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AYAI-VPX — لوحة التحكم</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b1020;color:#e8ecf8;font-family:Tahoma,Arial,sans-serif;padding:16px;max-width:1100px;margin:auto}
h1{font-size:22px;margin-bottom:4px}
.sub{color:#8b93b0;font-size:13px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:18px}
.card{background:#141b34;border:1px solid #263056;border-radius:12px;padding:12px;text-align:center}
.card .v{font-size:26px;font-weight:bold;color:#7cf5c4}
.card .l{font-size:12px;color:#8b93b0;margin-top:4px}
h2{font-size:17px;margin:18px 0 10px;color:#9fd0ff}
table{width:100%;border-collapse:collapse;font-size:13px;background:#141b34;border-radius:12px;overflow:hidden}
th,td{padding:8px 10px;border-bottom:1px solid #263056;text-align:right}
th{background:#1a2340;color:#9fd0ff}
tr:last-child td{border-bottom:none}
.bar{height:8px;background:#263056;border-radius:6px;overflow:hidden;min-width:90px}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#2dd4a7,#7cf5c4);border-radius:6px}
.badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:20px;background:#263056;color:#cfe3ff}
.badge.auto{background:#123f2c;color:#7cf5c4}
.badge.off{background:#3f1a1a;color:#ff9d9d}
.ok{color:#7cf5c4}.bad{color:#ff9d9d}
#q{width:100%;padding:10px;border-radius:10px;border:1px solid #263056;background:#141b34;color:#fff;font-size:14px;margin-bottom:10px}
.src{margin-bottom:12px}
.src h3{font-size:14px;color:#ffd88a;margin-bottom:6px;cursor:pointer}
.models{display:flex;flex-wrap:wrap;gap:6px}
.models span{font-size:12px;background:#1a2340;border:1px solid #2c3a63;padding:4px 10px;border-radius:16px;display:inline-flex;align-items:center;gap:6px}
.models button{background:none;border:none;color:#ffd88a;font-size:12px;padding:2px 4px;cursor:pointer}
.tres{font-size:11px}
@media(max-width:700px){table{display:block;overflow-x:auto}h1{font-size:18px}}
pre{background:#141b34;border:1px solid #263056;border-radius:12px;padding:12px;font-size:12px;overflow-x:auto;direction:ltr;text-align:left;color:#b9f5d6}
.foot{margin-top:20px;font-size:12px;color:#8b93b0;text-align:center}
</style>
</head>
<body>
<h1>🚀 AYAI-VPX — لوحة التحكم</h1>
<div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap"><a href="/playground" style="display:inline-block;background:#7c5cf0;color:#fff;padding:8px 18px;border-radius:10px;text-decoration:none;font-weight:bold">💬 ساحة التجربة</a><button id="syncb" onclick="doRefresh()" style="background:#123f2c;color:#7cf5c4;border:1px solid #2dd4a7;padding:8px 18px;border-radius:10px;font-weight:bold;font-size:14px">🔄 مزامنة أحدث البيانات</button></div>
<div class="sub" id="upd">جاري التحميل…</div>
<div class="grid" id="top"></div>
<h2>🏊 مجمعات الحسابات</h2>
<table><thead><tr><th>المجمع</th><th>العدد الكلي</th><th>النشط ✅</th><th>الهدف</th><th>اليوم</th><th>المولد</th><th>المستوى</th></tr></thead>
<tbody id="pools"></tbody></table>
<h2>🔑 المفاتيح</h2>
<table><tbody id="keys"></tbody></table>
<h2>🔄 المزامنة والحماية</h2>
<table><tbody id="sync"></tbody></table>
<h2>📡 حالة المصادر</h2>
<table><thead><tr><th>المصدر</th><th>نماذج حية</th></tr></thead><tbody id="srcs"></tbody></table>
<h2>🤖 النماذج (<span id="mc">0</span>)</h2>
<input id="q" placeholder="🔍 بحث عن نموذج…">
<div id="models"></div>
<h2>🔌 نقاط النهاية</h2>
<pre>GET  /v1/models
POST /v1/chat/completions   {"model":"...","messages":[{"role":"user","content":"..."}]}
GET  /api/status
GET  /api/cron  (Appwrite */2min + Vercel backup 2x/day)</pre>
<div class="foot">ayai-vpx • يعمل ذاتيا بدون Fly • تحديث تلقائي كل 60 ثانية</div>
<script>
let ALL=[];
function ago(t){if(!t)return "—";let s=Math.floor(Date.now()/1000-t);if(s<90)return "قبل "+s+" ث";if(s<5400)return "قبل "+Math.floor(s/60)+" د";return "قبل "+Math.floor(s/3600)+" س";}
async function load(){
 let t0=Date.now(),updEl=document.getElementById("upd");
 updEl.textContent="جاري التحميل…";
 let tick=setInterval(()=>{updEl.textContent="جاري التحميل… "+Math.floor((Date.now()-t0)/1000)+" ث";},1000);
 let s=null,m=null,errs=[];
 try{
  let rs=await Promise.allSettled([
   fetch("/api/status",{signal:AbortSignal.timeout(45000)}).then(r=>{if(!r.ok)throw new Error("الحالة "+r.status);return r.json();}),
   fetch("/v1/models",{signal:AbortSignal.timeout(45000)}).then(r=>{if(!r.ok)throw new Error("النماذج "+r.status);return r.json();})
  ]);
  clearInterval(tick);
  if(rs[0].status==="fulfilled")s=rs[0].value;else errs.push(rs[0].reason);
  if(rs[1].status==="fulfilled")m=rs[1].value;else errs.push(rs[1].reason);
  if(!s&&!m)throw new Error(errs.join(" / ")||"فشل الاتصال");
  if(m)ALL=(m.data||[]).map(x=>x.id);
  updEl.textContent="آخر تحديث: "+new Date().toLocaleString("ar")+(s?(s.ok?" • API يعمل ✅":" • API متوقف ❌"):"")+(errs.length?" • ⚠️ "+errs.join(" / "):"");
  if(s){
  document.getElementById("top").innerHTML=
   card(s.models,"نموذج")+
   card(Object.values(s.pools||{}).reduce((a,p)=>a+(p.n||0),0),"إجمالي الحسابات")+
   card(Object.values(s.pools||{}).reduce((a,p)=>a+(p.alive||0),0),"حساب نشط ✅")+
   card(s.proxies||0,"بروكسي نشط")+
   card(Object.keys(s.by_source||{}).length,"مصدر")+
   card(((s.usage||{}).inv_pct||0)+"%","حد الاستدعاء الشهري");
  let ph="";
  for(let k of Object.keys(s.pools||{})){
   let p=s.pools[k],t=p.target||1000,pc=Math.min(100,Math.round(100*(p.alive||0)/t));
   let auto=(p.minter&&p.minter!=="single-key"&&p.minter!=="fly-only");
   ph+="<tr><td><b>"+k+"</b></td><td>"+p.n+"</td><td class='ok'><b>"+(p.alive||0)+"</b></td><td>"+t+"</td><td>"+(p.today||0)+"</td>"+
    "<td><span class='badge "+(auto?"auto":(p.minter==="fly-only"?"off":""))+"'>"+(p.minter||"?")+"</span></td>"+
    "<td><div class='bar'><i style='width:"+pc+"%'></i></div></td></tr>";
  }
  document.getElementById("pools").innerHTML=ph;
  let kh="";
  for(let k of Object.keys(s.keys||{}))
   kh+="<tr><td>"+k+"</td><td class='"+(s.keys[k]?"ok":"bad")+"'>"+(s.keys[k]?"✅ مضبوط":"❌ ناقص")+"</td></tr>";
  document.getElementById("keys").innerHTML=kh;
  document.getElementById("sync").innerHTML=
   "<tr><td>آخر مزامنة للنماذج</td><td>"+ago(s.sync_t)+"</td></tr>"+
   "<tr><td>آخر تشغيل cron</td><td>"+ago(s.cron_t)+" (#"+(s.cron_n||"?")+")</td></tr>"+
   "<tr><td>البروكسيات النشطة</td><td>"+(s.proxies||0)+"</td></tr>"+
   "<tr><td>مخزن البيانات</td><td>"+(s.kv_backend||"?")+"</td></tr>"+
   "<tr><td>عداد الأعطال</td><td>"+(s.failctr||0)+"</td></tr>"+
   "<tr><td>حالة مخزن GitHub</td><td>"+((s.gist_backoff_s||0)>0?("⏳ حظر مؤقت "+s.gist_backoff_s+" ث"):"✅ سليم")+"</td></tr>"+
   "<tr><td>آخر cron</td><td>"+(s.cron_last&&s.cron_last.t?("تشغيل #"+s.cron_last.run+" • نماذج "+s.cron_last.models+" • مزامنة "+s.cron_last.sync_ok+" • سك "+s.cron_last.minted+" • "+s.cron_last.sec+"ث"):"—")+"</td></tr>"+
   "<tr><td>استخدام الشهر ("+((s.usage||{}).month||"—")+")</td><td>"+((s.usage||{}).inv||0)+" دعوة ("+((s.usage||{}).inv_pct||0)+"%) • "+((s.usage||{}).gb||0)+"GB ("+((s.usage||{}).gb_pct||0)+"%)</td></tr>";
  let sh="";
  for(let k of Object.keys(s.msync||{}).sort())
   sh+="<tr><td>"+k.replace(/_ok$/,"")+"</td><td>"+s.msync[k]+"</td></tr>";
  document.getElementById("srcs").innerHTML=sh||"<tr><td>—</td><td>—</td></tr>";
  }
  if(m)renderModels("");
 }catch(e){try{clearInterval(tick);}catch(_){}document.getElementById("upd").innerHTML="❌ خطأ في التحميل: "+esc(String((e&&e.message)||e))+" <button onclick='load()' style='background:#7c5cf0;color:#fff;padding:6px 16px;border-radius:8px;border:none;font-weight:bold'>إعادة المحاولة 🔄</button>";}
}
function card(v,l){return "<div class='card'><div class='v'>"+v+"</div><div class='l'>"+l+"</div></div>";}
let COLL={};
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function renderModels(q){
 q=(q||"").toLowerCase();
 let groups={};
 for(let i=0;i<ALL.length;i++){
  let id=ALL[i];
  if(q&&id.toLowerCase().indexOf(q)<0)continue;
  let src=id.split("-")[0];
  (groups[src]=groups[src]||[]).push(i);
 }
 document.getElementById("mc").textContent=ALL.length;
 let h="";
 for(let src of Object.keys(groups).sort()){
  let open=COLL[src]!==false;
  h+="<div class='src'><h3 data-src='"+src+"'>"+(open?"▼ ":"▶ ")+src+" ("+groups[src].length+")</h3>";
  if(open){
   h+="<div class='models'>"+groups[src].map(i=>"<span>"+esc(ALL[i])+" <span class='tres' id='d"+i+"'></span><button data-td='"+i+"' title='اختبار'>⚡</button></span>").join("")+"</div>";
  }
  h+="</div>";
 }
 document.getElementById("models").innerHTML=h||"لا نتائج";
}
document.getElementById("models").addEventListener("click",e=>{
 let t=e.target;
 if(t.dataset&&t.dataset.td!==undefined){testD(+t.dataset.td);return;}
 let h=t.closest?t.closest("h3[data-src]"):null;
 if(h){let s=h.dataset.src;COLL[s]=COLL[s]===false;renderModels(document.getElementById("q").value);}
});
function K(){return localStorage.vpxk||"";}
async function testD(i){
 let id=ALL[i],s=document.getElementById("d"+i);
 if(s)s.textContent="…";
 try{
  let r=await fetch("/api/play",{method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({key:K(),model:id,direct:true,messages:[{role:"user",content:"reply with exactly: OK-KURD"}]})});
  let d=await r.json();
  let ok=r.ok&&(d.text||"").indexOf("OK-KURD")>=0;
  if(s){s.textContent=(ok?"✅ ":"❌ ")+(d.seconds||"")+"s";s.style.color=ok?"#7cf5c4":"#ff9d9d";}
 }catch(e){if(s){s.textContent="❌";s.style.color="#ff9d9d";}}
}
async function doRefresh(){
 let b=document.getElementById("syncb");b.disabled=true;b.textContent="⏳ جاري المزامنة…";
 try{
  let r=await fetch("/api/refresh",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:K()})});
  let d=await r.json();
  alert(r.ok?("تم: "+d.sync_ok+"/"+d.sync_total+" مصدر • "+d.models+" نموذج"):("فشل: "+(d.error||r.status)));
  if(r.ok)load();
 }catch(e){alert("خطأ: "+e);}
 b.disabled=false;b.textContent="🔄 مزامنة أحدث البيانات";
}
document.getElementById("q").addEventListener("input",e=>renderModels(e.target.value));
load();setInterval(load,60000);
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
        try:
            providers.cron_slice()
        except Exception:
            pass
        return self._send(200, PAGE, "text/html; charset=utf-8")
