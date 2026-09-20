# SPDX-License-Identifier: MIT
"""Módulo de emissão de áudio via Multi-Tone FSK."""

import numpy as np
import sounddevice as sd
from scipy.signal.windows import tukey

import audio_config as cfg


def bits_to_audio(bits: list[int]) -> np.ndarray:
    """Converte lista de bits em sinal de áudio M-FSK com janela suave (Tukey)."""
    remainder = len(bits) % cfg.NUM_TONES
    if remainder != 0:
        bits = bits + [0] * (cfg.NUM_TONES - remainder)

    num_symbols = len(bits) // cfg.NUM_TONES
    samples_per_symbol = int(cfg.FS * cfg.SYMBOL_DURATION)
    t = np.linspace(0, cfg.SYMBOL_DURATION, samples_per_symbol, endpoint=False)
    
    # Janela de Tukey para suavizar bordas de cada símbolo (elimina estalos)
    window = tukey(samples_per_symbol, alpha=0.25)
    audio_signal = np.array([], dtype=np.float32)

    for i in range(num_symbols):
        chunk = bits[i * cfg.NUM_TONES : (i + 1) * cfg.NUM_TONES]
        symbol_wave = np.zeros(samples_per_symbol, dtype=np.float32)

        for tone_idx, bit in enumerate(chunk):
            if bit == 1:
                freq = cfg.FREQ_START + (tone_idx * cfg.FREQ_STEP)
                symbol_wave += np.sin(2 * np.pi * freq * t)

        # Normaliza amplitude para evitar distorção no hardware
        max_val = np.max(np.abs(symbol_wave))
        if max_val > 0:
            symbol_wave = (symbol_wave / max_val) * 0.4

        audio_signal = np.concatenate((audio_signal, symbol_wave * window))

    return audio_signal


def transmit_bits(bits: list[int]) -> None:
    """Gera o som e transmite através do alto-falante."""
    signal = bits_to_audio(bits)
    sd.play(signal, samplerate=cfg.FS)
    sd.wait()