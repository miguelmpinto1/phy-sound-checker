# SPDX-License-Identifier: MIT
from crc8 import crc8
from parity import check_frame, encode_frame


def test_parity_examples_from_assignment():
    assert encode_frame(0b11000000)[8] == 0   # 2 uns -> par
    assert encode_frame(0b11100000)[8] == 1   # 3 uns -> ímpar


def test_parity_letter_a():
    assert encode_frame(ord("A")) == [0, 1, 0, 0, 0, 0, 0, 1, 0]


def test_parity_detects_single_bit_flip():
    frame = encode_frame(ord("A"))
    assert check_frame(frame)
    frame[3] ^= 1
    assert not check_frame(frame)


def test_crc8_matches_hand_calculation():
    # tamanho=0x08, 'A'=0x41 -> 01101000
    assert crc8(bytes([0x08, 0x41])) == 0x68


def test_crc8_appended_gives_zero():
    msg = bytes([0x08, 0x41])
    assert crc8(msg + bytes([crc8(msg)])) == 0
