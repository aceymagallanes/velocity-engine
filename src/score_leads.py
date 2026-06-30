#!/usr/bin/env python3
"""Velocity engine — lead scoring & prioritization (deterministic rules pass).

Reads data/leads.json, scores each lead on BANT (Budget / Authority / Need /
Timeline) from its stated_need (with contact_role / company_size_band as
supporting signals), assigns a priority tier, and computes a 'to-be' first-
response SLA. Writes data/leads_scored.json and prints an as-is vs to-be
impact report.

This is the rules pass: transparent, free, offline. It establishes the pipeline
so a Claude-API scorer can be swapped in for the Need/intent read later.
"""
import json, re, statistics
from collections import Counter

SRC = "data/leads.json"
OUT = "data/leads_scored.json"

# ---- Signal cues (lowercased substring / regex matches) ------------------
BUDGET_CUES = [
    "budget", "approved", "sign-off", "signed off", "allocated", "allocate",
    "set aside", "purchasing authority", "purchase", "quote", "contract",
    "annual billing", "pricing proposal", "board approved", "money's set",
]
BUDGET_WEAK = ["pricing", "how much", "cost", "price", "per-seat", "per seat", "plan"]

AUTHORITY_CUES = [
    "i'm the", "i am the", "i run", "i manage", "head of", "director",
    " vp ", "vp of", "c-level", "coo", "ceo", "owner", "program lead",
    "purchasing authority", "approved to buy", "i've been approved",
    "i have purchasing", "asked me to", "board approved",
]
AUTHORITY_NEG = ["need my manager", "would need my manager", "bring it to the team",
                 "need to confirm with", "school assignment", "personal to-do"]

NEED_CUES = [
    "replace", "migrat", "consolidat", "switch", "outgrow", "killing us",
    "lose hours", "losing hours", "bleed hours", "billable hours",
    "missing deadlines", "miss deadlines", "late projects", "slipping",
    "status chasing", "visibility", "no portal", "reporting",
    "off spreadsheets", "spreadsheets are", "off trello", "off jira", "off asana",
    "standardize", "resource planning", "capacity planning", "scaling from",
    "scale with us", "double-book", "double booking", "dependencies",
    "onboard", "onboarding", "time tracking", "integrate", "integration",
    "auditable", "audit", "sprint",
]
NEED_WEAK = ["track", "manage", "evaluating", "evaluate", "looking for", "need ", "tool"]

TIMELINE_CUES = [
    "this week", "this quarter", "this month", "end of month", "by end of",
    "by july", "by august", "before q3", "before our", "deadline", "go-live",
    "go live", "renews in", "renewal", "fiscal year", "next sprint",
    "within the next", "weeks", "ready to buy now", "buy now", "before then",
    r"\bby \w+\b", "kickoff",
]
TIMELINE_WEAK = ["soon", "soon-ish", "this year", "next year", "upcoming"]

ROLE_AUTHORITY = {  # supporting signal from structured field
    "c_level": 3, "owner": 3, "vp": 3, "director": 2, "manager": 1, "junior": 0,
}
SIZE_WEIGHT = {  # bigger deal => slightly higher need/value
    "enterprise": 1.0, "large": 0.8, "mid": 0.6, "small": 0.4, "solo": 0.2,
}


def count_hits(text, cues):
    n = 0
    matched = []
    for c in cues:
        if c.startswith("\\") or "\\b" in c:
            if re.search(c, text):
                n += 1; matched.append(c)
        elif c in text:
            n += 1; matched.append(c)
    return n, matched


def score_lead(lead):
    t = lead["stated_need"].lower()
    role = lead["contact_role"]

    # --- Budget (0-3) ---
    strong, _ = count_hits(t, BUDGET_CUES)
    weak, _ = count_hits(t, BUDGET_WEAK)
    budget = min(3, strong * 2 + (1 if weak else 0))

    # --- Authority (0-3): message cues + structured role ---
    a_strong, _ = count_hits(t, AUTHORITY_CUES)
    a_neg, _ = count_hits(t, AUTHORITY_NEG)
    msg_auth = min(3, a_strong)
    authority = max(0, round((msg_auth + ROLE_AUTHORITY[role]) / 2) - a_neg)
    authority = min(3, authority)

    # --- Need (0-3) ---
    n_strong, _ = count_hits(t, NEED_CUES)
    n_weak, _ = count_hits(t, NEED_WEAK)
    need = min(3, n_strong * 2 + (1 if n_weak else 0))

    # --- Timeline (0-3) ---
    tl_strong, _ = count_hits(t, TIMELINE_CUES)
    tl_weak, _ = count_hits(t, TIMELINE_WEAK)
    timeline = min(3, tl_strong + (1 if tl_weak else 0))

    total = budget + authority + need + timeline  # 0..12

    if total >= 8:
        tier = "high"
    elif total >= 3:
        tier = "medium"
    else:
        tier = "low"

    return {
        "bant": {"budget": budget, "authority": authority, "need": need, "timeline": timeline},
        "bant_total": total,
        "priority": tier,
    }


# To-be SLA (minutes) by tier — the routed, automated target state.
TO_BE_SLA = {"high": 5, "medium": 60, "low": 1440}


def main():
    with open(SRC) as f:
        data = json.load(f)
    leads = data["leads"]

    for ld in leads:
        s = score_lead(ld)
        ld["bant"] = s["bant"]
        ld["bant_total"] = s["bant_total"]
        ld["priority"] = s["priority"]
        ld["to_be_first_response_minutes"] = TO_BE_SLA[s["priority"]]

    # ---- impact math ----
    N = len(leads)
    tiers = Counter(l["priority"] for l in leads)
    contacted = [l for l in leads if l["as_is_contacted"]]
    as_is_vals = [l["as_is_first_response_minutes"] for l in contacted]
    never = [l for l in leads if not l["as_is_contacted"]]

    # As-is, treating never-contacted as unbounded misses (use them for the
    # "leads dropped" story, not the average).
    as_is_mean = statistics.mean(as_is_vals)
    as_is_median = statistics.median(as_is_vals)

    # To-be: every lead gets routed (0% dropped).
    to_be_vals = [l["to_be_first_response_minutes"] for l in leads]
    to_be_mean = statistics.mean(to_be_vals)

    # The painful slice: HIGH-priority leads under the as-is process.
    high = [l for l in leads if l["priority"] == "high"]
    high_contacted = [l for l in high if l["as_is_contacted"]]
    high_never = [l for l in high if not l["as_is_contacted"]]
    high_as_is_mean = (statistics.mean(l["as_is_first_response_minutes"] for l in high_contacted)
                       if high_contacted else 0)

    meta = data.get("_meta", {})
    meta["scoring"] = {
        "engine": "Velocity rules pass v1 (deterministic BANT)",
        "tier_thresholds": {"high": ">=8 / 12", "medium": "3-7 / 12", "low": "0-2 / 12"},
        "to_be_sla_minutes": TO_BE_SLA,
        "tier_counts": dict(tiers),
    }
    data["_meta"] = meta

    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)

    # ---- report ----
    def pct(x): return f"{x/N*100:.1f}%"
    print("=== PRIORITY TIERS (emerged from the messages) ===")
    for k in ["high", "medium", "low"]:
        print(f"  {k:7} {tiers[k]:3}  ({pct(tiers[k])})")
    print(f"  (target was ~15% / 35% / 50%)")

    print("\n=== AS-IS  (current broken intake) ===")
    print(f"  contacted leads      : {len(contacted)} / {N}")
    print(f"  never contacted      : {len(never)}  ({pct(len(never))}) -> dropped revenue")
    print(f"  avg first response   : {as_is_mean:,.0f} min  (~{as_is_mean/60:.1f}h)")
    print(f"  median first response: {as_is_median:,.0f} min  (~{as_is_median/60:.1f}h)")

    print("\n=== HIGH-PRIORITY LEADS UNDER AS-IS (the costly failure) ===")
    print(f"  high-priority leads  : {len(high)}")
    print(f"  ...never contacted   : {len(high_never)}  ({len(high_never)/len(high)*100:.0f}% of hot leads dropped)")
    print(f"  ...avg response (when contacted): {high_as_is_mean:,.0f} min  (~{high_as_is_mean/60:.1f}h)")

    print("\n=== TO-BE  (Velocity-routed) ===")
    print(f"  leads routed         : {N} / {N}  (0% dropped)")
    print(f"  high  -> {TO_BE_SLA['high']} min,  medium -> {TO_BE_SLA['medium']} min,  low -> {TO_BE_SLA['low']} min")
    print(f"  avg first response   : {to_be_mean:,.0f} min  (~{to_be_mean/60:.1f}h)")

    print("\n=== HEADLINE IMPACT ===")
    print(f"  avg first response:  {as_is_mean:,.0f} min  ->  {to_be_mean:,.0f} min   "
          f"({as_is_mean/to_be_mean:.0f}x faster)")
    print(f"  hot-lead response:   {high_as_is_mean:,.0f} min  ->  {TO_BE_SLA['high']} min   "
          f"({high_as_is_mean/TO_BE_SLA['high']:.0f}x faster)")
    print(f"  leads dropped:       {pct(len(never))}  ->  0%")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
