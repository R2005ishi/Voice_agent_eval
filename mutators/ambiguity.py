"""
Generates ambiguous requests and mid-conversation topic switches.

Unlike ASR errors (rule-based text corruption), these mutations require
generation -- we use the local LLM itself to produce realistic ambiguous
or topic-switching user turns, conditioned on the conversation so far.
This mirrors how a real caller might behave: vague references, sudden
unrelated requests, or interrupting themselves.
"""

import json
import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

AMBIGUITY_GEN_PROMPT = """You are generating a test utterance for a phone caller talking to a
dental clinic's appointment-booking voice assistant. The conversation so far is below.

Generate ONE realistic but AMBIGUOUS next thing the caller might say -- something that
could reasonably mean more than one thing, or refers to something without enough context
(e.g. "the usual" without saying what that is, "can you change it" without saying what).

Conversation so far:
{history}

Respond with ONLY the caller's utterance, nothing else. Keep it short and natural,
like real speech (not written prose).
"""

TOPIC_SWITCH_GEN_PROMPT = """You are generating a test utterance for a phone caller talking to a
dental clinic's appointment-booking voice assistant. The conversation so far is below.

Generate ONE realistic mid-conversation TOPIC SWITCH -- the caller suddenly asks about
something unrelated to the current booking task (e.g. billing question, asking about a
different family member's appointment, asking about clinic hours, or asking to cancel
a completely different existing appointment) without acknowledging the topic change.

Conversation so far:
{history}

Respond with ONLY the caller's utterance, nothing else. Keep it short and natural,
like real speech (not written prose).
"""


def _call_llm(prompt: str) -> str:
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.9}
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip().strip('"')


def _format_history(history: list[dict]) -> str:
    lines = []
    for m in history:
        if m["role"] == "user":
            lines.append(f"Caller: {m['content']}")
        elif m["role"] == "assistant":
            lines.append(f"Assistant: {m['content']}")
    return "\n".join(lines) if lines else "(conversation just started)"

def generate_ambiguous_turn(history: list[dict]) -> dict:
    prompt = AMBIGUITY_GEN_PROMPT.format(history=_format_history(history))
    utterance = _call_llm(prompt)
    return {"category": "ambiguity", "subtype": "vague_reference", "mutated": utterance}


def generate_topic_switch_turn(history: list[dict]) -> dict:
    prompt = TOPIC_SWITCH_GEN_PROMPT.format(history=_format_history(history))
    utterance = _call_llm(prompt)
    return {"category": "ambiguity", "subtype": "topic_switch", "mutated": utterance}


if __name__ == "__main__":
    fake_history = [
        {"role": "user", "content": "Hi, I need to book a cleaning"},
        {"role": "assistant", "content": "Sure, can I get your name?"},
        {"role": "user", "content": "John Smith"},
    ]
    print("AMBIGUOUS:", generate_ambiguous_turn(fake_history))
    print("TOPIC SWITCH:", generate_topic_switch_turn(fake_history))
