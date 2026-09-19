# SPDX-License-Identifier: MIT
"""Quadro do Método 2: [101] + TAMANHO + DADO + CRC-8 + [101].

TAMANHO é o nº de bytes do DADO (1..255). O CRC-8 cobre TAMANHO + DADO.
Trabalha só com listas de bits (MSB first): nada de áudio aqui.
"""
from dataclasses import dataclass

from bits import bits_to_byte, bits_to_bytes, bytes_to_bits, byte_to_bits
from crc8 import crc8

DELIMITER = [1, 0, 1]
MAX_PAYLOAD = 255
OVERHEAD_BITS = 3 + 8 + 8 + 3  # início + tamanho + crc + fim = 22


@dataclass
class DecodeResult:
    ok: bool
    payload: bytes = b""
    reason: str = ""


def encode(payload: bytes) -> list[int]:
    if not 1 <= len(payload) <= MAX_PAYLOAD:
        raise ValueError(f"payload deve ter entre 1 e {MAX_PAYLOAD} bytes")
    body = bytes([len(payload)]) + payload
    return DELIMITER + bytes_to_bits(body) + byte_to_bits(crc8(body)) + DELIMITER


def decode(bits: list[int]) -> DecodeResult:
    if len(bits) < 3 + 8:
        return DecodeResult(False, reason="quadro curto demais")
    if bits[:3] != DELIMITER:
        return DecodeResult(False, reason="delimitador de início inválido")

    size = bits_to_byte(bits[3:11])  # campo TAMANHO ocupa os bits 3..10
    if size == 0:
        return DecodeResult(False, reason="tamanho zero")

    total = OVERHEAD_BITS + 8 * size
    if len(bits) < total:
        return DecodeResult(False, reason="quadro incompleto")

    data_end = 11 + 8 * size
    payload = bits_to_bytes(bits[11:data_end])
    crc_rx = bits_to_byte(bits[data_end:data_end + 8])
    if crc8(bytes([size]) + payload) != crc_rx:
        return DecodeResult(False, reason="CRC não confere")
    if bits[data_end + 8:total] != DELIMITER:
        return DecodeResult(False, reason="delimitador de fim inválido")

    return DecodeResult(True, payload)
