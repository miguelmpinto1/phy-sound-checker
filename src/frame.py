# SPDX-License-Identifier: MIT
"""Módulo unificado do Método 2: Estrutura, Geração, Verificação e Decodificação de Quadros.

Modelo do Quadro: [101] + TAMANHO (8 bits = nº de bytes do dado) + DADO + CRC-8 (8 bits) + [101].
O CRC-8 cobre obrigatoriamente TAMANHO + DADO.

Duas frentes convivem aqui:
  * encode()/decode(): quadro autocontido em listas de bits (usado pelo método 2 e pela CLI);
  * generate_frame_method2()/verify_frame_method2(): visão em dicionário, útil para inspeção.
"""

from dataclasses import dataclass

from bits import bits_to_byte, bits_to_bytes, bytes_to_bits, byte_to_bits
from crc8 import crc8

DELIMITER = [1, 0, 1]
MAX_PAYLOAD = 255                # payload máximo: 255 bytes (o campo TAMANHO tem 8 bits)
MAX_PAYLOAD_BITS = MAX_PAYLOAD * 8
OVERHEAD_BITS = 3 + 8 + 8 + 3    # início (3) + tamanho (8) + crc (8) + fim (3) = 22 bits de controle


@dataclass
class DecodeResult:
    """Estrutura de resultado para o processo de decodificação no receptor."""
    ok: bool
    payload: bytes = b""
    reason: str = ""


def encode(payload: bytes) -> list[int]:
    """Monta o quadro completo em bits: [101] + TAMANHO + DADO + CRC-8 + [101].

    O campo TAMANHO guarda o nº de BYTES do payload (1..255) e o CRC-8 cobre TAMANHO + DADO.
    """
    if not 1 <= len(payload) <= MAX_PAYLOAD:
        raise ValueError(f"payload deve ter entre 1 e {MAX_PAYLOAD} bytes")

    body = bytes([len(payload)]) + payload
    return DELIMITER + bytes_to_bits(body) + byte_to_bits(crc8(body)) + DELIMITER


def generate_frame_method2(payload: bytes, data_size: int) -> dict:
    """Gera e estrutura o quadro de comunicação para o Método 2 da camada física.
    O quadro contém preâmbulo [101], tamanho, dados úteis, CRC-8 e delimitador final [101].

    'data_size' é o valor bruto gravado no campo TAMANHO e participa do CRC-8 junto do payload.
    """
    data_for_crc = bytes([data_size & 0xFF]) + payload
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

    Recalcula o CRC-8 sobre os campos de tamanho e dados, comparando com o CRC anexado.
    """
    size = frame["size"]
    payload = frame["payload"]
    received_crc = frame["crc"]

    data_for_crc = bytes([size]) + payload
    calculated_crc = crc8(data_for_crc)

    return calculated_crc == received_crc


def decode(bits: list[int]) -> DecodeResult:
    """Decodifica a lista de bits recebida, validando delimitadores, tamanho e CRC-8.

    O campo TAMANHO é interpretado em BYTES (1..255); o quadro termina com o delimitador [101].
    """
    if len(bits) < 3 + 8:
        return DecodeResult(False, reason="quadro curto demais")

    if bits[:3] != DELIMITER:
        return DecodeResult(False, reason="delimitador de início inválido")

    # Lê o campo TAMANHO (ocupa os bits 3..10, total de 8 bits)
    size = bits_to_byte(bits[3:11])

    if size == 0:
        return DecodeResult(False, reason="tamanho zero")

    # Calcula o tamanho total esperado do quadro: 22 bits de controle + 8 bits por byte de dado
    total = OVERHEAD_BITS + 8 * size
    if len(bits) < total:
        return DecodeResult(False, reason="quadro incompleto")

    data_end = 11 + 8 * size
    payload = bits_to_bytes(bits[11:data_end])

    # Extrai o byte de CRC-8 logo após o payload
    crc_rx = bits_to_byte(bits[data_end:data_end + 8])

    # Valida o CRC-8 cobrindo TAMANHO + DADO
    if crc8(bytes([size]) + payload) != crc_rx:
        return DecodeResult(False, reason="CRC não confere")

    # Valida o delimitador de fim do pacote [1, 0, 1]
    if bits[data_end + 8:total] != DELIMITER:
        return DecodeResult(False, reason="delimitador de fim inválido")

    return DecodeResult(True, payload)