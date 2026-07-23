"""
LLM-as-judge: scores a transcript against a rubric to detect failures.

Rubric axes (each scored PASS/FAIL + short reason):
  1. task_coherence   - did the agent stay on task / handle it sensibly,
                         without hallucinating info the user never gave?
  2. clarification     - if the input was ambiguous/garbled, did the agent
                         ask for clarification instead of guessing?
  3. context_recovery  - after an interruption/topic-switch, did the agent
                         correctly track state (not silently drop or merge
                         tasks incorrectly)?
  4. no_repetition_loop - did the agent avoid re-asking something already
                         answered / looping?

We deliberately keep the rubric narrow and behavior-focused (not vague
"quality" scoring) because vague rubrics are what make LLM judges
unreliable. Each axis maps to one of our mutator categories, which is
also what makes validation against human labels tractable.
"""

import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

JUDGE_PROMPT = """You are a strict QA evaluator for a voice assistant. You will be shown a
transcript of a phone call between a caller and a dental-clinic appointment-booking
assistant. The caller's LAST message before the assistant's final response was an
adversarial test input (garbled transcription, ambiguous phrasing, mid-conversation
topic switch, or a barge-in interruption).

Evaluate the assistant's FINAL response against these criteria. Be strict -- a
"PASS" means a human caller would find the response reasonable and competent.

1. task_coherence: Did the assistant avoid hallucinating information the caller
   never actually provided, and avoid taking an action (like booking) based on a
   guess rather than confirmed info?
2. clarification: If the caller's input was garbled, ambiguous, or nonsensical,
   did the assistant ask a clarifying question rather than confidently guessing
   at the wrong interpretation?
3. context_recovery: If the caller interrupted or switched topics, did the
   assistant correctly acknowledge this and track state, rather than silently
   ignoring the change or losing the original task entirely?
4. no_repetition_loop: Did the assistant avoid re-asking for information the
   caller already provided earlier in the transcript?

Transcript:
{transcript}

Test category: {category} / {subtype}
Adversarial input given to assistant: "{mutated_input}"
Assistant's final response: "{final_response}"

Respond with ONLY valid JSON, no other text, in this exact format:
{{
  "task_coherence": {{"verdict": "PASS or FAIL", "reason": "one sentence"}},
  "clarification": {{"verdict": "PASS or FAIL or N/A", "reason": "one sentence"}},
  "context_recovery": {{"verdict": "PASS or FAIL or N/A", "reason": "one sentence"}},
  "no_repetition_loop": {{"verdict": "PASS or FAIL", "reason": "one sentence"}},
  "overall_failure": true or false
}}
"""


def _format_transcript(history: list[dict]) -> str:
    lines = []
    for m in history:
        if m["role"] == "system":
            continue
        role = "Caller" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def judge_transcript(test_case: dict) -> dict:
    prompt = JUDGE_PROMPT.format(
        transcript=_format_transcript(test_case["transcript"]),
        category=test_case.get("category", "unknown"),
        subtype=test_case.get("subtype", "unknown"),
        mutated_input=test_case.get("mutated_input", ""),
        final_response=test_case.get("final_response", ""),
    )
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0}
    }, timeout=60)
    resp.raise_for_status()
    raw = resp.json()["message"]["content"].strip()

    # strip markdown fences if the model adds them despite instructions
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        verdict = json.loads(raw)
    except json.JSONDecodeError:
        verdict = {"parse_error": True, "raw_output": raw}

    return {"test_id": test_case.get("test_id"), "verdict": verdict}


def judge_all(transcripts_path: str, output_path: str, latest: int | None = None):
    results_map = {}
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(exist_ok=True)

    # Load existing judgments if appending/updating latest
    if out_p.exists() and latest is not None:
        with open(out_p) as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    results_map[item["test_id"]] = item

    t_path = Path(transcripts_path).resolve()
    if not t_path.exists():
        print(f"\n❌ [Error] Transcripts file not found at {t_path}")
        print("💡 Please run the test generator first:\n   python runner/test_runner.py --category all\n")
        return []

    with open(t_path) as f:
        cases = [json.loads(line) for line in f]

    if latest is not None and latest > 0:
        cases_to_judge = cases[-latest:]
        print(f"🎯 Judging ONLY the latest {len(cases_to_judge)} test case(s)...")
    else:
        cases_to_judge = cases
        results_map = {}

    for case in cases_to_judge:
        print(f"Judging {case['test_id']} [{case['category']}/{case['subtype']}]...")
        result = judge_transcript(case)
        results_map[case['test_id']] = result

    # Save all updated judgments
    with open(out_p, "w") as f:
        for r in results_map.values():
            f.write(json.dumps(r) + "\n")

    print(f"Judged {len(cases_to_judge)} case(s) -> {out_p}")
    return list(results_map.values())


if __name__ == "__main__":
    import argparse
    DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcripts", default=str(DEFAULT_DATA_DIR / "transcripts.jsonl"))
    parser.add_argument("--out", default=str(DEFAULT_DATA_DIR / "judgments.jsonl"))
    parser.add_argument("--latest", type=int, default=None, help="Judge only the latest N recordings (e.g. --latest 1 or --latest 4)")
    args = parser.parse_args()
    judge_all(args.transcripts, args.out, latest=args.latest)
