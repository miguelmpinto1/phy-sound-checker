# SPDX-License-Identifier: MIT
"""Ponto de entrada do sistema integrando frame.py em Stream Contínuo de Áudio."""

import argparse
import sys
import time

import audio_config as cfg
import receiver
import transmitter

# Módulos oficiais do projeto
from bits import byte_to_bits, bytes_to_bits
from frame import generate_frame_method2, decode, OVERHEAD_BITS


def frame_dict_to_bits(frame: dict) -> list[int]:
    """Converte o dicionário gerado pelo generate_frame_method2 para a lista de bits de transmissão."""
    stream = []
    
    # 1. Start: '101' -> [1, 0, 1]
    stream.extend([int(b) for b in frame["start"]])

    # 2. Size: inteiro 'size' para 8 bits
    stream.extend(byte_to_bits(frame["size"]))

    # 3. Payload: bytes para bits
    stream.extend(bytes_to_bits(frame["payload"]))

    # 4. CRC: inteiro CRC-8 para 8 bits
    stream.extend(byte_to_bits(frame["crc"]))

    # 5. End: '101' -> [1, 0, 1]
    stream.extend([int(b) for b in frame["end"]])

    return stream


def handle_send(args: argparse.Namespace) -> None:
    cfg.set_mode(args.mode)
    message_bytes = args.message.encode("utf-8")

    print(f"[+] Iniciando envio da mensagem: '{args.message}' ({len(message_bytes)} caractere(s))")

    # Envia caractere por caractere em pacotes de até 8 bits
    for i, char_byte in enumerate(message_bytes):
        payload = bytes([char_byte])
        data_size_bits = len(payload) * 8

        frame = generate_frame_method2(payload, data_size_bits)
        bit_stream = frame_dict_to_bits(frame)

        print(f"[+] Enviando pacote {i + 1}/{len(message_bytes)} ({len(bit_stream)} bits): {bit_stream}")
        transmitter.transmit_bits(bit_stream)
        time.sleep(0.1)

    print("[✔] Transmissão de todos os pacotes concluída!")


def handle_listen(args: argparse.Namespace) -> None:
    cfg.set_mode(args.mode)
    threshold = getattr(cfg, "MAGNITUDE_THRESHOLD", 1.0)
    print(f"[*] Limiar de Magnitude Ativo: {threshold}")

    bit_buffer = []

    def on_bits_received(new_bits: list[int]) -> None:
        nonlocal bit_buffer
        bit_buffer.extend(new_bits)

        if len(bit_buffer) > 1000:
            bit_buffer = bit_buffer[-500:]

        i = 0
        while i <= len(bit_buffer) - 3:
            if bit_buffer[i : i + 3] == [1, 0, 1]:
                result = decode(bit_buffer[i:])

                if result.ok:
                    try:
                        char_str = result.payload.decode("utf-8")
                    except UnicodeDecodeError:
                        char_str = str(result.payload)

                    print("\n" + "=" * 50)
                    print("[✔] SUCESSO! Pacote decodificado via frame.decode()!")
                    print(f"[➔] Caractere/Payload: {char_str}")
                    print("=" * 50 + "\n")

                    payload_bits_len = len(result.payload) * 8
                    consumed = OVERHEAD_BITS + payload_bits_len
                    bit_buffer = bit_buffer[i + consumed :]
                    i = 0
                    continue
            i += 1

    try:
        receiver.listen_continuous_stream(on_bits_received)
    except KeyboardInterrupt:
        print("\n\n[!] Escuta encerrada pelo usuário.")
        sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Camada Física por Áudio")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send")
    send_parser.add_argument("message", type=str)
    send_parser.add_argument("--mode", choices=["audible", "ultrasonic"], default="audible")

    listen_parser = subparsers.add_parser("listen")
    listen_parser.add_argument("--mode", choices=["audible", "ultrasonic"], default="audible")

    args = parser.parse_args()
    if args.command == "send":
        handle_send(args)
    elif args.command == "listen":
        handle_listen(args)


if __name__ == "__main__":
    main()