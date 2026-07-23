"""
Simulates realistic ASR (speech-to-text) transcription errors.

Real STT engines (Whisper, Deepgram, etc.) systematically confuse certain
sounds. Instead of doing full audio synthesis + noise + re-transcription
(expensive, slow, hard to control), we simulate the *output distribution*
of ASR errors directly on text -- this is a well-established technique in
ASR-robustness research (see e.g. speech-perturbation and phonetic-confusion
literature). We note this as a scoping choice: real audio-level noise
injection is a natural next step (see README "Future Work").

Three classes of ASR error are modeled:
  1. Phonetic confusion  -- homophone / near-homophone substitution
     ("flight" -> "flat", "fifteen" -> "fifty")
  2. Number/date garbling -- ASR frequently mangles spoken numbers
  3. Dropped/merged words -- simulates low-confidence word dropping,
     common with background noise or fast speech
"""

import random
import re

# Common ASR confusion pairs (hand-curated from known Whisper/ASR failure
# patterns -- numbers, homophones, and clinic-domain-relevant terms).
PHONETIC_CONFUSIONS = {
    "flight": "flat",
    "cancel": "council",
    "fifteen": "fifty",
    "thirteen": "thirty",
    "fourteen": "forty",
    "two": "to",
    "tuesday": "choose day",
    "cleaning": "clean thing",
    "checkup": "check up",
    "appointment": "a point mint",
    "reschedule": "re-schedule",
    "morning": "warning",
    "afternoon": "after noon",
    "emergency": "emerge and see",
    "smith": "smit",
    "john": "jon",
}

FILLER_NOISE = ["um", "uh", "like", "you know", "[background noise]", "[static]"]


def apply_phonetic_confusion(text: str, rate: float = 0.6) -> str:
    """Replace words with their ASR-confusable counterpart at given rate."""
    words = text.split()
    out = []
    for w in words:
        stripped = re.sub(r"[^\w]", "", w.lower())
        if stripped in PHONETIC_CONFUSIONS and random.random() < rate:
            replacement = PHONETIC_CONFUSIONS[stripped]
            out.append(replacement)
        else:
            out.append(w)
    return " ".join(out)


def apply_number_garbling(text: str, rate: float = 0.5) -> str:
    """Randomly perturb spoken numbers, e.g. off-by-one digit confusion."""
    def repl(m):
        if random.random() < rate:
            n = int(m.group())
            delta = random.choice([-1, 1, 10, -10])
            return str(max(0, n + delta))
        return m.group()
    return re.sub(r"\b\d+\b", repl, text)


def apply_word_drop(text: str, rate: float = 0.15) -> str:
    """Simulate low-confidence ASR word dropping."""
    words = text.split()
    kept = [w for w in words if random.random() > rate]
    return " ".join(kept) if kept else text


def apply_filler_injection(text: str, rate: float = 0.3) -> str:
    """Inject disfluencies / noise markers, common in real phone audio."""
    words = text.split()
    out = []
    for w in words:
        out.append(w)
        if random.random() < rate:
            out.append(random.choice(FILLER_NOISE))
    return " ".join(out)


def generate_asr_mutations(clean_text: str, n: int = 3, seed: int | None = None) -> list[dict]:
    """
    Given a clean user utterance, produce n ASR-corrupted variants,
    each tagged with which corruption types were applied.
    """
    if seed is not None:
        random.seed(seed)

    variants = []
    strategies = [
        ("phonetic_confusion", lambda t: apply_phonetic_confusion(t)),
        ("number_garbling", lambda t: apply_number_garbling(t)),
        ("word_drop", lambda t: apply_word_drop(t)),
        ("filler_injection", lambda t: apply_filler_injection(t)),
        ("combined", lambda t: apply_word_drop(apply_phonetic_confusion(apply_number_garbling(t)))),
    ]
    chosen = random.sample(strategies, k=min(n, len(strategies)))
    for name, fn in chosen:
        corrupted = fn(clean_text)
        variants.append({
            "category": "asr_error",
            "subtype": name,
            "original": clean_text,
            "mutated": corrupted,
        })
    return variants


if __name__ == "__main__":
    examples = [
        "I want to cancel my appointment on Tuesday at fifteen hundred",
        "Can I book a cleaning for John Smith next Tuesday at two",
    ]
    for ex in examples:
        print(f"ORIGINAL: {ex}")
        for v in generate_asr_mutations(ex, n=3, seed=42):
            print(f"  [{v['subtype']}] {v['mutated']}")
        print()
