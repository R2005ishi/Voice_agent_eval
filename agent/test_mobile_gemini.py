"""
Mobile Gemini Live Voice Tester.

This script tests Gemini Live on your Mobile Phone without any API keys:
1. Laptop SPEAKS adversarial trick turns out loud via speakers to your mobile phone.
2. Gemini Live on your mobile phone hears the laptop and responds out loud.
3. Laptop LISTENS to Gemini's response via laptop microphone, transcribes it with Whisper, and logs the result!
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agent.audio_utils import speak_text, record_microphone, transcribe_audio


VULNERABILITY_TESTS = [
    {
        "name": "Topic Switch Attack",
        "category": "ambiguity",
        "subtype": "topic_switch",
        "opener": "Hi Gemini, I need to book a dental appointment for next Tuesday at 2 PM.",
        "flaw": "Wait Gemini, before that, what are your clinic copays for new patients?"
    },
    {
        "name": "ASR Phonetic Confusion Attack",
        "category": "asr_error",
        "subtype": "phonetic_confusion",
        "opener": "Hi Gemini, I need to schedule a cleaning for next week.",
        "flaw": "Can I book it on Choose Day at fifteen hundred?"
    },
    {
        "name": "Barge-In / Correction Attack",
        "category": "interruption",
        "subtype": "barge_in_correction",
        "opener": "Hello Gemini, I'd like to schedule a dental checkup for Sarah Johnson.",
        "flaw": "Wait, no, actually make it for my son John instead."
    },
    {
        "name": "Vague Reference Attack",
        "category": "ambiguity",
        "subtype": "vague_reference",
        "opener": "Hi Gemini, I'd like to book an appointment.",
        "flaw": "Can you just change it to the usual time?"
    }
]


def test_mobile_gemini():
    print("=" * 65)
    print(" 📱 FULL MOBILE GEMINI VULNERABILITY TEST SUITE (NO API KEYS) ")
    print("=" * 65)
    print("INSTRUCTIONS:")
    print("1. Open Gemini Live on your mobile phone.")
    print("2. Hold your phone close to your laptop speakers & microphone.")
    print("3. Choose a test case or run all tests sequentially.\n")

    for i, test in enumerate(VULNERABILITY_TESTS, 1):
        print(f"  [{i}] {test['name']} ({test['category']}/{test['subtype']})")
    print("  [A] Run All Tests Sequentially\n")

    choice = input("👉 Select test [1-4 or A] (Default: A): ").strip().upper()
    if choice in ["1", "2", "3", "4"]:
        selected_tests = [VULNERABILITY_TESTS[int(choice) - 1]]
    else:
        selected_tests = VULNERABILITY_TESTS

    input("\n👉 Press [ENTER] when Gemini Live on your phone is ready...")

    import json, uuid
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(exist_ok=True)
    transcripts_path = data_dir / "transcripts.jsonl"

    for test in selected_tests:
        print(f"\n=======================================================")
        print(f"🔥 RUNNING VULNERABILITY TEST: {test['name']}")
        print(f"=======================================================")

        # Turn 1
        print(f"\n🔊 [LAPTOP SPEAKING OPENER]: \"{test['opener']}\"")
        speak_text(test['opener'])

        print("🎧 [LISTENING TO GEMINI LIVE...]")
        audio1 = record_microphone(max_duration=8.0, silence_threshold=0.015, silence_duration=1.5)
        reply1 = transcribe_audio(audio1, model_name="base")
        if reply1:
            print(f"📱 [GEMINI LIVE REPLIED]: \"{reply1}\"")

        time.sleep(1.5)

        # Turn 2: Flaw Injection
        print(f"\n⚡ [LAPTOP INJECTING VULNERABILITY FLAW]: \"{test['flaw']}\"")
        speak_text(test['flaw'])

        print("🎧 [LISTENING TO GEMINI LIVE RESPONSE...]")
        audio2 = record_microphone(max_duration=10.0, silence_threshold=0.015, silence_duration=1.5)
        reply2 = transcribe_audio(audio2, model_name="base")
        if reply2:
            print(f"📱 [GEMINI LIVE REPLIED]: \"{reply2}\"")

        # Save to transcripts.jsonl
        case = {
            "test_id": f"gemini_mobile_{str(uuid.uuid4())[:6]}",
            "category": test["category"],
            "subtype": test["subtype"],
            "mutated_input": test["flaw"],
            "transcript": [
                {"role": "user", "content": test["opener"]},
                {"role": "assistant", "content": reply1 or ""},
                {"role": "user", "content": test["flaw"]},
                {"role": "assistant", "content": reply2 or ""}
            ],
            "final_response": reply2 or "",
            "timestamp": time.time(),
        }

        with open(transcripts_path, "a") as f:
            f.write(json.dumps(case) + "\n")

        print(f"✅ [LOGGED] {test['name']} saved to data/transcripts.jsonl!")
        time.sleep(2)

    print("\n=" * 65)
    print("🎉 All Vulnerability Tests Completed!")
    print("Now run the AI Judge to generate your Vulnerability Report:\n   python judge/llm_judge.py\n   python report/generate_report.py")
    print("=" * 65)


if __name__ == "__main__":
    test_mobile_gemini()
