# SPDX-License-Identifier: MIT
"""Módulo responsável por validar a integridade dos quadros recebidos no Método 2."""

from calculate_crc8 import crc8

def verify_frame_method2(frame: dict) -> bool:
    """Valida se o quadro recebido está íntegro ou corrompido por ruído.

    Recalcula o CRC-8 sobre os campos de tamanho e dados, comparando com o CRC
    anexado.

    Args:
        frame (dict): O dicionário estruturado representando o quadro recebido.

    Returns:
        bool: True se os dados estiverem íntegros (SUCESSO), ou False se houver
        corrupção (FALHA)[cite: 1].

    """
    size = frame["size"]
    payload = frame["payload"]
    received_crc = frame["crc"]

    # Recalcula o CRC usando exatamente os mesmos campos protegidos no envio[cite: 1]
    data_for_crc = bytes([size]) + payload
    calculated_crc = crc8(data_for_crc)

    # Compara o resultado calculado com o CRC recebido para checar sucesso ou falha[cite: 1]
    return calculated_crc == received_crc