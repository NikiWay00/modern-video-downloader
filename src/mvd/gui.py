"""
GUI Module per Modern Video Downloader.

Interfaccia grafica principale costruita con CustomTkinter.
Supporta download video/audio con queue management, progress tracking,
e cancellazione in tempo reale.
"""

import os
import threading
import queue
import logging
from typing import Dict, Any, Callable, Optional, Tuple

import customtkinter as ctk
import pyperclip
from tkinter import filedialog, messagebox

from .downloader import download_video
from .utils import is_valid_url, resource_path
from .config import (
    APP_TITLE,
    APP_VERSION,
    DEFAULT_DOWNLOAD_PATH,
    UI_STYLE,
    COLORS,
    UI_LAYOUT,
    UI_MSG,
    QUALITY_PRESETS,
    FORMAT_OPTIONS,
    PERFORMANCE_CONFIG,
    KEYBOARD,
    get_resolution_height,
    get_status_color,
)
from .exceptions import (
    DownloadCancelledError,
    TitleFetchError,
    InvalidURLError,
)
from . import updater

# Configura tema CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class VideoDownloaderGUI(ctk.CTk):
    """
    Finestra principale dell'applicazione Modern Video Downloader.

    Interfaccia grafica per download video/audio con features:
    - Download queue management
    - Progress tracking real-time
    - Cancellazione download
    - Fetch titoli in background
    - Logging dettagliato
    - Keyboard shortcuts
    """

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(self) -> None:
        """Inizializza la finestra principale e tutti i componenti UI."""
        super().__init__()

        # Icona finestra (barra in alto + ALT-TAB)
        try:
            self.iconbitmap(resource_path("assets/logo.ico"))
        except Exception as e:
            logging.warning(f"Could not load icon: {e}")

        # Configurazione finestra
        self.title(APP_TITLE)
        self.geometry(f"{UI_LAYOUT.WINDOW_WIDTH}x{UI_LAYOUT.WINDOW_HEIGHT}")
        self.minsize(UI_LAYOUT.WINDOW_MIN_WIDTH, UI_LAYOUT.WINDOW_MIN_HEIGHT)
        self.resizable(True, True)

        # Thread-safe UI queue per comunicazione worker->UI
        self._uiq: queue.Queue[Tuple[str, Any]] = queue.Queue()

        # Cancel event e stato download
        self._cancel_event: threading.Event = threading.Event()
        self._is_downloading: bool = False

        # Download queue con thread lock per sicurezza
        self._download_queue: list[Dict[str, str]] = []
        self._queue_lock: threading.Lock = threading.Lock()

        # Inizializza variabili e UI
        self._init_vars()
        self._build_ui()
        self._setup_keyboard_shortcuts()

        # Avvia polling UI queue
        self.after(PERFORMANCE_CONFIG.UI_POLL_INTERVAL_MS, self._drain_ui_queue)

        # Focus sull'input URL
        try:
            self.url_entry.focus_set()
        except (AttributeError, RuntimeError) as e:
            logging.debug(f"Could not set focus: {e}")

        # Imposta stato iniziale (DOPO che UI è costruita)
        self._set_busy(False)

        logging.info("GUI initialized successfully")

    def _init_vars(self) -> None:
        """Inizializza variabili StringVar per binding UI."""
        self.url_var = ctk.StringVar()
        self.format_var = ctk.StringVar(value="video")
        self.quality_preset_var = ctk.StringVar(value=QUALITY_PRESETS[0])
        self.path_var = ctk.StringVar(value=DEFAULT_DOWNLOAD_PATH)
        self.status_var = ctk.StringVar(value=UI_MSG.STATUS_READY)
        self.details_var = ctk.StringVar(value="")

    # ========================================================================
    # UI BUILDING
    # ========================================================================

    def _build_ui(self) -> None:
        """Costruisce l'interfaccia utente completa."""
        self._build_header()
        self._build_url_frame()
        self._build_format_quality()
        self._build_path_frame()
        self._build_actions()
        self._build_queue_and_logs()

    def _build_header(self) -> None:
        """Costruisce header con titolo, versione e bottone update."""
        header = self._create_frame(
            corner_radius=UI_STYLE.FRAME_RADIUS,
            pady=UI_LAYOUT.SECTION_PADDING_Y,
            padx=UI_LAYOUT.SECTION_PADDING_X,
            fill="x"
        )

        # Titolo a sinistra
        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=("Segoe UI", UI_LAYOUT.FONT_TITLE, "bold"),
            text_color=COLORS.TEXT_PRIMARY
        ).pack(side="left", padx=12, pady=10)

        # Container per versione + update button (a destra)
        right_container = ctk.CTkFrame(header, fg_color="transparent")
        right_container.pack(side="right", padx=12, pady=10)

        # Bottone Check Update
        ctk.CTkButton(
            right_container,
            text="🔄 Check Update",
            command=self._check_for_updates,
            width=120,
            height=28,
            corner_radius=14,
            font=("Segoe UI", 11),
            fg_color=COLORS.ACCENT_INFO,
            hover_color=COLORS.PRIMARY
        ).pack(side="right", padx=(10, 0))

        # Versione
        ctk.CTkLabel(
            right_container,
            text=APP_VERSION,
            text_color=COLORS.TEXT_TERTIARY,
            font=("Segoe UI", UI_LAYOUT.FONT_VERSION)
        ).pack(side="right")

    def _build_url_frame(self) -> None:
        """Costruisce frame input URL con bottoni Incolla e Aggiungi."""
        frame = self._create_frame(
            corner_radius=UI_STYLE.FRAME_RADIUS,
            pady=10,
            padx=UI_LAYOUT.SECTION_PADDING_X,
            fill="x"
        )

        # Entry URL
        self.url_entry = ctk.CTkEntry(
            frame,
            textvariable=self.url_var,
            corner_radius=UI_STYLE.ENTRY_RADIUS,
            height=UI_STYLE.BTN_HEIGHT_BIG,
            placeholder_text=UI_MSG.URL_PLACEHOLDER,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL)
        )
        self.url_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        # Bind Enter key su entry
        self.url_entry.bind("<Return>", lambda _: self.add_to_queue())

        # Bottone Incolla
        self.btn_paste = self._mk_btn(
            frame,
            text=UI_MSG.BTN_PASTE,
            width=130,
            height=UI_STYLE.BTN_HEIGHT_BIG,
            radius=UI_STYLE.BTN_RADIUS_BIG,
            command=self.paste_clipboard
        )
        self.btn_paste.pack(side="left", padx=(0, UI_LAYOUT.BUTTON_SPACING), pady=10)

        # Bottone Aggiungi
        self.btn_add = self._mk_btn(
            frame,
            text=UI_MSG.BTN_ADD,
            width=140,
            height=UI_STYLE.BTN_HEIGHT_BIG,
            radius=UI_STYLE.BTN_RADIUS_BIG,
            command=self.add_to_queue,
            fg_color=COLORS.PRIMARY,
            hover_color=COLORS.PRIMARY_HOVER
        )
        self.btn_add.pack(side="left", padx=(0, 10), pady=10)

    def _build_format_quality(self) -> None:
        """Costruisce frame selezione formato (Video/Audio) e qualità."""
        frame = self._create_frame(
            corner_radius=UI_STYLE.FRAME_RADIUS,
            pady=10,
            padx=UI_LAYOUT.SECTION_PADDING_X,
            fill="x"
        )

        # Label Formato
        ctk.CTkLabel(
            frame,
            text=UI_MSG.LBL_FORMAT,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL, "bold"),
            text_color=COLORS.TEXT_PRIMARY
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        # Radio buttons: Video / Audio
        self.rb_video = ctk.CTkRadioButton(
            frame,
            text=FORMAT_OPTIONS[0],  # "Video (MP4)"
            variable=self.format_var,
            value="video",
            command=self._on_format_changed,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL)
        )
        self.rb_video.grid(row=0, column=1, padx=10, pady=(12, 6), sticky="w")

        self.rb_audio = ctk.CTkRadioButton(
            frame,
            text=FORMAT_OPTIONS[1],  # "Audio (MP3)"
            variable=self.format_var,
            value="audio",
            command=self._on_format_changed,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL)
        )
        self.rb_audio.grid(row=0, column=2, padx=10, pady=(12, 6), sticky="w")

        # Label Qualità
        ctk.CTkLabel(
            frame,
            text=UI_MSG.LBL_QUALITY,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL, "bold"),
            text_color=COLORS.TEXT_PRIMARY
        ).grid(row=1, column=0, padx=12, pady=(6, 12), sticky="w")

        # ComboBox qualità
        self.quality_box = ctk.CTkComboBox(
            frame,
            values=list(QUALITY_PRESETS),
            variable=self.quality_preset_var,
            width=280,
            state="readonly",
            corner_radius=UI_STYLE.ENTRY_RADIUS,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL)
        )
        self.quality_box.grid(row=1, column=1, padx=10, pady=(6, 12), sticky="w")

        # Hint qualità
        self.quality_hint = ctk.CTkLabel(
            frame,
            text=UI_MSG.HINT_QUALITY_VIDEO,
            text_color=COLORS.TEXT_TERTIARY,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL)
        )
        self.quality_hint.grid(row=1, column=2, padx=10, pady=(6, 12), sticky="w")

        frame.grid_columnconfigure(3, weight=1)

    def _build_path_frame(self) -> None:
        """Costruisce frame selezione cartella output."""
        frame = self._create_frame(
            corner_radius=UI_STYLE.FRAME_RADIUS,
            pady=10,
            padx=UI_LAYOUT.SECTION_PADDING_X,
            fill="x"
        )

        # Label
        ctk.CTkLabel(
            frame,
            text=UI_MSG.LBL_SAVE_IN,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL, "bold"),
            text_color=COLORS.TEXT_PRIMARY
        ).pack(side="left", padx=12, pady=12)

        # Path display
        self.path_label = ctk.CTkLabel(
            frame,
            textvariable=self.path_var,
            width=520,
            anchor="w",
            text_color=COLORS.TEXT_SECONDARY,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL)
        )
        self.path_label.pack(side="left", padx=10)

        # Bottone Cartella
        self.btn_choose_folder = self._mk_btn(
            frame,
            text=UI_MSG.BTN_FOLDER,
            width=140,
            height=UI_STYLE.BTN_HEIGHT_MED,
            radius=UI_STYLE.BTN_RADIUS_MED,
            command=self.choose_folder
        )
        self.btn_choose_folder.pack(side="right", padx=12)

    def _build_actions(self) -> None:
        """Costruisce frame azioni: Download, Annulla, Progress bar."""
        frame = self._create_frame(
            corner_radius=UI_STYLE.FRAME_RADIUS,
            pady=12,
            padx=UI_LAYOUT.SECTION_PADDING_X,
            fill="x"
        )

        # Bottoni Download e Annulla
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=(UI_LAYOUT.SECTION_PADDING_Y, 8))

        self.btn_start = self._mk_btn(
            btn_frame,
            text=UI_MSG.BTN_DOWNLOAD,
            width=240,
            height=UI_STYLE.BTN_HEIGHT_BIG,
            radius=UI_STYLE.BTN_RADIUS_BIG,
            command=self.start_queue,
            fg_color=COLORS.ACCENT_SUCCESS,
            hover_color="#0EA06E"
        )
        self.btn_start.pack(side="left", padx=UI_LAYOUT.BUTTON_SPACING)

        self.btn_cancel = self._mk_btn(
            btn_frame,
            text=UI_MSG.BTN_CANCEL,
            width=240,
            height=UI_STYLE.BTN_HEIGHT_BIG,
            radius=UI_STYLE.BTN_RADIUS_BIG,
            command=self.cancel_download,
            fg_color=COLORS.ACCENT_ERROR,
            hover_color="#DC2626"
        )
        self.btn_cancel.pack(side="left", padx=UI_LAYOUT.BUTTON_SPACING)

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            frame,
            corner_radius=UI_STYLE.ENTRY_RADIUS,
            height=UI_LAYOUT.PROGRESS_BAR_HEIGHT,
            progress_color=COLORS.PROGRESS_FG
        )
        self.progress.pack(pady=(8, 10), fill="x", padx=20)
        self.progress.set(0)

        # Status e details
        status_row = ctk.CTkFrame(frame, fg_color="transparent")
        status_row.pack(padx=10, pady=(0, UI_LAYOUT.SECTION_PADDING_Y), fill="x")

        self.status_label = ctk.CTkLabel(
            status_row,
            textvariable=self.status_var,
            text_color=COLORS.TEXT_SECONDARY,
            font=("Segoe UI", UI_LAYOUT.FONT_STATUS)
        )
        self.status_label.pack(side="left")

        ctk.CTkLabel(
            status_row,
            textvariable=self.details_var,
            text_color=COLORS.TEXT_TERTIARY,
            font=("Segoe UI", UI_LAYOUT.FONT_LOG)
        ).pack(side="right")

    def _build_queue_and_logs(self) -> None:
        """Costruisce frame con queue download e log box side-by-side."""
        container = self._create_frame(
            corner_radius=UI_STYLE.FRAME_RADIUS,
            pady=10,
            padx=UI_LAYOUT.SECTION_PADDING_X,
            fill="both",
            expand=True
        )

        # === LEFT: Download Queue ===
        left = self._create_frame(
            parent=container,
            corner_radius=UI_STYLE.FRAME_RADIUS,
            side="left",
            padx=10,
            pady=10,
            fill="both",
            expand=True
        )

        ctk.CTkLabel(
            left,
            text=UI_MSG.LBL_QUEUE,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL, "bold"),
            text_color=COLORS.TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(10, 6))

        self.queue_box = ctk.CTkTextbox(
            left,
            height=UI_LAYOUT.QUEUE_BOX_HEIGHT,
            corner_radius=UI_STYLE.ENTRY_RADIUS,
            font=("Consolas", UI_LAYOUT.FONT_LOG)
        )
        self.queue_box.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        self.queue_box.configure(state="disabled")

        # Bottoni queue (devono essere assegnati a self per _set_busy)
        btnrow = ctk.CTkFrame(left, fg_color="transparent")
        btnrow.pack(padx=10, pady=(0, 10), fill="x")

        self.btn_clear_queue = self._mk_btn(
            btnrow,
            text=UI_MSG.BTN_CLEAR_QUEUE,
            height=UI_STYLE.BTN_HEIGHT_SMALL,
            radius=UI_STYLE.BTN_RADIUS_SMALL,
            command=self.clear_queue
        )
        self.btn_clear_queue.pack(side="left")

        self.btn_remove_last = self._mk_btn(
            btnrow,
            text=UI_MSG.BTN_REMOVE_LAST,
            height=UI_STYLE.BTN_HEIGHT_SMALL,
            radius=UI_STYLE.BTN_RADIUS_SMALL,
            command=self.remove_last
        )
        self.btn_remove_last.pack(side="left", padx=(UI_LAYOUT.BUTTON_SPACING, 0))

        # === RIGHT: Log ===
        right = self._create_frame(
            parent=container,
            corner_radius=UI_STYLE.FRAME_RADIUS,
            side="right",
            padx=10,
            pady=10,
            fill="both",
            expand=True
        )

        ctk.CTkLabel(
            right,
            text=UI_MSG.LBL_LOG,
            font=("Segoe UI", UI_LAYOUT.FONT_LABEL, "bold"),
            text_color=COLORS.TEXT_PRIMARY
        ).pack(anchor="w", padx=10, pady=(10, 6))

        self.log_box = ctk.CTkTextbox(
            right,
            corner_radius=UI_STYLE.ENTRY_RADIUS,
            font=("Consolas", UI_LAYOUT.FONT_LOG)
        )
        self.log_box.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        # Bottoni log
        self._build_button_row(
            right,
            [
                (UI_MSG.BTN_COPY_LOG, self.copy_log),
                (UI_MSG.BTN_CLEAR_LOG, self.clear_log),
            ],
            height=UI_STYLE.BTN_HEIGHT_SMALL,
            radius=UI_STYLE.BTN_RADIUS_SMALL
        )

        # Log iniziale
        self._log(UI_MSG.LOG_READY)

    # ========================================================================
    # UI HELPERS
    # ========================================================================

    def _mk_btn(
        self,
        master: ctk.CTkFrame,
        text: str,
        command: Optional[Callable[[], None]] = None,
        width: Optional[int] = None,
        height: int = UI_STYLE.BTN_HEIGHT_MED,
        radius: int = UI_STYLE.BTN_RADIUS_MED,
        fg_color: Optional[str] = None,
        hover_color: Optional[str] = None,
    ) -> ctk.CTkButton:
        """
        Crea un bottone con stile consistente.

        Args:
            master: Parent widget
            text: Testo bottone
            command: Callback click
            width: Larghezza (None per auto)
            height: Altezza
            radius: Corner radius
            fg_color: Colore foreground (None per default)
            hover_color: Colore hover (None per default)

        Returns:
            CTkButton configurato
        """
        return ctk.CTkButton(
            master,
            text=text,
            command=command,
            width=width if width is not None else 0,
            height=height,
            corner_radius=radius,
            fg_color=fg_color,
            hover_color=hover_color,
            font=("Segoe UI", UI_LAYOUT.FONT_BUTTON)
        )

    def _create_frame(
        self,
        parent: Optional[ctk.CTkFrame] = None,
        corner_radius: int = UI_STYLE.FRAME_RADIUS,
        **pack_kwargs: Any
    ) -> ctk.CTkFrame:
        """
        Crea un frame con stile consistente.

        Args:
            parent: Parent widget (default self)
            corner_radius: Corner radius
            **pack_kwargs: Argomenti per pack()

        Returns:
            CTkFrame configurato
        """
        if parent is None:
            parent = self

        frame = ctk.CTkFrame(parent, corner_radius=corner_radius)

        if pack_kwargs:
            frame.pack(**pack_kwargs)

        return frame

    def _build_button_row(
        self,
        parent: ctk.CTkFrame,
        buttons: list[Tuple[str, Callable[[], None]]],
        height: int = UI_STYLE.BTN_HEIGHT_SMALL,
        radius: int = UI_STYLE.BTN_RADIUS_SMALL,
        spacing: int = UI_LAYOUT.BUTTON_SPACING,
    ) -> None:
        """
        Costruisce una riga di bottoni con spacing consistente.

        Args:
            parent: Parent frame
            buttons: Lista di tuple (text, command)
            height: Altezza bottoni
            radius: Corner radius
            spacing: Spacing tra bottoni
        """
        btnrow = ctk.CTkFrame(parent, fg_color="transparent")
        btnrow.pack(padx=10, pady=(0, 10), fill="x")

        for i, (text, command) in enumerate(buttons):
            btn = self._mk_btn(
                btnrow,
                text=text,
                height=height,
                radius=radius,
                command=command
            )
            if i == 0:
                btn.pack(side="left")
            else:
                btn.pack(side="left", padx=(spacing, 0))

    def _setup_keyboard_shortcuts(self) -> None:
        """Configura keyboard shortcuts per azioni comuni."""
        self.bind(KEYBOARD.PASTE, lambda _: self.paste_clipboard())
        self.bind(KEYBOARD.ADD_TO_QUEUE, lambda _: self.add_to_queue())
        self.bind(KEYBOARD.START_DOWNLOAD, lambda _: self.start_queue())
        self.bind(KEYBOARD.CLEAR_QUEUE, lambda _: self.clear_queue())
        self.bind(KEYBOARD.CANCEL, lambda _: self.cancel_download())
        self.bind(KEYBOARD.COPY_LOG, lambda _: self.copy_log())
        self.bind(KEYBOARD.REFRESH, lambda _: self._render_queue())

        logging.info("Keyboard shortcuts configured")

    # ========================================================================
    # RENDERING & DISPLAY
    # ========================================================================

    def _log(self, msg: str) -> None:
        """
        Aggiunge messaggio al log box.

        Args:
            msg: Messaggio da loggare

        Thread safety: Safe da chiamare da main thread
        """
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.see("end")

    def _render_queue(self) -> None:
        """
        Renderizza la download queue nella UI.

        Thread safety: Usa lock per accesso sicuro alla queue
        """
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")

        # Lock per accesso thread-safe
        with self._queue_lock:
            queue_copy = self._download_queue.copy()

        # Render queue (fuori dal lock)
        for i, item in enumerate(queue_copy, start=1):
            title = item.get("title") or UI_MSG.TITLE_UNTITLED
            # Emoji numbers per visual appeal
            number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            emoji = number_emojis[i-1] if i <= 10 else f"{i}."
            self.queue_box.insert("end", f"{emoji} {title}\n")

        self.queue_box.configure(state="disabled")

    def _render_queue_safe(self) -> None:
        """
        Render queue in modo thread-safe (da worker thread).

        Schedula render sul main thread usando after().
        """
        self.after(0, self._render_queue)

    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================

    def _set_busy(self, busy: bool) -> None:
        """
        Imposta stato busy/idle della UI.

        Args:
            busy: True se download in corso, False altrimenti
        """
        self._is_downloading = busy
        state_inputs = "disabled" if busy else "normal"
        state_start = "disabled" if busy else "normal"
        state_cancel = "normal" if busy else "disabled"

        # Disabilita inputs durante download
        self.url_entry.configure(state=state_inputs)
        self.rb_video.configure(state=state_inputs)
        self.rb_audio.configure(state=state_inputs)
        self.btn_paste.configure(state=state_inputs)
        self.btn_add.configure(state=state_inputs)
        self.btn_choose_folder.configure(state=state_inputs)

        # Quality box: disabled se busy o audio mode
        if busy or self.format_var.get() == "audio":
            self.quality_box.configure(state="disabled")
        else:
            self.quality_box.configure(state="readonly")

        # Bottoni azione
        self.btn_start.configure(state=state_start)
        self.btn_cancel.configure(state=state_cancel)
        self.btn_clear_queue.configure(state=state_inputs)
        self.btn_remove_last.configure(state=state_inputs)

    def _update_download_progress(self, data: Dict[str, Any]) -> None:
        """
        Aggiorna progress bar e details con dati download.

        Args:
            data: Dizionario con percent, downloaded, total, speed, eta
        """
        percent = float(data.get("percent", 0.0))
        self.progress.set(max(0.0, min(1.0, percent / 100.0)))
        self.status_var.set(f"⬇️ {percent:.1f}%")

        # Update status color dinamicamente
        color = get_status_color(self.status_var.get())
        self.status_label.configure(text_color=color)

        self.details_var.set(
            f"📊 {data.get('downloaded','?')} / {data.get('total','?')}  |  "
            f"🚀 {data.get('speed','?')}  |  ⏱️ {data.get('eta','--:--')}"
        )

    def _update_status(self, status: str, log: bool = True) -> None:
        """
        Aggiorna status message.

        Args:
            status: Messaggio status
            log: Se True, logga anche il messaggio
        """
        self.status_var.set(status)

        # Update color dinamicamente
        color = get_status_color(status)
        self.status_label.configure(text_color=color)

        if log:
            self._log(status)

    # ========================================================================
    # FORMAT & QUALITY HELPERS
    # ========================================================================

    def _quality_to_ydl_format(self) -> str:
        """
        Converte preset qualità UI in format string yt-dlp.

        Returns:
            Format string per yt-dlp

        Examples:
            >>> # Con "1080p (Full HD)" selezionato
            >>> self._quality_to_ydl_format()
            'bestvideo[height<=1080]+bestaudio/best/best'

            >>> # Con "Best (auto)" selezionato
            >>> self._quality_to_ydl_format()
            'bestvideo+bestaudio/best'
        """
        preset = self.quality_preset_var.get()
        height = get_resolution_height(preset)

        if height:
            return f"bestvideo[height<={height}]+bestaudio/best/best"
        else:
            return "bestvideo+bestaudio/best"

    def _on_format_changed(self) -> None:
        """Callback quando formato (Video/Audio) cambia."""
        if self.format_var.get() == "audio":
            self.quality_box.configure(state="disabled")
            self.quality_hint.configure(text=UI_MSG.HINT_QUALITY_AUDIO_NA)
        else:
            if not self._is_downloading:
                self.quality_box.configure(state="readonly")
            self.quality_hint.configure(text=UI_MSG.HINT_QUALITY_VIDEO)

    # ========================================================================
    # UI QUEUE DRAIN
    # ========================================================================

    def _drain_ui_queue(self) -> None:
        """
        Drena UI queue e processa messaggi da worker thread.

        Chiamato periodicamente via after() per aggiornamenti thread-safe.
        """
        try:
            while True:
                kind, payload = self._uiq.get_nowait()

                if kind == "status":
                    self._update_status(payload, log=False)

                elif kind == "details":
                    self.details_var.set(payload)

                elif kind == "progress":
                    self._update_download_progress(payload)

                elif kind == "log":
                    self._log(payload)

                elif kind == "done":
                    self.progress.set(0)
                    self.details_var.set("")
                    self._set_busy(False)

                elif kind == "show_error":
                    title, msg = payload
                    messagebox.showerror(title, msg)

        except queue.Empty:
            pass

        # Re-schedule
        self.after(PERFORMANCE_CONFIG.UI_POLL_INTERVAL_MS, self._drain_ui_queue)

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    def paste_clipboard(self) -> None:
        """Incolla URL dalla clipboard nell'entry."""
        try:
            text = pyperclip.paste().strip()
            if text:
                self.url_var.set(text)
                self._uiq.put(("log", UI_MSG.LOG_PASTED))
            else:
                self._uiq.put(("log", "Clipboard vuoto."))
        except pyperclip.PyperclipException as e:
            logging.warning(f"Clipboard error: {e}")
            self._uiq.put(("log", UI_MSG.LOG_CLIPBOARD_ERROR))
        except Exception as e:
            logging.exception("Unexpected clipboard error")
            self._uiq.put(("log", f"Errore clipboard: {e}"))

    def choose_folder(self) -> None:
        """Apre dialog per selezione cartella output."""
        folder = filedialog.askdirectory(
            title="Scegli cartella di destinazione",
            initialdir=self.path_var.get()
        )
        if folder:
            self.path_var.set(folder)
            self._uiq.put(("log", UI_MSG.LOG_OUTPUT_FOLDER.format(folder)))
            logging.info(f"Output folder changed to: {folder}")

    def copy_log(self) -> None:
        """Copia contenuto log in clipboard."""
        try:
            text = self.log_box.get("1.0", "end").strip()
            if text:
                pyperclip.copy(text)
                self._log(UI_MSG.LOG_LOG_COPIED)
            else:
                self._log("Log vuoto.")
        except pyperclip.PyperclipException as e:
            logging.warning(f"Clipboard error copying log: {e}")
            self._log(UI_MSG.LOG_CANNOT_COPY)
        except Exception as e:
            logging.exception("Unexpected error copying log")
            self._log(f"Errore: {e}")

    def clear_log(self) -> None:
        """Pulisce log box."""
        self.log_box.delete("1.0", "end")
        logging.info("Log cleared")

    # ========================================================================
    # QUEUE MANAGEMENT
    # ========================================================================

    def add_to_queue(self) -> None:
        """
        Aggiunge URL dalla entry alla download queue.

        Valida URL, aggiunge alla queue, e spawna thread per fetch titolo.
        """
        if self._is_downloading:
            self._uiq.put(("log", UI_MSG.LOG_DOWNLOAD_IN_PROGRESS))
            return

        url = (self.url_var.get() or "").strip()

        # Validazione
        if not url:
            messagebox.showwarning(UI_MSG.WARN_URL_MISSING, UI_MSG.WARN_URL_MISSING_MSG)
            return

        if not is_valid_url(url):
            messagebox.showerror(UI_MSG.ERR_INVALID_URL, UI_MSG.ERR_INVALID_URL_MSG)
            return

        # Aggiungi alla queue (thread-safe)
        item = {"url": url, "title": UI_MSG.TITLE_LOADING}

        with self._queue_lock:
            self._download_queue.append(item)

        self._render_queue()
        self.url_var.set("")
        self._uiq.put(("log", UI_MSG.LOG_ADDED_TO_QUEUE))

        # Fetch titolo in background
        threading.Thread(
            target=self._fetch_title_worker,
            args=(item,),
            daemon=True,
            name="TitleFetchThread"
        ).start()

        logging.info(f"Added to queue: {url}")

    def clear_queue(self) -> None:
        """Svuota la download queue (thread-safe)."""
        with self._queue_lock:
            self._download_queue.clear()

        self._render_queue()
        self._uiq.put(("log", UI_MSG.LOG_QUEUE_CLEARED))
        logging.info("Queue cleared")

    def remove_last(self) -> None:
        """Rimuove ultimo elemento dalla queue (thread-safe)."""
        with self._queue_lock:
            if self._download_queue:
                removed = self._download_queue.pop()
                logging.info(f"Removed from queue: {removed.get('url', 'unknown')}")

        self._render_queue()
        self._uiq.put(("log", UI_MSG.LOG_REMOVED_LAST))

    # ========================================================================
    # DOWNLOAD LOGIC
    # ========================================================================

    def start_queue(self) -> None:
        """Avvia download di tutti gli elementi in queue."""
        if self._is_downloading:
            return

        # Se queue vuota ma c'è URL nell'entry, aggiungilo
        with self._queue_lock:
            queue_empty = len(self._download_queue) == 0

        if queue_empty:
            if (self.url_var.get() or "").strip():
                self.add_to_queue()
            else:
                messagebox.showinfo(UI_MSG.INFO_NOTHING_TO_DO, UI_MSG.INFO_NOTHING_TO_DO_MSG)
                return

        # Reset cancel event e imposta busy
        self._cancel_event.clear()
        self._set_busy(True)
        self._uiq.put(("status", UI_MSG.STATUS_READY))
        self._uiq.put(("details", ""))

        # Spawna worker thread
        threading.Thread(
            target=self._queue_worker,
            daemon=True,
            name="DownloadWorkerThread"
        ).start()

        logging.info("Download queue started")

    def cancel_download(self) -> None:
        """Richiede cancellazione download corrente."""
        if self._is_downloading:
            self._cancel_event.set()
            self._uiq.put(("log", UI_MSG.LOG_CANCEL_REQUESTED))
            logging.info("Download cancellation requested")

    # ========================================================================
    # BACKGROUND WORKERS
    # ========================================================================

    def _fetch_title_worker(self, item: Dict[str, str]) -> None:
        """
        Worker thread per fetch titolo video.

        Args:
            item: Dict con "url" key, verrà aggiornato con "title"

        Note:
            Aggiorna item dict in-place e triggera UI re-render
        """
        try:
            import yt_dlp

            url = item["url"]

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
                "socket_timeout": PERFORMANCE_CONFIG.TITLE_FETCH_TIMEOUT,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get("title") or url
            item["title"] = title
            self.after(0, self._render_queue)

            logging.info(f"Fetched title: {title}")

        except yt_dlp.utils.DownloadError as e:
            logging.warning(f"Failed to fetch title for {item['url']}: {e}")
            item["title"] = item.get("title") or item["url"]
            self.after(0, self._render_queue)

        except Exception as e:
            logging.exception(f"Unexpected error fetching title for {item['url']}")
            item["title"] = item.get("title") or item["url"]
            self.after(0, self._render_queue)

    def _queue_worker(self) -> None:
        """
        Worker thread principale per processare download queue.

        Itera sulla queue e scarica ogni elemento sequenzialmente.
        Comunica con UI via UI queue (thread-safe).
        """
        try:
            while True:
                # Check cancellazione
                if self._cancel_event.is_set():
                    break

                # Pop item dalla queue (thread-safe)
                with self._queue_lock:
                    if not self._download_queue:
                        break
                    item = self._download_queue.pop(0)

                # Estrai info
                url = item["url"]
                title = item.get("title", url)
                self._uiq.put(("log", UI_MSG.LOG_DOWNLOADING.format(title)))
                self._render_queue_safe()

                # Parametri download
                mode = self.format_var.get()
                out_dir = self.path_var.get()
                ydl_format = self._quality_to_ydl_format()

                # Callbacks
                def on_progress(data: Dict[str, Any]) -> None:
                    self._uiq.put(("progress", data))

                def on_status(msg: str) -> None:
                    self._uiq.put(("status", msg))
                    self._uiq.put(("log", msg))

                # Download
                try:
                    download_video(
                        url=url,
                        mode=mode,
                        quality=ydl_format,
                        output_path=out_dir,
                        progress_cb=on_progress,
                        status_cb=on_status,
                        cancel_event=self._cancel_event,
                    )
                except DownloadCancelledError:
                    # Cancellazione: esci dal loop
                    logging.info("Download cancelled, exiting worker")
                    break
                except Exception as e:
                    # Errore: logga e continua con prossimo
                    logging.exception(f"Error downloading {url}")
                    self._uiq.put(("log", f"❌ Errore: {e}"))
                    continue

            # Fine queue
            if self._cancel_event.is_set():
                self._uiq.put(("status", UI_MSG.STATUS_CANCELLED))
                self._uiq.put(("log", UI_MSG.LOG_QUEUE_CANCELLED))
            else:
                self._uiq.put(("status", UI_MSG.STATUS_COMPLETE))
                self._uiq.put(("log", UI_MSG.LOG_ALL_COMPLETE))

        except Exception as e:
            logging.exception("Unexpected error in queue worker")
            self._uiq.put(("status", UI_MSG.STATUS_ERROR.format(str(e))))
            self._uiq.put(("log", f"❌ Errore fatale: {e}"))
            self._uiq.put(("show_error", ("Errore", str(e))))

        finally:
            self._uiq.put(("done", None))
            logging.info("Queue worker terminated")

    # ========================================================================
    # AUTO-UPDATE SYSTEM
    # ========================================================================

    def _check_for_updates(self) -> None:
        """
        Controlla se è disponibile un aggiornamento e mostra dialog.

        Eseguito in background thread per non bloccare UI.
        """
        def check_worker():
            try:
                logging.info("Checking for updates...")
                update_info = updater.check_for_updates()

                if update_info:
                    # Update disponibile - mostra dialog
                    self.after(0, lambda: self._show_update_dialog(update_info))
                else:
                    # Nessun update - mostra messaggio
                    self.after(0, lambda: messagebox.showinfo(
                        "✅ Aggiornato",
                        f"Stai già usando l'ultima versione!\n\n"
                        f"Versione corrente: {updater.get_current_version()}"
                    ))

            except updater.UpdateCheckError as e:
                logging.error(f"Update check failed: {e}")
                self.after(0, lambda: messagebox.showerror(
                    "❌ Errore",
                    f"Impossibile controllare aggiornamenti:\n\n{str(e)}\n\n"
                    f"Verifica la connessione internet e riprova."
                ))
            except Exception as e:
                logging.exception("Unexpected error checking updates")
                self.after(0, lambda: messagebox.showerror(
                    "❌ Errore",
                    f"Errore imprevisto:\n\n{str(e)}"
                ))

        # Esegui in background thread
        threading.Thread(target=check_worker, daemon=True).start()

    def _show_update_dialog(self, update_info: Dict[str, Any]) -> None:
        """
        Mostra dialog con info aggiornamento disponibile.

        Args:
            update_info: Dictionary con info update da updater.check_for_updates()
        """
        version = update_info['version']
        changelog = update_info['changelog']
        size_mb = update_info['asset_size'] / 1024 / 1024

        # Crea dialog custom
        dialog = ctk.CTkToplevel(self)
        dialog.title("🔄 Aggiornamento Disponibile")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (600 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color=COLORS.PRIMARY)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header_frame,
            text=f"🎉 Nuova Versione Disponibile: v{version}",
            font=("Segoe UI", 16, "bold"),
            text_color="white"
        ).pack(pady=15)

        # Info frame
        info_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            info_frame,
            text=f"📦 Dimensione: {size_mb:.1f} MB",
            font=("Segoe UI", 12),
            anchor="w"
        ).pack(fill="x", pady=5)

        ctk.CTkLabel(
            info_frame,
            text="📝 Novità:",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(15, 5))

        # Changelog scrollable
        changelog_text = ctk.CTkTextbox(
            info_frame,
            height=250,
            font=("Segoe UI", 11),
            wrap="word"
        )
        changelog_text.pack(fill="both", expand=True, pady=(0, 10))
        changelog_text.insert("1.0", changelog)
        changelog_text.configure(state="disabled")

        # Buttons frame
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="⬇️ Scarica e Installa",
            command=lambda: [dialog.destroy(), self._download_and_apply_update(update_info)],
            width=200,
            height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS.PRIMARY,
            hover_color=COLORS.PRIMARY_HOVER
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="❌ Più Tardi",
            command=dialog.destroy,
            width=120,
            height=40,
            font=("Segoe UI", 13),
            fg_color=COLORS.ACCENT_ERROR,
            hover_color="#CC0000"
        ).pack(side="left")

    def _download_and_apply_update(self, update_info: Dict[str, Any]) -> None:
        """
        Scarica e applica l'aggiornamento.

        Args:
            update_info: Dictionary con info update
        """
        def download_worker():
            try:
                # Progress dialog
                progress_dialog = None

                def show_progress():
                    nonlocal progress_dialog
                    progress_dialog = ctk.CTkToplevel(self)
                    progress_dialog.title("⬇️ Download Update")
                    progress_dialog.geometry("400x150")
                    progress_dialog.resizable(False, False)
                    progress_dialog.transient(self)
                    progress_dialog.grab_set()

                    # Center
                    progress_dialog.update_idletasks()
                    x = self.winfo_x() + (self.winfo_width() // 2) - 200
                    y = self.winfo_y() + (self.winfo_height() // 2) - 75
                    progress_dialog.geometry(f"+{x}+{y}")

                    ctk.CTkLabel(
                        progress_dialog,
                        text="Downloading update...",
                        font=("Segoe UI", 14)
                    ).pack(pady=(20, 10))

                    progress_bar = ctk.CTkProgressBar(progress_dialog, width=350)
                    progress_bar.pack(pady=10)
                    progress_bar.set(0)

                    progress_label = ctk.CTkLabel(
                        progress_dialog,
                        text="0%",
                        font=("Segoe UI", 11)
                    )
                    progress_label.pack(pady=5)

                    return progress_dialog, progress_bar, progress_label

                # Mostra progress dialog
                self.after(0, show_progress)

                # Wait for dialog creation
                import time
                time.sleep(0.2)

                # Progress callback
                def on_progress(current, total):
                    if total > 0:
                        percent = (current / total) * 100
                        self.after(0, lambda: progress_dialog and (
                            getattr(progress_dialog, 'children', {}).get('!ctkprogressbar', None) and
                            getattr(progress_dialog, 'children', {})['!ctkprogressbar'].set(current / total),
                            getattr(progress_dialog, 'children', {}).get('!ctklabel2', None) and
                            getattr(progress_dialog, 'children', {})['!ctklabel2'].configure(text=f"{percent:.0f}%")
                        ))

                # Download update
                logging.info(f"Downloading update: {update_info['asset_name']}")
                installer_path = updater.download_update(
                    update_info['download_url'],
                    update_info['asset_name'],
                    progress_callback=on_progress
                )

                # Close progress dialog
                def close_and_apply():
                    if progress_dialog:
                        progress_dialog.destroy()

                    # Conferma installazione
                    result = messagebox.askyesno(
                        "✅ Download Completato",
                        f"Update scaricato con successo!\n\n"
                        f"L'applicazione verrà chiusa per installare l'aggiornamento.\n\n"
                        f"Continuare?",
                        icon="question"
                    )

                    if result:
                        try:
                            # Applica update (chiuderà l'app)
                            updater.apply_update(installer_path)
                        except Exception as e:
                            logging.error(f"Failed to apply update: {e}")
                            messagebox.showerror(
                                "❌ Errore",
                                f"Impossibile applicare l'aggiornamento:\n\n{str(e)}\n\n"
                                f"File scaricato in:\n{installer_path}\n\n"
                                f"Puoi installarlo manualmente."
                            )

                self.after(0, close_and_apply)

            except updater.UpdateDownloadError as e:
                logging.error(f"Update download failed: {e}")
                self.after(0, lambda: (
                    progress_dialog and progress_dialog.destroy(),
                    messagebox.showerror(
                        "❌ Errore Download",
                        f"Impossibile scaricare l'aggiornamento:\n\n{str(e)}"
                    )
                ))
            except Exception as e:
                logging.exception("Unexpected error downloading update")
                self.after(0, lambda: (
                    progress_dialog and progress_dialog.destroy(),
                    messagebox.showerror(
                        "❌ Errore",
                        f"Errore imprevisto:\n\n{str(e)}"
                    )
                ))

        # Esegui in background thread
        threading.Thread(target=download_worker, daemon=True).start()
