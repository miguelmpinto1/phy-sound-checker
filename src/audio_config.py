# SPDX-License-Identifier: MIT
"""Configurações da Camada Física de Áudio (Método 2)."""

FS = 44100              # Taxa de amostragem padrão (Hz)
SYMBOL_DURATION = 0.04  # 40 ms por símbolo (25 símbolos/s)
NUM_TONES = 16          # 16 subportadoras em paralelo (2 bytes por símbolo)

# Perfil Padrão: Quase-Ultrassônico (Silencioso)
FREQ_START = 18000
FREQ_STEP = 125
BANDPASS_LOW = 17500
BANDPASS_HIGH = 20500
MAGNITUDE_THRESHOLD = 0.03


def set_mode(mode: str) -> None:
    """Alterna os parâmetros físicos do áudio conforme o modo escolhido."""
    global FREQ_START, FREQ_STEP, BANDPASS_LOW, BANDPASS_HIGH, MAGNITUDE_THRESHOLD

    if mode == "audible":
        FREQ_START = 2000          # Início da faixa em 2 kHz (apitos/chimes)
        FREQ_STEP = 200            # Espaçamento de 200 Hz entre tons
        BANDPASS_LOW = 1800        # Corte inferior do filtro
        BANDPASS_HIGH = 5200       # Corte superior do filtro
        MAGNITUDE_THRESHOLD = 0.05 # Limiar de sensibilidade para a faixa audível
    elif mode == "ultrasonic":
        FREQ_START = 18000         # Início da faixa em 18 kHz (silencioso)
        FREQ_STEP = 125            # Espaçamento de 125 Hz entre tons
        BANDPASS_LOW = 17500       # Corte inferior do filtro
        BANDPASS_HIGH = 20500      # Corte superior do filtro
        MAGNITUDE_THRESHOLD = 0.03 # Limiar para o quase-ultrassom
    else:
        raise ValueError("Modo inválido. Escolha 'audible' ou 'ultrasonic'.")