"""
Utility functions per Modern Video Downloader.

Questo modulo fornisce funzioni helper per path management, logging,
validazione input, e formattazione dati.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse
from typing import Tuple, Optional

from .config import LOG_CONFIG
from .exceptions import InvalidPathError, InvalidURLError


# ============================================================================
# PATH RISORSE (DEV + EXE)
# ============================================================================

def resource_path(relative_path: str) -> str:
    """
    Restituisce il path corretto per risorse (icone, ffmpeg, asset).

    Funziona sia in sviluppo che in esecuzione come EXE PyInstaller.
    In modalità EXE, usa sys._MEIPASS fornito da PyInstaller.
    In modalità sviluppo, risale alla root del progetto.

    Args:
        relative_path: Path relativo alla root del progetto (es. "assets/logo.ico")

    Returns:
        Path assoluto alla risorsa

    Examples:
        >>> resource_path("ffmpeg/bin")
        'C:\\path\\to\\project\\ffmpeg\\bin'

        >>> resource_path("assets/logo.ico")
        'C:\\path\\to\\project\\assets\\logo.ico'

    Note:
        In modalità PyInstaller, sys._MEIPASS punta alla directory temporanea
        dove PyInstaller estrae i file compressi.
    """
    try:
        # PyInstaller (EXE): usa directory temporanea _MEIPASS
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # Sviluppo: risali alla root del progetto (fuori da src/mvd/)
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    full_path = os.path.join(base_path, relative_path)

    # In modalità produzione, verifica che la risorsa esista
    if hasattr(sys, '_MEIPASS') and not os.path.exists(full_path):
        logging.warning(f"Resource not found: {relative_path}")

    return full_path


# ============================================================================
# SETUP FFMPEG
# ============================================================================

def setup_ffmpeg() -> bool:
    """
    Cerca ffmpeg/bin e lo aggiunge al PATH di sistema.

    Cerca la directory ffmpeg/bin relativa al progetto e, se trovata,
    la aggiunge al PATH dell'ambiente corrente. Questo permette a yt-dlp
    e altri tool di trovare FFmpeg automaticamente.

    Returns:
        True se FFmpeg è stato trovato e aggiunto al PATH, False altrimenti

    Examples:
        >>> setup_ffmpeg()
        True  # FFmpeg trovato e aggiunto al PATH

        >>> setup_ffmpeg()
        False  # FFmpeg directory non trovata

    Note:
        Modifica os.environ["PATH"] per la sessione corrente.
        Non modifica il PATH di sistema in modo permanente.
    """
    ffmpeg_bin = resource_path("ffmpeg/bin")

    if os.path.isdir(ffmpeg_bin):
        # Verifica se già presente nel PATH
        current_path = os.environ.get("PATH", "")
        if ffmpeg_bin not in current_path:
            # Prepend per priorità (aggiunto all'inizio)
            os.environ["PATH"] = ffmpeg_bin + os.pathsep + current_path
            logging.info(f"Added FFmpeg to PATH: {ffmpeg_bin}")
        return True

    logging.warning(f"FFmpeg directory not found: {ffmpeg_bin}")
    return False


# ============================================================================
# LOGGER CONFIGURATION
# ============================================================================

def setup_logger(
    log_file: str = LOG_CONFIG.LOG_FILE_NAME,
    max_bytes: int = LOG_CONFIG.LOG_MAX_BYTES,
    backup_count: int = LOG_CONFIG.LOG_BACKUP_COUNT
) -> None:
    """
    Configura il logger dell'applicazione con rotating file handler.

    Crea un logger che scrive su file con rotazione automatica quando
    raggiunge la dimensione massima. I file di log vengono salvati in
    %APPDATA%\\ModernVideoDownloader su Windows, o ~/ su altri sistemi.

    Args:
        log_file: Nome del file di log (default da config)
        max_bytes: Dimensione massima del file prima della rotazione (default 10MB)
        backup_count: Numero di file di backup da mantenere (default 3)

    Examples:
        >>> setup_logger()
        # Crea app.log in %APPDATA%\\ModernVideoDownloader

        >>> setup_logger("debug.log", max_bytes=5*1024*1024, backup_count=5)
        # Crea debug.log con max 5MB e 5 backup

    Note:
        - In modalità sviluppo (non _MEIPASS), logga anche su console
        - Usa encoding UTF-8 per supportare caratteri speciali
        - Formato: "YYYY-MM-DD HH:MM:SS | LEVEL | Message"
    """
    # Determina directory di log
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    log_dir = os.path.join(appdata, LOG_CONFIG.LOG_DIR_NAME)

    # Crea directory se non esiste
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create log directory: {e}")
        return

    log_path = os.path.join(log_dir, log_file)

    # Crea rotating file handler
    try:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}")
        return

    # Formato log
    formatter = logging.Formatter(
        LOG_CONFIG.LOG_FORMAT,
        datefmt=LOG_CONFIG.LOG_DATE_FORMAT
    )
    file_handler.setFormatter(formatter)

    # Configura root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_CONFIG.LOG_LEVEL))
    logger.addHandler(file_handler)

    # In modalità sviluppo, aggiungi anche console handler
    if not hasattr(sys, '_MEIPASS'):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logging.info("Logger initialized (development mode with console output)")
    else:
        logging.info("Logger initialized (production mode)")

    logging.info(f"Log file: {log_path}")


# ============================================================================
# VALIDAZIONE INPUT
# ============================================================================

def is_valid_url(url: str) -> bool:
    """
    Verifica se l'URL è valido (http/https con netloc).

    Args:
        url: URL da validare

    Returns:
        True se URL valido, False altrimenti

    Examples:
        >>> is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        True

        >>> is_valid_url("http://example.com")
        True

        >>> is_valid_url("not a url")
        False

        >>> is_valid_url("ftp://example.com")
        False

        >>> is_valid_url("")
        False

    Note:
        - Accetta solo scheme http e https
        - Richiede che netloc (dominio) sia presente
        - Non verifica se l'URL sia raggiungibile
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except (ValueError, AttributeError) as e:
        logging.debug(f"URL validation failed for '{url}': {e}")
        return False


def validate_output_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Valida che il path di output sia una directory esistente e scrivibile.

    Args:
        path: Path da validare

    Returns:
        Tupla (is_valid, error_message) dove:
        - is_valid: True se path valido, False altrimenti
        - error_message: None se valido, messaggio errore se invalido

    Examples:
        >>> validate_output_path("C:\\Users\\User\\Downloads")
        (True, None)

        >>> validate_output_path("")
        (False, "Path cannot be empty")

        >>> validate_output_path("C:\\nonexistent\\path")
        (False, "Directory does not exist")

        >>> validate_output_path("C:\\Windows\\System32")
        (False, "Directory is not writable")

    Raises:
        InvalidPathError: Se il path non è valido (opzionale, per uso programmatico)
    """
    if not path:
        return False, "Path cannot be empty"

    if not isinstance(path, str):
        return False, "Path must be a string"

    # Normalizza il path
    path = os.path.abspath(path)

    if not os.path.exists(path):
        return False, f"Directory does not exist: {path}"

    if not os.path.isdir(path):
        return False, f"Path is not a directory: {path}"

    if not os.access(path, os.W_OK):
        return False, f"Directory is not writable: {path}"

    return True, None


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Pulisce il nome del file per compatibilità Windows.

    Rimuove caratteri non permessi da Windows, limita la lunghezza,
    e gestisce casi edge (es. nomi che iniziano/finiscono con spazio o punto).

    Args:
        filename: Nome file originale
        max_length: Lunghezza massima del nome file (default 200)

    Returns:
        Nome file sanitizzato e sicuro per Windows

    Examples:
        >>> sanitize_filename('video<test>.mp4')
        'video_test_.mp4'

        >>> sanitize_filename('file:name|test?.mp4')
        'file_name_test_.mp4'

        >>> sanitize_filename('   .leadingdot.mp4   ')
        'leadingdot.mp4'

        >>> sanitize_filename('a' * 300 + '.mp4')
        'aaa...aaa.mp4'  # Troncato a max_length

    Note:
        Caratteri Windows vietati: < > : " / \\ | ? *
        Rimuove anche spazi e punti leading/trailing
    """
    if not filename:
        return "untitled"

    # Caratteri vietati da Windows
    forbidden_chars = '<>:"/\\|?*'
    for char in forbidden_chars:
        filename = filename.replace(char, '_')

    # Rimuovi caratteri di controllo (ASCII 0-31)
    filename = ''.join(char if ord(char) >= 32 else '_' for char in filename)

    # Rimuovi leading/trailing spaces e dots
    filename = filename.strip('. ')

    # Se vuoto dopo cleanup, usa default
    if not filename:
        return "untitled"

    # Tronca se troppo lungo (mantieni estensione)
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        if max_name_length > 0:
            filename = name[:max_name_length] + ext
        else:
            filename = name[:max_length]

    return filename


# ============================================================================
# FORMATTAZIONE DATI
# ============================================================================

def format_bytes(size: int) -> str:
    """
    Converte byte in formato human-readable (KB, MB, GB, etc.).

    Args:
        size: Dimensione in byte

    Returns:
        Stringa formattata con unità appropriata

    Examples:
        >>> format_bytes(0)
        '0.00 B'

        >>> format_bytes(1024)
        '1.00 KB'

        >>> format_bytes(1048576)
        '1.00 MB'

        >>> format_bytes(1073741824)
        '1.00 GB'

        >>> format_bytes(1536)
        '1.50 KB'

    Note:
        Usa divisioni per 1024 (binarie) non 1000 (decimali)
        Supporta fino a PB (Petabyte)
    """
    if size < 0:
        return "0.00 B"

    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

    # Caso estremo: > 1PB
    return f"{size:.2f} EB"


def format_time(seconds: int) -> str:
    """
    Converte secondi in formato HH:MM:SS o MM:SS.

    Args:
        seconds: Tempo in secondi

    Returns:
        Stringa formattata come "HH:MM:SS" o "MM:SS" se < 1 ora

    Examples:
        >>> format_time(0)
        '00:00'

        >>> format_time(59)
        '00:59'

        >>> format_time(60)
        '01:00'

        >>> format_time(3661)
        '01:01:01'

        >>> format_time(-1)
        '--:--'

        >>> format_time(7265)
        '02:01:05'

    Note:
        Valori negativi restituiscono "--:--"
        Formato ore solo se >= 1 ora
    """
    if seconds < 0:
        return "--:--"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


# ============================================================================
# FILE SYSTEM HELPERS
# ============================================================================

def get_available_filename(directory: str, filename: str) -> str:
    """
    Trova un nome file disponibile aggiungendo (1), (2), etc. se necessario.

    Args:
        directory: Directory dove salvare il file
        filename: Nome file desiderato

    Returns:
        Nome file disponibile (possibilmente con suffisso numerico)

    Examples:
        >>> get_available_filename("C:\\Downloads", "video.mp4")
        'video.mp4'  # Se non esiste

        >>> get_available_filename("C:\\Downloads", "video.mp4")
        'video (1).mp4'  # Se video.mp4 esiste già

        >>> get_available_filename("C:\\Downloads", "video.mp4")
        'video (2).mp4'  # Se video.mp4 e video (1).mp4 esistono

    Note:
        Utile per evitare sovrascritture accidentali
    """
    base_path = os.path.join(directory, filename)

    if not os.path.exists(base_path):
        return filename

    # File esiste, trova nome alternativo
    name, ext = os.path.splitext(filename)
    counter = 1

    while True:
        new_filename = f"{name} ({counter}){ext}"
        new_path = os.path.join(directory, new_filename)

        if not os.path.exists(new_path):
            return new_filename

        counter += 1

        # Safeguard: non cercare all'infinito
        if counter > 9999:
            # Usa timestamp
            import time
            timestamp = int(time.time())
            return f"{name}_{timestamp}{ext}"


def ensure_directory_exists(path: str) -> bool:
    """
    Assicura che una directory esista, creandola se necessario.

    Args:
        path: Path della directory

    Returns:
        True se directory esiste o è stata creata, False se errore

    Examples:
        >>> ensure_directory_exists("C:\\new\\directory")
        True  # Directory creata

        >>> ensure_directory_exists("C:\\existing\\directory")
        True  # Directory già esistente

        >>> ensure_directory_exists("C:\\Windows\\System32\\forbidden")
        False  # Permessi insufficienti

    Note:
        Non solleva eccezioni, ritorna solo True/False
        Crea anche directory intermedie (parents)
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False
