# SPDX-License-Identifier: MIT
"""Módulo TESTE de Modulação FSK para transmissão acústica."""

import numpy as np
import sounddevice as sd

# Configurações de Frequência e Áudio para FSK
SAMPLE_RATE = 44100       # Taxa de amostragem padrão (44.1 kHz)
FREQ_ZERO = 1200          # Frequência em Hz para representar o bit '0'
FREQ_ONE = 2400           # Frequência em Hz para representar o bit '1'
BIT_DURATION = 0.05       # Duração de cada bit em segundos (velocidade de transmissão)

#atualmente conseguimos 1 / 0.05 = oque dá 20 bps, podemos futuramente testar tempos menores, e qualquer coisa aumentar a frequencia.

def bits_to_fsk_audio(bit_stream: str, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Converte uma string de bits (ex: '101000...') em um sinal de áudio FSK.
    
    Args:
        bit_stream (str): A sequência de bits contendo o quadro completo.
        sample_rate (int): Taxa de amostragem do áudio.
        
    Returns:
        np.ndarray: Array contendo a onda sonora pronta para reprodução.
    """
    audio_signal = []
    num_samples_per_bit = int(sample_rate * BIT_DURATION)
    
    for bit in bit_stream:
        # Define a frequência com base no valor do bit
        frequency = FREQ_ONE if bit == '1' else FREQ_ZERO
        
        # Gera o eixo do tempo para a duração deste bit específico
        t = np.linspace(0, BIT_DURATION, num_samples_per_bit, endpoint=False)
        
        # Cria a onda senoidal pura para o bit atual
        sine_wave = np.sin(2 * np.pi * frequency * t)
        
        # Adiciona ao sinal geral de áudio
        audio_signal.extend(sine_wave)
        
    return np.array(audio_signal, dtype=np.float32)


def transmit_frame_fsk(bit_stream: str):
    """Reproduz o quadro binário em formato de som FSK através do alto-falante."""
    print(f"Modulando e transmitindo quadro FSK ({len(bit_stream)} bits)...")
    
    # Gera o sinal sonoro baseado nos bits
    audio_data = bits_to_fsk_audio(bit_stream)
    
    # Executa a transmissão sonora no alto-falante
    sd.play(audio_data, samplerate=SAMPLE_RATE)
    sd.wait() # Aguarda terminar a reprodução completa do áudio
    print("Transmissão FSK concluída com sucesso!")
