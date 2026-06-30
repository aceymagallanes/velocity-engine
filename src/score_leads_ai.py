#!/usr/bin/env python3
"""Velocity engine — AI lead scoring (Claude API pass).

Replaces the keyword rules in score_leads.py with a real Claude call: each
lead's `stated_need` is read by the model, which returns a 0-3 BANT score
(Budget / Authority / Need / Timeline) plus a one-line reason. The pipeline,
tiers, and to-be SLAs are identical to the rules pass, so build_dashboard.py
works unchanged on the output.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 data/score_leads_ai.py                # score all 400 with Opus 4.8
    python3 data/score_leads_ai.py --limit 5      # cheap smoke test (5 leads)
    python3 data/score_leads_ai.py --model claude-haiku-4-5   # ~5x cheaper
    python3 data/score_leads_ai.py --out data/leads_scored_ai.json

Cost (all 400, rough): Opus 4.8 ~$0.90 · Haiku 4.5 ~$0.18.
"""
import argparse, json, os, sys, statistics
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import anthropic
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit("Missing deps. Run: pip install 'anthropic' pydantic")

SRC_DEFAULT = "data/leads.json"
OUT_DEFAULT = "data/leads_scored.json"  # canonical file the dashboard reads

# Same tier thresholds and SLAs as the rules pass, so the two are comparable.
TO_BE_SLA = {"high": 5, "medium": 60, "low": 1440}


class BantScore(BaseModel):
    """Structured BANT read of a single lead's message."""
    budget: int = Field(description="0-3: 0 no budget signal, 3 explicit approved budget/spend")
    authority: int = Field(description="0-3: 0 no authority, 3 clear decision-maker / purchasing power")
    need: int = Field(description="0-3: 0 vague curiosity, 3 specific, urgent, well-defined pain")
    timeline: int = Field(description="0-3: 0 no timeframe, 3 hard deadline / buying now")
    reason: str = Field(description="One short sentence justifying the scores")


SYSTEM = (
    "You are a B2B SDR-qualification engine for Cadence Workflow, a project-management "
    "SaaS sold per-seat to mid-market teams. You read a single inbound lead's own message "
    "and score it on BANT, each 0-3:\n"
    "- Budget: explicit money/approval/spend signals (0 none, 3 approved budget stated).\n"
    "- Authority: is the writer a decision-maker or buyer? Use role cues in the text "
    "(0 none/junior, 3 director/VP/C-level/owner with purchasing power).\n"
    "- Need: how specific and pressing is the pain? (0 'just browsing', 3 a defined, urgent project).\n"
    "- Timeline: how soon must they act? (0 none, 3 hard deadline or buying now).\n"
    "Score only what the message actually supports — do not invent signals. "
    "Return the four integers and one short reason."
)


def clamp(v):
    try:
        return max(0, min(3, int(v)))
    except (TypeError, ValueError):
        return 0


def score_one(client, model, lead):
    """Call Claude for one lead; return (lead_id, bant_dict, reason)."""
    msg = lead["stated_need"]
    ctx = (f"Source: {lead['source']} | company size: {lead['company_size_band']} | "
           f"stated role: {lead['contact_role']} | region: {lead['region']}\n"
           f'Lead message: "{msg}"')
    resp = client.messages.parse(
        model=model,
        max_tokens=400,
        system=SYSTEM,
        messages=[{"role": "user", "content": ctx}],
        output_format=BantScore,
    )
    s = resp.parsed_output
    bant = {"budget": clamp(s.budget), "authority": clamp(s.authority),
            "need": clamp(s.need), "timeline": clamp(s.timeline)}
    return lead["lead_id"], bant, s.reason.strip()


def tier_of(total):
    if total >= 8:
        return "high"
    if total >= 3:
        return "medium"
    return "low"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--model", default="claude-opus-4-8",
                    help="claude-opus-4-8 (default) | claude-haiku-4-5 | claude-sonnet-4-6")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N leads (smoke test)")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. export it, then re-run.")

    with open(args.src) as f:
        data = json.load(f)
    leads = data["leads"]
    if args.limit:
        leads = leads[:args.limit]
    by_id = {l["lead_id"]: l for l in leads}

    client = anthropic.Anthropic()
    print(f"Scoring {len(leads)} leads with {args.model} (concurrency {args.concurrency})...")

    done, errs = 0, 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futs = {pool.submit(score_one, client, args.model, l): l["lead_id"] for l in leads}
        for fut in as_completed(futs):
            lid = futs[fut]
            try:
                lead_id, bant, reason = fut.result()
                ld = by_id[lead_id]
                total = sum(bant.values())
                ld["bant"] = bant
                ld["bant_total"] = total
                ld["bant_reason"] = reason
                ld["priority"] = tier_of(total)
                ld["to_be_first_response_minutes"] = TO_BE_SLA[ld["priority"]]
            except Exception as e:  # keep going; flag failures
                errs += 1
                print(f"  ! {lid} failed: {e}", file=sys.stderr)
            done += 1
            if done % 25 == 0 or done == len(leads):
                print(f"  {done}/{len(leads)} done ({errs} errors)")

    scored = [l for l in leads if "priority" in l]
    if not scored:
        sys.exit("No leads scored successfully — aborting write.")

    # ---- write (preserve _meta, add scoring provenance) ----
    meta = data.get("_meta", {})
    meta["scoring"] = {
        "engine": f"Velocity AI pass — Claude ({args.model})",
        "method": "BANT scored from stated_need via structured outputs",
        "tier_thresholds": {"high": ">=8 / 12", "medium": "3-7 / 12", "low": "0-2 / 12"},
        "to_be_sla_minutes": TO_BE_SLA,
        "leads_scored": len(scored),
        "errors": errs,
    }
    out_data = {"_meta": meta, "leads": leads}
    with open(args.out, "w") as f:
        json.dump(out_data, f, indent=2)

    # ---- report ----
    N = len(scored)
    tiers = Counter(l["priority"] for l in scored)
    contacted = [l for l in scored if l["as_is_contacted"]]
    as_is = [l["as_is_first_response_minutes"] for l in contacted]
    never = [l for l in scored if not l["as_is_contacted"]]
    high = [l for l in scored if l["priority"] == "high"]
    high_never = [l for l in high if not l["as_is_contacted"]]
    to_be_mean = statistics.mean(l["to_be_first_response_minutes"] for l in scored)

    print("\n=== AI PRIORITY TIERS ===")
    for k in ["high", "medium", "low"]:
        print(f"  {k:7} {tiers[k]:3}  ({tiers[k]/N*100:.1f}%)")
    if as_is:
        print(f"\nas-is avg first response (contacted): {statistics.mean(as_is):,.0f} min")
        print(f"to-be avg first response (all routed): {to_be_mean:,.0f} min")
    if high:
        print(f"high-priority leads: {len(high)}  |  never contacted as-is: "
              f"{len(high_never)} ({len(high_never)/len(high)*100:.0f}%)")
    print(f"\nWrote {args.out}  ({N} scored, {errs} errors)")
    print("Run: python src/build_dashboard.py   to refresh the dashboard with AI scores.")


if __name__ == "__main__":
    main()
