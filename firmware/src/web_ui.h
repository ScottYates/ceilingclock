#pragma once
#include <Arduino.h>

// Single-page settings UI served at http://ceilingclock.local/
static const char INDEX_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ceiling Clock</title>
<style>
:root{--bg:#111316;--card:#1b1e23;--line:#2b3038;--fg:#e7e9ec;--mut:#8b939e;--acc:#ff8a3d;--ok:#4cc38a;--bad:#e5484d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,-apple-system,sans-serif}
main{max-width:640px;margin:auto;padding:12px}
h1{font-size:20px;margin:8px 0 12px}h2{font-size:15px;margin:0 0 10px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px}
.big{font-size:44px;font-weight:600;font-variant-numeric:tabular-nums}
.mut{color:var(--mut);font-size:13px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}
label{display:flex;flex-direction:column;font-size:12px;color:var(--mut);gap:3px}
input,select{background:#0f1114;color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:7px;font:inherit}
input[type=number]{width:72px}input[type=time]{width:120px}
button{background:#2a2f37;color:var(--fg);border:0;border-radius:8px;padding:9px 13px;font:inherit;cursor:pointer}
button.p{background:var(--acc);color:#111;font-weight:600}button.d{background:transparent;color:var(--bad);border:1px solid #4a2a2c}
.days{display:flex;gap:4px}.days span{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;border:1px solid var(--line);cursor:pointer;user-select:none;font-size:13px}
.days span.on{background:var(--acc);color:#111;border-color:var(--acc)}
.alarm{border-top:1px solid var(--line);padding-top:10px;margin-top:10px}.alarm:first-child{border:0;margin:0;padding:0}
.sw{flex-direction:row;align-items:center;gap:6px;color:var(--fg);font-size:14px}
#ringbar{display:none;background:var(--acc);color:#111}#ringbar button{background:#111;color:var(--fg)}
.pill{display:inline-block;padding:2px 8px;border-radius:99px;font-size:12px;background:#2a2f37}.pill.ok{background:#173a2b;color:var(--ok)}.pill.bad{background:#3d1d1f;color:var(--bad)}
#live{display:grid;grid-template-columns:1.5fr 1fr;gap:12px}
#live .lbl{font-size:12px;color:var(--mut);margin:0 0 4px}
#ceil{width:100%;height:auto;border-radius:8px;background:#07080b;display:block;image-rendering:pixelated}
.panel2{background:#0f1114;border:1px solid var(--line);border-radius:8px;padding:10px;margin-bottom:10px}
#front svg,#ring svg{display:block;width:100%;height:auto}
.vbar{height:6px;background:#2b3038;border-radius:3px;overflow:hidden;margin-top:6px}.vbar i{display:block;height:100%;background:var(--acc);width:0}
@media(max-width:560px){#live{grid-template-columns:1fr}}
#toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:#000;padding:8px 14px;border-radius:8px;display:none}
</style></head><body><main>
<h1>Ceiling Clock</h1>

<div class="card" id="ringbar"><div class="row" style="justify-content:space-between">
<b id="ringtxt">Alarm</b><span><button id="bSnz" onclick="act('snooze')">Snooze</button> <button onclick="act('dismiss')">Dismiss</button></span></div></div>

<div class="card">
<div class="big" id="clock">--:--</div>
<div class="mut" id="date"></div>
<div class="row"><span class="pill" id="sync">sync</span><span class="pill" id="rtc">RTC</span><span class="mut" id="next"></span></div>
<div class="row">
<button onclick="act('front')" id="bFront">Front display</button>
<button onclick="act('proj')" id="bProj">Projector</button>
<button onclick="act('flip').then(load)" id="bFlip">Flip projection</button>
<button onclick="act('peek')">Show 15 s</button>
<button onclick="act('resync')">Resync time</button></div>
</div>

<div class="card"><h2>Right now</h2>
<div id="live">
 <div><p class="lbl" id="ceilLbl">On the ceiling</p><canvas id="ceil" width="336" height="192"></canvas></div>
 <div>
  <div class="panel2" id="front"><p class="lbl" id="frontLbl">Front display</p><svg viewBox="0 0 200 60" id="frontSvg"></svg></div>
  <div class="panel2" id="ring"><p class="lbl" id="ringLbl">Sunrise light</p><svg viewBox="0 0 120 120" id="ringSvg" style="max-width:120px;margin:auto"></svg></div>
  <div class="panel2"><p class="lbl">Sound</p><div id="spk">Silent</div><div class="vbar"><i id="vbar"></i></div></div>
 </div>
</div></div>

<div class="card"><h2>Alarms</h2><div id="alarms"></div>
<div class="row" style="margin-top:12px"><button onclick="addAlarm()">+ Add alarm</button><button class="p" onclick="save()">Save</button></div></div>

<div class="card"><h2>Displays</h2>
<div class="row"><b style="width:100%">Front display</b>
<label>Mode<select id="f_mode"></select></label>
<label>Day brightness (0-7)<input type="number" min="0" max="7" id="f_day"></label>
<label>Night brightness (0-7)<input type="number" min="0" max="7" id="f_night"></label></div>
<div class="row"><b style="width:100%">Ceiling projector</b>
<label>Mode<select id="p_mode"></select></label>
<label>Day %<input type="number" min="0" max="100" id="p_day"></label>
<label>Night %<input type="number" min="0" max="100" id="p_night"></label>
<label>LCD contrast<input type="number" min="0" max="127" id="contrast"></label></div>
<div class="row">
<label class="sw"><input type="checkbox" id="mx">Mirror left/right</label>
<label class="sw"><input type="checkbox" id="my">Mirror top/bottom</label>
<label class="sw"><input type="checkbox" id="ud">Upside down (turn 180°)</label>
<label class="sw"><input type="checkbox" id="inv">Bright digits on dark</label></div>
<div class="row"><label class="sw"><input type="checkbox" id="showAlarm">Turn displays on while an alarm rings</label></div>
<div class="row"><b style="width:100%">Night</b>
<label>Starts<input type="time" id="nStart"></label><label>Ends<input type="time" id="nEnd"></label>
<label class="sw"><input type="checkbox" id="useLdr">Also when room is dark</label>
<label>Dark below<input type="number" min="0" max="4095" id="ldrT"></label><span class="mut">sensor now: <span id="ldr">-</span></span></div>
<div class="row"><label>Sunrise max brightness (0-255)<input type="number" min="0" max="255" id="sunMax"></label></div>
<div class="row"><button class="p" onclick="save()">Save</button></div></div>

<div class="card"><h2>Sounds</h2><div id="sounds"></div>
<div class="row"><input type="file" id="upfile" accept=".mp3,.wav,.m4a,.aac,.flac,.ogg,.opus"><button onclick="upload()">Upload</button></div>
<div class="mut" id="fs"></div></div>

<div class="card"><h2>Time &amp; system</h2>
<div class="row"><label>Time zone (POSIX)<input id="tz" style="width:240px"></label><label>NTP server<input id="ntp"></label></div>
<div class="row"><label class="sw"><input type="checkbox" id="h24">24-hour clock</label></div>
<div class="row"><label>Web password (blank = none, user "admin")<input type="password" id="pw"></label></div>
<div class="row"><button class="p" onclick="save()">Save</button></div>
<div class="row"><label>Firmware update (.bin)<input type="file" id="fwfile" accept=".bin"></label><button onclick="fwUpdate()">Update</button></div>
<div class="mut" id="sys"></div></div>
</main><div id="toast"></div>
<script>
const $=id=>document.getElementById(id);let C=null,S=[];const DN=['S','M','T','W','T','F','S'];
const MODES=['Always on','Always off','Only at night','Only in daytime'];
const toast=t=>{$('toast').textContent=t;$('toast').style.display='block';setTimeout(()=>$('toast').style.display='none',2500)};
const hm=m=>String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
const mh=s=>{const[a,b]=s.split(':');return(+a)*60+(+b)};
async function act(d,extra=''){await fetch('/api/action?do='+d+extra,{method:'POST'});poll()}
function fmtT(ep){const d=new Date(ep*1000);return d.toLocaleString([], {weekday:'short',hour:'numeric',minute:'2-digit',hour12:!C.hour24})}
// ---- live view
const SEG=[0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F];
function segDigit(x,d,on,col){const P=[[4,0,26,5],[27,3,5,22],[27,30,5,22],[4,51,26,5],[0,30,5,22],[0,3,5,22],[4,25.5,26,5]];
 const m=d<0?0:(d==10?0x40:SEG[d]);return P.map((p,i)=>`<rect x="${x+p[0]}" y="${4+p[1]}" width="${p[2]}" height="${p[3]}" rx="2" fill="${(m>>i)&1&&on?col:'#2a0d0d'}"/>`).join('')}
function drawFront(s,lv){const d=new Date(s.now*1000);let h=d.getHours(),m=d.getMinutes();const h24=C&&C.hour24;
 if(!h24){h%=12;if(!h)h=12}const on=lv.frontOn,col=`rgba(255,40,30,${0.35+0.65*lv.frontBright/7})`;
 const dg=s.timeValid?[(h24||h>=10)?Math.floor(h/10):-1,h%10,Math.floor(m/10),m%10]:[10,10,10,10];
 $('frontSvg').innerHTML=`<rect width="200" height="60" rx="6" fill="#0a0505"/>`+segDigit(14,dg[0],on,col)+segDigit(52,dg[1],on,col)+
  `<circle cx="99" cy="22" r="3" fill="${on?col:'#2a0d0d'}"/><circle cx="99" cy="40" r="3" fill="${on?col:'#2a0d0d'}"/>`+segDigit(114,dg[2],on,col)+segDigit(152,dg[3],on,col);
 $('frontLbl').textContent='Front display · '+(on?'on, brightness '+lv.frontBright+'/7':'off (dark)')}
function drawRing(lv){const [r,g,b]=lv.ring,mx=Math.max(r,g,b);let dots='';
 const col=mx?`rgb(${Math.round(r*255/mx)},${Math.round(g*255/mx)},${Math.round(b*255/mx)})`:'#1c1f24',op=mx?Math.max(.3,mx/255):1;
 for(let i=0;i<16;i++){const a=i/16*2*Math.PI;dots+=`<circle cx="${60+42*Math.cos(a)}" cy="${60+42*Math.sin(a)}" r="7" fill="${col}" opacity="${op}"/>`}
 $('ringSvg').innerHTML=(mx?`<circle cx="60" cy="60" r="50" fill="${col}" opacity="${op*0.25}"/>`:'')+dots;
 $('ringLbl').textContent='Sunrise light · '+(mx?Math.round(lv.sunrise*100)+'% of sunrise':'off')}
function drawCeil(lv){const c=$('ceil'),x=c.getContext('2d');x.fillStyle='#07080b';x.fillRect(0,0,336,192);
 if(!lv.projOn||!lv.projPct){x.fillStyle='#4a4f57';x.font='15px system-ui';x.textAlign='center';x.fillText('Projector off',168,100);$('ceilLbl').textContent='On the ceiling · projector off';return}
 const a=0.3+0.7*lv.projPct/100,h=lv.lcd||'';
 const ud=lv.upsideDown;
 for(let y=0;y<48;y++)for(let i=0;i<84;i++){const b=parseInt(h.substr((y*11+(i>>3))*2,2),16),bit=(b>>(7-(i&7)))&1,lit=lv.invert?bit:!bit,X=ud?83-i:i,Y=ud?47-y:y;
  if(lit){x.fillStyle=`rgba(255,214,150,${a})`;x.fillRect(X*4,Y*4,4,4)}else if(lv.invert){x.fillStyle=`rgba(255,214,150,${a*0.05})`;x.fillRect(X*4,Y*4,4,4)}}
 $('ceilLbl').textContent='On the ceiling · '+lv.projPct+'% brightness'+(ud?' · upside down':'')}
function drawSpk(s,lv){const v=lv.vol||0,st=s.stream||{};let t;
 if(st.state=='connecting')t='Connecting to stream…';
 else if(s.playing)t=(s.ring=='ringing'?(s.source=='backup'?'Backup sound playing':s.source=='stream'?'Alarm stream playing':'Alarm sound playing'):'Preview playing')+(s.source=='stream'&&st.title?' · '+st.title:'')+' · volume '+v+'/21';
 else t=s.ring=='snoozed'?'Snoozed':s.ring=='idle'&&st.state=='failed'?'Stream failed: '+st.note:'Silent';
 if(s.source=='backup'&&st.note)t+=' (stream: '+st.note+')';
 $('spk').textContent=t;
 $('vbar').style.width=(s.playing?v/21*100:0)+'%'}
function drawLive(s){if(!s.live)return;drawCeil(s.live);drawFront(s,s.live);drawRing(s.live);drawSpk(s,s.live)}
async function poll(){try{const s=await(await fetch('/api/state')).json();drawLive(s);
 const d=new Date(s.now*1000);
 $('clock').textContent=s.timeValid?d.toLocaleTimeString([], {hour:'numeric',minute:'2-digit',hour12:C?!C.hour24:true}):'--:--';
 $('date').textContent=s.timeValid?d.toDateString():'Waiting for time';
 const ago=s.lastSync?Math.round((s.now-s.lastSync)/60):null;
 $('sync').textContent=ago===null?'not synced yet':'synced '+(ago<1?'just now':ago+' min ago');$('sync').className='pill '+(ago!==null&&ago<180?'ok':'bad');
 $('rtc').textContent=s.rtc?'RTC backup ok':'no RTC';$('rtc').className='pill '+(s.rtc?'ok':'bad');
 $('next').textContent=s.nextAt?'Next: '+s.nextLabel+' '+fmtT(s.nextAt):'No alarms set';
 $('bFront').textContent='Front display: '+(s.frontOn?'on':'off');$('bProj').textContent='Projector: '+(s.projOn?'on':'off');
 if(s.live)$('bFlip').textContent='Flip projection'+(s.live.upsideDown?' (now upside down)':'');
 $('ldr').textContent=s.ldr+(s.night?' (night)':'');
 $('ringbar').style.display=s.ring=='idle'?'none':'block';$('bSnz').style.display=s.ring=='ringing'?'':'none';
 $('ringtxt').textContent=s.ring=='ringing'?(s.ringLabel||'Alarm')+' ringing':'Snoozed until '+fmtT(s.snoozeUntil);
 $('fs').textContent='Storage: '+(s.fsUsed/1048576).toFixed(1)+' of '+(s.fsTotal/1048576).toFixed(1)+' MB used';
 $('sys').textContent='Firmware '+s.fw+(s.fwBuild?' (built '+s.fwBuild+')':'')+' · IP '+s.ip+' · Wi-Fi '+s.rssi+' dBm';
}catch(e){}}
function soundOpts(sel){return S.map(x=>`<option ${x.path==sel?'selected':''} value="${x.path}">${x.path.replace('/sounds/','')}</option>`).join('')}
function renderAlarms(){$('alarms').innerHTML=C.alarms.map((a,i)=>`<div class="alarm">
<div class="row"><label class="sw"><input type="checkbox" ${a.enabled?'checked':''} onchange="C.alarms[${i}].enabled=this.checked">On</label>
<input value="${a.label.replace(/"/g,'&quot;')}" oninput="C.alarms[${i}].label=this.value" style="flex:1">
<input type="time" value="${hm(a.hour*60+a.minute)}" onchange="const m=mh(this.value);C.alarms[${i}].hour=Math.floor(m/60);C.alarms[${i}].minute=m%60"></div>
<div class="row"><div class="days">${DN.map((n,b)=>`<span class="${a.days>>b&1?'on':''}" onclick="C.alarms[${i}].days^=${1<<b};renderAlarms()">${n}</span>`).join('')}</div>
<span class="mut">${a.days?'':'One time'}</span></div>
<div class="row"><label style="flex:1">Stream or podcast URL (optional)<input type="url" placeholder="https://… internet radio, MP3 link or podcast feed" value="${(a.stream||'').replace(/"/g,'&quot;')}" onchange="C.alarms[${i}].stream=this.value.trim();renderAlarms()"></label></div>
${a.stream?'<div class="mut" style="margin:-4px 0 6px">Plays this instead of the sound file. A podcast feed plays its newest episode. If the stream hasn\'t started within 25 seconds or drops out, the backup sound rings instead.</div>':''}
<div class="row"><label>${a.stream?'Backup sound':'Sound'}<select onchange="C.alarms[${i}].sound=this.value">${soundOpts(a.sound)}</select></label>
<label>Volume (0-21)<input type="number" min="0" max="21" value="${a.volume}" onchange="C.alarms[${i}].volume=+this.value"></label>
<label>Fade-in (s)<input type="number" min="0" max="1800" value="${a.rampSec}" onchange="C.alarms[${i}].rampSec=+this.value"></label></div>
<div class="row"><label>Sunrise (min before)<input type="number" min="0" max="60" value="${a.sunriseMin}" onchange="C.alarms[${i}].sunriseMin=+this.value"></label>
<label>Snooze (min)<input type="number" min="1" max="60" value="${a.snoozeMin}" onchange="C.alarms[${i}].snoozeMin=+this.value"></label>
<label>Auto-stop (min)<input type="number" min="1" max="120" value="${a.maxRingMin}" onchange="C.alarms[${i}].maxRingMin=+this.value"></label></div>
<div class="row"><button onclick="testSound(${i})">${a.stream?'Preview stream':'Preview sound'}</button><button onclick="act('stop')">Stop</button>
<button onclick="save().then(()=>act('ring','&id=${i}'))">Ring now</button>
<button onclick="save().then(()=>act('skip','&id=${i}')).then(load)">${a.skipNext?'Un-skip next':'Skip next'}</button>
<button class="d" onclick="C.alarms.splice(${i},1);renderAlarms()">Delete</button></div></div>`).join('')||'<div class="mut">No alarms yet.</div>'}
function addAlarm(){if(C.alarms.length>=8)return toast('Max 8 alarms');C.alarms.push({enabled:true,hour:7,minute:0,days:62,skipNext:false,label:'Alarm',sound:'/sounds/beep.wav',stream:'',volume:12,rampSec:60,sunriseMin:15,snoozeMin:9,maxRingMin:30});renderAlarms()}
function testSound(i){const a=C.alarms[i];act('test',(a.stream?'&stream='+encodeURIComponent(a.stream):'&sound='+encodeURIComponent(a.sound))+'&vol='+a.volume)}
function fill(){const opt=MODES.map((m,i)=>`<option value="${i}">${m}</option>`).join('');$('f_mode').innerHTML=opt;$('p_mode').innerHTML=opt;
 $('f_mode').value=C.front.mode;$('f_day').value=C.front.dayBright;$('f_night').value=C.front.nightBright;
 $('p_mode').value=C.proj.mode;$('p_day').value=C.proj.dayBright;$('p_night').value=C.proj.nightBright;
 $('contrast').value=C.lcdContrast;$('mx').checked=C.projMirrorX;$('my').checked=C.projMirrorY;$('inv').checked=C.projInvert;$('ud').checked=C.projUpsideDown;
 $('showAlarm').checked=C.showOnAlarm;$('nStart').value=hm(C.nightStart);$('nEnd').value=hm(C.nightEnd);
 $('useLdr').checked=C.useLdr;$('ldrT').value=C.ldrThreshold;$('sunMax').value=C.sunriseMaxBright;
 $('tz').value=C.tz;$('ntp').value=C.ntp;$('h24').checked=C.hour24;$('pw').value=C.webPassword;renderAlarms()}
function collect(){C.front={mode:+$('f_mode').value,dayBright:+$('f_day').value,nightBright:+$('f_night').value};
 C.proj={mode:+$('p_mode').value,dayBright:+$('p_day').value,nightBright:+$('p_night').value};
 C.lcdContrast=+$('contrast').value;C.projMirrorX=$('mx').checked;C.projMirrorY=$('my').checked;C.projInvert=$('inv').checked;C.projUpsideDown=$('ud').checked;
 C.showOnAlarm=$('showAlarm').checked;C.nightStart=mh($('nStart').value);C.nightEnd=mh($('nEnd').value);
 C.useLdr=$('useLdr').checked;C.ldrThreshold=+$('ldrT').value;C.sunriseMaxBright=+$('sunMax').value;
 C.tz=$('tz').value.trim();C.ntp=$('ntp').value.trim();C.hour24=$('h24').checked;C.webPassword=$('pw').value}
async function save(){collect();const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(C)});
 if(r.ok){C=await r.json();fill();toast('Saved')}else toast('Save failed')}
async function loadSounds(){S=await(await fetch('/api/sounds')).json();
 $('sounds').innerHTML=S.map(x=>`<div class="row" style="justify-content:space-between"><span>${x.path.replace('/sounds/','')} <span class="mut">${(x.size/1024).toFixed(0)} KB</span></span>
 <span><button onclick="act('test','&vol=12&sound='+encodeURIComponent('${x.path}'))">Play</button> <button onclick="act('stop')">Stop</button>
 ${x.path.endsWith('/beep.wav')?'':`<button class="d" onclick="delSound('${x.path.replace('/sounds/','')}')">Delete</button>`}</span></div>`).join('')}
async function upload(){const f=$('upfile').files[0];if(!f)return;const fd=new FormData();fd.append('file',f,f.name);toast('Uploading…');
 const r=await fetch('/api/sounds',{method:'POST',body:fd});toast(r.ok?'Uploaded':await r.text());await loadSounds();renderAlarms()}
async function delSound(n){if(!confirm('Delete '+n+'?'))return;await fetch('/api/sounds/delete?name='+encodeURIComponent(n),{method:'POST'});await loadSounds();renderAlarms()}
async function fwUpdate(){const f=$('fwfile').files[0];if(!f)return;const fd=new FormData();fd.append('fw',f,f.name);toast('Updating, do not unplug…');
 const r=await fetch('/update',{method:'POST',body:fd});toast(await r.text())}
async function load(){C=await(await fetch('/api/config')).json();await loadSounds();fill()}
load().then(poll);setInterval(poll,1000);
</script></body></html>)rawliteral";
