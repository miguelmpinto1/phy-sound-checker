# SPDX-License-Identifier: MIT
"""Método 2: transmissão M-FSK com quadro [101]+TAM+CRC+[101]."""
import numpy as np

import frame
from mfsk import modulate, demodulate, SAMPLE_RATE, SYMBOL_DURATION, symbol_frequencies

M = 4                       # 4 frequências -> 2 bits/símbolo
SYMBOL_GAP = 0.002
SILENCE_LEAD = 0.3          # silêncio antes/depois para sincronismo


def _bits_to_str(bits: list[int]) -> str:
    return "".join(str(b) for b in bits)


def _split_symbols(bits: list[int]) -> list[int]:
    """Agrupa bits em símbolos (k bits cada) só para exibição."""
    k = M.bit_length() - 1
    padded = bits + [0] * ((-len(bits)) % k)
    out = []
    for i in range(0, len(padded), k):
        v = 0
        for b in padded[i:i + k]:
            v = (v << 1) | b
        out.append(v)
    return out


def transmit(payload: bytes, verbose: bool = False) -> np.ndarray:
    """Codifica o payload em quadro e devolve o sinal M-FSK."""
    bits = frame.encode(payload)
    freqs = symbol_frequencies(M)
    symbols = _split_symbols(bits)

    if verbose:
        # reconstruir as partes do quadro só para exibir
        tam = len(payload)
        crc_bits = bits[11 + 8 * tam:11 + 8 * tam + 8]
        print()
        print("┌─ MÉTODO 2 (M-FSK) ──────────────────────────────────────")
        print(f"│ mensagem   : {payload!r}")
        print(f"│ bytes      : {' '.join(f'0x{b:02X}' for b in payload)}")
        print(f"│ M          : {M} ({M.bit_length()-1} bits por símbolo)")
        print(f"│ frequências: {[f'{f:.0f} Hz' for f in freqs]}")
        print(f"│ símbolo    : {SYMBOL_DURATION*1000:.0f} ms "
              f"(+ {SYMBOL_GAP*1000:.0f} ms de gap)")
        print(f"│ taxa teórica: {estimated_bitrate():.0f} bps")
        print("└─────────────────────────────────────────────────────────")
        print()
        print("[quadro montado]")
        print(f"  delimitador início : {_bits_to_str(bits[:3])}  (3 bits)")
        print(f"  tamanho            : {_bits_to_str(bits[3:11])}  "
              f"(0x{tam:02X} = {tam} byte(s))")
        print(f"  dados              : {_bits_to_str(bits[11:11+8*tam])}  "
              f"({tam*8} bits)")
        print(f"  CRC-8              : {_bits_to_str(crc_bits)}  "
              f"(0x{int(_bits_to_str(crc_bits), 2):02X})")
        print(f"  delimitador fim    : {_bits_to_str(bits[-3:])}  (3 bits)")
        print(f"  total              : {len(bits)} bits")

        print()
        print("[símbolos M-FSK]")
        for i, s in enumerate(symbols):
            k = M.bit_length() - 1
            sbits = "".join(str((s >> j) & 1) for j in range(k - 1, -1, -1))
            print(f"  símbolo {i:>3} = {sbits} -> {freqs[s]:.0f} Hz")

    signal = modulate(bits, m=M)
    silence = np.zeros(int(SILENCE_LEAD * SAMPLE_RATE), dtype=np.float32)
    full = np.concatenate([silence, signal, silence])

    if verbose:
        duracao = len(full) / SAMPLE_RATE
        print()
        print(f"[resumo] {len(bits)} bits -> {len(symbols)} símbolos "
              f"-> {duracao:.2f} s de áudio")
        print(f"[resumo] taxa prática: {len(bits) / duracao:.1f} bps "
              f"(incluindo silêncio)")

    return full


def receive(signal: np.ndarray, verbose: bool = False) -> frame.DecodeResult:
    """Demodula o sinal e tenta decodificar o quadro."""
    bits = demodulate(signal, m=M)
    start = _find_delimiter(bits)

    if verbose:
        print()
        print("┌─ RECEPTOR — MÉTODO 2 ───────────────────────────────────")
        print(f"│ amostras     : {len(signal)}")
        print(f"│ duração      : {len(signal)/SAMPLE_RATE:.2f} s")
        print(f"│ bits demodulados: {len(bits)}")
        print(f"│ primeiros bits  : {_bits_to_str(bits[:32])}"
              + ("..." if len(bits) > 32 else ""))
        if start is None:
            print("│ delimitador  : NÃO encontrado")
        else:
            print(f"│ delimitador  : encontrado no índice {start}")
        print("└─────────────────────────────────────────────────────────")

    if start is None:
        return frame.DecodeResult(False, reason="delimitador não encontrado")

    result = frame.decode(bits[start:])

    if verbose:
        if result.ok:
            print(f"[receptor] SUCESSO: {result.payload!r}")
        else:
            print(f"[receptor] FALHA: {result.reason}")

    return result


def _find_delimiter(bits: list[int]) -> int | None:
    for i in range(len(bits) - 2):
        if bits[i:i + 3] == [1, 0, 1]:
            return i
    return None


def estimated_bitrate() -> float:
    """Taxa teórica em bps."""
    k = M.bit_length() - 1
    symbol_time = SYMBOL_DURATION + SYMBOL_GAP
    return k / symbol_time