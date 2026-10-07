import tkinter as tk
from tkinter import ttk
import threading
import audio_io
import method1
import method2
import spectrogram


BG = "#0b0f14"
PANEL = "#111820"
PANEL_2 = "#151e28"
BORDER = "#263442"
GREEN = "#39ff88"
GREEN_DARK = "#123d29"
BLUE = "#4db8ff"
WHITE = "#e8eef5"
GRAY = "#8795a5"
RED = "#ff5577"
FONT = "TkDefaultFont"

class PhysicalLayerInterface:
    def __init__(self, root):
        self.root = root

        self.root.title("Physical Layer Sound Checker")
        self.root.geometry("1100x700")
        self.root.minsize(950, 620)
        self.root.configure(bg=BG)
        self.duration_var = tk.StringVar(value="5.0")
        self.recording = False
        self.setup_style()
        self.create_interface()

    def setup_style(self):
        style = ttk.Style()
        
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TCombobox", fieldbackground=PANEL_2, background=PANEL_2, foreground=WHITE, bordercolor=BORDER, arrowcolor=GREEN, padding=8,)

        style.map("TCombobox", fieldbackground=[("readonly", PANEL_2)], foreground=[("readonly", WHITE)],)

    def create_interface(self):

        header = tk.Frame(self.root, bg=BG, height=85)
        header.pack(fill="x", padx=30, pady=(25, 10))
        header.pack_propagate(False)

        title_area = tk.Frame(header, bg=BG)
        title_area.pack(side="left", fill="y")

        tk.Label(title_area, text="PHYSICAL LAYER", font=(FONT, 24, "bold"), fg=WHITE, bg=BG).pack(anchor="w")

        tk.Label(title_area, text="SOUND CHECKER  //  ACOUSTIC DATA TRANSMISSION", font=(FONT, 9, "bold"), fg=GREEN, bg=BG).pack(anchor="w", pady=(3, 0))

        status_frame = tk.Frame(header, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        status_frame.pack(side="right", padx=(20, 0), pady=8)

        self.status_dot = tk.Label(status_frame, text="●", font=(FONT, 11), fg=GREEN, bg=PANEL)
        self.status_dot.pack(side="left", padx=(12, 5), pady=9)
        self.status_label = tk.Label(status_frame, text="SYSTEM READY", font=(FONT, 9, "bold"), fg=WHITE, bg=PANEL)
        self.status_label.pack(side="left", padx=(0, 12))

        # Linha decorativa inutil
        tk.Frame(self.root, bg=GREEN, height=1).pack(fill="x", padx=30)

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=30, pady=20)

        sidebar = tk.Frame(content, bg=PANEL, width=250, highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="OPERATION", font=(FONT, 9, "bold"), fg=GRAY, bg=PANEL).pack(anchor="w", padx=20, pady=(22, 10))

        self.role_var = tk.StringVar(value="Emissor")
        self.create_option(sidebar, "EMISSOR", "Transmitir dados através do áudio", "Emissor")
        self.create_option(sidebar, "RECEPTOR", "Receber dados através do áudio", "Receptor")

        # Separador
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=20)

        tk.Label(sidebar, text="TRANSMISSION METHOD", font=(FONT, 9, "bold"), fg=GRAY, bg=PANEL).pack(anchor="w", padx=20, pady=(0, 10))

        self.method_var = tk.StringVar(value="Método 1")
        self.method_combo = ttk.Combobox(sidebar, textvariable=self.method_var, values=["Método 1", "Método 2"], state="readonly", width=20)
        self.method_combo.pack(padx=20, fill="x")
        self.method_combo.bind("<<ComboboxSelected>>", self.update_method_info)

        # Informações do método
        info_box = tk.Frame(sidebar, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        info_box.pack(fill="x", padx=20, pady=20)

        tk.Label(info_box, text="METHOD INFO", font=(FONT, 8, "bold"), fg=GREEN, bg=PANEL_2).pack(anchor="w", padx=12, pady=(12, 5))

        self.method_info = tk.Label(info_box, text="8 bits + 1 bit de paridade\nCodificação por pulsos", font=(FONT, 9), fg=WHITE, bg=PANEL_2, justify="left")
        self.method_info.pack(anchor="w", padx=12, pady=(0, 12))

        duration_box = tk.Frame(sidebar, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        duration_box.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(duration_box, text="RECORDING TIME", font=(FONT, 8, "bold"), fg=GREEN, bg=PANEL_2).pack(anchor="w", padx=12, pady=(12, 5))

        duration_row = tk.Frame(duration_box, bg=PANEL_2)

        duration_row.pack(fill="x", padx=12, pady=(0, 12))

        self.duration_entry = tk.Entry(duration_row, textvariable=self.duration_var, font=(FONT, 10), bg="#0d131a", fg=WHITE, insertbackground=GREEN, relief="flat", justify="center")
        self.duration_entry.pack(side="left", fill="x", expand=True, ipady=7)

        tk.Label(duration_row, text="sec", font=(FONT, 9, "bold"), fg=GRAY, bg=PANEL_2).pack(side="left", padx=(8, 0))
        
        main = tk.Frame(content, bg=BG)
        main.pack(side="left", fill="both", expand=True, padx=(20, 0))

        #Temporizador (Tá funcionando)

        timer_box = tk.Frame(main, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        timer_box.pack(fill="x", pady=(0, 15))

        tk.Label(timer_box, text="RECORDING TIMER", font=(FONT, 8, "bold"), fg=GREEN, bg=PANEL).pack(pady=(10, 0))

        self.timer_label = tk.Label(timer_box, text="00:00", font=("Courier", 26, "bold"),fg=GRAY, bg=PANEL)
        self.timer_label.pack(pady=(2, 0))
        self.timer_status = tk.Label(timer_box, text="READY", font=(FONT, 9), fg=GRAY, bg=PANEL)
        self.timer_status.pack(pady=(0, 10))

        message_panel = tk.Frame(main, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        message_panel.pack(fill="x")
        message_header = tk.Frame(message_panel, bg=PANEL)
        message_header.pack(fill="x", padx=20, pady=(18, 8))

        tk.Label(message_header, text="DATA PAYLOAD", font=(FONT, 10, "bold"), fg=WHITE, bg=PANEL).pack(side="left")

        self.byte_label = tk.Label(message_header, text="0 bytes", font=(FONT, 9), fg=GREEN, bg=PANEL)
        self.byte_label.pack(side="right")
        self.message_entry = tk.Text(message_panel, height=5, bg="#0d131a", fg=WHITE, insertbackground=GREEN, selectbackground=GREEN_DARK, selectforeground=WHITE, font=(FONT, 11), relief="flat", wrap="word", padx=12, pady=12)
        self.message_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.message_entry.bind("<KeyRelease>", self.update_byte_count)

        # Botão
        button_area = tk.Frame(message_panel, bg=PANEL)
        button_area.pack(fill="x", padx=20, pady=(0, 18))

        self.action_button = tk.Button(
            button_area,
            text="▶  TRANSMIT DATA",
            command=self.action,
            bg=GREEN_DARK,
            fg=GREEN,
            activebackground="#1b5739",
            activeforeground=WHITE,
            font=(FONT, 10, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.action_button.pack(side="right")

        # flow

        flow_panel = tk.Frame(main, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        flow_panel.pack(fill="x", pady=20)

        tk.Label(flow_panel, text="TRANSMISSION PIPELINE", font=(FONT, 10, "bold"), fg=WHITE, bg=PANEL).pack(anchor="w", padx=20, pady=(18, 15))

        flow = tk.Frame(flow_panel, bg=PANEL)
        flow.pack(fill="x", padx=20, pady=(0, 20))

        self.flow_nodes = []

        nodes = [
            ("01", "DATA"),
            ("02", "FRAME"),
            ("03", "MODULATION"),
            ("04", "AUDIO"),
            ("05", "CHECK")
        ]

        for index, (number, name) in enumerate(nodes):
            node = tk.Frame(
                flow,
                bg=PANEL_2,
                highlightbackground=BORDER,
                highlightthickness=1
            )

            node.pack(side="left", fill="both", expand=True)

            self.flow_nodes.append(node)

            tk.Label(node, text=number, font=(FONT, 8, "bold"), fg=GREEN, bg=PANEL_2).pack(pady=(10, 2))
            tk.Label(node, text=name, font=(FONT, 8, "bold"), fg=WHITE, bg=PANEL_2).pack(pady=(0, 10))

            if index < len(nodes) - 1:
                tk.Label(
                    flow,
                    text="›",
                    font=(FONT, 18, "bold"),
                    fg=GRAY,
                    bg=PANEL
                ).pack(side="left", padx=7)

        # Terminar improvisado (testar para ver se da certo!)

        terminal_panel = tk.Frame(main, bg="#070b0f", highlightbackground=BORDER, highlightthickness=1)
        terminal_panel.pack(fill="both", expand=True)
        terminal_header = tk.Frame(terminal_panel, bg="#070b0f")
        terminal_header.pack(fill="x")

        tk.Label(terminal_header, text="  SYSTEM LOG", font=(FONT, 9, "bold"), fg=GREEN, bg="#070b0f").pack(side="left", pady=10)

        self.log = tk.Text(terminal_panel, bg="#070b0f", fg="#8fa3b5", insertbackground=GREEN, font=("Courier", 9), relief="flat", state="disabled", height=7)
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.write_log("[SYSTEM] Physical Layer Sound Checker initialized.")
        self.write_log("[SYSTEM] Audio transmission interface ready.")
        self.write_log("[INFO] Select a role and transmission method.")

    # SideBar (opções)
    def create_option(self, parent, title, description, value):

        frame = tk.Frame(parent, bg=PANEL, cursor="hand2")
        frame.pack(fill="x", padx=12, pady=3)

        def select(event=None):
            self.role_var.set(value)

            for child in parent.winfo_children():
                if hasattr(child, "option_value"):
                    if child.option_value == value:
                        child.configure(bg=GREEN_DARK)
                    else:
                        child.configure(bg=PANEL)

            self.write_log(f"[CONFIG] Operation changed to: {value}")

        frame.option_value = value
        frame.bind("<Button-1>", select)
        
        title_label = tk.Label(frame, text="●  " + title, font=(FONT, 9, "bold"), fg=GREEN if value == "Emissor" else BLUE, bg=PANEL, anchor="w")
        title_label.pack(fill="x", padx=10, pady=(9, 1))
        title_label.bind("<Button-1>", select)
        
        desc_label = tk.Label(frame, text=description, font=(FONT, 8), fg=GRAY, bg=PANEL, anchor="w")
        desc_label.pack(fill="x", padx=28, pady=(0, 9))
        desc_label.bind("<Button-1>", select)

    # MÉTODO
    def update_method_info(self, event=None):
        method = self.method_var.get()
        
        if method == "Método 1":
            self.method_info.config(
                text="8 bits + 1 bit de paridade\n"
                     "Codificação por pulsos"
            )

            self.write_log("[CONFIG] Method 1 selected — parity + beats.")
            
        else:
            self.method_info.config(
                text="M-FSK / 4 símbolos\n"
                     "CRC-8 / 2 bits por símbolo"
            )

            self.write_log("[CONFIG] Method 2 selected — M-FSK + CRC-8.")

    # Contador de bytes
    def update_byte_count(self, event=None):
        
        text = self.message_entry.get("1.0", "end-1c")
        size = len(text.encode("utf-8"))
        self.byte_label.config(text=f"{size} bytes")

    def write_log(self, message):

        self.log.config(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def action(self):
        message = self.message_entry.get("1.0", "end-1c").strip()
        role = self.role_var.get()
        method = self.method_var.get()

        self.write_log(f"[CONFIG] Role: {role}")
        self.write_log(f"[CONFIG] Method: {method}")

        #REceptor
        if role == "Receptor":
            self.start_receiver(method)
            return

        #Emissor
        if not message:
            self.write_log("[WARNING] No data to transmit.")
            self.set_status("WAITING FOR DATA", GRAY)
            return

        self.set_status("TRANSMITTING...", GREEN)
        self.write_log(f"[TX] Payload: {message}")

        try:
            payload = message.encode("utf-8")
            if method == "Método 1":

                self.write_log("[TX] Calling Method 1...")

                signal = method1.transmit(payload, verbose=False)

            else:
                self.write_log("[TX] Calling Method 2...")

                signal = method2.transmit(payload, verbose=False)
                
            self.write_log(f"[TX] Generated {len(signal)} audio samples.")

            if audio_io.AUDIO_AVAILABLE:
                self.write_log("[TX] Playing audio...")

                audio_io.play(signal)

                self.write_log("[OK] Audio transmission complete.")
                self.set_status("TRANSMISSION COMPLETE", GREEN)

            else:
                self.write_log("[WARNING] Audio unavailable.")
                self.write_log(f"[INFO] {audio_io.AUDIO_ERROR}")
                self.set_status("AUDIO UNAVAILABLE", RED)

        except Exception as error:

            self.write_log(f"[ERROR] {type(error).__name__}: {error}")
            self.set_status("TRANSMISSION ERROR", RED)
        
    def start_receiver(self, method):
        if not audio_io.AUDIO_AVAILABLE:
            self.write_log("[ERROR] Audio input is unavailable.")
            self.write_log(f"[INFO] {audio_io.AUDIO_ERROR}")
            self.set_status("AUDIO UNAVAILABLE", RED)

            return

        # Valida o tempo informado na interface
        try:
            duration = float(self.duration_var.get().replace(",", "."))
        except ValueError:
            self.write_log("[ERROR] Invalid recording duration.")
            self.set_status("INVALID DURATION", RED)

            return

        if duration <= 0:
            self.write_log("[ERROR] Recording duration must be greater than 0.")
            self.set_status("INVALID DURATION", RED)

            return

        # Limite razoável para evitar uma gravação acidentalmente enorme
        if duration > 60:
            self.write_log("[ERROR] Maximum recording duration is 60 seconds.")
            self.set_status("INVALID DURATION", RED)

            return

        self.set_status("RECEIVER READY", BLUE)
        self.write_log("[RX] Receiver mode started.")
        self.write_log(f"[RX] Recording for {duration:.1f} seconds...")

        self.timer_label.config(text=f"{int(duration // 60):02d}:{int(duration % 60):02d}", fg=GREEN)
        self.timer_status.config(text="RECORDING...")
        self.action_button.config(state="disabled")

        thread = threading.Thread(target=self.receive_audio, args=(method, duration), daemon=True)

        thread.start()
            
    def receive_audio(self, method, duration):
        try:
            live_spectrogram = spectrogram.LiveSpectrogram()

            def on_block(block, elapsed):
                live_spectrogram(block, elapsed)

                remaining = max(0, duration - elapsed)
                self.root.after(0, lambda r=remaining: self.update_recording_timer( r, duration))

            signal = audio_io.record(duration, on_block=on_block)
            self.root.after(0, lambda: self.process_received_signal(signal, method))

        except Exception as error:
            self.root.after(0,lambda: self.receiver_error(error))

        except Exception as error:
            self.root.after(0, lambda: self.receiver_error(error))
        
    def update_recording_timer(self, remaining, total):
        remaining = max(0, remaining)

        minutes = int(remaining // 60)
        seconds = int(remaining % 60)

        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        self.timer_status.config(text=f"{remaining:.1f}s remaining")

        if remaining <= 0:
            self.timer_label.config(fg=GREEN)
            self.timer_status.config(text="PROCESSING...")

        elif remaining <= total * 0.2:
            self.timer_label.config(fg=RED)

        elif remaining <= total * 0.5:
            self.timer_label.config(fg=BLUE)

        else:
            self.timer_label.config(fg=GREEN)
        
    def process_received_signal(self, signal, method):
        try:
            self.write_log(f"[RX] Recorded {len(signal)} audio samples.")
            self.write_log(f"[RX] Decoding using {method}...")

            if method == "Método 1":

                results = method1.receive(signal, verbose=False)

                if not results:
                    self.write_log("[RX] No valid frame detected.")
                    self.set_status("RECEPTION FAILED", RED)

                else:
                    valid_bytes = bytes(
                        r.byte
                        for r in results
                        if r.ok
                    )

                    text = valid_bytes.decode("utf-8", errors="replace")

                    self.write_log(f"[RX] Decoded message: {text}")
                    self.message_entry.delete("1.0", "end")
                    self.message_entry.insert("1.0", text)

                    self.update_byte_count()
                    self.write_log("[OK] Reception complete.")
                    self.set_status("RECEPTION COMPLETE", GREEN)

            else:
                result = method2.receive(signal, verbose=False)

                if result.ok:
                    text = result.payload.decode("utf-8", errors="replace")

                    self.write_log(f"[RX] Decoded message: {text}")
                    self.message_entry.delete("1.0", "end")
                    self.message_entry.insert("1.0", text)

                    self.update_byte_count()
                    self.write_log("[OK] CRC-8 verification successful.")
                    self.set_status("RECEPTION COMPLETE", GREEN)

                else:
                    self.write_log(f"[RX] Transmission failed: {result.reason}")
                    self.set_status("RECEPTION FAILED", RED)

        except Exception as error:
            self.receiver_error(error)

        finally:
            self.action_button.config(state="normal")
    
    def receiver_error(self, error):
        self.write_log(f"[ERROR] {type(error).__name__}: {error}")
        self.set_status("RECEPTION ERROR", RED)
        self.action_button.config(state="normal")
                    
    def animate_pipeline(self, index=0):
        if index >= len(self.flow_nodes):
            self.set_status("TRANSMISSION COMPLETE", GREEN)
            self.write_log("[OK] Transmission pipeline complete.")

            return

        node = self.flow_nodes[index]
        node.configure(bg=GREEN_DARK)

        for widget in node.winfo_children():
            widget.configure(bg=GREEN_DARK)

        self.root.after(
            350, lambda: self.animate_pipeline(index + 1))

    def set_status(self, text, color):

        self.status_label.config(text=text)

        self.status_dot.config(fg=color)

if __name__ == "__main__":

    root = tk.Tk()

    app = PhysicalLayerInterface(root)

    root.mainloop()