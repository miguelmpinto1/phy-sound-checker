# SPDX-License-Identifier: MIT
"""Conversões entre bytes e bits (MSB first)."""


def byte_to_bits(value: int) -> list[int]:
    return [(value >> i) & 1 for i in range(7, -1, -1)]


def bits_to_byte(bits: list[int]) -> int:
    value = 0
    for b in bits:
        value = (value << 1) | b
    return value


def bytes_to_bits(data: bytes) -> list[int]:
    return [bit for byte in data for bit in byte_to_bits(byte)]


def bits_to_bytes(bits: list[int]) -> bytes:
    if len(bits) % 8 != 0:
        raise ValueError("quantidade de bits deve ser múltiplo de 8")
    return bytes(bits_to_byte(bits[i:i + 8]) for i in range(0, len(bits), 8))
