"""Optional, local-only speech recognition and speech synthesis helpers."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from config import PIPER_EXECUTABLE, TTS_ENGINE, TTS_VOICE, WHISPER_MODEL


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file with Faster-Whisper on this computer."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
    except ImportError as exc:
        raise RuntimeError("Install the optional voice packages from requirements.txt to transcribe audio.") from exc


def synthesize_speech(text: str, output_path: str | None = None) -> str:
    """Synthesize speech locally with Windows/macOS/Linux voices or Piper."""
    if TTS_ENGINE == "pyttsx3":
        try:
            import pyttsx3
        except ImportError as exc:
            raise RuntimeError("Install the project requirements to use the local pyttsx3 voice.") from exc
        if output_path:
            target = Path(output_path)
        else:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                target = Path(temp.name)
        engine = pyttsx3.init()
        if TTS_VOICE and TTS_VOICE.lower() != "default":
            matching = [voice for voice in engine.getProperty("voices") if TTS_VOICE in (voice.id, voice.name)]
            if matching:
                engine.setProperty("voice", matching[0].id)
        engine.save_to_file(text, str(target))
        engine.runAndWait()
        engine.stop()
        return str(target)
    if TTS_ENGINE != "piper":
        raise RuntimeError(f"Unsupported local TTS engine: {TTS_ENGINE}. Use pyttsx3 or piper.")
    executable = shutil.which(PIPER_EXECUTABLE)
    if not executable:
        raise RuntimeError("Piper executable was not found. Install Piper and add it to PATH.")
    model_path = Path(TTS_VOICE)
    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parent / model_path
    if not model_path.is_file():
        raise RuntimeError(f"Piper voice model not found at {model_path}. See README for the local voice download steps.")
    if output_path:
        target = Path(output_path)
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            target = Path(temp.name)
    result = subprocess.run(
        [executable, "--model", str(model_path), "--output_file", str(target)],
        input=text,
        text=True,
        capture_output=True,
        timeout=90,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Piper could not synthesize speech.")
    return str(target)


def voice_status() -> tuple[bool, str]:
    if TTS_ENGINE == "pyttsx3":
        try:
            import pyttsx3  # noqa: F401
            return True, "Local system voices available"
        except ImportError:
            return False, "pyttsx3 not installed"
    if shutil.which(PIPER_EXECUTABLE) is None:
        return False, "Piper not installed"
    model_path = Path(TTS_VOICE)
    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parent / model_path
    if not model_path.is_file():
        return False, "Piper voice model not installed"
    return True, "Piper and voice model available"
