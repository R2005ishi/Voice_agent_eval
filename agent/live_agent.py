"""
Live Voice Agent Client Adapter.

Use this adapter to test any production Voice Agent (e.g. Vapi, Retell, OpenAI, custom REST/Webhook API)
instead of the local Ollama agent.
"""

import os
import requests


class LiveVoiceAgent:
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        Initialize client for your live production voice agent endpoint.
        """
        self.api_url = api_url or os.getenv("LIVE_AGENT_URL", "https://api.your-voice-agent.com/v1/chat")
        self.api_key = api_key or os.getenv("LIVE_AGENT_API_KEY", "your_api_key_here")
        self.session_id = None
        self.history = []

    def reset(self):
        self.session_id = None
        self.history = []

    def step(self, user_utterance: str) -> dict:
        """
        Sends one user turn to your live agent API and returns structured response.
        
        Expected output dictionary format:
          {"text": "Agent's text response", "tool_call": dict|None}
        """
        self.history.append({"role": "user", "content": user_utterance})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "message": user_utterance,
            "session_id": self.session_id,
            "history": self.history
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Save session_id if returned by the live platform
            if "session_id" in data:
                self.session_id = data["session_id"]

            agent_text = data.get("response", data.get("text", data.get("message", "")))
            tool_call = data.get("tool_call")

            self.history.append({"role": "assistant", "content": agent_text})

            return {
                "text": agent_text,
                "tool_call": tool_call,
                "turn_count": len([m for m in self.history if m["role"] == "user"])
            }
        except Exception as e:
            print(f"❌ [Live Agent Error] API request failed: {e}")
            return {
                "text": f"API Error: {str(e)}",
                "tool_call": None,
                "turn_count": len(self.history)
            }


if __name__ == "__main__":
    # Test client
    print("LiveVoiceAgent client ready.")
