# SPDX-License-Identifier: MIT
from calcular_crc8 import crc8

def gerar_quadro_metodo2(payload: bytes, tamanho_bits: int) -> dict:
    """
    Monta o quadro: [Início (101)] + [Tamanho] + [Payload] + [CRC-8] + [Fim (101)]
    """
    # O CRC protege obrigatoriamente o Tamanho + Payload combinados
    dados_para_crc = bytes([tamanho_bits]) + payload
    codigo_crc = crc8(dados_para_crc)
    
    quadro = {
        "inicio": "101",
        "tamanho": tamanho_bits,
        "payload": payload,
        "crc": codigo_crc,
        "fim": "101"
    }
    return quadro