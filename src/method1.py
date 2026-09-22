# SPDX-License-Identifier: MIT
"""Método 1: batidas (0 = 1 batida, 1 = 2 batidas) + paridade par.

O emissor converte cada byte em um quadro de 9 bits (8 de dados + 1 de paridade) e
transforma cada bit em batidas acústicas: 1 batida para o bit 0 e 2 batidas para o bit 1.
O receptor detecta as batidas pelo envelope do sinal e reconstrói os bits.
"""

from dataclasses import dataclass

import numpy as np

import parity

SAMPLE_RATE = 44100
BEAT_DURATION = 0.05    # duração de uma batida sintética (50 ms)
BEAT_GAP = 0.15         # silêncio entre as batidas de um mesmo bit
BIT_GAP = 0.35          # silêncio entre bits consecutivos
THRESHOLD = 0.1         # limiar de amplitude para detectar uma batida
REFRACTORY = 0.08       # tempo mínimo entre picos (evita contar a mesma batida 2x)


@dataclass
class ParityResult:
    """Resultado da validação de um quadro de 9 bits (8 de dados + 1 de paridade)."""
    ok: bool
    byte: int = 0


def _click(duration: float = BEAT_DURATION) -> np.ndarray:
    """Gera um clique curto (ruído com decaimento exponencial)."""
    n = int(duration * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    env = np.exp(-t * 40)
    return (noise * env).astype(np.float32)


def _bits_to_str(bits: list[int]) -> str:
    return "".join(str(b) for b in bits)


def _beats_label(n_beats: int) -> str:
    return "1 batida" if n_beats == 1 else f"{n_beats} batidas"


def transmit(payload: bytes, verbose: bool = False) -> np.ndarray:
    """Codifica os bytes em quadros de 9 bits (paridade par) e gera o áudio das batidas.

    Com verbose=True imprime o painel do método, o detalhe de cada byte/bit e o resumo final.
    """
    if verbose:
        print()
        print("┌─ MÉTODO 1 — BATIDAS E PARIDADE ─────────────────────────")
        print(f"│ mensagem : {payload!r}")
        print(f"│ bytes    : {' '.join(f'0x{b:02X}' for b in payload)} ({len(payload)} byte(s))")
        print("│ regra    : bit 0 -> 1 batida | bit 1 -> 2 batidas")
        print("│ quadro   : 8 bits de dados + 1 bit de paridade par = 9 bits/byte")
        print(f"│ tempos   : batida = {BEAT_DURATION * 1000:.0f} ms | "
              f"intervalo entre batidas = {BEAT_GAP * 1000:.0f} ms | "
              f"intervalo entre bits = {BIT_GAP * 1000:.0f} ms")
        print("└─────────────────────────────────────────────────────────")

    out = [np.zeros(int(0.3 * SAMPLE_RATE), dtype=np.float32)]   # silêncio de guarda inicial
    total_bits = 0
    total_beats = 0

    for idx, byte in enumerate(payload):
        bits = parity.encode_frame(byte)
        data_bits = bits[:8]
        ones = sum(data_bits)
        total_bits += len(bits)

        if verbose:
            print()
            print(f"[byte {idx}] 0x{byte:02X} = {byte} (ASCII {chr(byte)!r})")
            print(f"  dados    : {_bits_to_str(data_bits)}  (0x{byte:02X})")
            print(f"  paridade : {bits[8]}  (nº de 1s nos dados = {ones} -> "
                  f"{'par' if ones % 2 == 0 else 'ímpar'})")

        for j, b in enumerate(bits):
            n_beats = 1 if b == 0 else 2
            total_beats += n_beats

            if verbose:
                rotulo = "dado" if j < 8 else "paridade"
                print(f"    bit {j} ({rotulo:>8}) = {b} -> {_beats_label(n_beats)}")

            for i in range(n_beats):
                out.append(_click())
                if i < n_beats - 1:
                    out.append(np.zeros(int(BEAT_GAP * SAMPLE_RATE), dtype=np.float32))
            out.append(np.zeros(int(BIT_GAP * SAMPLE_RATE), dtype=np.float32))

    out.append(np.zeros(int(0.3 * SAMPLE_RATE), dtype=np.float32))   # silêncio de guarda final
    signal = np.concatenate(out)

    if verbose:
        duracao = len(signal) / SAMPLE_RATE
        print()
        print("[resumo — método 1]")
        print(f"  bytes transmitidos  : {len(payload)}")
        print(f"  bits (com paridade) : {total_bits}")
        print(f"  batidas geradas     : {total_beats}")
        print(f"  duração do áudio    : {duracao:.2f} s")
        print(f"  taxa prática        : {total_bits / duracao:.1f} bps")

    return signal



def _detect_beats(signal: np.ndarray) -> list[float]:
    """Devolve os instantes (em segundos) em que houve batida."""
    env = np.abs(np.asarray(signal, dtype=np.float32))
    above = env > THRESHOLD

    beats = []
    last = -1e9
    for i in range(1, len(above)):
        if above[i] and not above[i - 1]:
            t = i / SAMPLE_RATE
            if t - last > REFRACTORY:
                beats.append(t)
                last = t
    return beats


def receive(signal: np.ndarray, verbose: bool = False) -> list[ParityResult]:
    """Detecta batidas, agrupa em bits e valida a paridade de cada quadro de 9 bits."""
    sinal = np.asarray(signal, dtype=np.float32).ravel()
    beats = _detect_beats(sinal)

    if verbose:
        print()
        print("┌─ RECEPTOR — MÉTODO 1 ───────────────────────────────────")
        print(f"│ amostras          : {sinal.size}")
        print(f"│ duração           : {sinal.size / SAMPLE_RATE:.2f} s")
        print(f"│ limiar (THRESHOLD): {THRESHOLD}")
        print(f"│ batidas detectadas: {len(beats)}")
        print("└─────────────────────────────────────────────────────────")

    if len(beats) < 2:
        if verbose:
            print("[receptor] batidas insuficientes para reconstruir um bit.")
        return []

    # agrupa as batidas em bits: 2 batidas próximas = 1; 1 batida isolada = 0
    bits: list[int] = []
    i = 0
    while i < len(beats):
        if i + 1 < len(beats) and (beats[i + 1] - beats[i]) < BEAT_GAP * 1.5:
            bits.append(1)
            i += 2
        else:
            bits.append(0)
            i += 1

    if verbose:
        print(f"[receptor] sequência de bits reconstruída ({len(bits)} bits):")
        print(f"  {_bits_to_str(bits)}")

    results: list[ParityResult] = []
    for j in range(0, len(bits) - 8, 9):
        chunk = bits[j:j + 9]
        ok = parity.check_frame(chunk)
        value = 0
        for b in chunk[:8]:
            value = (value << 1) | b

        if verbose:
            esperada = sum(chunk[:8]) % 2
            print(f"[receptor] quadro {j // 9}: {_bits_to_str(chunk)} -> "
                  f"dados = 0x{value:02X} ({value}), "
                  f"paridade recebida = {chunk[8]}, esperada = {esperada} -> "
                  f"{'OK' if ok else 'FALHA'}")
        results.append(ParityResult(ok=ok, byte=value))

    if verbose and not results:
        print("[receptor] nenhum quadro completo de 9 bits foi reconstruído.")

    return results
