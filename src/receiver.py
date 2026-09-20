# SPDX-License-Identifier: MIT
"""Módulo de recepção e demodulação com Espectrômetro em Tempo Real."""

import time
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import audio_config as cfg

# Buffer global para a animação do gráfico
current_fft_vals = None
current_freqs = None


def process_audio_block(block: np.ndarray) -> list[int]:
    """Aplica FFT no bloco, atualiza dados do espectrômetro e extrai os bits."""
    global current_fft_vals, current_freqs

    windowed = block * np.hanning(len(block))
    fft_vals = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(block), 1 / cfg.FS)

    # Armazena para renderização no gráfico
    current_fft_vals = fft_vals
    current_freqs = freqs

    detected_bits = []
    threshold = getattr(cfg, "MAGNITUDE_THRESHOLD", 1.0)

    for i in range(cfg.NUM_TONES):
        target_freq = cfg.FREQ_START + (i * cfg.FREQ_STEP)
        idx = np.where((freqs >= target_freq - 50) & (freqs <= target_freq + 50))[0]

        if len(idx) > 0 and np.max(fft_vals[idx]) >= threshold:
            detected_bits.append(1)
        else:
            detected_bits.append(0)

    return detected_bits


def listen_continuous_stream(callback_on_bits) -> None:
    """Abre o microfone padrão e exibe o Espectrômetro visual em tempo real."""
    block_samples = int(cfg.FS * cfg.SYMBOL_DURATION)

    def audio_callback(indata, frames, time_info, status):
        block = indata[:, 0]
        bits = process_audio_block(block)
        if any(b == 1 for b in bits):
            callback_on_bits(bits)

    # Configuração da janela do Espectrômetro
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.canvas.manager.set_window_title("Espectrômetro de Áudio em Tempo Real - M-FSK")

    # Faixa de frequências relevante (com margem de exibição)
    freq_min = max(0, cfg.FREQ_START - 500)
    freq_max = cfg.FREQ_START + (cfg.NUM_TONES * cfg.FREQ_STEP) + 500

    line, = ax.plot([], [], color="#00FF66", lw=1.5, label="Energia da Frequência")
    
    # Linha amarela do Threshold de ruído
    threshold = getattr(cfg, "MAGNITUDE_THRESHOLD", 1.0)
    ax.axhline(y=threshold, color="yellow", linestyle="--", alpha=0.7, label=f"Threshold ({threshold})")

    # Linhas verticais azuis indicando onde estão as subportadoras (tons M-FSK)
    for i in range(cfg.NUM_TONES):
        f = cfg.FREQ_START + (i * cfg.FREQ_STEP)
        ax.axvline(x=f, color="#00CCFF", linestyle=":", alpha=0.5)

    ax.set_xlim(freq_min, freq_max)
    ax.set_ylim(0, max(10, threshold * 3))
    ax.set_title("Espectro de Frequências (FFT)", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Frequência (Hz)")
    ax.set_ylabel("Magnitude (Energia)")
    ax.grid(True, linestyle=":", alpha=0.3)
    ax.legend(loc="upper right")

    def update_graph(frame):
        if current_fft_vals is not None and current_freqs is not None:
            # Filtra dados na faixa visível
            mask = (current_freqs >= freq_min) & (current_freqs <= freq_max)
            x_data = current_freqs[mask]
            y_data = current_fft_vals[mask]

            line.set_data(x_data, y_data)
            
            # Ajusta dinâmica do eixo Y
            if len(y_data) > 0:
                max_y = max(np.max(y_data) * 1.2, threshold * 2)
                ax.set_ylim(0, max_y)

        return line,

    # Abre a gravação do microfone padrão
    with sd.InputStream(
        samplerate=cfg.FS,
        channels=1,
        blocksize=block_samples,
        callback=audio_callback,
    ):
        print("\n[🎙] Espectrômetro ativo! Feche a janela do gráfico ou aperte Ctrl+C para encerrar.")
        
        # Animação a 30 FPS
        ani = FuncAnimation(fig, update_graph, interval=33, blit=False, cache_frame_data=False)
        plt.tight_layout()
        plt.show()