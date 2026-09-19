# SPDX-License-Identifier: MIT
"""Módulo responsável por estruturar e gerar o quadro de transmissão do Método 2."""

from crc8 import crc8

def generate_frame_method2(payload: bytes, data_size: int) -> dict:
    """Gera e estrutura o quadro de comunicação para o Método 2 da camada física.

    O quadro contém preâmbulo[101], tamanho, dados úteis, CRC-8 e delimitador final[101].

    Args:
        payload (bytes): Os dados binários reais que serão transmitidos.
        data_size (int): O tamanho dos dados em bits.

    Returns:
        dict: Um dicionário contendo todos os campos formatados do quadro.

    """
    # O cálculo do CRC protege obrigatoriamente a junção do Tamanho com os Dados[cite: 1]
    data_for_crc = bytes([data_size]) + payload
    crc_code = crc8(data_for_crc)

    frame = {
        "start": "101",  # Preâmbulo (senha sonora para sincronismo)[101]
        "size": data_size,  # Tamanho dos dados em bits[8 bits]
        "payload": payload,  # Dados úteis (mensagem)[8 bits]
        "crc": crc_code,  # Byte de verificação de erros (CRC-8)[8 bits]
        "end": "101",  # Delimitador de fim do pacote[101]
    }
    return frame