#!/usr/bin/env python3
"""Generate a synthetic lead dataset for the Velocity engine demo (Cadence Workflow)."""
import json, random, math, statistics, datetime as dt

random.seed(42)

N = 400

# ---- Source mix (counts) -------------------------------------------------
SOURCE_COUNTS = {
    "demo_request": 100,   # 25%
    "free_trial": 120,     # 30%
    "content_webinar": 100,# 25%
    "paid_ad": 60,         # 15%
    "referral": 20,        # 5%
}

# ---- Per-source skew toward an intent tier -------------------------------
# tiers: high (B+A+N+T), medium (1-2 signals), low (weak / no signal)
SOURCE_TIER_WEIGHTS = {
    "demo_request":    {"high": 0.34, "medium": 0.46, "low": 0.20},
    "referral":        {"high": 0.45, "medium": 0.40, "low": 0.15},
    "free_trial":      {"high": 0.12, "medium": 0.38, "low": 0.50},
    "content_webinar": {"high": 0.04, "medium": 0.26, "low": 0.70},
    "paid_ad":         {"high": 0.03, "medium": 0.22, "low": 0.75},
}

# Company-size skew per source (bigger for demo/referral)
SOURCE_SIZE_WEIGHTS = {
    "demo_request":    {"solo": 0.03, "small": 0.17, "mid": 0.40, "large": 0.28, "enterprise": 0.12},
    "referral":        {"solo": 0.05, "small": 0.20, "mid": 0.38, "large": 0.25, "enterprise": 0.12},
    "free_trial":      {"solo": 0.20, "small": 0.34, "mid": 0.28, "large": 0.13, "enterprise": 0.05},
    "content_webinar": {"solo": 0.22, "small": 0.34, "mid": 0.26, "large": 0.13, "enterprise": 0.05},
    "paid_ad":         {"solo": 0.30, "small": 0.36, "mid": 0.22, "large": 0.09, "enterprise": 0.03},
}

# Role skew per source (more senior for demo/referral)
SOURCE_ROLE_WEIGHTS = {
    "demo_request":    {"junior": 0.08, "manager": 0.28, "director": 0.28, "vp": 0.16, "c_level": 0.12, "owner": 0.08},
    "referral":        {"junior": 0.05, "manager": 0.22, "director": 0.28, "vp": 0.18, "c_level": 0.15, "owner": 0.12},
    "free_trial":      {"junior": 0.26, "manager": 0.30, "director": 0.16, "vp": 0.07, "c_level": 0.05, "owner": 0.16},
    "content_webinar": {"junior": 0.30, "manager": 0.30, "director": 0.15, "vp": 0.06, "c_level": 0.04, "owner": 0.15},
    "paid_ad":         {"junior": 0.32, "manager": 0.26, "director": 0.12, "vp": 0.05, "c_level": 0.03, "owner": 0.22},
}

REGIONS = [
    ("United States", 0.30), ("United Kingdom", 0.10), ("Canada", 0.08),
    ("Australia", 0.07), ("Germany", 0.07), ("Netherlands", 0.04),
    ("France", 0.04), ("Singapore", 0.04), ("India", 0.06),
    ("Ireland", 0.03), ("Spain", 0.03), ("Sweden", 0.03),
    ("Philippines", 0.03), ("United Arab Emirates", 0.02), ("Brazil", 0.02),
    ("Japan", 0.02), ("New Zealand", 0.02),
]

# ---- Stated-need message pools by BANT strength --------------------------
# Each tier spans many industries, roles, and distinct problems — no two
# messages should read as paraphrases of one another.

# HIGH: clear Budget, Authority, Need, Timeline.
HIGH = [
    "I'm the COO of a 90-person marketing agency. The board wants real-time project reporting and I've approved the budget to fix it this quarter. We need to replace three disconnected tools before our fiscal close in 5 weeks.",
    "Director of Client Services here. Clients keep asking where their projects stand and we have no portal to show them. I've got sign-off to buy and need it live before our biggest account's renewal in 3 weeks — please send pricing for 45 seats.",
    "I run operations for a construction firm and we keep double-booking crews across sites. Ownership approved a budget to fix scheduling this month. We need to onboard 70 users and integrate with our timesheet system fast.",
    "VP of Engineering at a fully remote startup. We're missing sprint deadlines because work is invisible across time zones. Budget is approved for 120 seats and we want to roll out before the next quarter begins.",
    "Head of PMO at a healthcare admin group. Compliance needs an auditable trail on every project and our current tool can't produce one. The spend is signed off — we must migrate 110 users before our audit in 6 weeks.",
    "Program Director at a nonprofit juggling 20+ grant-funded projects with hard reporting deadlines we keep missing. The board approved funding to fix this; we need to be live before our next grant cycle next month.",
    "I own a 40-person consultancy and we lose billable hours to clumsy time tracking. Ready to buy now — our current tool renews in 20 days and I want to switch before then. Can you quote annual billing?",
    "Operations VP at a manufacturer. Our product launch is slipping because no one can see cross-team dependencies. The board approved tooling spend; we need 90 users live and integrated with our ERP before launch in 6 weeks.",
    "I'm the owner — we're scaling from 15 to 50 staff and our spreadsheets are buckling. Money's set aside and I want a system locked in this month. Does it handle client onboarding workflows end to end?",
    "Director of Development at a real estate firm. We manage dozens of build projects with zero central visibility. I have purchasing authority and a hard deadline — this needs to be in place before Q3 groundbreaking. Send enterprise pricing.",
    "VP of Operations at an edtech company. We onboard 30 new hires next month and the project chaos will only scale with us. Budget is approved — I need a tool that handles onboarding and reporting, rolled out within 3 weeks.",
    "Head of Delivery at a 200-person agency. We bleed hours every week to status chasing and I've been approved to consolidate onto one platform. I have sign-off for 85 seats and need to migrate before our Q3 kickoff.",
    "Director of Engineering. Our COO asked me to replace Jira by July and budget is approved for up to 150 seats. We need a clear migration plan and a contract — who can walk me through enterprise onboarding this week?",
    "I'm the founder of a creative studio. Late projects are costing us repeat business and I've ring-fenced budget to fix it now. We need capacity planning across 35 people, live before our busiest season starts in a month.",
]

# MEDIUM: one or two BANT signals present.
MEDIUM = [
    "We're a growing marketing team of about 25 and outgrowing our current setup. Curious how your seat pricing works and whether you offer onboarding support.",
    "I manage a small dev team and we keep stepping on each other's work. Evaluating a few tools this quarter — how do you compare to ClickUp?",
    "Looking for something to give clients visibility into project status. I'd champion it internally but my manager controls the budget. Can you send pricing?",
    "Our team keeps missing deadlines and I think we need better visibility. Not sure on budget yet — what does a mid-size plan cost?",
    "Director here, mapping out next year's resource planning. Interested but early — what's the difference between your tiers?",
    "We trialed two competitors already and I like yours best. I'd need to bring it to the team, but wanted pricing first.",
    "Manager of a 12-person team. We need better task tracking soon-ish. Is there a plan that fits a team our size?",
    "Exploring tools to handle our growing client load. Might expand to the whole agency later — what's the entry pricing?",
    "We're thinking about moving off email and spreadsheets. No hard deadline, but want to know if it's worth it. Can I get a walkthrough?",
    "Need to understand your Slack and Google Calendar integrations before we'd commit. Mid-size team weighing a couple of options.",
    "Evaluating PM tools for our department. Do you support time tracking and client reporting? Budget conversations haven't started.",
    "We might need this for an upcoming project — not confirmed yet. Curious about per-seat costs for around 30 people.",
    "Our agency is growing and handoffs between teams are getting messy. Want to see if your tool fixes that — pricing for 20 seats?",
    "Considering a switch because our current tool has no real reporting. Early stage, gathering options. What tiers do you offer?",
]

# LOW: weak — little or no BANT signal.
LOW = [
    "Just exploring what's out there.",
    "Saw your ad and wanted to see what this is about.",
    "How much is it?",
    "Looking for free project management software.",
    "Signed up to check it out.",
    "Is there a free version?",
    "Found you through a Google search, just browsing.",
    "Wanted to see the features.",
    "Doing some research for a school project.",
    "Came from the webinar — thanks for the tips!",
    "Not sure yet, just looking around.",
    "Can I get a trial without a credit card?",
    "What does this actually do?",
    "A friend mentioned it so I'm taking a look.",
    "Could this work for personal to-do lists?",
    "Just curious.",
    "Downloaded your ebook, now poking around the product.",
    "Testing this out for fun.",
    "Comparing a bunch of tools — you're one of many.",
    "Saw a LinkedIn post about you.",
    "Might use it someday, not right now.",
    "Interesting product, no immediate plans.",
    "Do you have a mobile app?",
    "Is this basically like Trello?",
    "Comparing your pricing to Asana out of curiosity.",
]

POOLS = {"high": HIGH, "medium": MEDIUM, "low": LOW}


def weighted_choice(weights: dict):
    keys = list(weights.keys())
    vals = list(weights.values())
    return random.choices(keys, weights=vals, k=1)[0]


def region_choice():
    names = [r[0] for r in REGIONS]
    w = [r[1] for r in REGIONS]
    return random.choices(names, weights=w, k=1)[0]


# ---- created_at: spread across June 2026, biased to evenings/weekends ----
YEAR, MONTH, DAYS = 2026, 6, 30

def random_timestamp():
    day = random.randint(1, DAYS)
    date = dt.date(YEAR, MONTH, day)
    is_weekend = date.weekday() >= 5  # Sat=5, Sun=6
    # Hour distribution: deliberately heavy on evenings/off-hours.
    # ~45% evening/night (18:00-23:59 + 00:00-06:59), rest business hours.
    r = random.random()
    if r < 0.30:           # evening 18-23
        hour = random.randint(18, 23)
    elif r < 0.45:         # late night / early morning 0-6
        hour = random.randint(0, 6)
    else:                  # business hours 7-17
        hour = random.randint(7, 17)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return dt.datetime(YEAR, MONTH, day, hour, minute, second), is_weekend


# ---- Build source assignment list ----------------------------------------
source_list = []
for src, cnt in SOURCE_COUNTS.items():
    source_list += [src] * cnt
random.shuffle(source_list)

leads = []
raw_response = []  # parallel list of raw lognormal minutes for contacted, else None

for i, src in enumerate(source_list, start=1):
    tier = weighted_choice(SOURCE_TIER_WEIGHTS[src])
    size = weighted_choice(SOURCE_SIZE_WEIGHTS[src])
    role = weighted_choice(SOURCE_ROLE_WEIGHTS[src])
    region = region_choice()
    need = random.choice(POOLS[tier])
    ts, _ = random_timestamp()

    # ~30% never contacted
    contacted = random.random() >= 0.30
    if contacted:
        # lognormal long tail; a small slice of genuinely fast responses
        if random.random() < 0.08:
            raw = random.uniform(5, 90)          # the rare quick rep
        else:
            raw = random.lognormvariate(7.0, 1.05)
        raw_response.append(raw)
    else:
        raw_response.append(None)

    leads.append({
        "lead_id": f"L{i:04d}",
        "created_at": ts.isoformat(),
        "source": src,
        "company_size_band": size,
        "contact_role": role,
        "region": region,
        "stated_need": need,
        "as_is_first_response_minutes": None,   # filled after calibration
        "as_is_contacted": contacted,
    })

# ---- Calibrate contacted response times to mean ~2520 min ----------------
contacted_idx = [k for k, v in enumerate(raw_response) if v is not None]
cur_mean = statistics.mean(raw_response[k] for k in contacted_idx)
scale = 2520.0 / cur_mean
for k in contacted_idx:
    val = max(1, round(raw_response[k] * scale))
    leads[k]["as_is_first_response_minutes"] = val

# Sort by created_at for a natural chronological file, then relabel ids.
leads.sort(key=lambda x: x["created_at"])
for i, ld in enumerate(leads, start=1):
    ld["lead_id"] = f"L{i:04d}"

# ---- _meta ---------------------------------------------------------------
meta = {
    "synthetic": True,
    "note": "This data is SYNTHETIC and modeled, not real. Generated for the Velocity engine demo to illustrate lead intake and BANT-style prioritization.",
    "models_company": {
        "name": "Cadence Workflow",
        "description": "Fictional B2B SaaS selling project-management software to mid-market teams on a monthly per-seat subscription.",
        "stage": "~120 employees, Series B, under pressure to grow new revenue.",
        "go_to_market": "Inbound handled by 3 SDRs feeding 4 Account Executives.",
    },
    "generated_for": "Velocity engine demo",
    "record_count": N,
    "calibration_targets": {
        "source_mix": {"demo_request": "25%", "free_trial": "30%", "content_webinar": "25%", "paid_ad": "15%", "referral": "5%"},
        "priority_spread_intended": {"high": "~15%", "medium": "~35%", "low": "~50%"},
        "as_is_first_response_minutes_mean_contacted": "~2520 (≈42 hours), long-tailed",
        "never_contacted_share": "~30%",
        "created_at_window": "Most recent calendar month (June 2026); deliberately includes evenings and weekends.",
    },
    "field_schema": {
        "lead_id": "L0001..L0400",
        "created_at": "ISO 8601 timestamp",
        "source": "demo_request | free_trial | content_webinar | paid_ad | referral",
        "company_size_band": "solo | small | mid | large | enterprise",
        "contact_role": "junior | manager | director | vp | c_level | owner",
        "region": "country/region string",
        "stated_need": "lead's own 1-2 sentence message",
        "as_is_first_response_minutes": "int minutes, or null if never contacted",
        "as_is_contacted": "bool",
    },
    "disclaimer": "No real persons, companies, or contact details are represented. Cadence Workflow is fictional.",
}

out = {"_meta": meta, "leads": leads}
with open("data/leads.json", "w") as f:
    json.dump(out, f, indent=2)

# ---- Report --------------------------------------------------------------
from collections import Counter
by_source = Counter(l["source"] for l in leads)
by_size = Counter(l["company_size_band"] for l in leads)
by_role = Counter(l["contact_role"] for l in leads)
contacted_vals = [l["as_is_first_response_minutes"] for l in leads if l["as_is_contacted"]]
never = sum(1 for l in leads if not l["as_is_contacted"])

print("=== COUNT BY SOURCE ===")
for k in ["demo_request","free_trial","content_webinar","paid_ad","referral"]:
    print(f"  {k:16} {by_source[k]:3}  ({by_source[k]/N*100:.1f}%)")
print("\n=== AS-IS RESPONSE (contacted only) ===")
print(f"  contacted leads : {len(contacted_vals)}")
print(f"  average minutes : {statistics.mean(contacted_vals):.1f}  (~{statistics.mean(contacted_vals)/60:.1f}h)")
print(f"  median minutes  : {statistics.median(contacted_vals):.1f}")
print(f"\n=== NEVER CONTACTED ===")
print(f"  {never} of {N}  ({never/N*100:.1f}%)")
