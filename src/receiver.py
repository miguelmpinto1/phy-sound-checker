# SPDX-License-Identifier: MIT
"""Módulo de recepção, filtragem passa-faixa e demodulação via FFT."""

import numpy as np
from scipy.signal import butter, sosfilt
from scipy.signal.windows import hann

import audio_config as cfg


def apply_bandpass_filter(audio_data: np.ndarray) -> np.ndarray:
    """Filtra o áudio mantendo apenas a faixa ativa configurada."""
    sos = butter(
        N=6,
        Wn=[cfg.BANDPASS_LOW, cfg.BANDPASS_HIGH],
        btype="bandpass",
        fs=cfg.FS,
        output="sos",
    )
    return sosfilt(sos, audio_data)


def demodulate_chunk(audio_chunk: np.ndarray) -> list[int]:
    """Processa um bloco do tamanho de 1 símbolo via FFT e extrai 16 bits."""
    n = len(audio_chunk)
    # Aplica janela de Hann no receptor para evitar vazamento de espectro
    windowed_chunk = audio_chunk * hann(n)
    
    fft_spectrum = np.abs(np.fft.rfft(windowed_chunk)) / n
    freqs = np.fft.rfftfreq(n, 1 / cfg.FS)

    bits = []
    for i in range(cfg.NUM_TONES):
        target_freq = cfg.FREQ_START + (i * cfg.FREQ_STEP)
        idx = np.argmin(np.abs(freqs - target_freq))
        magnitude = fft_spectrum[idx]

        bits.append(1 if magnitude > cfg.MAGNITUDE_THRESHOLD else 0)

    return bits


def process_audio_buffer(audio_data: np.ndarray) -> list[int]:
    """Filtra o áudio e demodula em uma lista de bits."""
    filtered_audio = apply_bandpass_filter(audio_data)
    samples_per_symbol = int(cfg.FS * cfg.SYMBOL_DURATION)
    total_symbols = len(filtered_audio) // samples_per_symbol

    extracted_bits = []
    for i in range(total_symbols):
        chunk = filtered_audio[i * samples_per_symbol : (i + 1) * samples_per_symbol]
        bits = demodulate_chunk(chunk)
        extracted_bits.extend(bits)

    return extracted_bits