# SPDX-License-Identifier: MIT
"""CLI da camada física por áudio: emissor/receptor didático dos métodos 1 e 2.

Ponto de entrada único (fluxo interativo):
    python src/main.py

O assistente pergunta, nesta ordem:
    1) papel   -> Emissor ou Receptor;
    2) método  -> Método 1 (batidas + paridade) ou Método 2 (M-FSK + CRC-8);
    3) verboso -> mostrar (ou não) o detalhamento do processamento.
"""

import os
import tempfile

import audio_io
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


def main() -> None:
    """Executa o assistente interativo, único modo de operação da CLI."""
    try:
        run_wizard()
    except KeyboardInterrupt:
        print("\n[i] execução interrompida pelo usuário.")
    except EOFError:
        print("\n[i] entrada padrão encerrada (EOF).")
        print("    rode a CLI em um terminal interativo: python src/main.py")


if __name__ == "__main__":
    main()
