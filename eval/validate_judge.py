"""
Validates the LLM-judge against human-labeled ground truth.

This is the most important file in the project. Anyone can build an
LLM-as-judge; the credible claim is knowing HOW RELIABLE it is. This
script:
  1. Samples N transcripts from data/transcripts.jsonl
  2. Prints them for YOU to hand-label (overall_failure: true/false)
     into data/human_labels.jsonl
  3. Compares judge verdicts against your labels: precision, recall,
     F1, and a confusion matrix

Usage:
  Step 1 (label): python validate_judge.py --label --n 30
  Step 2 (compare): python validate_judge.py --compare
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRANSCRIPTS_PATH = DATA_DIR / "transcripts.jsonl"
JUDGMENTS_PATH = DATA_DIR / "judgments.jsonl"
HUMAN_LABELS_PATH = DATA_DIR / "human_labels.jsonl"


def label_interactively(n: int = 30):
    with open(TRANSCRIPTS_PATH) as f:
        cases = [json.loads(line) for line in f]
    cases = cases[:n]

    existing_ids = set()
    if HUMAN_LABELS_PATH.exists():
        with open(HUMAN_LABELS_PATH) as f:
            existing_ids = {json.loads(line)["test_id"] for line in f}

    with open(HUMAN_LABELS_PATH, "a") as out:
        for case in cases:
            if case["test_id"] in existing_ids:
                continue
            print("\n" + "=" * 70)
            print(f"[{case['category']}/{case['subtype']}]  test_id={case['test_id']}")
            print("-" * 70)
            for m in case["transcript"]:
                if m["role"] == "system":
                    continue
                role = "CALLER" if m["role"] == "user" else "AGENT"
                print(f"{role}: {m['content']}")
            print("-" * 70)
            ans = input("Is the agent's FINAL response a FAILURE? [y/n/skip]: ").strip().lower()
            if ans == "skip":
                continue
            label = {"test_id": case["test_id"], "human_label_is_failure": ans == "y"}
            out.write(json.dumps(label) + "\n")
            out.flush()
    print(f"\nLabels saved to {HUMAN_LABELS_PATH}")


def compare():
    with open(JUDGMENTS_PATH) as f:
        judgments = {json.loads(line)["test_id"]: json.loads(line) for line in open(JUDGMENTS_PATH)}
    with open(HUMAN_LABELS_PATH) as f:
        human = [json.loads(line) for line in f]

    tp = fp = tn = fn = 0
    mismatches = []

    for h in human:
        tid = h["test_id"]
        if tid not in judgments:
            continue
        verdict = judgments[tid]["verdict"]
        judge_failure = verdict.get("overall_failure", None)
        if judge_failure is None:
            continue
        human_failure = h["human_label_is_failure"]

        if judge_failure and human_failure:
            tp += 1
        elif judge_failure and not human_failure:
            fp += 1
        elif not judge_failure and not human_failure:
            tn += 1
        else:
            fn += 1

        if judge_failure != human_failure:
            mismatches.append(tid)

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else float("nan")
    accuracy = (tp + tn) / total if total else float("nan")

    print(f"\n=== Judge Validation Report (n={total}) ===")
    print(f"Confusion matrix:")
    print(f"                 Human: FAIL   Human: OK")
    print(f"  Judge: FAIL       {tp:>4}          {fp:>4}")
    print(f"  Judge: OK         {fn:>4}          {tn:>4}")
    print()
    print(f"Precision: {precision:.2f}  (of judge-flagged failures, how many were real)")
    print(f"Recall:    {recall:.2f}  (of real failures, how many the judge caught)")
    print(f"F1:        {f1:.2f}")
    print(f"Accuracy:  {accuracy:.2f}")
    if mismatches:
        print(f"\nMismatched test_ids (inspect these for judge failure patterns): {mismatches}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", action="store_true", help="interactively label a sample")
    parser.add_argument("--compare", action="store_true", help="compare judge vs human labels")
    parser.add_argument("--n", type=int, default=30)
    args = parser.parse_args()

    if args.label:
        label_interactively(n=args.n)
    elif args.compare:
        compare()
    else:
        print("Specify --label or --compare")
