"""
Generates a markdown report: failure rates by category/subtype, plus
concrete example transcripts for each failure found. This is the
"failure taxonomy" deliverable -- the artifact you'd actually show in
an interview.
"""

import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TRANSCRIPTS_PATH = DATA_DIR / "transcripts.jsonl"
JUDGMENTS_PATH = DATA_DIR / "judgments.jsonl"
REPORT_PATH = Path(__file__).resolve().parent / "failure_report.md"


def generate():
    transcripts = {}
    with open(TRANSCRIPTS_PATH) as f:
        for line in f:
            c = json.loads(line)
            transcripts[c["test_id"]] = c

    judgments = []
    with open(JUDGMENTS_PATH) as f:
        for line in f:
            judgments.append(json.loads(line))

    by_category = defaultdict(lambda: {"total": 0, "failures": 0, "examples": []})

    for j in judgments:
        tid = j["test_id"]
        case = transcripts.get(tid)
        if not case:
            continue
        key = f"{case['category']}/{case['subtype']}"
        by_category[key]["total"] += 1
        verdict = j["verdict"]
        is_failure = verdict.get("overall_failure", False)
        if is_failure:
            by_category[key]["failures"] += 1
            by_category[key]["examples"].append((case, verdict))

    lines = ["# Voice Agent Failure Taxonomy Report\n"]
    lines.append("Automated adversarial testing results for the toy scheduling agent.\n")

    lines.append("## Summary\n")
    lines.append("| Category | Total Tests | Failures | Failure Rate |")
    lines.append("|---|---|---|---|")
    for key, stats in sorted(by_category.items()):
        rate = stats["failures"] / stats["total"] if stats["total"] else 0
        lines.append(f"| {key} | {stats['total']} | {stats['failures']} | {rate:.0%} |")

    lines.append("\n## Example Failures\n")
    for key, stats in sorted(by_category.items()):
        if not stats["examples"]:
            continue
        lines.append(f"### {key}\n")
        for case, verdict in stats["examples"][:2]:  # cap examples per category
            lines.append(f"**Test ID:** `{case['test_id']}`\n")
            lines.append("```")
            for m in case["transcript"]:
                if m["role"] == "system":
                    continue
                role = "CALLER" if m["role"] == "user" else "AGENT"
                lines.append(f"{role}: {m['content']}")
            lines.append("```")
            lines.append(f"**Judge findings:**")
            for axis, result in verdict.items():
                if axis == "overall_failure" or not isinstance(result, dict):
                    continue
                if result.get("verdict") == "FAIL":
                    lines.append(f"- `{axis}`: FAIL — {result.get('reason')}")
            lines.append("")

    REPORT_PATH.write_text("\n".join(lines))
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    generate()
