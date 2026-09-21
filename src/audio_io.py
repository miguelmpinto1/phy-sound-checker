# SPDX-License-Identifier: MIT
"""Reprodução e gravação de áudio via sounddevice."""
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100


def play(signal: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Reproduz um sinal de áudio pelo alto-falante."""
    sd.play(signal, samplerate=sample_rate)
    sd.wait()


def record(duration: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Grava áudio do microfone por 'duration' segundos."""
    print(f"[áudio] gravando por {duration:.1f}s...")
    rec = sd.rec(int(duration * sample_rate),
                 samplerate=sample_rate,
                 channels=1, dtype="float32")
    sd.wait()
    print("[áudio] gravação concluída.")
    return rec.flatten()