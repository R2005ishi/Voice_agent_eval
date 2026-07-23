<div align="center">

# 🎙️ Voice Agent Adversarial Evaluation & Red-Teaming Harness

**An automated framework for stress-testing, red-teaming, and evaluating production Voice AI Agents.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper_STT-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

---

</div>

## 📌 Executive Summary

Building production voice AI agents requires more than just testing happy-path conversations. Real-world voice calls suffer from **Speech-to-Text (STT) garbling, mid-sentence barge-in interruptions, and sudden contextual topic switches**.

`voice-agent-eval` is an end-to-end evaluation harness designed to automatically detect, catch, and categorize critical failure modes in Voice Agents. It stress-tests conversational state tracking using **state-conditioned LLM mutators**, evaluates transcripts with an **LLM-as-a-Judge**, and mathematically verifies judge reliability using **Human Ground-Truth Precision/Recall Validation**.

---

## 🌟 Key Engineering Features

- 🧠 **Validated LLM-as-a-Judge**: Solves the "untrustworthy AI judge" problem by statistically measuring Judge **Precision, Recall, F1-Score, and Accuracy** against human ground-truth hand-labels.
- ⚡ **Zero-Cost Distributional ASR Mutator**: Simulates STT output errors (phonetic homophones, digit garbling, word dropping, disfluency injection) directly at the text layer to run thousands of test cases per minute without expensive audio generation.
- 🎙️ **Real-Time Live Voice & Audio Stream**: Includes an interactive in-memory Voice Pipeline (`edge-tts` + local Whisper STT + mic/speakers) for zero-latency live voice red-teaming.
- 🔌 **Plug-and-Play Production Adapters**: Native support for evaluating local models (Ollama/Llama 3.2), cloud APIs (Deepgram, Vapi, Retell AI), and mobile voice assistants (Gemini Live).

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │           1. MUTATOR LAYER              │
                               │  - ASR Phonetic/Number Corruption       │
                               │  - State-Conditioned Topic Switches     │
                               │  - Mid-Sentence Barge-in Interruptions  │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
 ┌───────────────────────────┐ ┌─────────────────────────────────────────┐
 │ 🎙️ LIVE VOICE & AUDIO I/O │ │          2. EXECUTION ENGINE            │
 │  - edge-tts (TTS)         │ │  - Ollama (Local Llama 3.2)             │
 │  - Whisper (Local STT)    │ │  - Deepgram / Vapi / Retell Adapters    │
 │  - Mic/Speaker Stream     │ │  - Mobile Gemini Laptop Bridge          │
 └─────────────┬─────────────┘ └────────────────────┬────────────────────┘
               │                                    │
               └─────────────────┬──────────────────┘
                                 │
                                 ▼
               ┌───────────────────────────────────┐
               │    data/transcripts.jsonl          │
               └─────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌───────────────────────────────────┐
               │    3. LLM-AS-A-JUDGE LAYER         │
               │  Scores against 4 Strict Rubrics: │
               │  - Task Coherence                 │
               │  - Clarification Asking           │
               │  - Context Recovery               │
               │  - No Repetition Loops            │
               └─────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌───────────────────────────────────┐
               │    4. STATISTICAL VALIDATION      │
               │  - Precision / Recall / F1 Score  │
               │  - Failure Taxonomy Markdown      │
               └───────────────────────────────────┘
```

---

## 🎯 Evaluated Attack Vectors

| Failure Category | Attack Vector | Example Scenario | What is Tested |
| :--- | :--- | :--- | :--- |
| **1. ASR Errors** | Phonetic & Digit Garbling | *"Can I book on Choose Day at 15:00?"* | Does agent hallucinate wrong slots or ask for clarification? |
| **2. Ambiguity** | Topic Switches & Vague Refs | *"Wait, what are your clinic copays?"* | Does agent drop context or handle off-topic queries gracefully? |
| **3. Interruptions** | Mid-Sentence Barge-in | *"Wait no, make it for my son John."* | Does agent update memory when cut off mid-sentence? |

---

## 🚀 Quick Start & Installation

### 1. Setup Environment
```bash
git clone https://github.com/R2005ishi/Voice_agent_eval.git
cd Voice_agent_eval
pip install -r requirements.txt
```

### 2. Start Local Ollama Server
```bash
ollama pull llama3.2:latest
ollama serve
```

---

## 💻 Usage & Execution Modes

### Mode A: Interactive Live Voice Console (Mic & Speaker)
Talk directly into your microphone to stress-test your voice agent in real-time:
```bash
python agent/voice_agent.py
```

### Mode B: Automated Adversarial Test Suite
Generate 100+ adversarial test cases, run against the target agent, and log full transcripts:
```bash
python runner/test_runner.py --category all
```

### Mode C: Evaluate Only Latest Recording(s)
Grade only your latest test run or mobile voice recording:
```bash
python judge/llm_judge.py --latest 1
python report/generate_report.py
```

### Mode D: Test Mobile Assistants (Gemini Live)
Test mobile assistants over laptop speakers and microphone without API keys:
```bash
python agent/test_mobile_gemini.py
```

---

## 📊 Human Ground-Truth Judge Validation

An unvalidated AI judge is an unreliable eval signal. This harness measures the precision and recall of the LLM judge against human hand-labels before trusting failure metrics:

```bash
# 1. Hand-label a sample interactively
python eval/validate_judge.py --label --n 30

# 2. Compute Precision, Recall, and Confusion Matrix
python eval/validate_judge.py --compare
```

**Example Validation Output:**
```
=== Judge Validation Report (n=30) ===
Confusion Matrix:
                 Human: FAIL   Human: OK
  Judge: FAIL       14             1
  Judge: OK          1            14

Precision: 0.93  (Of judge-flagged failures, 93% were real)
Recall:    0.93  (Of real failures, judge caught 93%)
F1-Score:  0.93
Accuracy:  0.93
```

---

## 📄 Automated Failure Taxonomy Report

Running `python report/generate_report.py` generates **`report/failure_report.md`**, detailing breakdown metrics and concrete failure transcript excerpts:

```markdown
## Category Summary
| Category | Total Tests | Failures | Failure Rate |
|---|---|---|---|
| ambiguity/topic_switch | 8 | 2 | 25% |
| asr_error/phonetic_confusion | 12 | 7 | 58% |
| interruption/barge_in_correction | 6 | 4 | 66% |
```

---

## 📁 Repository Structure

```
├── agent/
│   ├── scheduling_agent.py    # Target stateful appointment voice agent (Ollama)
│   ├── audio_utils.py         # In-memory TTS (edge-tts) & STT (Whisper) engine
│   ├── voice_agent.py         # Interactive live voice console
│   ├── deepgram_agent.py      # Deepgram Cloud Voice Agent API adapter
│   ├── live_agent.py          # Generic Webhook/REST Live Agent adapter
│   └── test_mobile_gemini.py  # Laptop-to-mobile speaker/mic test runner
├── mutators/
│   ├── asr_errors.py          # Phonetic homophones, digit & filler noise generator
│   ├── ambiguity.py           # Context-aware LLM topic-switch generator
│   └── interruption.py        # Mid-sentence turn truncation & correction generator
├── runner/
│   └── test_runner.py         # Multi-category test runner & transcript recorder
├── judge/
│   └── llm_judge.py           # LLM-as-a-Judge scoring engine
├── eval/
│   └── validate_judge.py      # Human ground-truth labeling & statistical validation
├── report/
│   ├── generate_report.py     # Failure report generator
│   └── failure_report.md      # Final output markdown report
└── requirements.txt           # Python dependencies
```

---

## 🤝 License & Author

Developed by **Rishi Agrawal** as an open-source evaluation framework for Production Voice AI systems.

Distributed under the MIT License.
