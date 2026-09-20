# SPDX-License-Identifier: MIT
"""Módulo unificado do Método 2: Estrutura, Geração, Verificação e Decodificação de Quadros.

Modelo do Quadro: [101] + TAMANHO (8 bits) + DADO (máx. 8 bits) + CRC-8 (8 bits) + [101].
O CRC-8 cobre obrigatoriamente TAMANHO + DADO.
"""

from dataclasses import dataclass
from bits import bits_to_byte, bits_to_bytes, bytes_to_bits, byte_to_bits
from crc8 import crc8

DELIMITER = [1, 0, 1]
MAX_PAYLOAD_BITS = 8  # Restrito a no máximo 8 bits por pacote (1 caractere)
OVERHEAD_BITS = 3 + 8 + 8 + 3  # início (3) + tamanho (8) + crc (8) + fim (3) = 22 bits de controle


@dataclass
class DecodeResult:
    """Estrutura de resultado para o processo de decodificação no receptor."""
    ok: bool
    payload: bytes = b""
    reason: str = ""


def generate_frame_method2(payload: bytes, data_size: int) -> dict:
    """Gera e estrutura o quadro de comunicação para o Método 2 da camada física.
    O quadro contém preâmbulo [101], tamanho, dados úteis, CRC-8 e delimitador final [101].
    """
    # O cálculo do CRC protege obrigatoriamente a junção do Tamanho com os Dados[cite: 1]
    data_for_crc = bytes([data_size]) + payload
    crc_code = crc8(data_for_crc)

    frame = {
        "start": "101",          # Preâmbulo para sincronismo acústico
        "size": data_size,       # Tamanho dos dados em bits (ex: 8 bits)
        "payload": payload,      # Dados úteis (mensagem / 1 caractere)
        "crc": crc_code,         # Byte de verificação de erros (CRC-8)
        "end": "101",            # Delimitador de fim do pacote
    }
    return frame


def verify_frame_method2(frame: dict) -> bool:
    """Valida se o quadro recebido está íntegro ou corrompido por ruído.

    Recalcula o CRC-8 sobre os campos de tamanho e dados, comparando com o CRC anexado[cite: 1].
    """
    size = frame["size"]
    payload = frame["payload"]
    received_crc = frame["crc"]

    # Recalcula o CRC usando os mesmos campos protegidos no envio[cite: 1]
    data_for_crc = bytes([size]) + payload
    calculated_crc = crc8(data_for_crc)

    # Compara o resultado calculado com o CRC recebido (Sucesso se True)[cite: 1]
    return calculated_crc == received_crc


def decode(bits: list[int]) -> DecodeResult:
    """Decodifica a lista de bits recebida, validando delimitadores, tamanho (até 8 bits) e CRC-8."""
    if len(bits) < 3 + 8:
        return DecodeResult(False, reason="quadro curto demais")
    
    if bits[:3] != DELIMITER:
        return DecodeResult(False, reason="delimitador de início inválido")

    # Lê o campo TAMANHO (ocupa os bits 3..10, total de 8 bits)
    size = bits_to_byte(bits[3:11])
    
    # Restringe estritamente para pacotes de até 8 bits de dados
    if size == 0 or size > MAX_PAYLOAD_BITS:
        return DecodeResult(False, reason="tamanho de dados inválido ou superior a 8 bits")

    # Calcula o tamanho total esperado do quadro baseado nos bits de payload
    total = OVERHEAD_BITS + size
    if len(bits) < total:
        return DecodeResult(False, reason="quadro incompleto")

    data_end = 11 + size
    payload_bits_list = bits[11:data_end]
    
    # Converte os bits de dados obtidos para bytes
    payload = bits_to_bytes(payload_bits_list)
    
    # Extrai o byte de CRC-8 logo após o payload
    crc_rx = bits_to_byte(bits[data_end:data_end + 8])
    
    # Valida o CRC-8 cobrindo TAMANHO + DADO
    if crc8(bytes([size]) + payload) != crc_rx:
        return DecodeResult(False, reason="CRC não confere")
        
    # Valida o delimitador de fim do pacote [1, 0, 1]
    if bits[data_end + 8 : data_end + 11] != DELIMITER:
        return DecodeResult(False, reason="delimitador de fim inválido")

    return DecodeResult(True, payload)