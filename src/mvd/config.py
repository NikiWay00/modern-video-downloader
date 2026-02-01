"""
Configurazione centralizzata per Modern Video Downloader.

Questo modulo contiene tutte le configurazioni, costanti e messaggi
utilizzati nell'applicazione, eliminando valori hard-coded.
"""

import os
from dataclasses import dataclass
from typing import Final

# ============================================================================
# METADATA APPLICAZIONE
# ============================================================================

APP_TITLE: Final[str] = "Modern Easy Video Downloader"
APP_VERSION: Final[str] = "v0.4.1"
APP_AUTHOR: Final[str] = "Nicolò La Cognata"

# ============================================================================
# PATHS
# ============================================================================

DEFAULT_DOWNLOAD_PATH: Final[str] = os.path.join(os.path.expanduser("~"), "Downloads")

# ============================================================================
# CONFIGURAZIONE UI - STILE
# ============================================================================

@dataclass(frozen=True)
class UIStyle:
    """Configurazione stile UI: dimensioni, bordi, colori."""

    # Border radius (arrotondamenti)
    BTN_RADIUS_SMALL: int = 14
    BTN_RADIUS_MED: int = 18
    BTN_RADIUS_BIG: int = 22
    ENTRY_RADIUS: int = 18
    FRAME_RADIUS: int = 16

    # Altezze bottoni
    BTN_HEIGHT_SMALL: int = 34
    BTN_HEIGHT_MED: int = 38
    BTN_HEIGHT_BIG: int = 44

    # Colori testo (vecchi per compatibilità)
    COLOR_TEXT_GRAY: str = "#888888"
    COLOR_TEXT_LIGHT_GRAY: str = "#aaaaaa"


@dataclass(frozen=True)
class ColorScheme:
    """Schema colori moderno per l'applicazione."""

    # Primary colors (blu vibrante)
    PRIMARY: str = "#1E90FF"  # Dodger Blue
    PRIMARY_HOVER: str = "#1873CC"
    PRIMARY_DARK: str = "#155A99"

    # Accent colors (stato)
    ACCENT_SUCCESS: str = "#10B981"  # Verde - operazione riuscita
    ACCENT_ERROR: str = "#EF4444"    # Rosso - errore
    ACCENT_WARNING: str = "#F59E0B"  # Arancione - attenzione
    ACCENT_INFO: str = "#3B82F6"     # Blu - informazione

    # Backgrounds
    BG_DARK: str = "#1A1A1A"
    BG_MEDIUM: str = "#2D2D2D"
    BG_LIGHT: str = "#3D3D3D"
    BG_LIGHTER: str = "#4A4A4A"

    # Text colors
    TEXT_PRIMARY: str = "#FFFFFF"
    TEXT_SECONDARY: str = "#AAAAAA"
    TEXT_TERTIARY: str = "#888888"
    TEXT_MUTED: str = "#666666"

    # Progress bar
    PROGRESS_BG: str = "#2D2D2D"
    PROGRESS_FG: str = "#1E90FF"
    PROGRESS_SUCCESS: str = "#10B981"
    PROGRESS_ERROR: str = "#EF4444"

    # Borders
    BORDER_SUBTLE: str = "#3D3D3D"
    BORDER_MEDIUM: str = "#4A4A4A"


@dataclass(frozen=True)
class UILayout:
    """Configurazione layout e dimensioni UI."""

    # Finestra principale
    WINDOW_WIDTH: int = 900  # Aumentato da 850 per più respiro
    WINDOW_HEIGHT: int = 850  # Aumentato da 810
    WINDOW_MIN_WIDTH: int = 750
    WINDOW_MIN_HEIGHT: int = 700

    # Padding e spacing
    SECTION_PADDING_X: int = 20  # Aumentato da 16
    SECTION_PADDING_Y: int = 14  # Aumentato da 12
    BUTTON_SPACING: int = 10     # Aumentato da 8
    FRAME_SPACING: int = 12      # Spacing tra frames

    # Altezze componenti
    QUEUE_BOX_HEIGHT: int = 180  # Aumentato da 170
    LOG_BOX_HEIGHT: int = 180    # Aumentato da default
    PROGRESS_BAR_HEIGHT: int = 24  # Più alta per visibilità

    # Font sizes
    FONT_TITLE: int = 20
    FONT_VERSION: int = 12
    FONT_LABEL: int = 13
    FONT_BUTTON: int = 12
    FONT_STATUS: int = 14
    FONT_LOG: int = 11

    # Risoluzioni video
    RESOLUTION_2160P: int = 2160  # 4K
    RESOLUTION_1440P: int = 1440  # 2K
    RESOLUTION_1080P: int = 1080  # Full HD
    RESOLUTION_720P: int = 720    # HD
    RESOLUTION_480P: int = 480    # SD


# ============================================================================
# CONFIGURAZIONE YT-DLP
# ============================================================================

@dataclass(frozen=True)
class YTDLPConfig:
    """Configurazione per yt-dlp downloader."""

    # User-Agent per evitare blocchi
    USER_AGENTS: tuple[str, ...] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36",

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36",

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) "
        "Gecko/20100101 Firefox/123.0",
    )

    # HTTP Headers
    HTTP_HEADERS: dict = None  # Inizializzato dopo __post_init__

    # Retry e timeout
    RETRIES: int = 10
    FRAGMENT_RETRIES: int = 10
    SOCKET_TIMEOUT: int = 30  # secondi

    # Performance
    CONCURRENT_FRAGMENTS: int = 4  # Aumentato da 1 per velocità 4x
    HTTP_CHUNK_SIZE: int = 10485760  # 10 MB chunks per ottimizzazione

    # Audio settings
    AUDIO_BITRATE: str = "192k"
    AUDIO_FORMAT: str = "mp3"
    AUDIO_QUALITY: str = "192"  # Per postprocessor

    # Cookie sources (in ordine di priorità)
    COOKIE_BROWSERS: tuple[str, ...] = ("chrome", "firefox", "edge")

    def __post_init__(self):
        # Workaround per immutabilità e dict
        object.__setattr__(self, 'HTTP_HEADERS', {
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "*/*",
            "Referer": "https://www.youtube.com/",
        })


# ============================================================================
# CONFIGURAZIONE PERFORMANCE
# ============================================================================

@dataclass(frozen=True)
class PerformanceConfig:
    """Configurazione performance e threading."""

    UI_POLL_INTERVAL_MS: int = 80  # Polling interval per UI queue (ms)
    TITLE_FETCH_TIMEOUT: int = 10  # Timeout fetch titolo video (secondi)
    PROGRESS_UPDATE_INTERVAL: float = 0.1  # Debounce progress updates (100ms)
    DOWNLOAD_CHUNK_SIZE: int = 1048576  # 1MB chunk size


# ============================================================================
# CONFIGURAZIONE LOGGING
# ============================================================================

@dataclass(frozen=True)
class LogConfig:
    """Configurazione logging."""

    LOG_DIR_NAME: str = "ModernVideoDownloader"
    LOG_FILE_NAME: str = "app.log"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_LEVEL: str = "INFO"

    # Rotating file handler settings
    LOG_MAX_BYTES: int = 10485760  # 10 MB
    LOG_BACKUP_COUNT: int = 3  # Mantieni 3 backup


# ============================================================================
# PRESET QUALITÀ
# ============================================================================

QUALITY_PRESETS: Final[tuple[str, ...]] = (
    "Best (auto)",
    "2160p (4K)",
    "1440p (2K)",
    "1080p (Full HD)",
    "720p (HD)",
    "480p",
)

FORMAT_VIDEO: Final[str] = "Video (MP4)"
FORMAT_AUDIO: Final[str] = "Audio (MP3)"

FORMAT_OPTIONS: Final[tuple[str, str]] = (
    FORMAT_VIDEO,
    FORMAT_AUDIO,
)


# ============================================================================
# MESSAGGI UI (ITALIANO)
# ============================================================================

@dataclass(frozen=True)
class UIMessages:
    """Tutti i messaggi e testi dell'interfaccia utente."""

    # ========== Placeholders ==========
    URL_PLACEHOLDER: str = "Incolla qui il link..."

    # ========== Bottoni ==========
    BTN_PASTE: str = "📋 Incolla"
    BTN_ADD: str = "➕ Aggiungi"
    BTN_DOWNLOAD: str = "⬇️ Download"
    BTN_CANCEL: str = "❌ Annulla"
    BTN_CLEAR_QUEUE: str = "🗑️ Svuota"
    BTN_REMOVE_LAST: str = "⬅️ Rimuovi ultimo"
    BTN_COPY_LOG: str = "📄 Copia log"
    BTN_CLEAR_LOG: str = "🧹 Pulisci log"
    BTN_FOLDER: str = "📁 Cartella"

    # ========== Labels ==========
    LBL_FORMAT: str = "Formato"
    LBL_QUALITY: str = "Qualità"
    LBL_SAVE_IN: str = "Salva in"
    LBL_QUEUE: str = "Coda download"
    LBL_LOG: str = "Log"

    # ========== Status Messages ==========
    STATUS_READY: str = "⏳ In attesa di un download"
    STATUS_DOWNLOADING: str = "⬇️ Download in corso..."
    STATUS_PROCESSING: str = "⚙️ Elaborazione file..."
    STATUS_COMPLETE: str = "✅ Download completato!"
    STATUS_CANCELLED: str = "❌ Download annullato."
    STATUS_ERROR: str = "❌ Errore: {}"

    # ========== Log Messages ==========
    LOG_READY: str = "Pronto. Incolla un URL e premi 'Aggiungi' oppure INVIO."
    LOG_PASTED: str = "Incollato da clipboard."
    LOG_CLIPBOARD_ERROR: str = "Clipboard non disponibile."
    LOG_ADDED_TO_QUEUE: str = "Aggiunto alla coda. Recupero titolo..."
    LOG_QUEUE_CLEARED: str = "Coda svuotata."
    LOG_REMOVED_LAST: str = "Rimosso ultimo elemento dalla coda."
    LOG_CANCEL_REQUESTED: str = "Richiesto annullamento..."
    LOG_DOWNLOADING: str = "Download: {}"
    LOG_ALL_COMPLETE: str = "✅ Tutti i download completati!"
    LOG_QUEUE_CANCELLED: str = "❌ Coda annullata."
    LOG_LOG_COPIED: str = "Log copiato in clipboard."
    LOG_CANNOT_COPY: str = "Impossibile copiare il log."
    LOG_OUTPUT_FOLDER: str = "Output: {}"
    LOG_DOWNLOAD_IN_PROGRESS: str = "Download in corso: attendi la fine o annulla."

    # ========== Warnings/Errors ==========
    WARN_URL_MISSING: str = "URL mancante"
    WARN_URL_MISSING_MSG: str = "Incolla un URL."
    ERR_INVALID_URL: str = "URL non valido"
    ERR_INVALID_URL_MSG: str = "Inserisci un URL valido (http/https)."
    INFO_NOTHING_TO_DO: str = "Niente da fare"
    INFO_NOTHING_TO_DO_MSG: str = "Aggiungi almeno un URL alla coda."
    ERR_FFMPEG_NOT_FOUND: str = "FFmpeg non trovato. Controlla che esista: {}"

    # ========== Hints ==========
    HINT_QUALITY_VIDEO: str = "(Qualità video selezionata)"
    HINT_QUALITY_AUDIO: str = "(MP3: estrazione audio con FFmpeg)"
    HINT_QUALITY_AUDIO_NA: str = "(Per MP3 la qualità video non conta)"

    # ========== Altri ==========
    TITLE_LOADING: str = "(Caricamento titolo...)"
    TITLE_UNTITLED: str = "(senza titolo)"

    # ========== Tooltips (per feature futura) ==========
    TOOLTIP_PASTE: str = "Incolla URL dalla clipboard (oppure usa Ctrl+V)"
    TOOLTIP_ADD: str = "Aggiungi URL alla coda (oppure premi Invio)"
    TOOLTIP_QUALITY: str = "Seleziona la risoluzione video desiderata"
    TOOLTIP_FORMAT: str = "MP4 per video completo, MP3 per solo audio"
    TOOLTIP_FOLDER: str = "Scegli la cartella di destinazione"
    TOOLTIP_DOWNLOAD: str = "Avvia il download di tutti gli elementi in coda"
    TOOLTIP_CANCEL: str = "Interrompi il download corrente"


# ============================================================================
# CONFIGURAZIONE SETTINGS PERSISTENCE
# ============================================================================

@dataclass(frozen=True)
class SettingsConfig:
    """Configurazione per salvataggio persistente delle impostazioni utente."""

    SETTINGS_DIR_NAME: str = "ModernVideoDownloader"
    SETTINGS_FILE_NAME: str = "settings.json"

    # Default values
    DEFAULT_FORMAT: str = FORMAT_VIDEO
    DEFAULT_QUALITY: str = "Best (auto)"
    DEFAULT_WINDOW_SIZE: tuple[int, int] = (900, 850)


# ============================================================================
# KEYBOARD SHORTCUTS
# ============================================================================

@dataclass(frozen=True)
class KeyboardShortcuts:
    """Configurazione keyboard shortcuts."""

    PASTE: str = "<Control-v>"
    ADD_TO_QUEUE: str = "<Control-Return>"
    START_DOWNLOAD: str = "<Control-d>"
    CLEAR_QUEUE: str = "<Control-q>"
    CANCEL: str = "<Escape>"
    COPY_LOG: str = "<Control-l>"
    REFRESH: str = "<F5>"


# ============================================================================
# ISTANZE SINGLETON
# ============================================================================

# Crea istanze singleton per uso globale
UI_STYLE = UIStyle()
COLORS = ColorScheme()
UI_LAYOUT = UILayout()
YTDLP_CONFIG = YTDLPConfig()
YTDLP_CONFIG.__post_init__()  # Inizializza HTTP_HEADERS
PERFORMANCE_CONFIG = PerformanceConfig()
LOG_CONFIG = LogConfig()
UI_MSG = UIMessages()
SETTINGS_CONFIG = SettingsConfig()
KEYBOARD = KeyboardShortcuts()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_agent(index: int = 0) -> str:
    """
    Ottieni User-Agent dalla lista (con rotation).

    Args:
        index: Indice User-Agent (default 0)

    Returns:
        User-Agent string
    """
    return YTDLP_CONFIG.USER_AGENTS[index % len(YTDLP_CONFIG.USER_AGENTS)]


def get_resolution_height(preset: str) -> int | None:
    """
    Estrai altezza risoluzione da preset qualità.

    Args:
        preset: Preset qualità (es. "1080p (Full HD)")

    Returns:
        Altezza risoluzione o None se "Best (auto)"

    Examples:
        >>> get_resolution_height("1080p (Full HD)")
        1080
        >>> get_resolution_height("Best (auto)")
        None
    """
    preset_lower = preset.lower()

    resolution_map = {
        "2160": UI_LAYOUT.RESOLUTION_2160P,
        "1440": UI_LAYOUT.RESOLUTION_1440P,
        "1080": UI_LAYOUT.RESOLUTION_1080P,
        "720": UI_LAYOUT.RESOLUTION_720P,
        "480": UI_LAYOUT.RESOLUTION_480P,
    }

    for key, height in resolution_map.items():
        if key in preset_lower:
            return height

    return None


def get_status_color(status: str) -> str:
    """
    Ottieni colore per status message.

    Args:
        status: Status message

    Returns:
        Colore hex
    """
    if "✅" in status or "completato" in status.lower():
        return COLORS.ACCENT_SUCCESS
    elif "❌" in status or "errore" in status.lower() or "annullato" in status.lower():
        return COLORS.ACCENT_ERROR
    elif "⬇️" in status or "download" in status.lower():
        return COLORS.PRIMARY
    elif "⏳" in status or "attesa" in status.lower():
        return COLORS.TEXT_SECONDARY
    else:
        return COLORS.TEXT_PRIMARY
