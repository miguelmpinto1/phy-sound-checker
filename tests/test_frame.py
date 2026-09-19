# SPDX-License-Identifier: MIT
import pytest

import frame
from crc8 import crc8


def test_frame_letter_a_layout():
    bits = frame.encode(b"A")
    assert len(bits) == 30
    assert bits[:3] == [1, 0, 1] and bits[-3:] == [1, 0, 1]
    assert bits[3:11] == [0, 0, 0, 0, 0, 0, 0, 1]    # tamanho = 1 byte
    assert bits[11:19] == [0, 1, 0, 0, 0, 0, 0, 1]   # 'A'


def test_roundtrip():
    for msg in (b"A", b"Ola", bytes(range(1, 256))):
        result = frame.decode(frame.encode(msg))
        assert result.ok and result.payload == msg


def test_single_bit_flip_is_detected_everywhere():
    bits = frame.encode(b"Ola")
    for i in range(len(bits)):
        corrupted = bits.copy()
        corrupted[i] ^= 1
        assert not frame.decode(corrupted).ok, f"bit {i} passou"


def test_zero_size_rejected():
    assert not frame.decode([1, 0, 1] + [0] * 27).ok


def test_truncated_frame_rejected():
    assert not frame.decode(frame.encode(b"Ola")[:-5]).ok


def test_payload_limits():
    with pytest.raises(ValueError):
        frame.encode(b"")
    with pytest.raises(ValueError):
        frame.encode(bytes(256))


def test_crc_value_for_letter_a():
    assert crc8(bytes([0x01, 0x41])) == 0xD5
