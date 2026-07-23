"""
A minimal 'voice agent' for appointment scheduling.

This simulates what a voice agent does, minus actual audio I/O:
  - receives a (possibly garbled/ambiguous/interrupted) user utterance
  - maintains conversation + task state across turns
  - decides: respond, ask clarifying question, or call a "tool" (book_appointment)

We treat this as a text-level simulation of a voice agent. Real STT/TTS
noise is injected upstream by the mutators (see mutators/asr_errors.py),
so this agent doesn't need to know it's "voice" -- it just needs to behave
like a real production agent with state, so state-related bugs
(lost context, wrong slot-filling, ignoring interruptions) can surface.

Requires a local Ollama server running (`ollama serve`) with a pulled model,
e.g. `ollama pull llama3.1:8b`.
"""

import json
import os
import re
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
# Default to installed local model (llama3.2:latest, llama3:latest, or environment override)
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

SYSTEM_PROMPT = """You are a phone voice assistant for a dental clinic. Your ONLY job is to
book, reschedule, or cancel appointments. You must collect these slots before booking:
- patient_name
- appointment_type (cleaning, checkup, or emergency)
- preferred_date
- preferred_time

Strict System Rules:
1. Short & Complete Sentences: Always respond in 1-2 complete, grammatically sound sentences. Never leave a sentence cut off or incomplete.
2. Slot Filling: Ask ONE clear question at a time for missing info. Never ask for info already provided.
3. Garbled / ASR Noise Handling: If user input contains phonetic confusions (e.g. "Choose Day"), garbled words, or disfluencies, DO NOT guess or hallucinate strange terms. Politely ask for clarification (e.g. "Did you mean Tuesday?").
4. Interruptions & Corrections: If the user corrects a detail (e.g. "make it for my son John instead"), explicitly acknowledge the correction and update the slot (e.g. "Got it, setting up the booking for your son John.").
5. Vague References: If the user says "the usual time" or vague references, state that you do not have saved profile preferences and ask for the specific time.
6. Topic Switches: If the user asks an off-topic question mid-booking, answer it briefly if possible or state your policy, then explicitly ask if they want to resume the booking.
7. Tool Calling: Once ALL 4 slots are filled, respond with EXACTLY this line:
   TOOL_CALL: book_appointment(name=..., type=..., date=..., time=...)
   followed by a confirmation sentence.
"""


class SchedulingAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.slots = {"patient_name": None, "appointment_type": None,
                      "preferred_date": None, "preferred_time": None}
        self.tool_called = False

    def reset(self):
        self.__init__(model=self.model)

    def step(self, user_utterance: str) -> dict:
        """
        Send one user turn to the agent, return structured response.
        Returns: {"text": str, "tool_call": dict|None, "raw_history_len": int}
        """
        self.history.append({"role": "user", "content": user_utterance})

        resp = requests.post(OLLAMA_URL, json={
            "model": self.model,
            "messages": self.history,
            "stream": False,
            "options": {"temperature": 0.3}
        }, timeout=60)
        resp.raise_for_status()
        agent_text = resp.json()["message"]["content"].strip()

        self.history.append({"role": "assistant", "content": agent_text})

        tool_call = self._parse_tool_call(agent_text)
        if tool_call:
            self.tool_called = True

        return {
            "text": agent_text,
            "tool_call": tool_call,
            "turn_count": len([m for m in self.history if m["role"] == "user"]),
        }

    @staticmethod
    def _parse_tool_call(text: str):
        m = re.search(r"TOOL_CALL:\s*book_appointment\((.*?)\)", text)
        if not m:
            return None
        args_str = m.group(1)
        args = {}
        for pair in args_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                args[k.strip()] = v.strip().strip("'\"")
        return {"name": "book_appointment", "args": args}


if __name__ == "__main__":
    # quick smoke test
    agent = SchedulingAgent()
    for turn in ["Hi, I need to book a cleaning", "John Smith", "next Tuesday", "2pm works"]:
        out = agent.step(turn)
        print(f"USER: {turn}")
        print(f"AGENT: {out['text']}\n")
