# SPDX-License-Identifier: MIT
"""Software Único (Transmissor/Receptor) para o Método 2."""

import argparse
import sys
import sounddevice as sd

import audio_config as cfg
import frame
from receiver import process_audio_buffer
from transmitter import transmit_bits


def send_message(message: str) -> None:
    print(f"\n[+] Codificando mensagem: '{message}'")
    payload = message.encode("utf-8")

    tx_bits = frame.encode(payload)
    print(f"[+] Total de bits gerados: {len(tx_bits)} bits")
    print(f"[+] Transmitindo iniciando em {cfg.FREQ_START} Hz...")

    transmit_bits(tx_bits)
    print("[✔] Transmissão concluída!")


def listen_and_receive(duration_sec: float = 4.0) -> None:
    print(f"\n[+] Escutando microfone por {duration_sec} s na faixa {cfg.BANDPASS_LOW}-{cfg.BANDPASS_HIGH} Hz...")
    recording = sd.rec(
        int(duration_sec * cfg.FS),
        samplerate=cfg.FS,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    print("[+] Gravação concluída. Processando áudio e FFT...")

    audio_data = recording.flatten()
    received_bits = process_audio_buffer(audio_data)

    for idx in range(len(received_bits) - 3):
        if received_bits[idx : idx + 3] == [1, 0, 1]:
            candidate_bits = received_bits[idx:]
            result = frame.decode(candidate_bits)
            if result.ok:
                print(f"\n[✔] SUCESSO! Pacote recebido e validado via CRC-8!")
                print(f"[➔] Conteúdo: {result.payload.decode('utf-8', errors='replace')}\n")
                return

    print("\n[✘] FALHA: Nenhum quadro válido ou CRC inconsistente no áudio capturado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sistema de Comunicação Acústica - Método 2")
    parser.add_argument("action", choices=["send", "listen"], help="Ação a executar: 'send' ou 'listen'")
    parser.add_argument("message", nargs="?", default="A", help="Mensagem a ser enviada (apenas para a ação 'send')")
    parser.add_argument(
        "--mode", "-m",
        choices=["ultrasonic", "audible"],
        default="ultrasonic",
        help="Modo acústico: 'ultrasonic' (silencioso, 18kHz) ou 'audible' (apitos, 2kHz)"
    )

    args = parser.parse_args()

    cfg.set_mode(args.mode)
    print(f"[*] Modo de áudio ativado: {args.mode.upper()} (Frequência inicial: {cfg.FREQ_START} Hz)")

    if args.action == "send":
        send_message(args.message)
    elif args.action == "listen":
        listen_and_receive()