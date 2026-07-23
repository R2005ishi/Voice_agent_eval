"""
Orchestrates: seed conversation -> apply mutator -> run against agent ->
capture full transcript + metadata -> write to data/transcripts.jsonl

Each test case follows a "seed scenario" (a normal booking flow) up to a
random point, then injects one adversarial turn, then continues the
conversation a couple more turns to see whether the agent recovers.
"""

import json
import sys
import time
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agent.scheduling_agent import SchedulingAgent
from agent.live_agent import LiveVoiceAgent
from mutators.asr_errors import generate_asr_mutations
from mutators.ambiguity import generate_ambiguous_turn, generate_topic_switch_turn
from mutators.interruption import generate_interrupt_turn, generate_silence_timeout_turn

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
TRANSCRIPTS_PATH = DATA_DIR / "transcripts.jsonl"

USE_LIVE_AGENT = False
LIVE_AGENT_URL = None
LIVE_AGENT_KEY = None


def get_agent():
    if USE_LIVE_AGENT:
        return LiveVoiceAgent(api_url=LIVE_AGENT_URL, api_key=LIVE_AGENT_KEY)
    return SchedulingAgent()

# Seed scenarios: normal opening turns before we inject adversarial input
SEED_OPENERS = [
    "Hi, I'd like to book an appointment",
    "Hello, I need to schedule a cleaning",
    "Hi, can I book a checkup for next week",
]


def run_asr_test_cases(n_per_seed: int = 2, seed: int = 0):
    cases = []
    for opener in SEED_OPENERS:
        clean_followups = ["My name is Sarah Johnson", "I'd like a checkup", "next Tuesday", "at fifteen hundred"]
        for followup in clean_followups[:n_per_seed]:
            for variant in generate_asr_mutations(followup, n=2, seed=seed):
                cases.append({"opener": opener, "mutation": variant})
    return cases


def run_test_suite(category: str = "all", limit: int | None = None):
    """
    Runs test cases across categories, logs full transcripts to jsonl.
    category: "asr" | "ambiguity" | "interruption" | "all"
    """
    results = []

    if category in ("asr", "all"):
        results += _run_asr_suite(limit=limit)
    if category in ("ambiguity", "all"):
        results += _run_ambiguity_suite(limit=limit)
    if category in ("interruption", "all"):
        results += _run_interruption_suite(limit=limit)

    with open(TRANSCRIPTS_PATH, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print(f"Ran {len(results)} test cases. Appended to {TRANSCRIPTS_PATH}")
    return results


def _run_asr_suite(limit=None):
    print("Running ASR error test cases...")
    out = []
    cases = run_asr_test_cases()
    if limit:
        cases = cases[:limit]
    for case in cases:
        agent = get_agent()
        try:
            opener_resp = agent.step(case["opener"])
            mutated_resp = agent.step(case["mutation"]["mutated"])
        except Exception as e:
            print(f"  ERROR (agent call failed): {e}")
            continue
        out.append({
            "test_id": str(uuid.uuid4())[:8],
            "category": "asr_error",
            "subtype": case["mutation"]["subtype"],
            "original_clean_input": case["mutation"]["original"],
            "mutated_input": case["mutation"]["mutated"],
            "transcript": agent.history,
            "final_response": mutated_resp["text"],
            "timestamp": time.time(),
        })
        print(f"  [{case['mutation']['subtype']}] '{case['mutation']['mutated'][:50]}...' -> logged")
    return out


def _run_ambiguity_suite(limit=None):
    print("Running ambiguity/topic-switch test cases...")
    out = []
    seeds = SEED_OPENERS[:2] if not limit else SEED_OPENERS[:1]
    for opener in seeds:
        for gen_fn, subtype in [(generate_ambiguous_turn, "vague_reference"),
                                 (generate_topic_switch_turn, "topic_switch")]:
            agent = get_agent()
            try:
                agent.step(opener)
                mutation = gen_fn(agent.history)
                resp = agent.step(mutation["mutated"])
            except Exception as e:
                print(f"  ERROR: {e}")
                continue
            out.append({
                "test_id": str(uuid.uuid4())[:8],
                "category": "ambiguity",
                "subtype": subtype,
                "mutated_input": mutation["mutated"],
                "transcript": agent.history,
                "final_response": resp["text"],
                "timestamp": time.time(),
            })
            print(f"  [{subtype}] '{mutation['mutated'][:50]}...' -> logged")
    return out


def _run_interruption_suite(limit=None):
    print("Running interruption test cases...")
    out = []
    for opener in SEED_OPENERS[:2]:
        agent = get_agent()
        try:
            first_resp = agent.step(opener)
            interrupt = generate_interrupt_turn(first_resp["text"], seed=1)
            # Overwrite the agent's last logged turn with the truncated version
            # to reflect that the agent was actually cut off mid-sentence.
            agent.history[-1]["content"] = interrupt["truncated_agent_turn"]
            resp = agent.step(interrupt["mutated"])
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        out.append({
            "test_id": str(uuid.uuid4())[:8],
            "category": "interruption",
            "subtype": "barge_in_correction",
            "mutated_input": interrupt["mutated"],
            "truncated_agent_turn": interrupt["truncated_agent_turn"],
            "transcript": agent.history,
            "final_response": resp["text"],
            "timestamp": time.time(),
        })
        print(f"  [barge_in_correction] '{interrupt['mutated'][:50]}...' -> logged")
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="all", choices=["asr", "ambiguity", "interruption", "all"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--live", action="store_true", help="Run against a live production agent endpoint")
    parser.add_argument("--url", default=None, help="Live Agent API URL")
    parser.add_argument("--key", default=None, help="Live Agent API Key")
    args = parser.parse_args()

    if args.live:
        USE_LIVE_AGENT = True
        LIVE_AGENT_URL = args.url
        LIVE_AGENT_KEY = args.key

    run_test_suite(category=args.category, limit=args.limit)
