# SPDX-License-Identifier: MIT
"""CLI do software de camada física: emissor/receptor, Métodos 1 e 2."""
import audio_io
import method1
import method2


def ask(prompt: str, options: list[str]) -> str:
    print(prompt)
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        choice = input("> ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("opção inválida, tente de novo.")


def ask_yes_no(prompt: str) -> bool:
    while True:
        r = input(f"{prompt} [s/N] ").strip().lower()
        if r in ("", "n", "nao", "não"):
            return False
        if r in ("s", "sim", "y", "yes"):
            return True
        print("responda com 's' ou 'n'.")


def run_emitter(method: str, verbose: bool) -> None:
    msg = input("mensagem a transmitir: ").strip()
    payload = msg.encode("utf-8")

    if method == "Método 1 (batidas)":
        signal = method1.transmit(payload, verbose=verbose)
    else:
        signal = method2.transmit(payload, verbose=verbose)
        if not verbose:
            print(f"[M-FSK] taxa teórica ≈ {method2.estimated_bitrate():.0f} bps")

    print()
    print(f"[emissor] transmitindo {len(payload)} bytes "
          f"({len(signal)/audio_io.SAMPLE_RATE:.2f} s de áudio)...")
    audio_io.play(signal)
    print("[emissor] pronto.")


def run_receiver(method: str, verbose: bool) -> None:
    duration = float(input("duração da gravação (s): ").strip())
    signal = audio_io.record(duration)

    if method == "Método 1 (batidas)":
        results = method1.receive(signal, verbose=verbose)
        if not results:
            print("[receptor] FALHA: nenhum quadro detectado")
            return
        print()
        for r in results:
            status = "SUCESSO" if r.ok else "FALHA DE TRANSMISSÃO"
            print(f"[receptor] byte=0x{r.byte:02X} ({r.byte}) -> {status}")
    else:
        result = method2.receive(signal, verbose=verbose)
        print()
        if result.ok:
            print(f"[receptor] SUCESSO: {result.payload!r}")
        else:
            print(f"[receptor] FALHA DE TRANSMISSÃO: {result.reason}")


def main() -> None:
    print("=== Camada Física — Emissor/Receptor ===")
    role = ask("Selecione o papel:", ["Emissor", "Receptor"])
    method = ask("Selecione o método:", ["Método 1 (batidas)", "Método 2 (M-FSK)"])
    verbose = ask_yes_no("Mostrar detalhes do processamento (modo verboso)?")

    if role == "Emissor":
        run_emitter(method, verbose)
    else:
        run_receiver(method, verbose)


if __name__ == "__main__":
    main()