# SPDX-License-Identifier: MIT
"""Módulo para traduzir texto do terminal em bits e montar o quadro do Método 2."""

# Importa a função do gerador de quadros e o modulador FSK
from frame_generator import generate_frame_method2
from fsk_modulator import transmit_frame_fsk
from bits import text_to_bits

if __name__ == "__main__":
    print("=== Tradutor de Texto para Quadro - Método 2 ===")
    user_input = input("Digite o texto que deseja transmitir (ex: A): ")

    if not user_input:
        user_input = "A"
        print(f"Nenhum texto inserido. Usando o padrão: '{user_input}'")

    # Prepara os dados de entrada
    payload_bytes = user_input.encode("ascii")
    data_size_bits = len(payload_bytes) * 8  # Tamanho total em bits (ex: 8 bits)

    # CHAMADA DA FUNÇÃO: Gera o dicionário estruturado do quadro utilizando o módulo existente
    frame_dict = generate_frame_method2(payload_bytes, data_size_bits)

    # Converte os campos numéricos de volta para string binária para exibição e modulação
    size_bits_str = format(frame_dict["size"], "08b")
    payload_bits_str = text_to_bits(user_input)
    crc_bits_str = format(frame_dict["crc"], "08b")

    # Monta a sequência contínua de bits do quadro final (30 bits para a letra 'A')
    binary_stream = (
        frame_dict["start"]
        + size_bits_str
        + payload_bits_str
        + crc_bits_str
        + frame_dict["end"]
    )

    print("\n--- Resultado da Tradução ---")
    print(f"Texto Original: {user_input}")
    print(f"Início (Preâmbulo): {frame_dict['start']}")
    print(f"Tamanho (8 bits):   {size_bits_str}")
    print(f"Payload (Dados):    {payload_bits_str}")
    print(f"Erro (CRC-8):       {crc_bits_str}")
    print(f"Fim (Delimitador):  {frame_dict['end']}")
    print(f"\nFluxo Binário Final do Quadro: \n{binary_stream}")

    # exemplo de implementação para escutar modulação
    transmit_frame_fsk(binary_stream)