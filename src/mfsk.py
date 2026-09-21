# SPDX-License-Identifier: MIT
"""Modulação e demodulação M-FSK (Multiple Frequency-Shift Keying).

Cada símbolo de k bits é mapeado para uma frequência distinta.
Com M frequências, cada símbolo carrega k = log2(M) bits.
"""
import numpy as np

SAMPLE_RATE = 44100
SYMBOL_DURATION = 0.02          # 20 ms por símbolo
BASE_FREQ = 1000.0              # frequência do símbolo 0
FREQ_STEP = 500.0               # espaçamento entre frequências


def symbol_frequencies(m: int) -> list[float]:
    """Devolve as M frequências usadas na modulação."""
    return [BASE_FREQ + i * FREQ_STEP for i in range(m)]


def bits_per_symbol(m: int) -> int:
    """Quantos bits cabem em cada símbolo (k = log2(M))."""
    k = m.bit_length() - 1
    if 1 << k != m:
        raise ValueError("M deve ser potência de 2")
    return k


def _tone(freq: float, duration: float, sample_rate: int) -> np.ndarray:
    """Gera um tom senoidal puro com envelope suave (evita cliques)."""
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    wave = np.sin(2 * np.pi * freq * t)
    # envelope de 5 ms nas bordas
    fade = int(0.005 * sample_rate)
    if fade > 0:
        env = np.ones(n)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        wave *= env
    return wave.astype(np.float32)


def bits_to_symbols(bits: list[int], m: int) -> list[int]:
    """Agrupa bits em símbolos de k bits (com padding no fim)."""
    k = bits_per_symbol(m)
    padded = bits + [0] * ((-len(bits)) % k)
    symbols = []
    for i in range(0, len(padded), k):
        value = 0
        for b in padded[i:i + k]:
            value = (value << 1) | b
        symbols.append(value)
    return symbols


def symbols_to_bits(symbols: list[int], m: int) -> list[int]:
    """Desfaz o agrupamento: símbolos -> lista de bits."""
    k = bits_per_symbol(m)
    bits = []
    for s in symbols:
        for i in range(k - 1, -1, -1):
            bits.append((s >> i) & 1)
    return bits


def modulate(bits: list[int], m: int = 4,
             sample_rate: int = SAMPLE_RATE,
             symbol_duration: float = SYMBOL_DURATION) -> np.ndarray:
    """Converte uma lista de bits em um sinal de áudio M-FSK."""
    freqs = symbol_frequencies(m)
    symbols = bits_to_symbols(bits, m)
    chunks = [_tone(freqs[s], symbol_duration, sample_rate) for s in symbols]
    # silêncio curto entre símbolos ajuda a evitar interferência
    gap = np.zeros(int(0.002 * sample_rate), dtype=np.float32)
    out = []
    for c in chunks:
        out.append(c)
        out.append(gap)
    return np.concatenate(out) if out else np.zeros(0, dtype=np.float32)


def demodulate(signal: np.ndarray, m: int = 4,
               sample_rate: int = SAMPLE_RATE,
               symbol_duration: float = SYMBOL_DURATION) -> list[int]:
    """Converte um sinal M-FSK de volta em bits via FFT por janela."""
    freqs = symbol_frequencies(m)
    n = int(symbol_duration * sample_rate)
    step = n + int(0.002 * sample_rate)   # símbolo + gap
    bits = []
    for start in range(0, len(signal) - n, step):
        window = signal[start:start + n]
        if len(window) < n:
            break
        # janela de Hann reduz vazamento espectral
        window = window * np.hanning(len(window))
        spectrum = np.abs(np.fft.rfft(window))
        fft_freqs = np.fft.rfftfreq(len(window), 1 / sample_rate)
        # energia em cada frequência esperada (bin mais próximo)
        energies = []
        for f in freqs:
            idx = int(np.argmin(np.abs(fft_freqs - f)))
            energies.append(spectrum[idx])
        symbol = int(np.argmax(energies))
        bits.extend(symbols_to_bits([symbol], m))
    return bits