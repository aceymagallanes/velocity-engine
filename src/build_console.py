#!/usr/bin/env python3
"""Build the Velocity Console — a functional, interactive lead-triage app.

Unlike the narrative dashboard, this is a working tool: a filterable/sortable
lead queue, per-lead BANT detail + routing, live-updating KPIs, and a real-time
scorer that runs the actual BANT rules engine in the browser on any message you
type. Emits a single self-contained data/console.html (no dependencies).
"""
import json, statistics
from collections import Counter

SRC = "data/leads_scored.json"
OUT = "docs/console.html"
SLA = {"high": 5, "medium": 60, "low": 1440}
SRC_LABEL = {"demo_request": "Demo request", "free_trial": "Free trial",
             "content_webinar": "Webinar", "paid_ad": "Paid ad", "referral": "Referral"}

with open(SRC) as f:
    data = json.load(f)
leads = data["leads"]

slim = [{
    "id": l["lead_id"], "created": l["created_at"],
    "source": l["source"], "source_label": SRC_LABEL.get(l["source"], l["source"]),
    "size": l["company_size_band"], "role": l["contact_role"], "region": l["region"],
    "msg": l["stated_need"], "bant": l.get("bant", {}), "total": l.get("bant_total", 0),
    "priority": l["priority"], "sla": SLA[l["priority"]],
    "reason": l.get("bant_reason", ""),
    "asis": l["as_is_first_response_minutes"], "contacted": l["as_is_contacted"],
} for l in leads]

payload = {"leads": slim, "sla": SLA,
           "engine": data.get("_meta", {}).get("scoring", {}).get("engine", "Velocity rules pass")}
DATA_JSON = json.dumps(payload).replace("</", "<\\/")

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Velocity Console — Live Lead Triage</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --emerald:#0D6B4F;--forest:#094D3A;--navy:#0A1D37;--gold:#D4AF37;--slate:#475569;
  --ink:#0B1620;--muted:#6B7B82;--line:#E6ECEA;--bg:#F4F6F5;--card:#fff;--lowc:#9FB0AE;
  --head:'Playfair Display',Georgia,serif;--body:'Montserrat',-apple-system,Segoe UI,sans-serif;
  --sh:0 6px 20px rgba(9,29,55,.08);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--body);color:var(--ink);background:var(--bg);font-size:14px;-webkit-font-smoothing:antialiased}
.num{font-variant-numeric:tabular-nums}
button{font-family:var(--body);cursor:pointer}

/* header */
header{background:linear-gradient(120deg,#0D6B4F,#094D3A 55%,#0A1D37);color:#fff;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px;position:sticky;top:0;z-index:30}
.logo{font-family:var(--head);font-weight:700;font-size:20px;letter-spacing:.01em}
.logo .g{color:var(--gold)}
.logo small{display:block;font-family:var(--body);font-weight:500;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#bfe0d3;margin-top:2px}
.hbtns{display:flex;gap:10px;align-items:center}
.badge{font-size:11px;font-weight:600;letter-spacing:.06em;color:#cfe6dd;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);padding:6px 12px;border-radius:100px}
.btn{border:0;border-radius:10px;font-weight:600;font-size:13px;padding:10px 16px;transition:.2s}
.btn.gold{background:linear-gradient(135deg,#E7C658,#D4AF37);color:var(--navy)}
.btn.gold:hover{filter:brightness(1.05);transform:translateY(-1px)}
.btn.ghost{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.25)}
.btn.pri{background:var(--emerald);color:#fff}.btn.pri:hover{background:var(--forest)}
.btn.sm{padding:7px 12px;font-size:12px;border-radius:8px}
a.btn{text-decoration:none;display:inline-flex;align-items:center}

/* kpi strip */
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:18px 24px}
@media(max-width:900px){.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:560px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:var(--sh)}
.kpi .v{font-family:var(--head);font-weight:700;font-size:26px;line-height:1;color:var(--navy)}
.kpi .v.hi{color:var(--emerald)}.kpi .v.gold{color:#B8941f}.kpi .v.warn{color:#B4452E}
.kpi .k{font-size:11px;color:var(--muted);margin-top:6px;font-weight:500;letter-spacing:.02em}

/* toolbar */
.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:4px 24px 16px}
.search{flex:1;min-width:200px;position:relative}
.search input{width:100%;border:1px solid var(--line);border-radius:10px;padding:11px 14px 11px 36px;font-family:var(--body);font-size:13.5px;background:var(--card)}
.search input:focus{outline:none;border-color:var(--emerald)}
.search::before{content:"";position:absolute;left:13px;top:50%;width:13px;height:13px;margin-top:-8px;border:2px solid var(--muted);border-radius:50%}
.search::after{content:"";position:absolute;left:23px;top:50%;width:6px;height:2px;background:var(--muted);transform:rotate(45deg);margin-top:4px}
.chips{display:flex;gap:6px;background:#EAEFED;border-radius:10px;padding:4px}
.chips button{border:0;background:transparent;font-weight:600;font-size:12.5px;color:var(--slate);padding:7px 13px;border-radius:8px;transition:.2s;display:flex;align-items:center;gap:6px}
.chips button.on{background:#fff;color:var(--navy);box-shadow:var(--sh)}
.chips button i{width:8px;height:8px;border-radius:50%;display:inline-block}
select{border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-family:var(--body);font-size:13px;background:var(--card);color:var(--ink)}
.tgl{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--slate);font-weight:500;user-select:none;cursor:pointer}
.tgl input{display:none}
.tgl .sw{width:34px;height:20px;background:#cfd8d5;border-radius:20px;position:relative;transition:.2s}
.tgl .sw::after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;background:#fff;border-radius:50%;transition:.2s}
.tgl input:checked+.sw{background:var(--emerald)}
.tgl input:checked+.sw::after{transform:translateX(14px)}

/* main layout */
.main{display:grid;grid-template-columns:1fr 380px;gap:16px;padding:0 24px 28px;align-items:start}
@media(max-width:980px){.main{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);overflow:hidden}
.tablewrap{max-height:calc(100vh - 300px);overflow:auto}
table{width:100%;border-collapse:collapse}
thead th{position:sticky;top:0;background:#F7FAF9;z-index:2;text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700;padding:12px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
thead th.srt{cursor:pointer}
thead th.srt:hover{color:var(--emerald)}
tbody td{padding:12px 14px;border-bottom:1px solid #F0F4F3;font-size:13px;vertical-align:top}
tbody tr{cursor:pointer;transition:background .15s}
tbody tr:hover{background:#FAFCFB}
tbody tr.sel{background:#F0F7F4;box-shadow:inset 3px 0 0 var(--emerald)}
.pill{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 9px;border-radius:100px;white-space:nowrap}
.pill.high{background:rgba(13,107,79,.13);color:var(--emerald)}
.pill.medium{background:rgba(212,175,55,.2);color:#8a6d12}
.pill.low{background:rgba(71,85,105,.12);color:var(--slate)}
.msgcell{max-width:340px;color:var(--ink);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.scoretag{font-weight:700;color:var(--navy);font-variant-numeric:tabular-nums}
.meta-sm{font-size:11.5px;color:var(--muted)}
.status{font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px}
.status.new{background:#EEF2F1;color:var(--slate)}
.status.done{background:rgba(13,107,79,.13);color:var(--emerald)}
.empty{padding:50px;text-align:center;color:var(--muted)}
.tblhead{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid var(--line)}
.tblhead h3{font-family:var(--head);font-size:16px;color:var(--navy)}
.tblhead .count{font-size:12.5px;color:var(--muted)}

/* detail */
.detail{position:sticky;top:88px;padding:22px}
.detail .none{color:var(--muted);text-align:center;padding:40px 0;font-size:13.5px}
.detail .q{font-family:var(--head);font-style:italic;font-size:16px;color:var(--navy);line-height:1.5;border-left:3px solid var(--gold);padding-left:14px;margin-bottom:14px}
.dmeta{font-size:11.5px;color:var(--muted);letter-spacing:.03em;margin-bottom:18px;text-transform:uppercase}
.bant{display:flex;flex-direction:column;gap:11px;margin:6px 0 18px}
.brow{display:grid;grid-template-columns:74px 1fr 30px;align-items:center;gap:10px}
.bname{font-size:12px;font-weight:600;color:var(--slate)}
.btrack{height:8px;background:#EEF2F1;border-radius:6px;overflow:hidden}
.bfill{height:100%;width:0;border-radius:6px;background:linear-gradient(90deg,#13a07a,#0D6B4F);transition:width .5s cubic-bezier(.16,1,.3,1)}
.bscore{font-size:12.5px;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.totalbar{display:flex;justify-content:space-between;align-items:center;background:#F6F8F7;border-radius:10px;padding:11px 14px;font-size:13px;margin-bottom:16px}
.totalbar b{font-family:var(--head);font-size:17px;color:var(--navy)}
.reason{font-size:12.5px;color:var(--slate);background:#F6F8F7;border-radius:10px;padding:12px 14px;line-height:1.55;margin-bottom:16px}
.action{border-radius:12px;padding:14px 16px;margin-bottom:16px;color:#fff}
.action.high{background:linear-gradient(135deg,#0D6B4F,#094D3A)}
.action.medium{background:linear-gradient(135deg,#c9a63a,#a5851f)}
.action.low{background:linear-gradient(135deg,#6b7f7a,#516560)}
.action .lab{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;opacity:.85}
.action .txt{font-size:14px;font-weight:600;margin-top:5px}
.action .sla{font-size:12px;opacity:.9;margin-top:4px}
.detail .actbtns{display:flex;gap:8px}
.detail .actbtns .btn{flex:1;text-align:center}

/* modal scorer */
.overlay{position:fixed;inset:0;background:rgba(10,29,55,.55);backdrop-filter:blur(3px);z-index:50;display:none;align-items:flex-start;justify-content:center;padding:40px 16px;overflow:auto}
.overlay.on{display:flex}
.modal{background:#fff;border-radius:20px;max-width:900px;width:100%;box-shadow:0 30px 80px rgba(9,29,55,.4);overflow:hidden}
.modal .mhead{background:linear-gradient(120deg,#0D6B4F,#0A1D37);color:#fff;padding:20px 26px;display:flex;justify-content:space-between;align-items:center}
.modal .mhead h3{font-family:var(--head);font-size:20px}
.modal .mhead p{font-size:12.5px;color:#c3d6ce;margin-top:3px}
.modal .close{background:rgba(255,255,255,.15);border:0;color:#fff;width:32px;height:32px;border-radius:8px;font-size:18px}
.mbody{display:grid;grid-template-columns:1fr 1fr;gap:0}
@media(max-width:720px){.mbody{grid-template-columns:1fr}}
.mform{padding:26px;border-right:1px solid var(--line)}
.mform label{display:block;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 7px}
.mform textarea{width:100%;min-height:130px;border:1px solid var(--line);border-radius:12px;padding:13px;font-family:var(--body);font-size:13.5px;resize:vertical;line-height:1.5}
.mform textarea:focus{outline:none;border-color:var(--emerald)}
.mrow{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:14px 0}
.mrow select{width:100%}
.presets{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 16px}
.presets button{font-size:11.5px;border:1px solid var(--line);background:#F6F8F7;color:var(--slate);border-radius:100px;padding:6px 12px}
.presets button:hover{border-color:var(--emerald);color:var(--emerald)}
.mout{padding:26px;background:#FAFCFB}
.mout .ph{color:var(--muted);text-align:center;padding:60px 20px;font-size:13.5px}
.mres .verdict{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.mres .verdict .big{font-family:var(--head);font-weight:700;font-size:34px}
.mres .verdict .pill{font-size:12px}
</style></head>
<body>

<header>
  <div class="logo">Velocity<span class="g"> Console</span><small>Live lead triage &amp; scoring</small></div>
  <div class="hbtns">
    <span class="badge" id="engineBadge">engine</span>
    <a class="btn ghost" href="guide.html">How to use</a>
    <button class="btn gold" id="openScorer">⚡ Score a lead</button>
  </div>
</header>

<div class="kpis" id="kpis"></div>

<div class="toolbar">
  <div class="search"><input id="q" type="text" placeholder="Search messages, region, role…"></div>
  <div class="chips" id="tierChips">
    <button data-t="all" class="on">All</button>
    <button data-t="high"><i style="background:var(--emerald)"></i>High</button>
    <button data-t="medium"><i style="background:var(--gold)"></i>Medium</button>
    <button data-t="low"><i style="background:var(--lowc)"></i>Low</button>
  </div>
  <select id="sourceSel">
    <option value="all">All sources</option>
    <option value="Demo request">Demo request</option>
    <option value="Free trial">Free trial</option>
    <option value="Webinar">Webinar</option>
    <option value="Paid ad">Paid ad</option>
    <option value="Referral">Referral</option>
  </select>
  <select id="sortSel">
    <option value="score">Sort: Score (high→low)</option>
    <option value="newest">Sort: Newest</option>
    <option value="slowest">Sort: Slowest response</option>
    <option value="oldest">Sort: Oldest</option>
  </select>
  <label class="tgl"><input type="checkbox" id="onlyNever"><span class="sw"></span>Only never-contacted</label>
</div>

<div class="main">
  <div class="panel">
    <div class="tblhead"><h3>Lead queue</h3><span class="count" id="count"></span></div>
    <div class="tablewrap">
      <table>
        <thead><tr>
          <th>Priority</th><th>Source</th><th>Company</th><th>Region</th>
          <th>Message</th><th class="srt" data-s="score">Score</th>
          <th class="srt" data-s="slowest">As-is</th><th>Status</th>
        </tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
  </div>
  <div class="panel detail" id="detail"><div class="none">Select a lead from the queue to see its scoring and routing.</div></div>
</div>

<!-- live scorer modal -->
<div class="overlay" id="overlay">
  <div class="modal">
    <div class="mhead">
      <div><h3>Live BANT scorer</h3><p>The real scoring engine, running in your browser. Type a lead and score it.</p></div>
      <button class="close" id="closeScorer">&times;</button>
    </div>
    <div class="mbody">
      <div class="mform">
        <label>Lead message</label>
        <textarea id="sMsg" placeholder="Paste or type a lead's message…"></textarea>
        <div class="presets" id="presets"></div>
        <div class="mrow">
          <div><label>Source</label><select id="sSource"><option value="demo_request">Demo</option><option value="free_trial">Trial</option><option value="content_webinar">Webinar</option><option value="paid_ad">Paid ad</option><option value="referral">Referral</option></select></div>
          <div><label>Role</label><select id="sRole"><option value="junior">Junior</option><option value="manager">Manager</option><option value="director">Director</option><option value="vp">VP</option><option value="c_level">C-level</option><option value="owner">Owner</option></select></div>
          <div><label>Size</label><select id="sSize"><option value="solo">Solo</option><option value="small">Small</option><option value="mid">Mid</option><option value="large">Large</option><option value="enterprise">Enterprise</option></select></div>
        </div>
        <button class="btn pri" id="runScore" style="width:100%">Score this lead</button>
      </div>
      <div class="mout" id="mout"><div class="ph">Your live BANT score and routing decision will appear here.</div></div>
    </div>
  </div>
</div>

<script>
const D = __PAYLOAD__;
const $ = s=>document.querySelector(s);
const SLA = D.sla;
document.getElementById('engineBadge').textContent = D.engine;

/* ---------- BANT rules engine (ported from score_leads.py) ---------- */
const BUDGET_CUES=["budget","approved","sign-off","signed off","allocated","allocate","set aside","purchasing authority","purchase","quote","contract","annual billing","pricing proposal","board approved","money's set"];
const BUDGET_WEAK=["pricing","how much","cost","price","per-seat","per seat","plan"];
const AUTHORITY_CUES=["i'm the","i am the","i run","i manage","head of","director"," vp ","vp of","c-level","coo","ceo","owner","program lead","purchasing authority","approved to buy","i've been approved","i have purchasing","asked me to","board approved"];
const AUTHORITY_NEG=["need my manager","would need my manager","bring it to the team","need to confirm with","school assignment","personal to-do"];
const NEED_CUES=["replace","migrat","consolidat","switch","outgrow","killing us","lose hours","losing hours","bleed hours","billable hours","missing deadlines","miss deadlines","late projects","slipping","status chasing","visibility","no portal","reporting","off spreadsheets","spreadsheets are","off trello","off jira","off asana","standardize","resource planning","capacity planning","scaling from","scale with us","double-book","double booking","dependencies","onboard","onboarding","time tracking","integrate","integration","auditable","audit","sprint"];
const NEED_WEAK=["track","manage","evaluating","evaluate","looking for","need ","tool"];
const TIMELINE_CUES=["this week","this quarter","this month","end of month","by end of","by july","by august","before q3","before our","deadline","go-live","go live","renews in","renewal","fiscal year","next sprint","within the next","weeks","ready to buy now","buy now","before then","__RX__by ","kickoff"];
const TIMELINE_WEAK=["soon","soon-ish","this year","next year","upcoming"];
const ROLE_AUTHORITY={c_level:3,owner:3,vp:3,director:2,manager:1,junior:0};
const RX_BY=/\bby \w+\b/;
function hits(t,cues){let n=0;for(const c of cues){if(c==="__RX__by "){if(RX_BY.test(t))n++;}else if(t.includes(c))n++;}return n;}
function clamp3(v){return Math.max(0,Math.min(3,v));}
function scoreLead(text, role){
  const t=(text||"").toLowerCase();
  const budget=clamp3(hits(t,BUDGET_CUES)*2 + (hits(t,BUDGET_WEAK)>0?1:0));
  const aStrong=Math.min(3,hits(t,AUTHORITY_CUES)), aNeg=hits(t,AUTHORITY_NEG);
  const authority=clamp3(Math.max(0, Math.round((aStrong+(ROLE_AUTHORITY[role]||0))/2) - aNeg));
  const need=clamp3(hits(t,NEED_CUES)*2 + (hits(t,NEED_WEAK)>0?1:0));
  const timeline=clamp3(hits(t,TIMELINE_CUES) + (hits(t,TIMELINE_WEAK)>0?1:0));
  const total=budget+authority+need+timeline;
  const priority=total>=8?"high":total>=3?"medium":"low";
  return {budget,authority,need,timeline,total,priority};
}

/* ---------- helpers ---------- */
function fmtDur(m){return m==null?"—":m<60?Math.round(m)+" min":(m/60>=10?Math.round(m/60)+"h":(m/60).toFixed(1).replace(/\.0$/,'')+"h");}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
const ACTIONS={
  high:{lab:"Route now",txt:"Alert an Account Executive + auto-book a call"},
  medium:{lab:"Queue",txt:"SDR queue — same-hour personal follow-up"},
  low:{lab:"Nurture",txt:"Automated nurture sequence"}
};

/* ---------- state ---------- */
const state={tier:"all",source:"all",q:"",sort:"score",onlyNever:false,sel:null,worked:{}};

function view(){
  let xs=D.leads.slice();
  if(state.tier!=="all")xs=xs.filter(l=>l.priority===state.tier);
  if(state.source!=="all")xs=xs.filter(l=>l.source_label===state.source);
  if(state.onlyNever)xs=xs.filter(l=>!l.contacted);
  if(state.q){const q=state.q.toLowerCase();xs=xs.filter(l=>(l.msg+" "+l.region+" "+l.role+" "+l.source_label+" "+l.id).toLowerCase().includes(q));}
  const P={high:0,medium:1,low:2};
  if(state.sort==="score")xs.sort((a,b)=>b.total-a.total||P[a.priority]-P[b.priority]);
  else if(state.sort==="newest")xs.sort((a,b)=>b.created.localeCompare(a.created));
  else if(state.sort==="oldest")xs.sort((a,b)=>a.created.localeCompare(b.created));
  else if(state.sort==="slowest")xs.sort((a,b)=>(b.asis==null?1e12:b.asis)-(a.asis==null?1e12:a.asis));
  return xs;
}

function renderKPIs(xs){
  const n=xs.length, hi=xs.filter(l=>l.priority==="high").length,
    md=xs.filter(l=>l.priority==="medium").length, lo=xs.filter(l=>l.priority==="low").length,
    avg=n?(xs.reduce((s,l)=>s+l.total,0)/n):0,
    never=xs.filter(l=>!l.contacted).length,
    worked=Object.keys(state.worked).length;
  $("#kpis").innerHTML=`
    <div class="kpi"><div class="v num">${n}</div><div class="k">Leads in view</div></div>
    <div class="kpi"><div class="v hi num">${hi}</div><div class="k">High priority</div></div>
    <div class="kpi"><div class="v gold num">${md}</div><div class="k">Medium priority</div></div>
    <div class="kpi"><div class="v num" style="color:var(--slate)">${lo}</div><div class="k">Low priority</div></div>
    <div class="kpi"><div class="v num">${avg.toFixed(1)}</div><div class="k">Avg BANT / 12</div></div>
    <div class="kpi"><div class="v warn num">${never}</div><div class="k">Never contacted (as-is)</div></div>`;
}

function renderTable(xs){
  $("#count").textContent=`${xs.length} shown`;
  if(!xs.length){$("#rows").innerHTML=`<tr><td colspan="8"><div class="empty">No leads match these filters.</div></td></tr>`;return;}
  $("#rows").innerHTML=xs.slice(0,300).map(l=>{
    const worked=state.worked[l.id];
    return `<tr data-id="${l.id}" class="${state.sel===l.id?'sel':''}">
      <td><span class="pill ${l.priority}">${l.priority}</span></td>
      <td>${l.source_label}<div class="meta-sm">${l.id}</div></td>
      <td>${l.size}<div class="meta-sm">${l.role}</div></td>
      <td>${esc(l.region)}</td>
      <td><div class="msgcell">${esc(l.msg)}</div></td>
      <td><span class="scoretag">${l.total}</span><span class="meta-sm">/12</span></td>
      <td>${l.contacted?fmtDur(l.asis):'<span style="color:#B4452E;font-weight:600">never</span>'}</td>
      <td><span class="status ${worked?'done':'new'}">${worked?'Routed':'New'}</span></td>
    </tr>`;}).join("");
  document.querySelectorAll("#rows tr[data-id]").forEach(tr=>tr.addEventListener("click",()=>select(tr.dataset.id)));
}

function bantRows(b){
  const N=[["budget","Budget"],["authority","Authority"],["need","Need"],["timeline","Timeline"]];
  return N.map(([k,lab])=>{const v=b[k]!=null?b[k]:0;return `<div class="brow"><span class="bname">${lab}</span><div class="btrack"><i class="bfill" data-w="${v/3*100}"></i></div><span class="bscore">${v}/3</span></div>`;}).join("");
}

function select(id){
  state.sel=id;const l=D.leads.find(x=>x.id===id);if(!l)return;
  document.querySelectorAll("#rows tr").forEach(t=>t.classList.toggle("sel",t.dataset.id===id));
  const A=ACTIONS[l.priority], worked=state.worked[id];
  $("#detail").innerHTML=`
    <div class="q">${esc(l.msg)}</div>
    <div class="dmeta">${l.source_label} · ${esc(l.region)} · ${l.size} · ${l.role} · ${l.id}</div>
    <div class="bant">${bantRows(l.bant)}</div>
    <div class="totalbar"><span>BANT total</span><span><b>${l.total}</b> / 12 · <span class="pill ${l.priority}">${l.priority}</span></span></div>
    ${l.reason?`<div class="reason"><b>Why:</b> ${esc(l.reason)}</div>`:''}
    <div class="action ${l.priority}"><div class="lab">${A.lab} · SLA ${fmtDur(SLA[l.priority])}</div><div class="txt">${A.txt}</div><div class="sla">As-is, this lead ${l.contacted?'waited '+fmtDur(l.asis):'was never contacted'}.</div></div>
    <div class="actbtns">
      <button class="btn ${worked?'ghost':'pri'} sm" id="routeBtn" style="${worked?'color:var(--emerald);border-color:var(--emerald)':''}">${worked?'✓ Routed':'Route this lead'}</button>
    </div>`;
  requestAnimationFrame(()=>$("#detail").querySelectorAll(".bfill").forEach(f=>f.style.width=f.dataset.w+"%"));
  const rb=$("#routeBtn");if(rb)rb.addEventListener("click",()=>{if(state.worked[id])delete state.worked[id];else state.worked[id]=true;render();select(id);});
}

function render(){const xs=view();renderKPIs(xs);renderTable(xs);}

/* ---------- filters ---------- */
$("#q").addEventListener("input",e=>{state.q=e.target.value;render();});
$("#tierChips").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;state.tier=b.dataset.t;$("#tierChips").querySelectorAll("button").forEach(x=>x.classList.toggle("on",x===b));render();});
$("#sourceSel").addEventListener("change",e=>{state.source=e.target.value;render();});
$("#sortSel").addEventListener("change",e=>{state.sort=e.target.value;render();});
$("#onlyNever").addEventListener("change",e=>{state.onlyNever=e.target.checked;render();});

/* ---------- live scorer modal ---------- */
const PRESETS=[
  {label:"Strong lead",msg:"I'm the VP of Operations and we've approved budget for 120 seats. We're replacing Jira and need to roll out before our Q3 deadline in 5 weeks.",role:"vp",size:"large",source:"demo_request"},
  {label:"Warm / vague",msg:"We're a growing team and outgrowing our current setup. Curious how your pricing works and whether you do onboarding support.",role:"manager",size:"mid",source:"free_trial"},
  {label:"Cold",msg:"Just browsing, saw your ad. Is there a free version?",role:"junior",size:"solo",source:"paid_ad"}
];
$("#presets").innerHTML=PRESETS.map((p,i)=>`<button data-i="${i}">${p.label}</button>`).join("");
$("#presets").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;const p=PRESETS[+b.dataset.i];$("#sMsg").value=p.msg;$("#sRole").value=p.role;$("#sSize").value=p.size;$("#sSource").value=p.source;});
$("#openScorer").addEventListener("click",()=>$("#overlay").classList.add("on"));
$("#closeScorer").addEventListener("click",()=>$("#overlay").classList.remove("on"));
$("#overlay").addEventListener("click",e=>{if(e.target.id==="overlay")$("#overlay").classList.remove("on");});
$("#runScore").addEventListener("click",()=>{
  const msg=$("#sMsg").value.trim();
  if(!msg){$("#mout").innerHTML='<div class="ph">Type a message first.</div>';return;}
  const r=scoreLead(msg,$("#sRole").value);
  const A=ACTIONS[r.priority];
  const col=r.priority==="high"?"var(--emerald)":r.priority==="medium"?"#B8941f":"var(--slate)";
  $("#mout").innerHTML=`<div class="mres">
    <div class="verdict"><span class="big" style="color:${col}">${r.total}<span style="font-size:16px;color:var(--muted)">/12</span></span><span class="pill ${r.priority}">${r.priority} priority</span></div>
    <div class="bant">${bantRows(r)}</div>
    <div class="action ${r.priority}"><div class="lab">${A.lab} · SLA ${fmtDur(SLA[r.priority])}</div><div class="txt">${A.txt}</div></div>
    <p style="font-size:11.5px;color:var(--muted);margin-top:14px">Scored live by the same BANT rules engine used on all ${D.leads.length} leads — no server call.</p>
  </div>`;
  requestAnimationFrame(()=>$("#mout").querySelectorAll(".bfill").forEach(f=>f.style.width=f.dataset.w+"%"));
});

/* init */
render();
select(view()[0] && view()[0].id);
</script>
</body></html>"""

HTML = HTML.replace("__PAYLOAD__", DATA_JSON)
with open(OUT, "w") as f:
    f.write(HTML)
print(f"Wrote {OUT}  ({len(slim)} leads embedded)")

# ---------------------------------------------------------------------------
# Guide page — "How to use the Velocity Console"
# ---------------------------------------------------------------------------
GUIDE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>How to use — Velocity Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--emerald:#0D6B4F;--forest:#094D3A;--navy:#0A1D37;--gold:#D4AF37;--slate:#475569;
  --ink:#0B1620;--muted:#6B7B82;--line:#E6ECEA;--bg:#F4F6F5;--card:#fff;--lowc:#9FB0AE;
  --head:'Playfair Display',Georgia,serif;--body:'Montserrat',-apple-system,Segoe UI,sans-serif;
  --sh:0 8px 24px rgba(9,29,55,.09);}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--body);color:var(--ink);background:var(--bg);line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit}
header{background:linear-gradient(120deg,#0D6B4F,#094D3A 55%,#0A1D37);color:#fff;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:20}
.logo{font-family:var(--head);font-weight:700;font-size:20px}.logo .g{color:var(--gold)}
.back{text-decoration:none;color:#fff;font-size:13px;font-weight:600;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);padding:9px 15px;border-radius:10px}
.back:hover{background:rgba(255,255,255,.2)}
.wrap{max-width:960px;margin:0 auto;padding:0 24px}
.hero{padding:56px 0 34px}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:#B8941f}
.hero h1{font-family:var(--head);font-weight:800;font-size:clamp(30px,5vw,46px);line-height:1.08;color:var(--navy);margin:12px 0 14px}
.hero p{font-size:17px;color:var(--slate);max-width:64ch}
.cta{display:inline-block;margin-top:22px;background:var(--emerald);color:#fff;text-decoration:none;font-weight:600;font-size:14px;padding:13px 22px;border-radius:12px;box-shadow:var(--sh)}
.cta:hover{background:var(--forest)}
section{padding:26px 0}
h2{font-family:var(--head);font-weight:700;font-size:26px;color:var(--navy);margin-bottom:6px}
.sub{color:var(--muted);font-size:14px;margin-bottom:22px}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:720px){.steps{grid-template-columns:1fr}}
.step{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:var(--sh)}
.step .n{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;background:rgba(13,107,79,.12);color:var(--emerald);font-family:var(--head);font-weight:700;font-size:16px;margin-bottom:12px}
.step h3{font-size:18px;color:var(--navy);margin-bottom:8px}
.step p{font-size:14px;color:var(--slate)}
.step ul{margin:12px 0 0;padding-left:18px}
.step li{font-size:13.5px;color:var(--ink);margin-bottom:6px}
.step li b{color:var(--navy)}
.step .tip{margin-top:14px;font-size:12.5px;color:var(--muted);background:#F6F8F7;border-radius:10px;padding:11px 13px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:var(--sh)}
th,td{text-align:left;padding:13px 16px;font-size:14px;border-bottom:1px solid var(--line)}
th{background:#F7FAF9;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}
tr:last-child td{border-bottom:0}
.pill{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:3px 9px;border-radius:100px}
.pill.high{background:rgba(13,107,79,.13);color:var(--emerald)}
.pill.medium{background:rgba(212,175,55,.2);color:#8a6d12}
.pill.low{background:rgba(71,85,105,.12);color:var(--slate)}
.hm{background:var(--navy);color:#fff;border-radius:20px;padding:32px;margin-top:8px}
.hm h2{color:#fff}
.hm .sub{color:#aebfb8}
.hm .grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:8px}
@media(max-width:720px){.hm .grid{grid-template-columns:1fr}}
.hm h4{font-family:var(--head);font-size:16px;color:var(--gold);margin-bottom:10px}
.hm ol{padding-left:20px}.hm ol li{margin-bottom:8px;color:#dbe7e2;font-size:14px}
.hm ul{list-style:none;padding:0}.hm ul li{color:#dbe7e2;font-size:14px;margin-bottom:9px;padding-left:22px;position:relative}
.hm ul li::before{content:"\2713";position:absolute;left:0;color:#43d6a6;font-weight:700}
footer{text-align:center;padding:44px 24px 56px;color:var(--muted);font-size:13px}
footer .brand{font-family:var(--head);font-weight:700;font-size:18px;color:var(--navy)}
footer .brand .g{color:var(--gold)}
footer .tag{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#B8941f;margin-top:6px}
</style></head>
<body>
<header>
  <span class="logo">Velocity<span class="g"> Console</span> · Guide</span>
  <a class="back" href="console.html">← Back to the console</a>
</header>

<div class="wrap">
  <div class="hero">
    <span class="eyebrow">How to use</span>
    <h1>A 60-second guide to the Velocity Console.</h1>
    <p>The Console is a live lead-triage tool. It takes 400 sample leads, scores every one on BANT (Budget · Authority · Need · Timeline), and lets you filter, inspect, route, and even score brand-new leads in real time. Here's how to drive it.</p>
    <a class="cta" href="console.html">Open the console →</a>
  </div>

  <section>
    <h2>Four things you can do</h2>
    <div class="sub">Everything runs in your browser — no login, no server, no wait.</div>
    <div class="steps">
      <div class="step">
        <span class="n">1</span>
        <h3>Read the pipeline at a glance</h3>
        <p>The strip of numbers at the top is your live snapshot. It updates instantly whenever you filter.</p>
        <ul>
          <li><b>Leads in view</b> · <b>High / Medium / Low</b> counts</li>
          <li><b>Avg BANT / 12</b> — average score of what's shown</li>
          <li><b>Never contacted</b> — leads the old manual process dropped</li>
        </ul>
      </div>
      <div class="step">
        <span class="n">2</span>
        <h3>Work the queue</h3>
        <p>Slice the 400 leads down to exactly what you care about.</p>
        <ul>
          <li><b>Search</b> — type any word (region, role, a phrase in the message)</li>
          <li><b>Tier chips</b> — All / High / Medium / Low</li>
          <li><b>Source</b> and <b>Sort</b> — by score, newest, or slowest response</li>
          <li><b>Only never-contacted</b> — surface the dropped leads</li>
        </ul>
      </div>
      <div class="step">
        <span class="n">3</span>
        <h3>Open a lead & route it</h3>
        <p>Click any row. The panel on the right shows the full picture.</p>
        <ul>
          <li>The lead's own <b>message</b> and details</li>
          <li>Its <b>BANT bars</b> and total, with the <b>reason</b></li>
          <li>The <b>recommended action + SLA</b>, and how long it actually waited</li>
          <li>Hit <b>Route this lead</b> to action it — the queue updates</li>
        </ul>
      </div>
      <div class="step">
        <span class="n">4</span>
        <h3>Score a brand-new lead</h3>
        <p>Click <b>⚡ Score a lead</b> (top-right). This is the real engine, live.</p>
        <ul>
          <li>Type or paste any message, or click a <b>preset</b> (Strong / Warm / Cold)</li>
          <li>Pick source, role, size → <b>Score this lead</b></li>
          <li>See its BANT breakdown, tier, and routing decision instantly</li>
        </ul>
        <div class="tip">This uses the same scoring logic as the 400 leads — proof the engine actually reads and reasons over the text, not a canned result.</div>
      </div>
    </div>
  </section>

  <section>
    <h2>What the scores mean</h2>
    <div class="sub">Each lead is scored 0–3 on four signals; the total (0–12) sets the priority and the routing SLA.</div>
    <table>
      <tr><th>Signal</th><th>What it measures</th></tr>
      <tr><td><b>Budget</b></td><td>Money / approval / spend signals — is there budget to buy?</td></tr>
      <tr><td><b>Authority</b></td><td>Is the writer a decision-maker or buyer? (role + language)</td></tr>
      <tr><td><b>Need</b></td><td>How specific and pressing is the pain?</td></tr>
      <tr><td><b>Timeline</b></td><td>How soon must they act? (deadline / buying now)</td></tr>
    </table>
    <table style="margin-top:18px">
      <tr><th>Tier</th><th>BANT total</th><th>Routing SLA</th><th>Action</th></tr>
      <tr><td><span class="pill high">High</span></td><td>8–12</td><td>5 min</td><td>Alert an AE + auto-book a call</td></tr>
      <tr><td><span class="pill medium">Medium</span></td><td>3–7</td><td>60 min</td><td>SDR queue, same-hour follow-up</td></tr>
      <tr><td><span class="pill low">Low</span></td><td>0–2</td><td>24 h</td><td>Automated nurture sequence</td></tr>
    </table>
  </section>

  <section>
    <div class="hm">
      <span class="eyebrow" style="color:var(--gold)">For reviewers</span>
      <h2 style="margin-top:8px">What this demonstrates</h2>
      <div class="sub">A quick guide if you're evaluating the work behind it.</div>
      <div class="grid">
        <div>
          <h4>30-second demo</h4>
          <ol>
            <li>"Here's a real intake queue — 400 leads, scored and prioritized." <i>(filter to High)</i></li>
            <li>"Click a hot one — it explains why it's high and what to do." <i>(open a lead)</i></li>
            <li>"And it's not a mockup —" <i>(⚡ Score a lead → a preset → Score)</i> "same logic, running live on anything you type."</li>
          </ol>
        </div>
        <div>
          <h4>Under the hood</h4>
          <ul>
            <li>LLM-based BANT scoring (Claude) with structured JSON outputs</li>
            <li>A deterministic rules engine, ported to run client-side</li>
            <li>Interactive data UI — filtering, sorting, live KPIs, routing state</li>
            <li>Zero dependencies — hostable free on GitHub Pages</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</div>

<footer>
  <div class="brand">AceLiora<span class="g"> AI</span></div>
  <div class="tag">Accelerate Change · Sustain Excellence</div>
  <p style="margin-top:14px"><a href="console.html" style="color:var(--emerald);font-weight:600;text-decoration:none">← Back to the Velocity Console</a></p>
</footer>
</body></html>"""

GUIDE_OUT = "docs/guide.html"
with open(GUIDE_OUT, "w") as f:
    f.write(GUIDE)
print(f"Wrote {GUIDE_OUT}")
