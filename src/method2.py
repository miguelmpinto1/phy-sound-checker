# SPDX-License-Identifier: MIT
"""Método 2: transmissão M-FSK com quadro [101] + TAMANHO + DADO + CRC-8 + [101].

Cada símbolo M-FSK carrega k = log2(M) bits em uma frequência distinta, o que dá
uma taxa bem maior que a do método 1, ao custo de exigir sincronismo mais fino.
"""

import numpy as np

import frame
import mfsk
from mfsk import SAMPLE_RATE, SYMBOL_DURATION

M = 4                       # 4 frequências -> 2 bits por símbolo
SYMBOL_GAP = mfsk.SYMBOL_GAP
SILENCE_LEAD = 0.3          # silêncio antes/depois do quadro (sincronismo)


def _bits_to_str(bits: list[int]) -> str:
    return "".join(str(b) for b in bits)


def bits_per_symbol() -> int:
    """Quantos bits cada símbolo carrega (k = log2(M))."""
    return mfsk.bits_per_symbol(M)


def theoretical_rate(m: int = M, symbol_duration: float = SYMBOL_DURATION,
                     symbol_gap: float = SYMBOL_GAP) -> float:
    """Taxa teórica da modulação em bps: k bits por (símbolo + gap)."""
    return mfsk.bits_per_symbol(m) / (symbol_duration + symbol_gap)


def estimated_bitrate() -> float:
    """Apelido didático de theoretical_rate() para a configuração padrão."""
    return theoretical_rate()


def find_delimiter(bits: list[int], start: int = 0) -> int | None:
    """Índice do primeiro delimitador [101] encontrado a partir de 'start'."""
    for i in range(max(0, start), len(bits) - 2):
        if bits[i:i + 3] == frame.DELIMITER:
            return i
    return None


def _signal_from_bits(bits: list[int]) -> np.ndarray:
    """Modula os bits em M-FSK e acrescenta os silêncios de guarda nas pontas."""
    signal = mfsk.modulate(bits, m=M)
    silence = np.zeros(int(SILENCE_LEAD * SAMPLE_RATE), dtype=np.float32)
    return np.concatenate([silence, signal, silence])


def encode_signal(payload: bytes) -> np.ndarray:
    """Gera o sinal M-FSK completo (com silêncios de guarda) para o payload informado."""
    return _signal_from_bits(frame.encode(payload))


def transmit(payload: bytes, verbose: bool = False) -> np.ndarray:
    """Codifica o payload em quadro, modula em M-FSK e devolve o sinal de áudio.

    Com verbose=True imprime o painel do método, a estrutura do quadro, o mapa de
    símbolos M-FSK e o resumo (bits, símbolos, duração e taxa prática).
    """
    bits = frame.encode(payload)
    symbols = mfsk.bits_to_symbols(bits, M)
    freqs = mfsk.symbol_frequencies(M)
    k = bits_per_symbol()

    if verbose:
        print()
        print("┌─ MÉTODO 2 — M-FSK COM ENQUADRAMENTO ────────────────────")
        print(f"│ mensagem    : {payload!r}")
        print(f"│ bytes       : {' '.join(f'0x{b:02X}' for b in payload)} ({len(payload)} byte(s))")
        print(f"│ ordem M     : {M} ({k} bits por símbolo)")
        print(f"│ frequências : {', '.join(f'{f:.0f} Hz' for f in freqs)}")
        print(f"│ símbolo     : {SYMBOL_DURATION * 1000:.0f} ms "
              f"(+ {SYMBOL_GAP * 1000:.0f} ms de gap)")
        print(f"│ taxa teórica: {theoretical_rate():.1f} bps")
        print("└─────────────────────────────────────────────────────────")

        print()
        print("[quadro gerado por frame.encode()]")
        data_bits = bits[11:11 + 8 * len(payload)]
        crc_bits = bits[11 + 8 * len(payload):19 + 8 * len(payload)]
        print(f"  delimitador inicial (101) : {_bits_to_str(bits[:3])}")
        print(f"  tamanho (8 bits)          : {_bits_to_str(bits[3:11])} "
              f"(0x{len(payload):02X} = {len(payload)} byte(s))")
        print(f"  dados ({len(data_bits)} bits)           : {_bits_to_str(data_bits)} "
              f"({payload!r})")
        print(f"  CRC-8 (8 bits)            : {_bits_to_str(crc_bits)} "
              f"(0x{int(_bits_to_str(crc_bits), 2):02X})")
        print(f"  delimitador final (101)   : {_bits_to_str(bits[-3:])}")
        print(f"  total                     : {len(bits)} bits")

        print()
        print(f"[símbolos M-FSK] {len(symbols)} símbolo(s) gerado(s)")
        for i, s in enumerate(symbols):
            symbol_bits = "".join(str((s >> j) & 1) for j in range(k - 1, -1, -1))
            print(f"  símbolo {i:>3} = {symbol_bits} -> {freqs[s]:.0f} Hz")

    signal = _signal_from_bits(bits)

    if verbose:
        duracao = len(signal) / SAMPLE_RATE
        print()
        print("[resumo — método 2]")
        print(f"  bits no quadro : {len(bits)}")
        print(f"  símbolos       : {len(symbols)}")
        print(f"  duração        : {duracao:.2f} s "
              f"(inclui {SILENCE_LEAD * 1000:.0f} ms de guarda em cada ponta)")
        print(f"  taxa prática   : {len(bits) / duracao:.1f} bps")

    return signal


def decode_bits(bits: list[int], verbose: bool = False) -> frame.DecodeResult:
    """Sincroniza no delimitador [101] e decodifica o quadro a partir dele.

    Bits de ruído antes do delimitador (e candidatos inválidos) são ignorados até que um
    quadro passe na validação de tamanho, delimitadores e CRC-8.
    """
    flow = list(bits)
    first = find_delimiter(flow)

    if first is None:
        if verbose:
            print("[decodificador] delimitador [101] não encontrado na sequência de bits.")
        return frame.DecodeResult(False, reason="delimitador [101] não encontrado")

    reason = "quadro inválido"
    candidate = first
    while candidate is not None:
        result = frame.decode(flow[candidate:])
        if result.ok:
            if verbose:
                print(f"[decodificador] delimitador [101] no índice {candidate}: "
                      f"CRC-8 conferido, payload = {result.payload!r}")
            return result
        if candidate == first:
            reason = result.reason
        candidate = find_delimiter(flow, candidate + 1)

    if verbose:
        print(f"[decodificador] delimitador [101] no índice {first}, "
              f"mas o quadro é inválido ({reason}).")
    return frame.DecodeResult(False, reason=reason)


def receive(signal: np.ndarray, verbose: bool = False) -> frame.DecodeResult:
    """Demodula o sinal M-FSK, sincroniza no delimitador e devolve o quadro decodificado."""
    sinal = np.asarray(signal, dtype=np.float64).ravel()
    bits = mfsk.demodulate(sinal, m=M)
    index = find_delimiter(bits)

    if verbose:
        preview = _bits_to_str(bits[:32]) + ("..." if len(bits) > 32 else "")
        print()
        print("┌─ RECEPTOR — MÉTODO 2 ───────────────────────────────────")
        print(f"│ amostras         : {sinal.size}")
        print(f"│ duração          : {sinal.size / SAMPLE_RATE:.2f} s")
        print(f"│ bits demodulados : {len(bits)}")
        print(f"│ primeiros bits   : {preview}")
        if index is None:
            print("│ delimitador [101]: NÃO encontrado")
        else:
            print(f"│ delimitador [101]: encontrado no índice {index}")
        print("└─────────────────────────────────────────────────────────")

    result = decode_bits(bits, verbose=verbose)

    if verbose:
        if result.ok:
            print(f"[receptor] SUCESSO: payload = {result.payload!r}")
        else:
            print(f"[receptor] FALHA: {result.reason}")

    return result

