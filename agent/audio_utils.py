"""
Audio utilities for Voice Agent Eval:
- Text-to-Speech (TTS) using edge-tts
- Audio playback via sounddevice/soundfile
- Speech-to-Text (STT) using Whisper
- Microphone recording with voice activity / silence detection
"""

import asyncio
import os
import sys
import tempfile
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import edge_tts

# Try importing whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

_whisper_model = None


def get_whisper_model(model_name: str = "base"):
    global _whisper_model
    if not WHISPER_AVAILABLE:
        raise ImportError("openai-whisper is not installed. Run 'pip install openai-whisper'")
    if _whisper_model is None:
        print(f"[STT] Loading Whisper model ({model_name})...")
        _whisper_model = whisper.load_model(model_name)
    return _whisper_model


async def _generate_tts_async(text: str, output_path: str, voice: str = "en-US-AvaNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def speak_text(text: str, voice: str = "en-US-AvaNeural"):
    """
    Synthesizes text to speech and plays it over speakers.
    """
    if not text or not text.strip():
        return

    print(f"\n🗣️ [AGENT SPEAKING]: {text}")
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_mp3 = f.name

    try:
        # Generate TTS audio file
        asyncio.run(_generate_tts_async(text, temp_mp3, voice))
        
        # Read and play audio
        data, fs = sf.read(temp_mp3)
        sd.play(data, fs)
        sd.wait()
    except Exception as e:
        print(f"[TTS Error] Could not play audio: {e}")
    finally:
        if os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except Exception:
                pass


def record_microphone(
    sample_rate: int = 16000,
    max_duration: float = 10.0,
    silence_threshold: float = 0.015,
    silence_duration: float = 1.5
) -> np.ndarray:
    """
    Records audio from the default microphone until silence is detected or max_duration is reached.
    Returns 1D float32 numpy array sampled at sample_rate (16000Hz).
    """
    print("\n🎙️ [LISTENING... Speak into your mic! Press Ctrl+C to stop early]")
    
    chunk_duration = 0.1  # 100ms chunks
    chunk_samples = int(sample_rate * chunk_duration)
    
    audio_buffer = []
    silent_chunks = 0
    required_silent_chunks = int(silence_duration / chunk_duration)
    has_speech_started = False
    
    start_time = time.time()
    
    def callback(indata, frames, time_info, status):
        nonlocal silent_chunks, has_speech_started
        if status:
            print(f"[Mic Warning] {status}", file=sys.stderr)
        
        volume_norm = np.linalg.norm(indata) / np.sqrt(len(indata))
        
        if volume_norm > silence_threshold:
            if not has_speech_started:
                print("   [Speech detected... recording]")
            has_speech_started = True
            silent_chunks = 0
        elif has_speech_started:
            silent_chunks += 1
            
        audio_buffer.append(indata.copy())

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', callback=callback, blocksize=chunk_samples):
            while time.time() - start_time < max_duration:
                sd.sleep(100)
                if has_speech_started and silent_chunks >= required_silent_chunks:
                    print("   [Silence detected, stopping recording]")
                    break
    except Exception as e:
        print(f"[Mic Error] Could not access microphone: {e}")
        return np.array([], dtype=np.float32)

    if not audio_buffer or not has_speech_started:
        print("   [No speech detected]")
        return np.array([], dtype=np.float32)

    audio_data = np.concatenate(audio_buffer, axis=0).flatten().astype(np.float32)
    return audio_data


def transcribe_audio(audio_input, model_name: str = "base") -> str:
    """
    Transcribes audio using Whisper.
    audio_input can be either a filepath (str) or numpy float32 array.
    """
    if audio_input is None:
        return ""
    if isinstance(audio_input, np.ndarray) and len(audio_input) == 0:
        return ""
    if isinstance(audio_input, str) and (not audio_input or not os.path.exists(audio_input)):
        return ""

    try:
        model = get_whisper_model(model_name)
        result = model.transcribe(audio_input, fp16=False)
        transcription = result.get("text", "").strip()
        print(f"👂 [USER HEARD]: \"{transcription}\"")
        return transcription
    except Exception as e:
        print(f"[STT Error] Transcription failed: {e}")
        return ""


if __name__ == "__main__":
    # Test speak
    speak_text("Testing microphone and audio utilities.")
    
    # Test mic & STT
    audio_np = record_microphone(max_duration=5.0)
    if len(audio_np) > 0:
        text = transcribe_audio(audio_np)
        print(f"Result: {text}")
