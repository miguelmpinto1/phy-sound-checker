# SPDX-License-Identifier: MIT
"""Quadro de 9 bits com paridade par (Método 1)."""
from src import byte_to_bits


def encode_frame(value: int) -> list[int]:
    data = byte_to_bits(value)
    return data + [sum(data) % 2]  # nº de 1s par -> 0, ímpar -> 1


def check_frame(bits: list[int]) -> bool:
    return len(bits) == 9 and sum(bits[:8]) % 2 == bits[8]
