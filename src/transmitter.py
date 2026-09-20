# SPDX-License-Identifier: MIT
"""Módulo de emissão de áudio via Multi-Tone FSK."""

import numpy as np
import sounddevice as sd
from scipy.signal.windows import tukey
import audio_config as cfg


def bits_to_audio(bits: list[int]) -> np.ndarray:
    """Converte o vetor de bits do quadro em frequências de áudio M-FSK."""
    remainder = len(bits) % cfg.NUM_TONES
    if remainder != 0:
        bits = bits + [0] * (cfg.NUM_TONES - remainder)

    num_symbols = len(bits) // cfg.NUM_TONES
    samples_per_symbol = int(cfg.FS * cfg.SYMBOL_DURATION)
    t = np.linspace(0, cfg.SYMBOL_DURATION, samples_per_symbol, endpoint=False)
    
    window = tukey(samples_per_symbol, alpha=0.2)
    audio_chunks = []

    # Silêncio + Bip de alerta para acordar a placa de som
    silence = np.zeros(int(cfg.FS * 0.2), dtype=np.float32)
    audio_chunks.append(silence)
    
    t_pre = np.linspace(0, 0.1, int(cfg.FS * 0.1), endpoint=False)
    preamble = (np.sin(2 * np.pi * 1000 * t_pre) * 0.5).astype(np.float32)
    audio_chunks.append(preamble)
    audio_chunks.append(silence)

    # Modulação dos bits em tons
    for i in range(num_symbols):
        chunk = bits[i * cfg.NUM_TONES : (i + 1) * cfg.NUM_TONES]
        symbol_wave = np.zeros(samples_per_symbol, dtype=np.float32)

        has_active_tone = False
        for tone_idx, bit in enumerate(chunk):
            if bit == 1:
                has_active_tone = True
                freq = cfg.FREQ_START + (tone_idx * cfg.FREQ_STEP)
                symbol_wave += np.sin(2 * np.pi * freq * t)

        if has_active_tone:
            max_sym = np.max(np.abs(symbol_wave))
            if max_sym > 0:
                symbol_wave = (symbol_wave / max_sym) * window
            
        audio_chunks.append(symbol_wave)

    audio_chunks.append(silence)
    full_signal = np.concatenate(audio_chunks).astype(np.float32)

    max_val = np.max(np.abs(full_signal))
    if max_val > 0:
        full_signal = (full_signal / max_val) * 0.9

    return full_signal


def transmit_bits(bits: list[int]) -> None:
    """Toca o sinal de áudio gerado pelo quadro de bits."""
    signal = bits_to_audio(bits)
    if len(signal) > 0:
        sd.play(signal, samplerate=cfg.FS)
        sd.wait()