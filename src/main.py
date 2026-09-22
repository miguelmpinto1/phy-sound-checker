# SPDX-License-Identifier: MIT
"""CLI da camada física por áudio: emissor/receptor didático dos métodos 1 e 2.

Fluxo interativo (padrão):
    python src/main.py

Modo contínuo/legado, com faixa audível ou quase-ultrassônica:
    python src/main.py send "mensagem" [--mode audible|ultrasonic]
    python src/main.py listen [--mode audible|ultrasonic]
"""

import argparse
import os
import sys
import tempfile
import time

import audio_io
import frame
import method1
import method2

METHOD_1 = "Método 1 (batidas + paridade)"
METHOD_2 = "Método 2 (M-FSK + CRC-8)"


def ask(prompt: str, options: list[str]) -> str:
    """Pergunta de múltipla escolha: devolve a opção escolhida pelo usuário."""
    print(prompt)
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        choice = input("> ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("opção inválida, tente de novo.")


def ask_yes_no(prompt: str) -> bool:
    """Pergunta sim/não (padrão: não)."""
    while True:
        answer = input(f"{prompt} [s/N] ").strip().lower()
        if answer in ("", "n", "nao", "não"):
            return False
        if answer in ("s", "sim", "y", "yes"):
            return True
        print("responda com 's' ou 'n'.")


def run_emitter(method: str, verbose: bool) -> None:
    """Pergunta a mensagem, gera o sinal pelo método escolhido e reproduz o áudio."""
    message = input("mensagem a transmitir: ")
    payload = message.encode("utf-8")
    if not payload:
        print("[emissor] mensagem vazia: nada a transmitir.")
        return

    if method == METHOD_1:
        signal = method1.transmit(payload, verbose=verbose)
    else:
        signal = method2.transmit(payload, verbose=verbose)
        if not verbose:
            print(f"[M-FSK] M={method2.M} -> {method2.bits_per_symbol()} bits/símbolo | "
                  f"taxa teórica ≈ {method2.theoretical_rate():.0f} bps")

    duracao = len(signal) / audio_io.SAMPLE_RATE
    print()
    print(f"[emissor] {len(payload)} byte(s) -> {len(signal)} amostras "
          f"({duracao:.2f} s de áudio a {audio_io.SAMPLE_RATE} Hz)")

    if not audio_io.AUDIO_AVAILABLE:
        name = "phy-sound-metodo1.wav" if method == METHOD_1 else "phy-sound-metodo2.wav"
        path = os.path.join(tempfile.gettempdir(), name)
        audio_io.save_wav(signal, path)
        print(f"[emissor] saída de áudio indisponível ({audio_io.AUDIO_ERROR}).")
        print(f"[emissor] sinal salvo em {path} para reprodução manual.")
        return

    print("[emissor] reproduzindo o sinal...")
    audio_io.play(signal)
    print("[emissor] pronto.")


def run_receiver(method: str, verbose: bool) -> None:
    """Grava o áudio do microfone e tenta decodificar o quadro transmitido."""
    if not audio_io.AUDIO_AVAILABLE:
        print(f"[receptor] entrada de áudio indisponível ({audio_io.AUDIO_ERROR}).")
        print("[receptor] instale o PortAudio (ex.: libportaudio2) para usar o microfone.")
        return

    try:
        duration = float(input("duração da gravação (s): ").strip())
    except ValueError:
        print("[receptor] duração inválida.")
        return

    signal = audio_io.record(duration)

    if method == METHOD_1:
        results = method1.receive(signal, verbose=verbose)
        print()
        if not results:
            print("[receptor] FALHA: nenhum quadro de 9 bits foi reconstruído.")
            return
        for r in results:
            print(f"[receptor] byte = 0x{r.byte:02X} ({r.byte}) -> "
                  f"{'SUCESSO' if r.ok else 'FALHA'}")
        texto = bytes(r.byte for r in results if r.ok).decode("utf-8", errors="replace")
        print(f"[receptor] mensagem decodificada: {texto!r}")
        return

    result = method2.receive(signal, verbose=verbose)
    print()
    if result.ok:
        print(f"[receptor] SUCESSO: {result.payload.decode('utf-8', errors='replace')!r}")
    else:
        print(f"[receptor] FALHA DE TRANSMISSÃO: {result.reason}")


def run_wizard() -> None:
    """Fluxo interativo: papel -> método -> modo verboso -> execução."""
    print("=== Camada Física por Áudio — Emissor/Receptor ===")
    role = ask("Selecione o papel:", ["Emissor", "Receptor"])
    method = ask("Selecione o método:", [METHOD_1, METHOD_2])
    verbose = ask_yes_no("Mostrar detalhes do processamento (modo verboso)?")

    if role == "Emissor":
        run_emitter(method, verbose)
    else:
        run_receiver(method, verbose)


# --------------------------------------------------------------------------- #
# Modo contínuo (legado): envia/escuta quadros de 1 byte em fluxo de áudio      #
# --------------------------------------------------------------------------- #

def handle_send(args: argparse.Namespace) -> None:
    """Envia a mensagem caractere por caractere em fluxo contínuo de áudio."""
    import audio_config as cfg
    import transmitter

    cfg.set_mode(args.mode)
    payload = args.message.encode("utf-8")

    print(f"[+] Iniciando envio da mensagem: {args.message!r} "
          f"({len(payload)} caractere(s), modo {args.mode})")

    for i, char_byte in enumerate(payload):
        packet = bytes([char_byte])
        bit_stream = frame.encode(packet)

        if args.verbose:
            crc_bits = bit_stream[19:27]
            crc_value = int("".join(str(b) for b in crc_bits), 2)
            print(f"[+] quadro {i + 1}: dados=0x{char_byte:02X} crc=0x{crc_value:02X} "
                  f"total={len(bit_stream)} bits")

        print(f"[+] Enviando pacote {i + 1}/{len(payload)} ({len(bit_stream)} bits): {bit_stream}")
        transmitter.transmit_bits(bit_stream)
        time.sleep(0.1)

    print("[✔] Transmissão de todos os pacotes concluída!")


def handle_listen(args: argparse.Namespace) -> None:
    """Escuta o fluxo contínuo e decodifica cada quadro reconhecido pelo delimitador."""
    import audio_config as cfg
    import receiver

    cfg.set_mode(args.mode)
    threshold = getattr(cfg, "MAGNITUDE_THRESHOLD", 1.0)
    print(f"[*] Limiar de Magnitude Ativo: {threshold}")

    bit_buffer: list[int] = []

    def on_bits_received(new_bits: list[int]) -> None:
        nonlocal bit_buffer
        bit_buffer.extend(new_bits)

        if args.verbose:
            print(f"[~] bloco recebido: {''.join(str(b) for b in new_bits)} "
                  f"({sum(new_bits)} tom(s) ativo(s))")

        if len(bit_buffer) > 1000:
            bit_buffer = bit_buffer[-500:]

        i = 0
        while i <= len(bit_buffer) - 3:
            if bit_buffer[i:i + 3] == [1, 0, 1]:
                result = frame.decode(bit_buffer[i:])

                if result.ok:
                    try:
                        char_str = result.payload.decode("utf-8")
                    except UnicodeDecodeError:
                        char_str = str(result.payload)

                    print("\n" + "=" * 50)
                    print("[✔] SUCESSO! Pacote decodificado via frame.decode()!")
                    print(f"[➔] Caractere/Payload: {char_str}")
                    print("=" * 50 + "\n")

                    consumed = frame.OVERHEAD_BITS + len(result.payload) * 8
                    bit_buffer = bit_buffer[i + consumed:]
                    i = 0
                    continue
            i += 1

    try:
        receiver.listen_continuous_stream(on_bits_received)
    except KeyboardInterrupt:
        print("\n\n[!] Escuta encerrada pelo usuário.")
        sys.exit(0)


def build_parser() -> argparse.ArgumentParser:
    """Argumentos para o modo legado; sem subcomando o CLI abre o fluxo interativo."""
    parser = argparse.ArgumentParser(description="Camada Física por Áudio")
    subparsers = parser.add_subparsers(dest="command")

    send_parser = subparsers.add_parser("send",
                                        help="envia a mensagem em fluxo contínuo (modo legado)")
    send_parser.add_argument("message", type=str)
    send_parser.add_argument("--mode", choices=["audible", "ultrasonic"], default="audible")
    send_parser.add_argument("-v", "--verbose", action="store_true",
                             help="mostra o detalhamento dos quadros enviados")

    listen_parser = subparsers.add_parser("listen",
                                          help="escuta o fluxo contínuo (modo legado)")
    listen_parser.add_argument("--mode", choices=["audible", "ultrasonic"], default="audible")
    listen_parser.add_argument("-v", "--verbose", action="store_true",
                               help="mostra o detalhamento do processamento recebido")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "send":
        handle_send(args)
        return
    if args.command == "listen":
        handle_listen(args)
        return

    try:
        run_wizard()
    except KeyboardInterrupt:
        print("\n[i] execução interrompida pelo usuário.")
    except EOFError:
        print("\n[i] entrada padrão encerrada (EOF).")
        print("    rode em um terminal interativo ou use os modos diretos:")
        print("      python src/main.py send \"mensagem\"")
        print("      python src/main.py listen")


if __name__ == "__main__":
    main()
