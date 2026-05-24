"""
voice_agent.py — CLI Voice Agent (microphone loop)
Fixed indentation bug + UUID temp files + confidence threshold
Kannada Disaster Management AI System
"""

import asyncio
import uuid
import numpy as np
import sounddevice as sd
import soundfile as sf
import edge_tts

from faster_whisper import WhisperModel
from config import WHISPER_MODEL_SIZE, TTS_VOICE, AUDIO_DIR
from services.chatbot_service import ask_chatbot

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
DURATION = 7
MIN_LOGPROB = -1.0      # Whisper segment confidence threshold

# ─────────────────────────────────────────────────────────────────────────────
# Load Whisper
# ─────────────────────────────────────────────────────────────────────────────
print("Loading Whisper model...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("Voice Agent Ready!\n")


# ─────────────────────────────────────────────────────────────────────────────
# Record Audio
# ─────────────────────────────────────────────────────────────────────────────
def record_audio() -> str:
    """Record from microphone and save as WAV. Returns file path."""
    print("\n🎤 Speak now...")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()

    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    audio = (audio * 32767).astype("int16")

    # UUID filename — no collision
    audio_path = str(AUDIO_DIR / f"cli_{uuid.uuid4().hex}.wav")
    sf.write(audio_path, audio, SAMPLE_RATE)
    return audio_path


# ─────────────────────────────────────────────────────────────────────────────
# Speech to Text  (indentation bug FIXED)
# ─────────────────────────────────────────────────────────────────────────────
def speech_to_text(audio_file: str) -> str:
    """Transcribe audio to Kannada text using Whisper."""
    try:
        segments, info = whisper_model.transcribe(
            audio_file,
            language="kn",
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )

        # Filter by confidence — FIXED: was outside try block before
        valid = [
            seg.text for seg in segments
            if getattr(seg, "avg_logprob", -0.5) >= MIN_LOGPROB
        ]
        text = " ".join(valid).strip()

        # Kannada script detection fallback
        if text and not any("\u0C80" <= ch <= "\u0CFF" for ch in text):
            transliteration_prompt = (
                f"Convert this Kannada speech transliteration to proper Kannada script.\n"
                f"Text: {text}\nReturn ONLY Kannada text."
            )
            try:
                result = ask_chatbot(transliteration_prompt)
                recovered = result.get("response", "").strip()
                if recovered:
                    text = recovered
            except Exception:
                pass  # keep original text if recovery fails

        print(f"\n🗣️  You: {text}")
        return text

    except Exception as e:
        print(f"❌ STT Error: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Text to Speech
# ─────────────────────────────────────────────────────────────────────────────
async def _speak_async(text: str) -> None:
    out_path = str(AUDIO_DIR / f"cli_resp_{uuid.uuid4().hex}.mp3")
    try:
        communicate = edge_tts.Communicate(text, voice=TTS_VOICE)
        await communicate.save(out_path)
        data, samplerate = sf.read(out_path)
        sd.play(data, samplerate)
        sd.wait()
    except Exception as e:
        print(f"❌ TTS Error: {e}")


def speak(text: str) -> None:
    asyncio.run(_speak_async(text))


# ─────────────────────────────────────────────────────────────────────────────
# CLI Main Loop
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    session_id = f"cli_{uuid.uuid4().hex[:8]}"
    print("Press ENTER to speak | Type 'exit' to quit\n")

    while True:
        user_input = input(">>> ")
        if user_input.lower() == "exit":
            break

        audio_path = record_audio()
        query = speech_to_text(audio_path)

        if not query:
            print("⚠️  Could not understand audio — please try again\n")
            continue

        try:
            result = ask_chatbot(query, session_id=session_id)
            severity = result["severity"]
            response = result["response"]

            severity_icons = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
            icon = severity_icons.get(severity, "🔵")

            print(f"\n{icon} Severity: {severity}")
            print(f"\n🤖 Assistant:\n{response}")
            if result["is_offline"]:
                print("⚠️  [Offline Mode — LLM API unavailable]")
            print("\n🔊 Speaking...\n")
            speak(response)

        except Exception as e:
            print(f"❌ Chatbot Error: {e}")


if __name__ == "__main__":
    main()