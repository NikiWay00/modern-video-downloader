"""
Download module per Modern Video Downloader.

Gestisce il download di video e audio tramite yt-dlp con supporto per:
- Download video MP4 con qualità selezionabile
- Estrazione audio MP3
- Progress tracking in tempo reale
- Cancellazione download
- Ottimizzazioni performance (concurrent fragments, debouncing)
"""

import os
import time
import threading
import logging
from typing import Callable, Optional, Dict, Any

import yt_dlp

from .utils import setup_ffmpeg, resource_path, format_bytes, format_time
from .config import YTDLP_CONFIG, PERFORMANCE_CONFIG, UI_MSG, get_user_agent
from .exceptions import (
    DownloadCancelledError,
    FFmpegNotFoundError,
    wrap_ytdlp_exception,
    NetworkError,
)


# ============================================================================
# DOWNLOAD FUNCTION
# ============================================================================

def download_video(
    url: str,
    mode: str,
    quality: str,
    output_path: str,
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    status_cb: Optional[Callable[[str], None]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> None:
    """
    Scarica video o audio da URL usando yt-dlp.

    Supporta download da YouTube e 800+ altri siti tramite yt-dlp.
    Gestisce progress tracking, cancellazione, e conversione formati.

    Args:
        url: URL del video da scaricare
        mode: Modalità download - "video" per MP4, "audio" per MP3
        quality: Stringa formato yt-dlp per qualità (es. "bestvideo[height<=1080]+bestaudio")
        output_path: Cartella di destinazione per il file scaricato
        progress_cb: Callback per aggiornamenti progresso. Riceve dict con:
            - percent: Percentuale completamento (float)
            - downloaded: Byte scaricati (str formattato)
            - total: Byte totali (str formattato)
            - speed: Velocità download (str formattato)
            - eta: Tempo rimanente stimato (str formattato)
        status_cb: Callback per messaggi di stato (str)
        cancel_event: Event per cancellare il download

    Raises:
        DownloadCancelledError: Se download viene annullato dall'utente
        FFmpegNotFoundError: Se FFmpeg non è disponibile
        NetworkError: Se ci sono problemi di connessione
        DownloadError: Per altri errori durante il download

    Examples:
        >>> # Download video 1080p
        >>> download_video(
        ...     url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...     mode="video",
        ...     quality="bestvideo[height<=1080]+bestaudio/best",
        ...     output_path="C:\\Downloads",
        ...     progress_cb=lambda d: print(f"{d['percent']:.1f}%"),
        ...     status_cb=lambda s: print(s)
        ... )

        >>> # Download audio MP3
        >>> download_video(
        ...     url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...     mode="audio",
        ...     quality="bestaudio/best",
        ...     output_path="C:\\Downloads"
        ... )

    Note:
        - Per video: scarica MP4 con audio AAC (compatibilità Windows Media Player)
        - Per audio: estrae MP3 a 192kbps
        - Usa concurrent fragment downloads (4 thread) per velocità ottimale
        - Progress callback ha debouncing (100ms) per evitare saturazione UI
    """
    # Setup FFmpeg (PATH) + path esplicito per yt-dlp
    if not setup_ffmpeg():
        msg = UI_MSG.ERR_FFMPEG_NOT_FOUND.format(resource_path("ffmpeg/bin"))
        logging.error(msg)
        if status_cb:
            status_cb(msg)
        raise FFmpegNotFoundError(msg)

    ffmpeg_bin = resource_path("ffmpeg/bin")

    # Verifica presenza eseguibile FFmpeg
    ffmpeg_exe_win = os.path.join(ffmpeg_bin, "ffmpeg.exe")
    ffmpeg_exe_nix = os.path.join(ffmpeg_bin, "ffmpeg")
    if not (os.path.exists(ffmpeg_exe_win) or os.path.exists(ffmpeg_exe_nix)):
        msg = UI_MSG.ERR_FFMPEG_NOT_FOUND.format(ffmpeg_bin)
        logging.error(msg)
        if status_cb:
            status_cb(msg)
        raise FFmpegNotFoundError(msg)

    # Crea directory output se non esiste
    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as e:
        logging.error(f"Cannot create output directory {output_path}: {e}")
        raise

    # Progress tracking con debouncing
    last_progress_time = 0.0

    def progress_hook(d: Dict[str, Any]) -> None:
        """
        Hook per aggiornamenti progresso yt-dlp.

        Chiamato frequentemente durante il download. Implementa debouncing
        per evitare di saturare la UI queue con troppi aggiornamenti.

        Args:
            d: Dizionario con informazioni progresso da yt-dlp

        Raises:
            DownloadCancelledError: Se cancel_event è impostato
        """
        nonlocal last_progress_time

        # Check cancellazione
        if cancel_event and cancel_event.is_set():
            logging.info("Download cancellation requested")
            raise DownloadCancelledError("Download cancelled by user")

        status = d.get("status")

        if status == "downloading":
            # Debouncing: aggiorna solo ogni PROGRESS_UPDATE_INTERVAL
            current_time = time.time()
            if current_time - last_progress_time < PERFORMANCE_CONFIG.PROGRESS_UPDATE_INTERVAL:
                return

            last_progress_time = current_time

            # Estrai informazioni
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed")
            eta = d.get("eta")

            # Calcola percentuale
            if total and total > 0:
                percent = (downloaded / total * 100.0)
            else:
                percent = 0.0

            # Prepara dati per callback
            progress_data = {
                "percent": round(percent, 1),
                "downloaded": format_bytes(int(downloaded)) if downloaded else "0 B",
                "total": format_bytes(int(total)) if total else "?",
                "speed": (format_bytes(int(speed)) + "/s") if speed else "?",
                "eta": format_time(int(eta)) if eta is not None else "--:--",
            }

            # Invia callback
            if progress_cb:
                progress_cb(progress_data)

        elif status == "finished":
            # Download finito, inizia elaborazione
            if status_cb:
                status_cb(UI_MSG.STATUS_PROCESSING)
            logging.info("Download finished, starting post-processing")

    # ========================================================================
    # Configurazione yt-dlp (BASE)
    # ========================================================================

    ydl_opts: Dict[str, Any] = {
        # Output template
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),

        # Download settings
        "noplaylist": True,  # Solo singolo video, non playlist

        # Progress
        "progress_hooks": [progress_hook],

        # Logging
        "quiet": True,
        "no_warnings": True,

        # Merge format
        "merge_output_format": "mp4",

        # FFmpeg
        "ffmpeg_location": ffmpeg_bin,
    }

    # ========================================================================
    # Configurazione OTTIMIZZATA per performance e compatibilità
    # ========================================================================

    ydl_opts.update({
        # User-Agent (usa primo della lista, rotation possibile in futuro)
        "user_agent": get_user_agent(0),

        # HTTP Headers
        "http_headers": YTDLP_CONFIG.HTTP_HEADERS,

        # Performance: concurrent fragments per download 4x più veloce
        "concurrent_fragment_downloads": YTDLP_CONFIG.CONCURRENT_FRAGMENTS,

        # Chunk size ottimizzato (10MB chunks)
        "http_chunk_size": YTDLP_CONFIG.HTTP_CHUNK_SIZE,

        # Retry settings
        "retries": YTDLP_CONFIG.RETRIES,
        "fragment_retries": YTDLP_CONFIG.FRAGMENT_RETRIES,

        # Timeout
        "socket_timeout": YTDLP_CONFIG.SOCKET_TIMEOUT,
    })

    # Cookies da browser: DISABILITATO
    # Causa problemi se Chrome è aperto (database bloccato)
    # La maggior parte dei video YouTube funziona senza cookies
    # Se necessario in futuro, chiudere Chrome prima del download
    #
    # for browser in YTDLP_CONFIG.COOKIE_BROWSERS:
    #     try:
    #         ydl_opts["cookiesfrombrowser"] = (browser,)
    #         logging.info(f"Using cookies from {browser}")
    #         break
    #     except Exception:
    #         continue

    # ========================================================================
    # Configurazione modalità: VIDEO o AUDIO
    # ========================================================================

    if mode == "video":
        # VIDEO MODE: MP4 con audio AAC
        # Format string ottimizzato con fallback multipli per massima compatibilità
        ydl_opts["format"] = (
            # 1. Prova: video MP4 + audio M4A (AAC) - ideale per Windows
            "bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/"
            # 2. Fallback: qualsiasi MP4 best quality
            "best[ext=mp4]/"
            # 3. Fallback: usa quality parameter (es. height<=1080)
            f"{quality}/"
            # 4. Fallback: best video + best audio qualsiasi formato
            "bestvideo+bestaudio/"
            # 5. Fallback finale: best disponibile
            "best"
        )

        # Post-processing: forza audio AAC per compatibilità Windows Media Player
        # Copia video senza ricodifica (veloce), ricodifica solo audio
        ydl_opts["postprocessor_args"] = {
            "ffmpeg": [
                "-c:v", "copy",  # Copia video stream (no re-encoding)
                "-c:a", "aac",   # Converti audio in AAC
                "-b:a", YTDLP_CONFIG.AUDIO_BITRATE  # Bitrate 192k
            ]
        }

        logging.info(f"Video mode: MP4 with quality={quality}")

    elif mode == "audio":
        # AUDIO MODE: estrazione MP3
        ydl_opts["format"] = "bestaudio/best"

        # Post-processor per estrarre audio e convertire in MP3
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": YTDLP_CONFIG.AUDIO_FORMAT,
                "preferredquality": YTDLP_CONFIG.AUDIO_QUALITY,
            }
        ]

        logging.info("Audio mode: MP3 extraction at 192kbps")

    else:
        # Modalità non valida
        error_msg = f"Invalid mode: {mode}. Must be 'video' or 'audio'"
        logging.error(error_msg)
        raise ValueError(error_msg)

    # ========================================================================
    # DOWNLOAD
    # ========================================================================

    try:
        # Notifica inizio
        if status_cb:
            status_cb(UI_MSG.STATUS_DOWNLOADING)
        logging.info(f"Starting download: {url} (mode={mode})")

        # Download con yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Notifica completamento
        if status_cb:
            status_cb(UI_MSG.STATUS_COMPLETE)
        logging.info(f"Download completed: {url}")

    except DownloadCancelledError:
        # Download annullato dall'utente
        if status_cb:
            status_cb(UI_MSG.STATUS_CANCELLED)
        logging.info("Download cancelled by user")
        raise

    except yt_dlp.utils.DownloadError as e:
        # Errore specifico yt-dlp: converti in eccezione MVD appropriata
        logging.error(f"yt-dlp download error for {url}: {e}")
        mvd_exception = wrap_ytdlp_exception(e)

        if status_cb:
            status_cb(UI_MSG.STATUS_ERROR.format(str(e)))

        raise mvd_exception

    except (ConnectionError, TimeoutError) as e:
        # Errori di rete
        logging.error(f"Network error downloading {url}: {e}")
        if status_cb:
            status_cb(UI_MSG.STATUS_ERROR.format("Network error"))
        raise NetworkError(f"Network error: {e}") from e

    except FileNotFoundError as e:
        # FFmpeg non trovato o file output non creato
        logging.error(f"File not found error: {e}")
        if status_cb:
            status_cb(UI_MSG.STATUS_ERROR.format("File not found"))
        raise

    except Exception as e:
        # Errore generico: logga con traceback completo
        logging.exception(f"Unexpected error downloading {url}")
        if status_cb:
            status_cb(UI_MSG.STATUS_ERROR.format(str(e)))
        raise


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_video_info(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Recupera informazioni su un video senza scaricarlo.

    Utile per ottenere titolo, durata, thumbnail prima del download.

    Args:
        url: URL del video
        timeout: Timeout in secondi (default 10)

    Returns:
        Dizionario con informazioni video o None se fallisce

    Examples:
        >>> info = get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> print(info["title"])
        'Rick Astley - Never Gonna Give You Up'

        >>> print(info["duration"])
        212  # secondi

    Note:
        Può fallire per video privati, rimossi, o siti non supportati
    """
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": timeout,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return info

    except Exception as e:
        logging.warning(f"Failed to get video info for {url}: {e}")
        return None
