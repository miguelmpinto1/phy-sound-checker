# SPDX-License-Identifier: MIT
"""Modulação e demodulação M-FSK (Multiple Frequency-Shift Keying).
Feat: AGC e noise floor
"""

import numpy as np

SAMPLE_RATE = 44100
SYMBOL_DURATION = 0.02
SYMBOL_GAP = 0.002
BASE_FREQ = 1000.0
FREQ_STEP = 500.0
FADE_TIME = 0.005

# --------------------------------------------------------------------------- #
# Parâmetros de robustez do receptor. Nenhum é um nível absoluto de volume ou #
# ruído — todos são multiplicadores sobre uma medida feita na própria         #
# gravação, então funcionam em qualquer hardware, não só no que foi testado. #
# --------------------------------------------------------------------------- #
NOISE_PROBE_DURATION = 0.1   # s — trecho inicial assumido como só ruído
                              #     (cabe dentro do SILENCE_LEAD do método 2, que é maior)
ONSET_SAFETY_FACTOR = 4.0    # a energia de alguma frequência candidata precisa superar
                              #     o ruído medido nessa proporção pra virar "início"
MIN_ONSET_LEVEL = 1e-6       # piso mínimo contra gravação com ruído medido ~0
CONFIDENCE_MARGIN = 2.0      # o vencedor de uma janela precisa ter o dobro de energia do 2º
NOISE_MARGIN = 3.0           # e precisa estar 3x acima do ruído medido, não só acima dos outros


def symbol_frequencies(m: int) -> list[float]:
    return [BASE_FREQ + i * FREQ_STEP for i in range(m)]


def bits_per_symbol(m: int) -> int:
    k = m.bit_length() - 1
    if 1 << k != m:
        raise ValueError("M deve ser potência de 2")
    return k


def _tone(freq: float, duration: float, sample_rate: int) -> np.ndarray:
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    wave = np.sin(2 * np.pi * freq * t)
    fade = min(int(FADE_TIME * sample_rate), n // 2)
    if fade > 0:
        envelope = np.ones(n)
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
        wave *= envelope
    return wave.astype(np.float32)


def _gap(sample_rate: int, duration: float = SYMBOL_GAP) -> np.ndarray:
    return np.zeros(int(duration * sample_rate), dtype=np.float32)


def bits_to_symbols(bits: list[int], m: int) -> list[int]:
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
    k = bits_per_symbol(m)
    bits = []
    for s in symbols:
        for i in range(k - 1, -1, -1):
            bits.append((s >> i) & 1)
    return bits


def modulate(bits: list[int], m: int = 4, sample_rate: int = SAMPLE_RATE,
             symbol_duration: float = SYMBOL_DURATION) -> np.ndarray:
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
    window = samples[start:start + n] * np.hanning(n)
    spectrum = np.abs(np.fft.rfft(window))
    return [float(spectrum[int(np.argmin(np.abs(fft_freqs - f)))]) for f in freqs]


def _estimate_noise_energy(samples: np.ndarray, fft_freqs: np.ndarray, freqs: list[float],
                           n: int, probe_samples: int) -> float:
    """Nível de ruído medido na MESMA unidade das energias por janela (magnitude
    espectral nas frequências candidatas), a partir do trecho inicial da própria
    gravação. Usar a mesma unidade é o que permite comparar ruído com sinal de forma
    justa; usar várias janelas + mediana evita que um único pico de ruído (comum em
    qualquer gravação curta) distorça a medida."""
    if probe_samples < n:
        return 0.0
    probe = samples[:probe_samples]
    step = max(n // 2, 1)
    levels = [
        max(_window_energies(probe, fft_freqs, freqs, n, pos))
        for pos in range(0, len(probe) - n + 1, step)
    ]
    return float(np.median(levels)) if levels else 0.0


def _first_active_window(samples: np.ndarray, fft_freqs: np.ndarray, freqs: list[float],
                         n: int, noise_energy: float) -> int | None:
    """Posição (em amostras) de onde o primeiro tom parece começar, buscando por
    energia espectral (nas frequências candidatas), não amplitude bruta no tempo:
    um tom estreito se destaca do ruído de banda larga na FFT muito mais do que na
    forma de onda crua, então isso localiza o início mesmo com pouca margem de sinal.

    Usa um passo BEM mais fino que o passo de símbolo+gap: se a busca pulasse de
    símbolo em símbolo, o ponto encontrado podia cair no meio do primeiro tom em vez
    do começo dele, e todas as janelas seguintes sairiam desalinhadas a partir daí.
    """
    threshold = max(noise_energy * ONSET_SAFETY_FACTOR, MIN_ONSET_LEVEL)
    hop = max(n // 8, 1)
    candidate = None
    for pos in range(0, len(samples) - n + 1, hop):
        window = _window_energies(samples, fft_freqs, freqs, n, pos)
        if max(window) > threshold:
            candidate = pos
            break
    if candidate is None:
        return None

    # Refinamento: o primeiro cruzamento do limiar pode cair numa janela que só
    # contém uma FRAÇÃO do tom (o resto ainda é silêncio/ruído) — nesse caso a
    # energia detectada é menor que a do tom inteiro, mas ainda passa no limiar.
    # Por isso procura, na vizinhança desse candidato, a posição de energia máxima
    # (a janela mais "cheia" de tom), não a primeira que passou no limiar.
    lo = max(candidate - n, 0)
    hi = min(candidate + n, len(samples) - n)
    fine_hop = max(n // 20, 1)
    best_pos = candidate
    best_energy = 0.0
    for pos in range(lo, hi + 1, fine_hop):
        window = _window_energies(samples, fft_freqs, freqs, n, pos)
        energy = max(window)
        if energy > best_energy:
            best_energy = energy
            best_pos = pos
    return best_pos


def _decide_symbol(window_energies: list[float], noise_energy: float) -> tuple[int, bool]:
    """Decide a frequência vencedora de uma janela exigindo confiança, não só o maior
    valor: o vencedor precisa se destacar tanto do ruído medido quanto do 2º colocado.
    Se a janela for ambígua (símbolo perdido no ruído, ou disputa entre duas frequências
    perto de empatar), ela é marcada como não confiável em vez de arriscar um palpite.
    """
    ranked = sorted(window_energies, reverse=True)
    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else 0.0

    if best < noise_energy * NOISE_MARGIN:
        return 0, False
    if second > 0 and best < second * CONFIDENCE_MARGIN:
        return 0, False

    return int(np.argmax(window_energies)), True


def demodulate(signal: np.ndarray, m: int = 4, sample_rate: int = SAMPLE_RATE,
               symbol_duration: float = SYMBOL_DURATION) -> list[int]:
    samples = np.asarray(signal, dtype=np.float64).ravel()
    n = int(symbol_duration * sample_rate)
    if n <= 0 or len(samples) < n:
        return []

    # AGC: normaliza pelo percentil 99,9 (não o pico bruto — um único pico de ruído
    # isolado infla o pico bruto e distorce a normalização). Diferença de volume
    # entre microfones/alto-falantes distintos deixa de importar a partir daqui.
    peak = float(np.percentile(np.abs(samples), 99.9))
    if peak <= 0:
        return []
    samples = samples / peak

    freqs = symbol_frequencies(m)
    fft_freqs = np.fft.rfftfreq(n, 1 / sample_rate)
    step = n + int(_gap(sample_rate).size)

    probe_samples = min(int(NOISE_PROBE_DURATION * sample_rate), len(samples))
    noise_energy = _estimate_noise_energy(samples, fft_freqs, freqs, n, probe_samples)

    start = _first_active_window(samples, fft_freqs, freqs, n, noise_energy)
    if start is None:
        return []

    bits: list[int] = []
    for pos in range(start, len(samples) - n + 1, step):
        window = _window_energies(samples, fft_freqs, freqs, n, pos)
        symbol, confident = _decide_symbol(window, noise_energy)
        if not confident:
            continue
        bits.extend(symbols_to_bits([symbol], m))
    return bits