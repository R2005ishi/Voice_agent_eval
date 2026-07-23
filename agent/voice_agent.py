"""
Interactive Real Voice Agent for Appointment Scheduling.

This script runs the SchedulingAgent with real audio:
- Speaks to you via Text-to-Speech (edge-tts)
- Listens to your voice via Microphone & transcribes with Whisper (STT)
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from agent.scheduling_agent import SchedulingAgent
from agent.audio_utils import speak_text, record_microphone, transcribe_audio


def run_interactive_voice_agent(whisper_model: str = "base"):
    print("=" * 60)
    print("      🎙️ DENTAL CLINIC VOICE AGENT (INTERACTIVE MODE)      ")
    print("=" * 60)
    print("Speak clearly into your microphone when prompt appears.")
    print("Type 'exit' or press Ctrl+C to quit at any time.\n")

    agent = SchedulingAgent()
    
    greeting = "Hello! Welcome to the dental clinic. How can I help you today?"
    speak_text(greeting)
    
    turn = 0
    while True:
        turn += 1
        print(f"\n--- [TURN {turn}] ---")
        
        # 1. Record user audio
        audio_data = record_microphone(max_duration=10.0, silence_threshold=0.015, silence_duration=1.5)
        
        if len(audio_data) == 0:
            print("[Voice Agent] No input detected. Asking user again...")
            speak_text("I'm sorry, I didn't catch that. Could you please repeat?")
            continue
            
        # 2. Transcribe user audio
        user_utterance = transcribe_audio(audio_data, model_name=whisper_model)
        
        if not user_utterance or len(user_utterance.strip()) == 0:
            speak_text("I didn't hear anything. Could you try speaking again?")
            continue
            
        if user_utterance.lower().strip() in ["exit", "quit", "bye", "goodbye"]:
            speak_text("Thank you for calling. Have a great day!")
            print("\n[Voice Agent Session Ended]")
            break
            
        # 3. Agent response step
        try:
            agent_output = agent.step(user_utterance)
            agent_text = agent_output["text"]
            
            # 4. Speak response back
            speak_text(agent_text)
            
            # 5. Check if booking was completed
            if agent_output.get("tool_call"):
                tool = agent_output["tool_call"]
                print(f"\n🎉 [SUCCESS] Tool Executed: {tool['name']} with args {tool['args']}")
                speak_text("Your appointment is all set. Thank you for calling!")
                print("\n[Voice Agent Session Completed Successfully]")
                break
                
        except Exception as e:
            print(f"❌ Error during agent processing: {e}")
            speak_text("I encountered a technical issue. Please make sure Ollama is running.")
            break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium)")
    args = parser.parse_args()
    
    run_interactive_voice_agent(whisper_model=args.model)
