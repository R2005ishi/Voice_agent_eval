"""
Simulates barge-in / interruption behavior.

In a real voice call, a user can start speaking before the agent finishes
its turn (barge-in). This creates specific failure modes:
  - agent's response gets truncated mid-sentence, but downstream state
    still assumes the full response was heard
  - user's new utterance may reference something the agent never
    finished saying
  - agent may re-ask a question it (partially) already asked

We simulate this at the text level: given the agent's full response,
we truncate it at some point (simulating the user cutting in before the
agent finished), then inject a new user utterance -- either a correction,
a completely new request, or a short "wait, what?" -- as if the user
spoke over the agent.

We can't literally play overlapping audio here, but we CAN test the thing
that actually matters for the eval: does the agent's *state and next
response* stay coherent when it only "said" a truncated version of its
intended turn, and the user jumps in before confirmation completes.
"""

import random

INTERRUPT_UTTERANCES = [
    "Wait, no, actually",
    "Hold on, sorry",
    "Actually can we change that",
    "No wait",
    "Sorry go back",
]

CORRECTION_FOLLOWUPS = [
    "make it Wednesday instead",
    "I meant a checkup not a cleaning",
    "actually book it for my son not me",
    "can we do the afternoon instead",
    "actually never mind, cancel that",
]


def truncate_response(agent_text: str, fraction: float = 0.4) -> str:
    """Simulate the user barging in partway through the agent's turn."""
    words = agent_text.split()
    cutoff = max(1, int(len(words) * fraction))
    return " ".join(words[:cutoff])


def generate_interrupt_turn(agent_text: str, seed: int | None = None) -> dict:
    """
    Given the agent's just-produced response, simulate the user
    interrupting partway through with a correction or new direction.

    Returns the truncated agent text (what the agent "actually got to say"
    before being cut off) plus the interrupting user utterance to feed
    back into the agent next.
    """
    if seed is not None:
        random.seed(seed)

    truncated = truncate_response(agent_text, fraction=random.uniform(0.25, 0.6))
    interrupt_opener = random.choice(INTERRUPT_UTTERANCES)
    followup = random.choice(CORRECTION_FOLLOWUPS)
    interrupt_text = f"{interrupt_opener}, {followup}"

    return {
        "category": "interruption",
        "subtype": "barge_in_correction",
        "truncated_agent_turn": truncated,
        "mutated": interrupt_text,
    }


def generate_silence_timeout_turn() -> dict:
    """Simulate a user going silent / trailing off mid-thought."""
    silences = [
        "um... let me think...",
        "...",
        "hold on, uh...",
        "sorry, one sec... [long pause]",
    ]
    return {
        "category": "interruption",
        "subtype": "silence_timeout",
        "mutated": random.choice(silences),
    }


if __name__ == "__main__":
    fake_agent_text = "Sure, I can book a cleaning for you. Can I get your preferred date and time for the appointment?"
    print(generate_interrupt_turn(fake_agent_text, seed=1))
    print(generate_silence_timeout_turn())
