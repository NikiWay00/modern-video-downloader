"""
Eccezioni custom per Modern Video Downloader.

Questo modulo definisce una gerarchia di eccezioni specifiche
per gestire errori in modo preciso e fornire feedback dettagliato.
"""


class MVDError(Exception):
    """
    Eccezione base per Modern Video Downloader.

    Tutte le eccezioni custom del progetto ereditano da questa classe.
    """
    pass


class DownloadError(MVDError):
    """
    Errore generico durante il processo di download.

    Usata come base per errori specifici di download o quando
    il tipo di errore di download non è ulteriormente specificabile.
    """
    pass


class DownloadCancelledError(DownloadError):
    """
    Download annullato dall'utente.

    Sollevata quando l'utente interrompe manualmente un download
    in corso tramite il pulsante Annulla o evento di cancellazione.
    """
    pass


class NetworkError(DownloadError):
    """
    Errore di rete durante il download.

    Include timeout, connessione persa, DNS failures, e altri
    problemi legati alla connettività di rete.

    Examples:
        >>> raise NetworkError("Connection timeout after 30s")
        >>> raise NetworkError("DNS resolution failed for domain")
    """
    pass


class TitleFetchError(DownloadError):
    """
    Impossibile recuperare il titolo del video.

    Sollevata quando il fetch del titolo fallisce ma il download
    potrebbe comunque essere possibile. Non blocca il download.

    Examples:
        >>> raise TitleFetchError("Site not supported by yt-dlp")
        >>> raise TitleFetchError("Video is private or deleted")
    """
    pass


class UnsupportedSiteError(DownloadError):
    """
    Sito non supportato da yt-dlp.

    Sollevata quando l'URL punta a un sito che yt-dlp non
    è in grado di gestire.
    """
    pass


class VideoUnavailableError(DownloadError):
    """
    Video non disponibile (privato, rimosso, geograficamente bloccato).

    Sollevata quando il video esiste ma non è accessibile per
    restrizioni di vario tipo.

    Examples:
        >>> raise VideoUnavailableError("Video is private")
        >>> raise VideoUnavailableError("Video removed by uploader")
        >>> raise VideoUnavailableError("Video not available in your country")
    """
    pass


class ConfigurationError(MVDError):
    """
    Errore nella configurazione o setup dell'applicazione.

    Include problemi con file di configurazione, dipendenze
    mancanti, o impostazioni non valide.
    """
    pass


class FFmpegNotFoundError(ConfigurationError):
    """
    FFmpeg non trovato o non disponibile.

    Sollevata quando FFmpeg non è presente nel path previsto
    o non è eseguibile. FFmpeg è necessario per conversioni audio/video.

    Examples:
        >>> raise FFmpegNotFoundError("FFmpeg binary not found in ffmpeg/bin/")
        >>> raise FFmpegNotFoundError("FFmpeg found but not executable")
    """
    pass


class ValidationError(MVDError):
    """
    Errore di validazione input utente.

    Sollevata quando l'input fornito dall'utente non è valido
    (URL malformato, path non esistente, etc.)

    Examples:
        >>> raise ValidationError("URL must start with http:// or https://")
        >>> raise ValidationError("Output path does not exist")
        >>> raise ValidationError("File name contains invalid characters")
    """
    pass


class InvalidURLError(ValidationError):
    """
    URL non valido o malformato.

    Sollevata quando l'URL fornito non rispetta il formato
    richiesto o non è accessibile.

    Examples:
        >>> raise InvalidURLError("URL scheme must be http or https")
        >>> raise InvalidURLError("URL is missing domain name")
    """
    pass


class InvalidPathError(ValidationError):
    """
    Path non valido o non accessibile.

    Sollevata quando il path specificato non esiste, non è
    una directory, o non è scrivibile.

    Examples:
        >>> raise InvalidPathError("Directory does not exist: C:\\invalid\\path")
        >>> raise InvalidPathError("Path is not writable: C:\\Windows\\System32")
    """
    pass


class FileSystemError(MVDError):
    """
    Errore generico del filesystem.

    Include problemi di permessi, disco pieno, file già esistente, etc.

    Examples:
        >>> raise FileSystemError("Disk is full")
        >>> raise FileSystemError("Permission denied")
        >>> raise FileSystemError("File already exists")
    """
    pass


class SettingsError(MVDError):
    """
    Errore nel caricamento o salvataggio delle impostazioni.

    Sollevata quando il file di settings è corrotto, non leggibile,
    o non può essere salvato.

    Examples:
        >>> raise SettingsError("Settings file is corrupted")
        >>> raise SettingsError("Cannot write settings to AppData")
    """
    pass


# ============================================================================
# EXCEPTION HELPERS
# ============================================================================

def wrap_ytdlp_exception(exc: Exception) -> DownloadError:
    """
    Converte eccezioni yt-dlp in eccezioni MVD appropriate.

    Args:
        exc: Eccezione originale da yt-dlp

    Returns:
        Eccezione MVD appropriata

    Examples:
        >>> from yt_dlp.utils import DownloadError as YTDLPDownloadError
        >>> ytdlp_exc = YTDLPDownloadError("Video unavailable")
        >>> mvd_exc = wrap_ytdlp_exception(ytdlp_exc)
        >>> isinstance(mvd_exc, VideoUnavailableError)
        True
    """
    exc_str = str(exc).lower()

    # Video non disponibile
    if any(keyword in exc_str for keyword in ["private", "unavailable", "removed", "deleted", "blocked"]):
        return VideoUnavailableError(str(exc))

    # Problemi di rete
    if any(keyword in exc_str for keyword in ["timeout", "connection", "network", "dns", "unreachable"]):
        return NetworkError(str(exc))

    # Sito non supportato
    if any(keyword in exc_str for keyword in ["unsupported", "not supported", "no suitable"]):
        return UnsupportedSiteError(str(exc))

    # Errore generico download
    return DownloadError(str(exc))
