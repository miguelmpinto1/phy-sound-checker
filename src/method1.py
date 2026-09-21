# SPDX-License-Identifier: MIT
"""Método 1: batidas (0 = 1 batida, 1 = 2 batidas) + paridade par."""
from dataclasses import dataclass

import numpy as np

import parity

SAMPLE_RATE = 44100
BEAT_DURATION = 0.05        # duração de uma batida sintética
BEAT_GAP = 0.15             # gap entre batidas do mesmo bit
BIT_GAP = 0.35              # gap entre bits
THRESHOLD = 0.1             # limiar de amplitude para detectar batida
REFRACTORY = 0.08           # tempo mínimo entre picos


@dataclass
class ParityResult:
    ok: bool
    byte: int = 0


def _click(duration: float = BEAT_DURATION) -> np.ndarray:
    """Gera um clique curto (ruído com decaimento)."""
    n = int(duration * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    env = np.exp(-t * 40)
    return (noise * env).astype(np.float32)


def _bits_to_str(bits: list[int]) -> str:
    return "".join(str(b) for b in bits)


def transmit(payload: bytes, verbose: bool = False) -> np.ndarray:
    """Codifica bytes em quadros de 9 bits e gera o áudio das batidas."""
    if verbose:
        print()
        print("┌─ MÉTODO 1 (batidas + paridade par) ─────────────────────")
        print(f"│ mensagem : {payload!r}")
        print(f"│ bytes    : {' '.join(f'0x{b:02X}' for b in payload)}")
        print(f"│ taxa     : 1 bit por batida-símbolo (0 = 1 batida, 1 = 2 batidas)")
        print(f"│ duração  : {BEAT_DURATION*1000:.0f} ms por batida, "
              f"{BIT_GAP*1000:.0f} ms entre bits")
        print("└─────────────────────────────────────────────────────────")

    out = [np.zeros(int(0.3 * SAMPLE_RATE), dtype=np.float32)]
    total_bits = 0
    total_beats = 0

    for idx, byte in enumerate(payload):
        bits = parity.encode_frame(byte)
        total_bits += len(bits)
        if verbose:
            print()
            print(f"[byte {idx}] 0x{byte:02X} = {byte} "
                  f"(ASCII {chr(byte)!r})")
            print(f"  dados  : {_bits_to_str(bits[:8])}")
            print(f"  paridade: {bits[8]}  (nº de 1s nos dados = "
                  f"{sum(bits[:8])} -> {'par' if sum(bits[:8]) % 2 == 0 else 'ímpar'})")

        for j, b in enumerate(bits):
            n_beats = 1 if b == 0 else 2
            total_beats += n_beats
            if verbose:
                rotulo = "dado" if j < 8 else "paridade"
                print(f"    bit {j} ({rotulo}) = {b} -> "
                      f"{n_beats} batida{'s' if n_beats > 1 else ''}")
            for i in range(n_beats):
                out.append(_click())
                if i < n_beats - 1:
                    out.append(np.zeros(int(BEAT_GAP * SAMPLE_RATE), dtype=np.float32))
            out.append(np.zeros(int(BIT_GAP * SAMPLE_RATE), dtype=np.float32))

    out.append(np.zeros(int(0.3 * SAMPLE_RATE), dtype=np.float32))
    signal = np.concatenate(out)

    if verbose:
        duracao = len(signal) / SAMPLE_RATE
        print()
        print(f"[resumo] {len(payload)} byte(s) -> {total_bits} bits "
              f"-> {total_beats} batidas")
        print(f"[resumo] duração do áudio : {duracao:.2f} s")
        print(f"[resumo] taxa prática     : {total_bits / duracao:.1f} bps "
              f"(1 bit por intervalo de bit)")

    return signal


def _detect_beats(signal: np.ndarray) -> list[float]:
    """Devolve os instantes (em segundos) em que houve batida."""
    env = np.abs(signal)
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
    """Detecta batidas, agrupa em bits e valida paridade por byte."""
    beats = _detect_beats(signal)

    if verbose:
        print()
        print("┌─ RECEPTOR — MÉTODO 1 ───────────────────────────────────")
        print(f"│ amostras      : {len(signal)}")
        print(f"│ duração       : {len(signal)/SAMPLE_RATE:.2f} s")
        print(f"│ limiar        : {THRESHOLD}")
        print(f"│ batidas achadas: {len(beats)}")
        print("└─────────────────────────────────────────────────────────")

    if len(beats) < 2:
        if verbose:
            print("[receptor] batidas insuficientes para decodificar um bit.")
        return []

    # agrupa batidas em bits: 1 batida = 0, 2 batidas próximas = 1
    bits = []
    i = 0
    while i < len(beats):
        if i + 1 < len(beats) and (beats[i + 1] - beats[i]) < BEAT_GAP * 1.5:
            bits.append(1)
            i += 2
        else:
            bits.append(0)
            i += 1

    if verbose:
        print(f"[receptor] bits detectados: {_bits_to_str(bits)} "
              f"({len(bits)} bits)")

    # agrupa em quadros de 9 bits
    results = []
    for j in range(0, len(bits) - 8, 9):
        chunk = bits[j:j + 9]
        ok = parity.check_frame(chunk)
        value = 0
        for b in chunk[:8]:
            value = (value << 1) | b
        if verbose:
            par = sum(chunk[:8]) % 2
            print(f"[receptor] quadro {j//9}: {_bits_to_str(chunk)} "
                  f"-> dados 0x{value:02X}, paridade recebida={chunk[8]}, "
                  f"esperada={par} -> {'OK' if ok else 'FALHA'}")
        results.append(ParityResult(ok=ok, byte=value))
    return results