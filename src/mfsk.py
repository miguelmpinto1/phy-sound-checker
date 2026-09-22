# SPDX-License-Identifier: MIT
"""Modulação e demodulação M-FSK (Multiple Frequency-Shift Keying).

Cada símbolo de k bits é mapeado para uma frequência distinta.
Com M frequências, cada símbolo carrega k = log2(M) bits.
"""

import numpy as np

SAMPLE_RATE = 44100
SYMBOL_DURATION = 0.02      # 20 ms por símbolo
SYMBOL_GAP = 0.002          # 2 ms de silêncio entre símbolos
BASE_FREQ = 1000.0          # frequência do símbolo 0
FREQ_STEP = 500.0           # espaçamento entre frequências
FADE_TIME = 0.005           # envelope de 5 ms nas bordas de cada tom (evita cliques)
SILENCE_RATIO = 1e-3        # energia abaixo desta fração do pico é tratada como silêncio


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
    # envelope nas bordas
    fade = min(int(FADE_TIME * sample_rate), n // 2)
    if fade > 0:
        env = np.ones(n)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        wave *= env
    return wave.astype(np.float32)


def _gap(sample_rate: int, duration: float = SYMBOL_GAP) -> np.ndarray:
    """Silêncio curto usado entre símbolos."""
    return np.zeros(int(duration * sample_rate), dtype=np.float32)


def bits_to_symbols(bits: list[int], m: int) -> list[int]:
    """Agrupa bits em símbolos de k bits (com padding de zeros no fim)."""
    k = bits_per_symbol(m)
    padded = list(bits) + [0] * ((-len(bits)) % k)

    symbols = []
    for i in range(0, len(padded), k):
        value = 0
        for b in padded[i:i + k]:
            value = (value << 1) | b
        symbols.append(value)
    return symbols


def symbols_to_bits(symbols: list[int], m: int) -> list[int]:
    """Desfaz o agrupamento: símbolos -> lista de bits (MSB first)."""
    k = bits_per_symbol(m)
    bits = []
    for s in symbols:
        for i in range(k - 1, -1, -1):
            bits.append((s >> i) & 1)
    return bits


def modulate(bits: list[int], m: int = 4,
             sample_rate: int = SAMPLE_RATE,
             symbol_duration: float = SYMBOL_DURATION) -> np.ndarray:
    """Converte uma lista de bits em um sinal de áudio M-FSK.

    Cada símbolo vira um tom na frequência correspondente, seguido de um gap de silêncio.
    """
    freqs = symbol_frequencies(m)
    symbols = bits_to_symbols(bits, m)
    if not symbols:
        return np.zeros(0, dtype=np.float32)

    chunks = []
    for s in symbols:
        chunks.append(_tone(freqs[s], symbol_duration, sample_rate))
        chunks.append(_gap(sample_rate))
    return np.concatenate(chunks)


def _window_energies(samples: np.ndarray, fft_freqs: np.ndarray,
                     freqs: list[float], n: int, start: int) -> list[float]:
    """Energia da janela [start, start + n) em cada frequência esperada (bin mais próximo)."""
    window = samples[start:start + n] * np.hanning(n)
    spectrum = np.abs(np.fft.rfft(window))
    return [float(spectrum[int(np.argmin(np.abs(fft_freqs - f)))]) for f in freqs]


def _first_active_sample(samples: np.ndarray) -> int | None:
    """Índice da primeira amostra relevante (ignora o silêncio de sincronismo inicial)."""
    if len(samples) == 0:
        return None
    peak = float(np.max(np.abs(samples)))
    if peak <= 0:
        return None
    active = np.flatnonzero(np.abs(samples) > peak * SILENCE_RATIO)
    return int(active[0]) if len(active) else None


def demodulate(signal: np.ndarray, m: int = 4,
               sample_rate: int = SAMPLE_RATE,
               symbol_duration: float = SYMBOL_DURATION) -> list[int]:
    """Converte um sinal M-FSK de volta em bits via FFT por janela.

    O primeiro trecho ativo do sinal serve de referência de sincronismo e janelas sem
    energia relevante (silêncio de guarda) não geram bits.
    """
    samples = np.asarray(signal, dtype=np.float64).ravel()
    n = int(symbol_duration * sample_rate)
    if n <= 0 or len(samples) < n:
        return []

    freqs = symbol_frequencies(m)
    fft_freqs = np.fft.rfftfreq(n, 1 / sample_rate)
    step = n + int(_gap(sample_rate).size)

    start = _first_active_sample(samples)
    if start is None:
        return []

    energies = [
        _window_energies(samples, fft_freqs, freqs, n, pos)
        for pos in range(start, len(samples) - n + 1, step)
    ]
    if not energies:
        return []

    peak = max(max(window) for window in energies)
    if peak <= 0:
        return []

    floor = peak * SILENCE_RATIO
    bits: list[int] = []
    for window in energies:
        if max(window) < floor:
            continue    # janela silenciosa (gap ou guarda): não representa símbolo
        bits.extend(symbols_to_bits([int(np.argmax(window))], m))
    return bits
