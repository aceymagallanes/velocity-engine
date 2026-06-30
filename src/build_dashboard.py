#!/usr/bin/env python3
"""Build the interactive, executive-grade Velocity dashboard from leads_scored.json.

Emits a single self-contained docs/index.html (inline CSS + inline vanilla JS,
brand fonts from Google Fonts). No external JS/CSS dependencies — it renders the
same offline. The full lead set is embedded so the page can filter, score, and
animate client-side. AceLiora AI brand system applied (DESIGN.md).
"""
import json, statistics
from collections import Counter

SRC = "data/leads_scored.json"
OUT = "docs/index.html"
SLA = {"high": 5, "medium": 60, "low": 1440}

with open(SRC) as f:
    data = json.load(f)
leads = data["leads"]
N = len(leads)

tiers = Counter(l["priority"] for l in leads)
contacted = [l for l in leads if l["as_is_contacted"]]
never = [l for l in leads if not l["as_is_contacted"]]
as_is_vals = [l["as_is_first_response_minutes"] for l in contacted]
as_is_mean = statistics.mean(as_is_vals)
as_is_median = statistics.median(as_is_vals)
to_be_mean = statistics.mean(SLA[l["priority"]] for l in leads)

high = [l for l in leads if l["priority"] == "high"]
high_contacted = [l for l in high if l["as_is_contacted"]]
high_never = [l for l in high if not l["as_is_contacted"]]
high_as_is_mean = statistics.mean(l["as_is_first_response_minutes"] for l in high_contacted) if high_contacted else 0

# off-hours share (evenings/weekends — when the manual process fails worst)
import datetime as dt
off = 0
for l in leads:
    try:
        d = dt.datetime.fromisoformat(l["created_at"])
        if d.weekday() >= 5 or d.hour >= 18 or d.hour < 7:
            off += 1
    except Exception:
        pass
offhours_pct = off / N * 100

# response-time distribution (contacted only) — shows the long tail
BINS = [(0, 60, "<1h"), (60, 240, "1–4h"), (240, 720, "4–12h"), (720, 1440, "12–24h"),
        (1440, 2880, "1–2d"), (2880, 5760, "2–4d"), (5760, 10**9, "4d+")]
hist = []
for lo, hi, lab in BINS:
    c = sum(1 for v in as_is_vals if lo <= v < hi)
    hist.append({"label": lab, "count": c})

SRC_LABEL = {"demo_request": "Demo request", "free_trial": "Free trial",
             "content_webinar": "Webinar", "paid_ad": "Paid ad", "referral": "Referral"}
sources = []
for s in ["demo_request", "free_trial", "content_webinar", "paid_ad", "referral"]:
    sl = [l for l in leads if l["source"] == s]
    t = Counter(l["priority"] for l in sl)
    sources.append({"label": SRC_LABEL[s], "count": len(sl),
                    "high": t["high"], "medium": t["medium"], "low": t["low"]})

# slim lead records for the client-side explorer
slim = [{
    "id": l["lead_id"], "source": SRC_LABEL.get(l["source"], l["source"]),
    "size": l["company_size_band"], "role": l["contact_role"], "region": l["region"],
    "msg": l["stated_need"], "priority": l["priority"],
    "bant": l.get("bant", {}), "total": l.get("bant_total", 0),
    "reason": l.get("bant_reason", ""),
    "contacted": l["as_is_contacted"], "asis": l["as_is_first_response_minutes"],
} for l in leads]

engine = data.get("_meta", {}).get("scoring", {}).get("engine", "Velocity rules pass")

payload = {
    "n": N,
    "tiers": {"high": tiers["high"], "medium": tiers["medium"], "low": tiers["low"]},
    "contacted": len(contacted), "never": len(never), "never_pct": len(never) / N * 100,
    "as_is_mean": as_is_mean, "as_is_median": as_is_median, "to_be_mean": to_be_mean,
    "sla": SLA, "speed_x": as_is_mean / to_be_mean,
    "high_total": len(high), "high_never": len(high_never),
    "high_never_pct": (len(high_never) / len(high) * 100) if high else 0,
    "high_as_is_mean": high_as_is_mean, "hot_x": (high_as_is_mean / SLA["high"]) if high_as_is_mean else 0,
    "offhours_pct": offhours_pct, "hist": hist, "sources": sources, "leads": slim,
    "engine": engine,
}
DATA_JSON = json.dumps(payload).replace("</", "<\\/")

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Velocity Engine — Lead Intake Transformation · AceLiora AI</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;1,500;1,600&family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --emerald:#0D6B4F;--forest:#094D3A;--navy:#0A1D37;--gold:#D4AF37;--gold-soft:#E7C658;
  --slate:#475569;--white:#fff;--off:#F6F8F7;--ink:#0B1620;--muted:#6B7B82;
  --line:rgba(9,29,55,.08);--lowc:#9FB0AE;
  --head:'Playfair Display',Georgia,serif;--body:'Montserrat',-apple-system,Segoe UI,sans-serif;
  --shadow-sm:0 8px 24px rgba(9,29,55,.10);--shadow:0 24px 60px rgba(9,29,55,.18);
  --grad:linear-gradient(135deg,#0D6B4F 0%,#094D3A 45%,#0A1D37 100%);
  --maxw:1120px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--body);color:var(--ink);background:var(--off);line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 28px}
.eyebrow{font-weight:700;font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:var(--gold);display:inline-block}
h2{font-family:var(--head);font-weight:700;font-size:clamp(30px,4.2vw,46px);line-height:1.08;letter-spacing:-.01em;color:var(--navy)}
h3{font-family:var(--head);font-weight:600;font-size:22px;color:var(--navy)}
.lead{font-size:clamp(16px,1.6vw,19px);color:var(--slate);max-width:62ch}
.section{padding:clamp(64px,9vw,118px) 0}
.reveal{opacity:0;transform:translateY(26px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}
.reveal.in{opacity:1;transform:none}
.num{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}

/* ---- top nav ---- */
nav{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;align-items:center;justify-content:space-between;
  padding:16px 28px;backdrop-filter:saturate(140%) blur(12px);background:rgba(246,248,247,0);transition:.4s;border-bottom:1px solid transparent}
nav.scrolled{background:rgba(246,248,247,.82);border-bottom:1px solid var(--line)}
.brand{font-family:var(--head);font-weight:700;font-size:19px;color:var(--navy);letter-spacing:.01em}
.brand .ai{color:var(--gold)}
.navlinks{display:flex;gap:26px}
.navlinks a{font-size:13px;font-weight:600;letter-spacing:.02em;color:var(--slate);text-decoration:none;transition:.2s;position:relative}
.navlinks a:hover{color:var(--emerald)}
@media(max-width:760px){.navlinks{display:none}}

/* ---- hero ---- */
.hero{min-height:100vh;display:flex;align-items:center;background:var(--grad);color:#fff;position:relative;overflow:hidden}
.hero .orb{position:absolute;border-radius:50%;filter:blur(60px);opacity:.5}
.hero .orb.a{width:520px;height:520px;background:radial-gradient(circle,#138a66,transparent 70%);top:-160px;right:-120px}
.hero .orb.b{width:440px;height:440px;background:radial-gradient(circle,#caa53a,transparent 70%);bottom:-180px;left:-140px;opacity:.28}
.hero-inner{position:relative;z-index:2;max-width:var(--maxw);margin:0 auto;padding:120px 28px 90px;width:100%}
.hero h1{font-family:var(--head);font-weight:800;font-size:clamp(42px,7vw,82px);line-height:1.02;letter-spacing:-.02em;margin:18px 0 22px;max-width:16ch}
.hero h1 .g{color:var(--gold);font-style:italic;font-weight:600}
.hero p{font-size:clamp(17px,1.8vw,21px);color:#D7E5DF;max-width:60ch}
.hero .meta{margin-top:40px;display:flex;gap:36px;flex-wrap:wrap;border-top:1px solid rgba(255,255,255,.16);padding-top:26px;max-width:760px}
.hero .meta div{display:flex;flex-direction:column}
.hero .meta b{font-family:var(--head);font-size:26px;font-weight:700;color:#fff}
.hero .meta span{font-size:12.5px;letter-spacing:.04em;color:#A9C0B8;margin-top:2px}
.scrollcue{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);z-index:2;color:#9fc;font-size:11px;letter-spacing:.25em;text-transform:uppercase;color:rgba(255,255,255,.6);text-align:center}
.scrollcue .dot{width:22px;height:36px;border:1.5px solid rgba(255,255,255,.4);border-radius:12px;margin:0 auto 10px;position:relative}
.scrollcue .dot::after{content:"";position:absolute;top:7px;left:50%;transform:translateX(-50%);width:3px;height:7px;border-radius:2px;background:var(--gold);animation:cue 1.6s infinite}
@keyframes cue{0%{opacity:0;transform:translate(-50%,0)}40%{opacity:1}100%{opacity:0;transform:translate(-50%,12px)}}

/* ---- generic layout ---- */
.split{display:grid;grid-template-columns:1.05fr 1fr;gap:clamp(32px,5vw,72px);align-items:center}
@media(max-width:860px){.split{grid-template-columns:1fr;gap:40px}}
.tint{background:#fff}
.dark{background:var(--navy);color:#fff}
.dark h2,.dark h3{color:#fff}
.dark .lead{color:#C3D2CC}

/* ---- stat cards ---- */
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:8px}
@media(max-width:760px){.cards{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);border-radius:24px;padding:30px;box-shadow:var(--shadow-sm);transition:transform .35s,box-shadow .35s}
.card:hover{transform:translateY(-4px);box-shadow:var(--shadow)}
.card .big{font-family:var(--head);font-weight:700;font-size:clamp(38px,5vw,52px);line-height:1;color:var(--emerald)}
.card .big.gold{color:#B8941f}.card .big.warn{color:#B4452E}
.card .lab{font-size:13.5px;color:var(--muted);margin-top:12px;font-weight:500}
.card .sub{font-size:13px;color:var(--ink);margin-top:6px;font-weight:600}

/* ---- distribution chart ---- */
.chartcard{background:#fff;border:1px solid var(--line);border-radius:24px;padding:32px 30px 24px;box-shadow:var(--shadow-sm)}
.bars{display:flex;align-items:flex-end;gap:14px;height:230px;margin-top:24px}
.bar{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;cursor:default}
.bar .col{width:100%;max-width:54px;border-radius:8px 8px 3px 3px;height:0;transition:height 1s cubic-bezier(.16,1,.3,1);background:linear-gradient(180deg,#5d7d74,#475569)}
.bar.fast .col{background:linear-gradient(180deg,#13a07a,#0D6B4F)}
.bar.slow .col{background:linear-gradient(180deg,#c96a4f,#9a3f29)}
.bar:hover .col{filter:brightness(1.08)}
.bar .vlab{font-size:13px;font-weight:700;color:var(--ink);margin-bottom:8px;opacity:0;transition:opacity .6s .4s}
.bar.in .vlab{opacity:1}
.bar .xlab{font-size:11.5px;color:var(--muted);margin-top:10px;font-weight:600;text-align:center}
.axisnote{display:flex;justify-content:space-between;margin-top:6px;font-size:11px;color:var(--muted);letter-spacing:.04em}

/* ---- priority mix ---- */
.mix{height:54px;border-radius:12px;overflow:hidden;display:flex;box-shadow:var(--shadow-sm)}
.mix .seg{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;width:0;transition:width 1.1s cubic-bezier(.16,1,.3,1);white-space:nowrap;overflow:hidden}
.mix .seg.high{background:var(--emerald)}.mix .seg.medium{background:var(--gold);color:var(--navy)}.mix .seg.low{background:var(--lowc)}
.legend{display:flex;justify-content:center;gap:22px;flex-wrap:wrap;margin-top:18px;font-size:13.5px}
.legend span{display:flex;align-items:center;gap:8px;color:var(--ink)}
.legend i{width:13px;height:13px;border-radius:4px;display:inline-block}
.srctable{width:100%;border-collapse:collapse;margin-top:26px;font-size:14px}
.srctable th{text-align:left;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700;padding:0 8px 12px}
.srctable td{padding:11px 8px;border-top:1px solid var(--line)}
.srctable td.n{text-align:right;font-variant-numeric:tabular-nums}
.srctable td.hi{color:var(--emerald);font-weight:700}.srctable td.mut{color:var(--muted)}
.srctable tr:hover td{background:#FAFBFB}

/* ---- cost callout ---- */
.cost{display:flex;align-items:center;gap:clamp(24px,4vw,56px);flex-wrap:wrap}
.cost .figure{font-family:var(--head);font-weight:800;font-size:clamp(86px,15vw,170px);line-height:.85;color:var(--gold);letter-spacing:-.03em}

/* ---- engine / explorer ---- */
.tabs{display:inline-flex;background:#EEF2F1;border-radius:100px;padding:5px;gap:4px;margin-top:8px}
.tabs button{border:0;background:transparent;font-family:var(--body);font-weight:600;font-size:13.5px;letter-spacing:.02em;color:var(--slate);padding:9px 20px;border-radius:100px;cursor:pointer;transition:.25s}
.tabs button.active{background:#fff;color:var(--navy);box-shadow:var(--shadow-sm)}
.tabs button .d{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:7px;vertical-align:middle}
.explorer{display:grid;grid-template-columns:1fr 1.15fr;gap:24px;margin-top:30px}
@media(max-width:860px){.explorer{grid-template-columns:1fr}}
.leadlist{display:flex;flex-direction:column;gap:10px;max-height:440px;overflow-y:auto;padding-right:6px}
.leadlist::-webkit-scrollbar{width:8px}.leadlist::-webkit-scrollbar-thumb{background:#D5DEDB;border-radius:8px}
.litem{text-align:left;border:1px solid var(--line);background:#fff;border-radius:16px;padding:15px 17px;cursor:pointer;transition:.22s;font-family:var(--body)}
.litem:hover{border-color:#bcd;transform:translateX(3px)}
.litem.sel{border-color:var(--emerald);box-shadow:0 0 0 2px rgba(13,107,79,.12)}
.litem .top{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:7px}
.litem .pill{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 9px;border-radius:100px}
.pill.high{background:rgba(13,107,79,.12);color:var(--emerald)}.pill.medium{background:rgba(212,175,55,.18);color:#8a6d12}.pill.low{background:rgba(71,85,105,.12);color:var(--slate)}
.litem .meta{font-size:11.5px;color:var(--muted)}
.litem .q{font-size:13.5px;color:var(--ink);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.litem .drop{font-size:11px;color:#B4452E;font-weight:700;margin-top:6px}
.detail{background:#fff;border:1px solid var(--line);border-radius:24px;padding:30px;box-shadow:var(--shadow-sm);align-self:start;position:sticky;top:84px}
.detail .q{font-family:var(--head);font-style:italic;font-weight:500;font-size:19px;color:var(--navy);line-height:1.45;border-left:3px solid var(--gold);padding-left:16px;margin-bottom:22px}
.bant{display:flex;flex-direction:column;gap:14px;margin:6px 0 20px}
.bant .row{display:grid;grid-template-columns:96px 1fr 28px;align-items:center;gap:12px}
.bant .name{font-size:12.5px;font-weight:600;color:var(--slate)}
.bant .track{height:9px;background:#EEF2F1;border-radius:6px;overflow:hidden}
.bant .fill{height:100%;width:0;border-radius:6px;background:linear-gradient(90deg,#13a07a,#0D6B4F);transition:width .7s cubic-bezier(.16,1,.3,1)}
.bant .score{font-size:13px;font-weight:700;color:var(--ink);text-align:right;font-variant-numeric:tabular-nums}
.detail .reason{font-size:13.5px;color:var(--slate);background:#F6F8F7;border-radius:14px;padding:14px 16px;line-height:1.55}
.detail .routed{margin-top:18px;display:flex;align-items:center;gap:10px;font-size:13.5px}
.detail .routed b{font-family:var(--head);color:var(--emerald);font-size:18px}

/* ---- transformation toggle ---- */
.toggle{display:inline-flex;background:#EEF2F1;border-radius:100px;padding:5px;margin-top:10px;position:relative;user-select:none;min-width:330px}
.toggle button{flex:1 1 0;border:0;background:transparent;font-family:var(--body);font-weight:700;font-size:14px;letter-spacing:.03em;color:var(--slate);padding:12px 18px;border-radius:100px;cursor:pointer;z-index:2;transition:color .3s;text-align:center;white-space:nowrap}
.toggle button.on{color:#fff}
.toggle .glider{position:absolute;top:5px;bottom:5px;left:5px;width:calc(50% - 5px);border-radius:100px;background:var(--slate);transition:transform .42s cubic-bezier(.16,1,.3,1),background .42s;z-index:1}
.toggle.v .glider{transform:translateX(100%);background:var(--emerald)}
.tcards{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:34px}
@media(max-width:760px){.tcards{grid-template-columns:1fr}}
.tcard{background:#fff;border:1px solid var(--line);border-radius:24px;padding:30px;box-shadow:var(--shadow-sm);transition:border-color .4s}
.tcard.live{border-color:rgba(13,107,79,.4)}
.tcard .k{font-size:13px;color:var(--muted);font-weight:600;letter-spacing:.02em}
.tcard .v{font-family:var(--head);font-weight:700;font-size:clamp(36px,5vw,50px);line-height:1.05;margin-top:10px;transition:color .4s}
.tcard .v.good{color:var(--emerald)}.tcard .v.bad{color:#B4452E}
.tcard .bar2{height:8px;background:#EEF2F1;border-radius:6px;margin-top:18px;overflow:hidden}
.tcard .bar2 i{display:block;height:100%;width:100%;border-radius:6px;transition:width .6s,background .4s}

/* ---- payoff ---- */
.payoff{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:44px;border-radius:24px;overflow:hidden;border:1px solid rgba(255,255,255,.12)}
@media(max-width:760px){.payoff{grid-template-columns:1fr}}
.payoff div{padding:38px 30px;border-right:1px solid rgba(255,255,255,.12)}
.payoff div:last-child{border-right:0}
.payoff .v{font-family:var(--head);font-weight:800;font-size:clamp(40px,6vw,60px);color:var(--gold);line-height:1}
.payoff .k{font-size:13.5px;color:#C3D2CC;margin-top:12px}

/* ---- footer ---- */
footer{background:var(--navy);color:#9fb3ab;padding:54px 28px 60px;text-align:center;border-top:1px solid rgba(255,255,255,.08)}
footer .brand{color:#fff;font-size:22px;display:block;margin-bottom:14px}
footer .tag{font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold)}
footer .fine{font-size:12px;margin-top:18px;color:#6f867e;max-width:60ch;margin-left:auto;margin-right:auto}

/* tooltip */
#tip{position:fixed;z-index:99;pointer-events:none;background:var(--navy);color:#fff;font-size:12.5px;padding:8px 12px;border-radius:10px;box-shadow:var(--shadow);opacity:0;transform:translateY(4px);transition:opacity .15s,transform .15s;max-width:220px}
#tip.show{opacity:1;transform:none}
#tip b{color:var(--gold-soft)}

/* ---- blueprint diagram ---- */
.diagram{display:flex;align-items:stretch;margin-top:36px;flex-wrap:nowrap}
@media(max-width:960px){.diagram{flex-direction:column}}
.node{flex:1 1 0;min-width:0;text-align:left;background:#fff;border:1px solid var(--line);border-top:3px solid var(--slate);border-radius:16px;padding:18px 16px;cursor:pointer;transition:.25s;display:flex;flex-direction:column;gap:7px;font-family:var(--body);position:relative}
.node.engine{border-top-color:var(--emerald)}
.node:hover{transform:translateY(-3px);box-shadow:var(--shadow-sm)}
.node.sel{box-shadow:0 0 0 2px var(--emerald),var(--shadow);transform:translateY(-3px)}
.node .step{font-family:var(--head);font-weight:700;font-size:19px;color:var(--slate);line-height:1}
.node.engine .step{color:var(--gold)}
.node .ntag{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:100px;align-self:flex-start}
.ntag.engine{background:rgba(13,107,79,.12);color:var(--emerald)}
.ntag.yours{background:rgba(71,85,105,.12);color:var(--slate)}
.node .ntitle{font-weight:700;font-size:14.5px;color:var(--navy);line-height:1.25}
.node .nshort{font-size:11.5px;color:var(--muted);line-height:1.35}
.flow{flex:0 0 32px;align-self:center;position:relative;height:3px}
.flow .line{position:absolute;inset:0;background:repeating-linear-gradient(90deg,var(--emerald) 0 7px,transparent 7px 14px);background-size:28px 100%;opacity:.45;animation:flowmove 1s linear infinite}
.flow .dot{position:absolute;top:50%;margin-top:-3px;width:6px;height:6px;border-radius:50%;background:var(--gold);box-shadow:0 0 8px rgba(212,175,55,.7);animation:travel 1.6s linear infinite}
.flow .head{position:absolute;right:-1px;top:50%;margin-top:-5px;width:0;height:0;border-top:5px solid transparent;border-bottom:5px solid transparent;border-left:7px solid var(--emerald);opacity:.6}
@keyframes flowmove{to{background-position:28px 0}}
@keyframes travel{from{left:0}to{left:100%}}
@media(max-width:960px){
  .flow{flex:0 0 24px;width:3px;height:24px;align-self:center}
  .flow .line{background:repeating-linear-gradient(180deg,var(--emerald) 0 7px,transparent 7px 14px);background-size:100% 28px;animation:flowmoveV 1s linear infinite}
  .flow .dot{left:50%;margin-left:-3px;margin-top:0;animation:travelV 1.6s linear infinite}
  .flow .head{right:50%;top:auto;bottom:-1px;margin-right:-5px;margin-top:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid var(--emerald);border-bottom:0}
  @keyframes flowmoveV{to{background-position:0 28px}}
  @keyframes travelV{from{top:0}to{top:100%}}
}
.bp-legend{display:flex;justify-content:center;gap:26px;flex-wrap:wrap;margin-top:26px;font-size:12.5px;color:var(--slate)}
.bp-legend span{display:flex;align-items:center;gap:8px}
.bp-legend i{width:12px;height:12px;border-radius:4px;display:inline-block}
.bp-detail{background:#fff;border:1px solid var(--line);border-radius:24px;padding:clamp(24px,4vw,38px);box-shadow:var(--shadow-sm);margin-top:26px}
.bp-detail .bp-h{display:flex;flex-direction:column;gap:11px;margin-bottom:16px}
.bp-detail h3{font-size:clamp(22px,3vw,28px)}
.bp-desc{font-size:clamp(15px,1.7vw,18px);color:var(--slate);max-width:72ch;margin-bottom:24px}
.bp-grid{display:grid;grid-template-columns:1fr 1fr;gap:26px;margin-bottom:22px}
@media(max-width:680px){.bp-grid{grid-template-columns:1fr;gap:18px}}
.bp-k{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#B8941f;margin-bottom:7px}
.bp-v{font-size:14.5px;color:var(--ink);line-height:1.6}
.bp-ex{font-size:13.5px;color:var(--slate);background:#F6F8F7;border-radius:14px;padding:15px 18px;line-height:1.55}
.bp-ex b{color:var(--navy)}

/* ---- rollout timeline ---- */
.timeline{position:relative;display:flex;justify-content:space-between;margin-top:46px;padding-top:2px}
.timeline .rail{position:absolute;top:9px;left:12.5%;right:12.5%;height:3px;background:#E2E8E5;border-radius:3px;overflow:hidden}
.timeline .rail .prog{position:absolute;top:0;bottom:0;left:0;right:100%;background:linear-gradient(90deg,var(--emerald),var(--gold));transition:right .7s cubic-bezier(.16,1,.3,1)}
.mile{position:relative;z-index:2;flex:1 1 0;display:flex;flex-direction:column;align-items:center;gap:12px;cursor:pointer}
.mile .dot{width:20px;height:20px;border-radius:50%;background:#fff;border:3px solid #CBD5D1;transition:.3s}
.mile:hover .dot{border-color:var(--emerald)}
.mile.done .dot{border-color:var(--emerald);background:var(--emerald)}
.mile.active .dot{border-color:var(--emerald);background:var(--gold);box-shadow:0 0 0 5px rgba(212,175,55,.18)}
.mile .wk{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:center;transition:.3s}
.mile.active .wk,.mile.done .wk{color:var(--navy)}
.tl-detail{background:#fff;border:1px solid var(--line);border-radius:24px;padding:clamp(24px,4vw,38px);box-shadow:var(--shadow-sm);margin-top:34px;display:grid;grid-template-columns:1.45fr 1fr;gap:clamp(24px,4vw,40px)}
@media(max-width:760px){.tl-detail{grid-template-columns:1fr}}
.tl-detail h3{font-size:clamp(22px,3vw,28px)}
.tl-detail .tl-lead{color:var(--slate);font-size:clamp(15px,1.7vw,17px);margin:10px 0 20px;line-height:1.6}
.tl-list{list-style:none;display:flex;flex-direction:column;gap:12px}
.tl-list li{position:relative;padding-left:30px;font-size:14.5px;color:var(--ink);line-height:1.55}
.tl-list li::before{content:"";position:absolute;left:0;top:1px;width:19px;height:19px;border-radius:50%;background:rgba(13,107,79,.12)}
.tl-list li::after{content:"\2713";position:absolute;left:5px;top:0;color:var(--emerald);font-size:12px;font-weight:700}
.tl-side{align-self:start;background:#F6F8F7;border-radius:18px;padding:24px;display:flex;flex-direction:column;gap:20px}

/* ---- architecture (dark) ---- */
.arch{margin-top:36px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.10);border-radius:24px;padding:clamp(18px,3vw,30px)}
.arch svg{width:100%;height:auto;display:block;overflow:visible}
.flowline{stroke:rgba(19,160,122,.55);stroke-width:2;fill:none;stroke-dasharray:6 7;animation:dash 1s linear infinite}
@keyframes dash{to{stroke-dashoffset:-26}}
.feedline{stroke:rgba(212,175,55,.5);stroke-width:1.6;fill:none;stroke-dasharray:5 7;animation:dash 1.5s linear infinite}
.a-node{fill:#10243f;stroke:rgba(255,255,255,.16);stroke-width:1.2}
.a-core{fill:#0b1f3b;stroke:var(--gold);stroke-width:1.6}
.a-glow{fill:var(--emerald);animation:coreglow 2.6s ease-in-out infinite}
@keyframes coreglow{0%,100%{opacity:.10}50%{opacity:.32}}
.a-t{fill:#fff;font-family:var(--body);font-weight:600;font-size:14px}
.a-s{fill:#9fb6ad;font-family:var(--body);font-weight:500;font-size:11px}
.a-cap{fill:var(--gold);font-family:var(--body);font-weight:700;font-size:10px;letter-spacing:.14em}
.pkt{fill:var(--gold-soft)} .pkt.e{fill:#43d6a6}
.io{display:grid;grid-template-columns:1fr 64px 1fr;gap:18px;align-items:center;margin-top:30px}
@media(max-width:780px){.io{grid-template-columns:1fr}.io .arrow span{transform:rotate(90deg);display:inline-block}}
.iobox{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.12);border-radius:18px;padding:22px 24px}
.iobox .lab{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:12px}
.iobox pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;color:#cfe6dd;white-space:pre;line-height:1.65;margin:0;overflow-x:auto}
.iobox .res{margin-top:12px;font-size:13px;color:#e7d39a;font-weight:600}
.io .arrow{text-align:center;color:var(--gold)}
.io .arrow span{font-size:30px;line-height:1}
.io .arrow small{display:block;font-size:9.5px;letter-spacing:.16em;color:#9fb6ad;margin-top:4px}
.stack{display:flex;flex-wrap:wrap;gap:10px;margin-top:36px}
.stack .chip{font-size:12.5px;font-weight:600;color:#dbe7e2;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:100px;padding:9px 16px;transition:.25s}
.stack .chip:hover{border-color:var(--gold);color:#fff;transform:translateY(-2px)}
.stack .chip b{color:var(--gold-soft);font-weight:700}
.built{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:30px}
@media(max-width:860px){.built{grid-template-columns:1fr}}
.bcard{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.12);border-radius:20px;padding:26px}
.bcard .step{font-family:var(--head);color:var(--gold);font-size:15px;font-weight:700;margin-bottom:8px;display:block}
.bcard h4{font-family:var(--head);font-weight:600;font-size:19px;color:#fff;margin:0 0 10px}
.bcard p{font-size:13.5px;color:#bcccc5;line-height:1.6}
</style></head>
<body>
<div id="tip"></div>

<nav id="nav">
  <span class="brand">AceLiora<span class="ai"> AI</span></span>
  <div class="navlinks">
    <a href="#problem">The problem</a>
    <a href="#asis">As-is</a>
    <a href="#engine">The engine</a>
    <a href="#architecture">Under the hood</a>
    <a href="#impact">The transformation</a>
    <a href="#blueprint">The blueprint</a>
  </div>
</nav>

<!-- HERO -->
<header class="hero">
  <span class="orb a"></span><span class="orb b"></span>
  <div class="hero-inner">
    <span class="eyebrow">AceLiora AI · Velocity Engine</span>
    <h1>Speed is the <span class="g">whole</span> deal.</h1>
    <p>Cadence Workflow gets <b id="h-n">400</b> inbound leads a month. Three SDRs and four AEs can't reach them in time — so the best buyers go cold before anyone calls. Here's what that costs, and what changes when AI scores and routes every lead the moment it lands.</p>
    <div class="meta">
      <div><b>120</b><span>EMPLOYEES · SERIES B</span></div>
      <div><b id="h-avg">42h</b><span>AVG FIRST RESPONSE TODAY</span></div>
      <div><b id="h-drop">27%</b><span>LEADS NEVER CONTACTED</span></div>
      <div><b id="h-speed">3×</b><span>FASTER WITH VELOCITY</span></div>
    </div>
  </div>
  <div class="scrollcue"><div class="dot"></div>Scroll</div>
</header>

<!-- THE PROBLEM -->
<section class="section" id="problem">
  <div class="wrap split">
    <div class="reveal">
      <span class="eyebrow">The problem</span>
      <h2 style="margin:14px 0 20px">More leads than the team can humanly answer.</h2>
      <p class="lead">Inbound is healthy — demos, trials, webinars, referrals. But qualification is manual, and the people doing it are outnumbered. Leads arrive around the clock; the team works business hours. The gap is where revenue quietly disappears.</p>
    </div>
    <div class="reveal cards" style="grid-template-columns:1fr 1fr">
      <div class="card"><div class="big num" data-count="400">0</div><div class="lab">Leads / month</div><div class="sub">across 5 channels</div></div>
      <div class="card"><div class="big" style="color:var(--navy)">7</div><div class="lab">People to handle them</div><div class="sub">3 SDRs · 4 AEs</div></div>
      <div class="card"><div class="big gold num" data-count="" id="off">0</div><div class="lab">Arrive evenings / weekends</div><div class="sub">when no one is watching</div></div>
      <div class="card"><div class="big warn num" data-count="" id="manual">0</div><div class="lab">Hours to first reply, avg</div><div class="sub">if a reply comes at all</div></div>
    </div>
  </div>
</section>

<!-- AS-IS -->
<section class="section tint" id="asis">
  <div class="wrap">
    <div class="reveal" style="max-width:720px">
      <span class="eyebrow">The as-is process</span>
      <h2 style="margin:14px 0 18px">A 42-hour average — and a very long tail.</h2>
      <p class="lead">Most leads wait a day or more. A few get a fast reply; many get one far too late; over a quarter get nothing. This is the distribution executives never see — every bar to the right of "4h" is a buyer losing interest.</p>
    </div>
    <div class="reveal cards" style="margin-top:40px">
      <div class="card"><div class="big warn"><span class="num" data-count="42" data-suffix="h">0</span></div><div class="lab">Average first response</div><div class="sub" id="med">median ~25h</div></div>
      <div class="card"><div class="big warn"><span class="num" data-count="" id="dropcard">0</span></div><div class="lab">Never contacted</div><div class="sub" id="dropn">— leads dropped</div></div>
      <div class="card"><div class="big" style="color:var(--navy)"><span class="num" data-count="" id="conv">0</span></div><div class="lab">Eventually contacted</div><div class="sub">at wildly varying speed</div></div>
    </div>
    <div class="reveal chartcard" style="margin-top:24px">
      <h3>First-response time distribution <span style="font-weight:400;font-size:14px;color:var(--muted)">— contacted leads</span></h3>
      <div class="bars" id="hist"></div>
      <div class="axisnote"><span>faster ←</span><span>time to first human reply</span><span>→ slower</span></div>
    </div>
  </div>
</section>

<!-- COST -->
<section class="section dark">
  <div class="wrap cost reveal">
    <div class="figure num" id="hotnever">0</div>
    <div style="flex:1;min-width:280px">
      <span class="eyebrow">The cost</span>
      <h2 style="margin:14px 0 16px">High-intent buyers, ignored entirely.</h2>
      <p class="lead"><span id="hotnever-line"></span> of <b id="hottotal">61</b> high-priority leads — people who named a budget, the authority to buy, and a deadline — were never contacted under the as-is process. These are the deals that pay for the quarter, lost to a queue.</p>
    </div>
  </div>
</section>

<!-- ENGINE -->
<section class="section" id="engine">
  <div class="wrap">
    <div class="reveal" style="max-width:760px">
      <span class="eyebrow">The engine</span>
      <h2 style="margin:14px 0 18px">Every lead, scored the second it arrives.</h2>
      <p class="lead">Velocity reads each lead's own message and scores it on <b>BANT</b> — Budget, Authority, Need, Timeline — then routes it: hot leads to an AE in minutes, the rest into the right nurture track. Click any lead to see how it's read. <span style="color:var(--muted)" id="engine-note"></span></p>
    </div>
    <div class="reveal">
      <div class="tabs" id="tabs">
        <button data-t="high" class="active"><span class="d" style="background:var(--emerald)"></span>High</button>
        <button data-t="medium"><span class="d" style="background:var(--gold)"></span>Medium</button>
        <button data-t="low"><span class="d" style="background:var(--lowc)"></span>Low</button>
      </div>
      <div class="explorer">
        <div class="leadlist" id="leadlist"></div>
        <div class="detail" id="detail"></div>
      </div>
    </div>
  </div>
</section>

<!-- ARCHITECTURE -->
<section class="section dark" id="architecture">
  <div class="wrap">
    <div class="reveal" style="max-width:780px">
      <span class="eyebrow">Under the hood</span>
      <h2 style="margin:14px 0 18px">How Velocity works.</h2>
      <p class="lead">Velocity is a small, transparent Python service with a large-language model at its core. Every lead is normalized into one schema, sent to Claude with a fixed BANT rubric, and returned as a structured, auditable score — then routed by rules into your tools. Here is the path a single lead takes, end to end.</p>
    </div>

    <div class="reveal arch">
      <svg viewBox="0 0 1000 300" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Velocity data architecture">
        <defs>
          <marker id="ah" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="rgba(19,160,122,.8)"/></marker>
          <marker id="ahg" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="rgba(212,175,55,.8)"/></marker>
          <path id="p1" d="M138 140 H586" fill="none"/>
          <path id="p2" d="M694 140 H1000" fill="none"/>
          <path id="p3" d="M930 167 C 930 252, 590 252, 590 188" fill="none"/>
        </defs>

        <ellipse class="a-glow" cx="590" cy="140" rx="130" ry="76"/>

        <line class="flowline" x1="138" y1="140" x2="172" y2="140" marker-end="url(#ah)"/>
        <line class="flowline" x1="294" y1="140" x2="328" y2="140" marker-end="url(#ah)"/>
        <line class="flowline" x1="450" y1="140" x2="486" y2="140" marker-end="url(#ah)"/>
        <line class="flowline" x1="690" y1="140" x2="724" y2="140" marker-end="url(#ah)"/>
        <line class="flowline" x1="840" y1="140" x2="874" y2="140" marker-end="url(#ah)"/>
        <path class="feedline" d="M930 167 C 930 252, 590 252, 590 188" marker-end="url(#ahg)"/>
        <text class="a-s" x="590" y="278" text-anchor="middle">outcomes continuously refine the rubric</text>

        <g>
          <rect class="a-node" x="20" y="113" width="118" height="54" rx="14"/>
          <text class="a-t" x="79" y="137" text-anchor="middle">Lead sources</text>
          <text class="a-s" x="79" y="154" text-anchor="middle">5 channels</text>

          <rect class="a-node" x="176" y="113" width="118" height="54" rx="14"/>
          <text class="a-t" x="235" y="137" text-anchor="middle">Ingest API</text>
          <text class="a-s" x="235" y="154" text-anchor="middle">webhook · REST</text>

          <rect class="a-node" x="332" y="113" width="118" height="54" rx="14"/>
          <text class="a-t" x="391" y="137" text-anchor="middle">Normalize</text>
          <text class="a-s" x="391" y="154" text-anchor="middle">&#8594; lead schema</text>

          <text class="a-cap" x="590" y="80" text-anchor="middle">AI SCORING ENGINE</text>
          <rect class="a-core" x="490" y="92" width="200" height="96" rx="18"/>
          <text class="a-t" x="590" y="134" text-anchor="middle" style="font-size:16px">Claude · BANT</text>
          <text class="a-s" x="590" y="153" text-anchor="middle">structured output · reason</text>
          <text class="a-s" x="590" y="169" text-anchor="middle" style="fill:#7fa39a">Opus 4.8 / Haiku 4.5</text>

          <rect class="a-node" x="728" y="113" width="112" height="54" rx="14"/>
          <text class="a-t" x="784" y="137" text-anchor="middle">Route</text>
          <text class="a-s" x="784" y="154" text-anchor="middle">tier · SLA</text>

          <rect class="a-node" x="878" y="113" width="104" height="54" rx="14"/>
          <text class="a-t" x="930" y="137" text-anchor="middle">Act</text>
          <text class="a-s" x="930" y="154" text-anchor="middle">CRM · Slack</text>
        </g>

        <circle class="pkt" r="4"><animateMotion dur="2.6s" repeatCount="indefinite" begin="0s"><mpath href="#p1"/></animateMotion></circle>
        <circle class="pkt" r="4"><animateMotion dur="2.6s" repeatCount="indefinite" begin="1.3s"><mpath href="#p1"/></animateMotion></circle>
        <circle class="pkt" r="4"><animateMotion dur="2.4s" repeatCount="indefinite" begin="0.3s"><mpath href="#p2"/></animateMotion></circle>
        <circle class="pkt" r="4"><animateMotion dur="2.4s" repeatCount="indefinite" begin="1.6s"><mpath href="#p2"/></animateMotion></circle>
        <circle class="pkt e" r="3.5"><animateMotion dur="4s" repeatCount="indefinite" begin="0s"><mpath href="#p3"/></animateMotion></circle>
      </svg>

      <div class="io">
        <div class="iobox">
          <div class="lab">Request to Claude — per lead</div>
          <pre>system:  BANT rubric (fixed, cached)
input:   lead.message + context
output:  JSON Schema (structured)</pre>
        </div>
        <div class="arrow"><span>&#8594;</span><small>CLAUDE</small></div>
        <div class="iobox">
          <div class="lab">Structured response</div>
          <pre>{
  "budget": 3, "authority": 3,
  "need": 3,   "timeline": 3,
  "reason": "Approved budget for
    120 seats, Q3 deadline, VP buyer."
}</pre>
          <div class="res">total 12/12 &#8594; HIGH &#8594; route to an AE in 5 min</div>
        </div>
      </div>

      <div class="stack">
        <span class="chip"><b>Python 3</b> core service</span>
        <span class="chip"><b>Anthropic Claude API</b></span>
        <span class="chip">Claude <b>Opus 4.8</b></span>
        <span class="chip">Claude <b>Haiku 4.5</b> · cost mode</span>
        <span class="chip"><b>Structured Outputs</b> (Pydantic + JSON Schema)</span>
        <span class="chip">Concurrent scoring</span>
        <span class="chip">Prompt caching</span>
        <span class="chip"><b>n8n</b> / webhooks</span>
        <span class="chip">CRM &amp; <b>MCP</b> integrations</span>
        <span class="chip">JSON data layer</span>
      </div>
    </div>

    <div class="reveal built">
      <div class="bcard"><span class="step">01 · Read, don't guess</span><h4>An LLM at the core</h4><p>Claude Opus 4.8 reads each lead's own words and returns a BANT object. JSON Schema and Pydantic guarantee a valid result every time — about $0.002 per lead, ~1 minute for 400 via concurrent requests.</p></div>
      <div class="bcard"><span class="step">02 · Auditable by design</span><h4>Every score has a reason</h4><p>One fixed rubric lives in a single system prompt, and each score ships with a one-line justification. A deterministic rules engine mirrors it for free, offline runs and CI tests.</p></div>
      <div class="bcard"><span class="step">03 · Open at both ends</span><h4>Drops into your stack</h4><p>A small Python core: webhooks / n8n in; CRM, Slack, email and calendar out via each tool's API or MCP. State is plain JSON, so it fits anywhere without a migration.</p></div>
    </div>
  </div>
</section>

<!-- TRANSFORMATION -->
<section class="section tint" id="impact">
  <div class="wrap">
    <div class="reveal" style="max-width:720px">
      <span class="eyebrow">The transformation</span>
      <h2 style="margin:14px 0 18px">Flip the switch.</h2>
      <p class="lead">Same 400 leads, same team. The difference is that scoring and routing happen instantly instead of whenever someone gets to it. Toggle between today and Velocity.</p>
    </div>
    <div class="reveal">
      <div class="toggle" id="toggle"><span class="glider"></span><button class="on" data-s="asis">Today</button><button data-s="v">With Velocity</button></div>
      <div class="tcards">
        <div class="tcard"><div class="k">Average first response</div><div class="v" id="t-avg">0</div><div class="bar2"><i id="b-avg"></i></div></div>
        <div class="tcard"><div class="k">Response to high-priority leads</div><div class="v" id="t-hot">0</div><div class="bar2"><i id="b-hot"></i></div></div>
        <div class="tcard"><div class="k">Leads dropped</div><div class="v" id="t-drop">0</div><div class="bar2"><i id="b-drop"></i></div></div>
      </div>
    </div>
  </div>
</section>

<!-- PRIORITY MIX -->
<section class="section">
  <div class="wrap split">
    <div class="reveal">
      <span class="eyebrow">What's in the pipe</span>
      <h2 style="margin:14px 0 18px">The mix is the strategy.</h2>
      <p class="lead">The tiers emerged from the messages themselves — nothing was pre-labeled. Knowing that ~15% are hot and half are low-intent is exactly what lets you spend AE time where it converts.</p>
      <table class="srctable" id="srctable">
        <tr><th>Source</th><th class="n">Leads</th><th class="n">High</th><th class="n">Med</th><th class="n">Low</th></tr>
      </table>
    </div>
    <div class="reveal">
      <div class="mix" id="mix"></div>
      <div class="legend" id="legend"></div>
    </div>
  </div>
</section>

<!-- BLUEPRINT -->
<section class="section tint" id="blueprint">
  <div class="wrap">
    <div class="reveal" style="max-width:780px">
      <span class="eyebrow">The blueprint</span>
      <h2 style="margin:14px 0 18px">How you run this on your own data.</h2>
      <p class="lead">The engine in the middle is reusable and ships ready — the same scoring and routing you've just seen. The two edges are yours: your channels flow in, your tools take the action out. Click any step to see exactly what you plug in.</p>
    </div>
    <div class="reveal">
      <div class="diagram" id="diagram"></div>
      <div class="bp-legend">
        <span><i style="background:var(--emerald)"></i> AceLiora engine — reusable, ships ready</span>
        <span><i style="background:var(--slate)"></i> Your systems — plug in your own</span>
        <span><i style="background:var(--gold)"></i> Data flowing in real time</span>
      </div>
      <div class="bp-detail" id="bp-detail"></div>
    </div>

    <div class="reveal" style="margin-top:clamp(60px,9vw,104px);max-width:780px">
      <span class="eyebrow">The rollout</span>
      <h2 style="margin:14px 0 18px">From sign-off to live in three weeks.</h2>
      <p class="lead">No rip-and-replace. We plug the engine between the systems you already run, calibrate it on your own history, and switch it on. Click each milestone to see what happens.</p>
    </div>
    <div class="reveal">
      <div class="timeline" id="timeline"></div>
      <div class="tl-detail" id="tl-detail"></div>
    </div>
  </div>
</section>

<!-- PAYOFF -->
<section class="section dark">
  <div class="wrap reveal">
    <span class="eyebrow">The payoff</span>
    <h2 style="margin:14px 0 6px;max-width:18ch">From 42 hours to minutes — and nothing dropped.</h2>
    <div class="payoff">
      <div><div class="v num" id="p-speed">0</div><div class="k">Faster average first response</div></div>
      <div><div class="v num" id="p-hot">0</div><div class="k">Faster to high-priority buyers</div></div>
      <div><div class="v">0%</div><div class="k">Leads dropped, down from <span id="p-drop">27%</span></div></div>
    </div>
  </div>
</section>

<footer>
  <span class="brand">AceLiora<span class="ai" style="color:var(--gold)"> AI</span></span>
  <div class="tag">Accelerate Change · Sustain Excellence</div>
  <p class="fine">Synthetic demonstration data modeling a fictional company, Cadence Workflow. Scored by the <span id="f-engine"></span>. No real persons or companies are represented.</p>
</footer>

<script>
const D = __PAYLOAD__;

/* ---------- helpers ---------- */
const $ = s => document.querySelector(s);
const fmtDur = m => m < 1 ? "0m" : m < 60 ? Math.round(m)+" min" : (m/60>=10 ? Math.round(m/60)+"h" : (m/60).toFixed(1).replace(/\.0$/,'')+"h");
function easeOut(t){return 1-Math.pow(1-t,3);}
function countUp(el, to, {suffix="",dur=1400,dec=0}={}){
  const start=performance.now();
  function tick(now){
    const p=Math.min(1,(now-start)/dur), v=to*easeOut(p);
    el.textContent=(dec?v.toFixed(dec):Math.round(v)).toLocaleString()+suffix;
    if(p<1)requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---------- tooltip ---------- */
const tip=$("#tip");
function showTip(html,x,y){tip.innerHTML=html;tip.classList.add("show");tip.style.left=Math.min(x+14,innerWidth-230)+"px";tip.style.top=(y+14)+"px";}
function hideTip(){tip.classList.remove("show");}

/* ---------- nav scroll ---------- */
addEventListener("scroll",()=>{$("#nav").classList.toggle("scrolled",scrollY>40);});

/* ---------- hero stat fills ---------- */
$("#h-n").textContent=D.n;
$("#h-avg").textContent=Math.round(D.as_is_mean/60)+"h";
$("#h-drop").textContent=Math.round(D.never_pct)+"%";
$("#h-speed").textContent=Math.round(D.speed_x)+"×";
$("#engine-note").textContent="Currently scored by the "+D.engine+".";
$("#f-engine").textContent=D.engine;

/* ---------- reveal on scroll ---------- */
const ro=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add("in");onReveal(e.target);ro.unobserve(e.target);}});},{threshold:.18});
document.querySelectorAll(".reveal").forEach(el=>ro.observe(el));

function onReveal(el){
  // count-up any numbers inside
  el.querySelectorAll("[data-count]").forEach(n=>{
    if(n.dataset.done)return;n.dataset.done=1;
    const id=n.id;
    if(id==="off")countUp(n,Math.round(D.offhours_pct),{suffix:"%"});
    else if(id==="manual")countUp(n,Math.round(D.as_is_mean/60));
    else if(id==="dropcard")countUp(n,Math.round(D.never_pct),{suffix:"%"});
    else if(id==="conv")countUp(n,D.contacted);
    else countUp(n,+n.dataset.count||0,{suffix:n.dataset.suffix||""});
  });
  if(el.querySelector("#hist"))drawHist();
  if(el.querySelector("#hotnever")){countUp($("#hotnever"),D.high_never);$("#hottotal").textContent=D.high_total;
    $("#hotnever-line").innerHTML="<b>"+D.high_never+"</b> ("+Math.round(D.high_never_pct)+"%)";}
  if(el.querySelector(".tcards"))renderToggle();
  if(el.querySelector("#mix"))drawMix();
  if(el.querySelector("#p-speed")){countUp($("#p-speed"),Math.round(D.speed_x),{suffix:"×"});countUp($("#p-hot"),Math.round(D.hot_x),{suffix:"×"});$("#p-drop").textContent=Math.round(D.never_pct)+"%";}
}
// static text cards
$("#med").textContent="median ~"+Math.round(D.as_is_median/60)+"h";
$("#dropn").textContent=D.never+" leads dropped";

/* ---------- histogram ---------- */
function drawHist(){
  const host=$("#hist");if(host.dataset.done)return;host.dataset.done=1;
  const max=Math.max(...D.hist.map(h=>h.count))||1, tot=D.hist.reduce((a,h)=>a+h.count,0);
  D.hist.forEach((h,i)=>{
    const fast=i<=1, slow=i>=4;
    const bar=document.createElement("div");
    bar.className="bar"+(fast?" fast":slow?" slow":"");
    bar.innerHTML=`<div class="vlab">${h.count}</div><div class="col"></div><div class="xlab">${h.label}</div>`;
    host.appendChild(bar);
    const col=bar.querySelector(".col");
    setTimeout(()=>{col.style.height=(h.count/max*100)+"%";bar.classList.add("in");},120+i*90);
    bar.addEventListener("mousemove",e=>showTip(`<b>${h.count}</b> leads &middot; ${(h.count/tot*100).toFixed(0)}%<br>replied in ${h.label}`,e.clientX,e.clientY));
    bar.addEventListener("mouseleave",hideTip);
  });
}

/* ---------- priority mix + sources ---------- */
function drawMix(){
  const host=$("#mix");if(host.dataset.done)return;host.dataset.done=1;
  const order=[["high","High",D.tiers.high],["medium","Medium",D.tiers.medium],["low","Low",D.tiers.low]];
  order.forEach(([cls,lab,c],i)=>{
    const seg=document.createElement("div");seg.className="seg "+cls;
    seg.innerHTML=c/D.n>.08?`${c} · ${Math.round(c/D.n*100)}%`:"";
    host.appendChild(seg);
    setTimeout(()=>seg.style.width=(c/D.n*100)+"%",100+i*180);
  });
  $("#legend").innerHTML=order.map(([cls,lab,c])=>`<span><i style="background:${cls==='high'?'var(--emerald)':cls==='medium'?'var(--gold)':'var(--lowc)'}"></i>${lab} — ${c}</span>`).join("");
}
$("#srctable").insertAdjacentHTML("beforeend",D.sources.map(s=>
  `<tr><td>${s.label}</td><td class="n">${s.count}</td><td class="n hi">${s.high}</td><td class="n">${s.medium}</td><td class="n mut">${s.low}</td></tr>`).join(""));

/* ---------- lead explorer ---------- */
let curTier="high";
function listFor(t){
  let xs=D.leads.filter(l=>l.priority===t);
  xs.sort((a,b)=>(b.total-a.total)|| (a.contacted-b.contacted));
  const seen=new Set(), out=[];      // one card per distinct message
  for(const l of xs){ if(seen.has(l.msg))continue; seen.add(l.msg); out.push(l); }
  return out.slice(0,16);
}
function renderList(){
  const host=$("#leadlist");host.innerHTML="";
  listFor(curTier).forEach((l,idx)=>{
    const b=document.createElement("button");b.className="litem"+(idx===0?" sel":"");
    b.innerHTML=`<div class="top"><span class="pill ${l.priority}">${l.priority}</span><span class="meta">${l.source} · ${l.size} · ${l.role}</span></div>
      <div class="q">${esc(l.msg)}</div>${(!l.contacted)?'<div class="drop">⚠ Never contacted under as-is</div>':''}`;
    b.addEventListener("click",()=>{host.querySelectorAll(".litem").forEach(x=>x.classList.remove("sel"));b.classList.add("sel");renderDetail(l);});
    host.appendChild(b);
  });
  const first=listFor(curTier)[0];if(first)renderDetail(first);
}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function renderDetail(l){
  const names=[["budget","Budget"],["authority","Authority"],["need","Need"],["timeline","Timeline"]];
  const rows=names.map(([k,lab])=>{
    const v=(l.bant&&l.bant[k]!=null)?l.bant[k]:0;
    return `<div class="row"><span class="name">${lab}</span><div class="track"><i class="fill" data-w="${v/3*100}"></i></div><span class="score">${v}/3</span></div>`;
  }).join("");
  const sla=D.sla[l.priority];
  $("#detail").innerHTML=`
    <div class="q">${esc(l.msg)}</div>
    <div style="font-size:11.5px;color:var(--muted);letter-spacing:.04em;margin-bottom:14px">${l.source.toUpperCase()} · ${l.region} · ${l.size} · ${l.role}</div>
    <div class="bant">${rows}</div>
    ${l.reason?`<div class="reason"><b>Why:</b> ${esc(l.reason)}</div>`:`<div class="reason">BANT total <b>${l.total}/12</b> → <b>${l.priority}</b> priority.</div>`}
    <div class="routed"><span style="color:var(--muted)">Velocity routes this lead in</span> <b>${fmtDur(sla)}</b></div>`;
  requestAnimationFrame(()=>$("#detail").querySelectorAll(".fill").forEach(f=>f.style.width=f.dataset.w+"%"));
}
$("#tabs").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  curTier=b.dataset.t;$("#tabs").querySelectorAll("button").forEach(x=>x.classList.remove("active"));b.classList.add("active");renderList();});
renderList();

/* ---------- transformation toggle ---------- */
const states={
  asis:{avg:[D.as_is_mean,"bad"],hot:[D.high_as_is_mean,"bad"],drop:[D.never_pct,"bad"]},
  v:{avg:[D.to_be_mean,"good"],hot:[D.sla.high,"good"],drop:[0,"good"]}
};
let tState="asis", maxAvg=D.as_is_mean, maxHot=D.high_as_is_mean, maxDrop=D.never_pct;
function setMetric(vEl,bEl,val,cls,fmt,frac,color){
  vEl.className="v "+cls;
  if(fmt==="pct"){countUp(vEl,Math.round(val),{suffix:"%"});}
  else{ // duration: animate then format
    const start=performance.now(),from=parseFloat(vEl.dataset.cur||val);
    (function tick(now){const p=Math.min(1,(now-start)/900),cur=from+(val-from)*easeOut(p);vEl.textContent=fmtDur(cur);if(p<1)requestAnimationFrame(tick);})(performance.now());
    vEl.dataset.cur=val;
  }
  bEl.style.width=Math.max(3,frac*100)+"%";bEl.style.background=color;
}
function renderToggle(){
  const s=states[tState], good=tState==="v";
  const col=good?"linear-gradient(90deg,#13a07a,#0D6B4F)":"linear-gradient(90deg,#c96a4f,#9a3f29)";
  setMetric($("#t-avg"),$("#b-avg"),s.avg[0],s.avg[1],"dur",s.avg[0]/maxAvg,col);
  setMetric($("#t-hot"),$("#b-hot"),s.hot[0],s.hot[1],"dur",s.hot[0]/maxHot,col);
  setMetric($("#t-drop"),$("#b-drop"),s.drop[0],s.drop[1],"pct",(s.drop[0]/maxDrop)||0.02,col);
  document.querySelectorAll(".tcard").forEach(c=>c.classList.toggle("live",good));
}
$("#toggle").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  tState=b.dataset.s;$("#toggle").classList.toggle("v",tState==="v");
  $("#toggle").querySelectorAll("button").forEach(x=>x.classList.toggle("on",x.dataset.s===tState));renderToggle();});

/* ---------- blueprint diagram ---------- */
const STAGES=[
 {id:"sources",kind:"yours",title:"Lead sources",short:"Every inbound channel",
  desc:`Every way a prospect reaches you becomes an input — no channel left unwatched.`,
  bring:`Web forms, CRM, shared inbox, ad & landing pages, demo bookings, live chat.`,
  tech:`Native integrations or webhooks push each new lead the moment it is created.`,
  example:`A Typeform submission and a HubSpot contact both arrive as the same kind of event.`},
 {id:"ingest",kind:"engine",title:"Capture & normalize",short:"One lead, one schema",
  desc:`Messy inputs from many channels are mapped into one consistent lead record the engine understands.`,
  bring:`A one-time field map from your forms and CRM to the standard schema.`,
  tech:`n8n / Make / Zapier or a small API endpoint, mapping to { source, role, company size, region, message, timestamp }.`,
  example:`Your form's "Company" and "Title" fields become company-size band and contact role.`},
 {id:"score",kind:"engine",title:"AI scoring",short:"Claude reads & scores BANT",
  desc:`Claude reads each lead's own words and scores Budget, Authority, Need and Timeline — with a reason for every score.`,
  bring:`Your definition of a good lead — your qualifying criteria, in plain English.`,
  tech:`Claude API with structured outputs and your BANT rubric in the prompt. Auditable, ~$0.002 per lead.`,
  example:`"Approved budget for 85 seats, rollout by Q3" scores High, with the reasoning attached.`},
 {id:"route",kind:"engine",title:"Routing rules",short:"Tier maps to action & SLA",
  desc:`Each priority tier triggers an action and a response-time target — automatically, day or night.`,
  bring:`Your SLAs and ownership rules: who gets what, and how fast.`,
  tech:`A rules layer: High to an AE in 5 min, Medium to the SDR queue, Low to a nurture track.`,
  example:`A hot lead pages the right AE and offers a meeting before it has a chance to cool.`},
 {id:"act",kind:"yours",title:"Your tools act",short:"CRM, Slack, email, calendar",
  desc:`The decision flows straight into the tools your team already works in — no new screen to babysit.`,
  bring:`Your CRM, your comms, your calendar.`,
  tech:`CRM update + Slack/Teams alert + email/SMS + calendar auto-booking, via each tool's API or MCP.`,
  example:`A deal is created, the sales channel is pinged, and a meeting link is sent — hands-free.`},
 {id:"learn",kind:"engine",title:"Measure & improve",short:"Outcomes refine scoring",
  desc:`Won and lost outcomes feed back so the scoring gets sharper on your business over time.`,
  bring:`Deal outcomes from your CRM.`,
  tech:`This dashboard plus a feedback loop that tunes the rubric on your real results.`,
  example:`If trial leads convert better than scored, the weights adjust to match reality.`}
];
const nodeHost=$("#diagram"), bpDetail=$("#bp-detail");
function renderBP(s){
  bpDetail.innerHTML=`<div class="bp-h"><span class="ntag ${s.kind}">${s.kind==="engine"?"AceLiora engine — ships ready":"Your system — plug in yours"}</span><h3>${s.title}</h3></div>
    <p class="bp-desc">${s.desc}</p>
    <div class="bp-grid">
      <div><div class="bp-k">What you bring</div><div class="bp-v">${esc(s.bring)}</div></div>
      <div><div class="bp-k">How it's built</div><div class="bp-v">${esc(s.tech)}</div></div>
    </div>
    <div class="bp-ex"><b>Example:</b> ${esc(s.example)}</div>`;
}
function renderDiagram(){
  nodeHost.innerHTML="";
  STAGES.forEach((s,i)=>{
    const n=document.createElement("button");
    n.className="node "+s.kind+(i===0?" sel":"");
    n.innerHTML=`<span class="step">${String(i+1).padStart(2,"0")}</span>
      <span class="ntag ${s.kind}">${s.kind==="engine"?"AceLiora":"Your system"}</span>
      <span class="ntitle">${s.title}</span><span class="nshort">${s.short}</span>`;
    n.addEventListener("click",()=>{nodeHost.querySelectorAll(".node").forEach(x=>x.classList.remove("sel"));n.classList.add("sel");renderBP(s);});
    nodeHost.appendChild(n);
    if(i<STAGES.length-1){const f=document.createElement("div");f.className="flow";f.innerHTML='<span class="line"></span><span class="dot"></span><span class="head"></span>';nodeHost.appendChild(f);}
  });
  renderBP(STAGES[0]);
}
renderDiagram();

/* ---------- rollout timeline ---------- */
const PHASES=[
 {wk:"Week 1",title:"Connect & map",
  lead:"Wire up your channels and teach the engine your data.",
  items:["Connect lead sources — forms, CRM, shared inbox, ads — via webhooks or native integrations","Map your fields to the standard lead schema (a one-time step)","Import 3–6 months of historical leads to calibrate against"],
  who:"AceLiora + your RevOps / admin",
  out:"Every new lead flowing into one clean, normalized stream."},
 {wk:"Week 2",title:"Calibrate the engine",
  lead:"Tune the scoring to what “good” means for your business.",
  items:["Define your BANT rubric in plain English","Score your historical leads and compare tiers to known won/lost deals","Adjust thresholds until High / Medium / Low match your reality"],
  who:"AceLiora + your sales lead",
  out:"A scoring model validated against your own outcomes — not a generic template."},
 {wk:"Week 3",title:"Route & go live",
  lead:"Connect the actions and switch it on.",
  items:["Wire actions into your CRM, Slack/Teams, email and calendar","Set SLAs and ownership — who gets what, and how fast","Run in shadow mode for a few days, confirm, then go live"],
  who:"AceLiora + your tools admin",
  out:"Hot leads reaching the right rep in minutes — automatically, around the clock."},
 {wk:"Ongoing",title:"Measure & improve",
  lead:"Keep it sharp as your pipeline evolves.",
  items:["Weekly review on this dashboard","Feed won/lost outcomes back to refine the rubric","Add new channels or tools as you grow"],
  who:"AceLiora (light-touch)",
  out:"Compounding accuracy with near-zero ongoing manual effort."}
];
function renderTL(i){
  const host=$("#timeline");
  host.querySelectorAll(".mile").forEach((m,j)=>{m.classList.toggle("active",j===i);m.classList.toggle("done",j<i);});
  $("#tl-prog").style.right=(100-(PHASES.length>1?i/(PHASES.length-1)*100:0))+"%";
  const p=PHASES[i];
  $("#tl-detail").innerHTML=`
    <div class="tl-main">
      <span class="eyebrow">${p.wk}</span>
      <h3 style="margin-top:10px">${p.title}</h3>
      <p class="tl-lead">${esc(p.lead)}</p>
      <ul class="tl-list">${p.items.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
    </div>
    <div class="tl-side">
      <div><div class="bp-k">Who's involved</div><div class="bp-v">${esc(p.who)}</div></div>
      <div><div class="bp-k">You walk away with</div><div class="bp-v">${esc(p.out)}</div></div>
    </div>`;
}
function buildTL(){
  const host=$("#timeline");
  host.innerHTML='<div class="rail"><div class="prog" id="tl-prog"></div></div>'+
    PHASES.map((p,i)=>`<div class="mile" data-i="${i}"><span class="dot"></span><span class="wk">${p.wk}</span></div>`).join("");
  host.querySelectorAll(".mile").forEach(m=>m.addEventListener("click",()=>renderTL(+m.dataset.i)));
  renderTL(0);
}
buildTL();
</script>
</body></html>"""

HTML = HTML.replace("__PAYLOAD__", DATA_JSON)
with open(OUT, "w") as f:
    f.write(HTML)
print(f"Wrote {OUT}")
print(f"  tiers {dict(tiers)} | speed {payload['speed_x']:.0f}x | hot {payload['hot_x']:.0f}x | dropped {payload['never_pct']:.0f}%")
