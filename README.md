# Voice Agent Adversarial Eval Harness

An adversarial test-case generator and eval pipeline for voice agents.
Built as a scoped-down demo of the failure-detection layer a production
voice-agent eval product would need: it generates realistic failure-inducing
inputs (ASR errors, ambiguous requests, interruptions), runs them against a
toy voice agent, and uses an LLM-as-judge (validated against human labels)
to catch failures automatically.

Everything runs locally against [Ollama](https://ollama.com) — no API costs,
fully reproducible.

## Why this scope

Rather than build 6 shallow failure categories, this project goes deep on 3
that matter most and are hardest to get right:

1. **ASR/transcription errors** — rule-based phonetic confusion, number
   garbling, word dropping, disfluency injection (simulates STT output
   distribution without needing full audio synthesis)
2. **Ambiguity / topic switches** — LLM-generated adversarial user turns,
   conditioned on conversation state
3. **Interruptions (barge-in)** — truncates the agent's response mid-turn
   and injects a correction, simulating a user talking over the agent

The single most important piece isn't the mutators — it's the **judge
validation step**. An LLM-as-judge that hasn't been checked against human
labels is not a trustworthy eval signal. This project measures precision/
recall of the judge against a hand-labeled sample before trusting its
failure counts.

## Architecture

```
mutators/          -> generate adversarial user inputs (3 categories)
agent/              -> toy appointment-scheduling voice agent (stateful)
runner/             -> orchestrates mutator -> agent -> transcript capture
judge/              -> LLM-as-judge scores transcripts against a rubric
eval/               -> validates judge against human-labeled ground truth
report/             -> generates failure taxonomy report (markdown)
```

## Setup

```bash
pip install -r requirements.txt

# pull and serve a local model (separate terminal)
ollama pull llama3.1:8b
ollama serve
```

## Running Interactive Live Voice Agent

To talk to the agent in real-time with your microphone and hear responses via Text-to-Speech:

```bash
python agent/voice_agent.py
```

## Running the full evaluation pipeline

```bash
# 1. Generate adversarial test cases and run them against the agent
python runner/test_runner.py --category all

# 2. Judge all transcripts
cd judge && python llm_judge.py --transcripts ../data/transcripts.jsonl --out ../data/judgments.jsonl

# 3. Hand-label a sample for judge validation (interactive)
cd ../eval && python validate_judge.py --label --n 30

# 4. Compare judge vs human labels
python validate_judge.py --compare

# 5. Generate the failure taxonomy report
cd ../report && python generate_report.py
```

Output: `report/failure_report.md` — failure rates by category + concrete
example transcripts, and a judge validation report (precision/recall/F1)
printed to console in step 4.

## What I found (fill in after running)

- [ ] Overall failure rate by category
- [ ] Judge precision/recall vs human labels
- [ ] 3-5 concrete bugs with transcript excerpts
- [ ] Root-cause categorization (ASR error vs logic bug vs state bug)

## Scoping notes / future work

- **Real audio**: ASR errors are currently simulated at the text level via
  phonetic confusion rules rather than actual TTS→noise→STT round-trips.
  A natural extension: synthesize audio with a TTS model, inject background
  noise / pitch shift, re-transcribe with Whisper, and use the *actual*
  transcription errors instead of hand-curated confusion pairs.
- **Real interruption timing**: barge-in is simulated via text truncation
  rather than actual overlapping audio streams / turn-taking latency.
- **Target agent**: tested against a toy agent built for this project.
  Testing against a real platform (Vapi/Retell) would validate the harness
  against production-grade agents rather than a agent built to be testable.
