# SPDX-License-Identifier: MIT
"""Reprodução e gravação de áudio via sounddevice."""

import numpy as np

SAMPLE_RATE = 44100

try:
    import sounddevice as sd
    AUDIO_ERROR = ""
except (ImportError, OSError) as exc:   # libportaudio ausente no ambiente
    sd = None
    AUDIO_ERROR = str(exc)

AUDIO_AVAILABLE = sd is not None


def _require_audio() -> None:
    if not AUDIO_AVAILABLE:
        raise RuntimeError(
            "dispositivo de áudio indisponível neste ambiente "
            f"(sounddevice/PortAudio: {AUDIO_ERROR})"
        )


def play(signal: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Reproduz um sinal de áudio pelo alto-falante."""
    _require_audio()
    sd.play(signal, samplerate=sample_rate)
    sd.wait()


def record(duration: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Grava áudio do microfone por 'duration' segundos."""
    _require_audio()
    print(f"[áudio] gravando por {duration:.1f}s...")
    rec = sd.rec(int(duration * sample_rate),
                 samplerate=sample_rate,
                 channels=1, dtype="float32")
    sd.wait()
    print("[áudio] gravação concluída.")
    return rec.flatten()


def save_wav(signal: np.ndarray, path: str, sample_rate: int = SAMPLE_RATE) -> str:
    """Salva o sinal em um arquivo .wav (útil em ambientes sem placa de som)."""
    import wave

    samples = np.clip(np.asarray(signal, dtype=np.float32), -1.0, 1.0)
    pcm = (samples * 32767).astype("<i2").tobytes()

    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)

    return path
