# SPDX-License-Identifier: MIT
"""Conversões entre bytes e bits (MSB first)."""


def byte_to_bits(value: int) -> list[int]:
    return [(value >> i) & 1 for i in range(7, -1, -1)]


def bits_to_byte(bits: list[int]) -> int:
    value = 0
    for b in bits:
        value = (value << 1) | b
    return value
