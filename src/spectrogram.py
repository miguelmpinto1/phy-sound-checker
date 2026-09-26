# SPDX-License-Identifier: MIT
"""Espectrograma ao vivo no terminal (somente numpy, sem matplotlib).

Cada bloco de áudio vira UMA linha de texto:
    tempo (↓ rola pra baixo) | frequência (→ da esquerda pra direita) | intensidade (▒▓█)

Uso: passe uma instância como 'on_block' de audio_io.record().
"""

import shutil

import numpy as np

SAMPLE_RATE = 44100
FFT_SIZE = SAMPLE_RATE // 10   # amostras por linha (0,1 s) -> 10 linhas por segundo, 10 Hz por bin
FREQ_MAX = 5000          # maior frequência exibida (Hz): cobre os tons 1000-2500 Hz do método 2
DB_FLOOR = -75.0         # abaixo disso vira espaço em branco (silêncio) — suba se houver ruído
DB_CEIL = -20.0          # acima disso vira o caractere mais escuro (som forte)
RAMP = " ░▒▓█"           # do silêncio ao som mais forte


def _axis(cols: int) -> str:
    """Régua de frequências: 0 1k 2k 3k 4k 5k espalhados pela largura."""
    row = [" "] * cols
    for f in range(0, FREQ_MAX + 1, 1000):
        label = f"{f // 1000}k" if f else "0"
        pos = min(int(f / FREQ_MAX * (cols - 1)), cols - len(label))
        row[pos:pos + len(label)] = label
    return "".join(row)


class LiveSpectrogram:
    """Recebe blocos de áudio e imprime uma linha do espectrograma para cada um."""

    def __init__(self, cols: int | None = None) -> None:
        if cols is None:
            cols = shutil.get_terminal_size((80, 24)).columns - 10
        self.cols = max(20, min(cols, 100))
        self._started = False

    def render(self, block: np.ndarray) -> str:
        """Transforma um bloco de áudio em uma linha de caracteres (sem imprimir)."""
        x = np.zeros(FFT_SIZE)
        tail = np.asarray(block, dtype=np.float64).ravel()[-FFT_SIZE:]
        x[:tail.size] = tail                       # bloco curto (fim da gravação): completa com zeros

        window = np.hanning(FFT_SIZE)
        mag = np.abs(np.fft.rfft(x * window)) * 2 / window.sum()   # amplitude de cada frequência
        db = 20 * np.log10(mag + 1e-12)

        n_bins = int(FREQ_MAX / (SAMPLE_RATE / FFT_SIZE))          # só até FREQ_MAX
        edges = np.linspace(0, n_bins, self.cols + 1).astype(int)
        db = np.maximum.reduceat(db[:n_bins], edges[:-1])          # o maior valor de cada coluna

        level = np.clip((db - DB_FLOOR) / (DB_CEIL - DB_FLOOR), 0.0, 1.0)
        idx = np.rint(level * (len(RAMP) - 1)).astype(int)
        return "".join(RAMP[i] for i in idx)

    def __call__(self, block: np.ndarray, elapsed: float) -> None:
        """Imprime uma linha (e o cabeçalho, na primeira chamada)."""
        if not self._started:
            print("[espectrograma] tempo ↓ | frequência (Hz) → | intensidade: ░ fraco ... █ forte")
            print(f"{'':>7} │{_axis(self.cols)}│")
            self._started = True
        print(f"{elapsed:5.1f}s │{self.render(block)}│", flush=True)
