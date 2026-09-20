# SPDX-License-Identifier: MIT
"""Ponto de entrada do sistema integrando frame_generator e frame_verifier em Stream Contínuo."""

import argparse
import sys

import audio_config as cfg
import receiver
import transmitter

# Módulos oficiais do projeto
from bits import bits_to_bytes, byte_to_bits, bytes_to_bits
from frame import generate_frame_method2
from frame import verify_frame_method2


def frame_dict_to_bits(frame: dict) -> list[int]:
    """Converte o dicionário do frame_generator.py para a lista de bits do alto-falante."""
    stream = []
    
    # 1. Start: '101' -> [1, 0, 1]
    stream.extend([int(b) for b in frame["start"]])

    # 2. Size: inteiro 'data_size' para 8 bits
    stream.extend(byte_to_bits(frame["size"]))

    # 3. Payload: bytes para bits
    stream.extend(bytes_to_bits(frame["payload"]))

    # 4. CRC: inteiro CRC-8 para 8 bits
    stream.extend(byte_to_bits(frame["crc"]))

    # 5. End: '101' -> [1, 0, 1]
    stream.extend([int(b) for b in frame["end"]])

    return stream


def bits_to_frame_dict(bits: list[int]) -> tuple[bool, dict]:
    """Reconstrói o dicionário do quadro a partir da lista de bits recebida."""
    # Start(3) + Size(8) + Payload(min 8) + CRC(8) + End(3) = 30 bits mínimo
    if len(bits) < 30:
        return False, {}

    # Verifica delimitador inicial "101"
    if bits[0:3] != [1, 0, 1]:
        return False, {}

    # Extrai Size (bits 3..10)
    data_size_bits = (
        bits[3] << 7
        | bits[4] << 6
        | bits[5] << 5
        | bits[6] << 4
        | bits[7] << 3
        | bits[8] << 2
        | bits[9] << 1
        | bits[10]
    )
    
    # Prevenção contra ruídos: o tamanho dos bits do payload deve ser > 0 e múltiplo de 8
    if data_size_bits == 0 or data_size_bits % 8 != 0:
        return False, {}

    total_expected_bits = 3 + 8 + data_size_bits + 8 + 3
    if len(bits) < total_expected_bits:
        return False, {}

    # Extrai Payload e trata a exceção caso ruídos quebrem a lista de bits
    payload_bits = bits[11 : 11 + data_size_bits]
    try:
        payload_bytes = bits_to_bytes(payload_bits)
    except ValueError:
        return False, {}

    # Extrai CRC
    crc_offset = 11 + data_size_bits
    crc_bits = bits[crc_offset : crc_offset + 8]
    received_crc = 0
    for b in crc_bits:
        received_crc = (received_crc << 1) | b

    # Extrai End
    end_offset = crc_offset + 8
    end_bits = bits[end_offset : end_offset + 3]
    if end_bits != [1, 0, 1]:
        return False, {}

    frame = {
        "start": "101",
        "size": data_size_bits,
        "payload": payload_bytes,
        "crc": received_crc,
        "end": "101",
    }
    return True, frame


def handle_send(args: argparse.Namespace) -> None:
    cfg.set_mode(args.mode)
    payload_bytes = args.message.encode("utf-8")
    data_size_bits = len(payload_bytes) * 8

    # Chama o gerador oficial
    frame = generate_frame_method2(payload_bytes, data_size_bits)
    
    # Converte o dicionário nos bits exatos
    bit_stream = frame_dict_to_bits(frame)

    print(f"[+] Codificando mensagem: '{args.message}'")
    print(f"[+] Quadro gerado ({len(bit_stream)} bits): {bit_stream}")

    transmitter.transmit_bits(bit_stream)
    print("[✔] Transmissão concluída!")


def handle_listen(args: argparse.Namespace) -> None:
    cfg.set_mode(args.mode)
    print(f"[*] Limiar de Magnitude Ativo: {cfg.MAGNITUDE_THRESHOLD}")

    bit_buffer = []

    def on_bits_received(new_bits: list[int]) -> None:
        nonlocal bit_buffer
        bit_buffer.extend(new_bits)

        # Mantém tamanho do buffer gerenciável
        if len(bit_buffer) > 1000:
            bit_buffer = bit_buffer[-500:]

        # Varre o buffer acumulado procurando por padrões que iniciem em [1, 0, 1]
        for i in range(len(bit_buffer) - 29):
            if bit_buffer[i : i + 3] == [1, 0, 1]:
                ok, frame = bits_to_frame_dict(bit_buffer[i:])
                if ok and verify_frame_method2(frame):
                    msg = frame["payload"].decode("utf-8")
                    print("\n" + "=" * 50)
                    print("[✔] SUCESSO! Pacote recebido e validado via verify_frame_method2!")
                    print(f"[➔] Conteúdo: {msg}")
                    print("=" * 50 + "\n")
                    
                    # Limpa o buffer até o final do pacote processado
                    processed_len = 3 + 8 + frame["size"] + 8 + 3
                    bit_buffer = bit_buffer[i + processed_len :]
                    break

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