"""Auto-update system per Modern Video Downloader.

Questo modulo gestisce il controllo e l'installazione degli aggiornamenti
utilizzando GitHub Releases come fonte per le nuove versioni.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError, HTTPError
import platform

from . import __version__


# ============================================================================
# CONFIGURAZIONE
# ============================================================================

# Repository GitHub (MODIFICARE CON IL TUO!)
GITHUB_REPO_OWNER = "NikiWay00"  # es: "vegeta"
GITHUB_REPO_NAME = "modern-video-downloader"  # nome repository

# API URLs
GITHUB_API_BASE = "https://api.github.com"
RELEASES_URL = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

# Timeout per richieste HTTP (secondi)
REQUEST_TIMEOUT = 10


# ============================================================================
# FUNZIONI PRINCIPALI
# ============================================================================

def get_current_version() -> str:
    """Ottiene la versione corrente dell'applicazione.

    Returns:
        Stringa versione (es: "0.4.1")
    """
    return __version__


def check_for_updates() -> Optional[Dict[str, Any]]:
    """Controlla se è disponibile una nuova versione su GitHub.

    Returns:
        Dictionary con info update se disponibile, None altrimenti:
        {
            'version': '0.5.0',
            'download_url': 'https://...',
            'changelog': 'Release notes...',
            'published_at': '2026-02-01T12:00:00Z',
            'asset_name': 'ModernVideoDownloader-v0.5.0.exe'
        }

    Raises:
        UpdateCheckError: Se il controllo fallisce

    Example:
        >>> update = check_for_updates()
        >>> if update:
        ...     print(f"Nuova versione: {update['version']}")
    """
    try:
        logging.info(f"Checking for updates at {RELEASES_URL}")

        # Chiamata API GitHub
        with urlopen(RELEASES_URL, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode())

        # Estrai versione (rimuovi 'v' se presente)
        latest_version = data['tag_name'].lstrip('v')
        current_version = get_current_version()

        logging.info(f"Current version: {current_version}, Latest: {latest_version}")

        # Confronta versioni
        if _is_newer_version(latest_version, current_version):
            # Trova asset appropriato per la piattaforma
            asset = _find_platform_asset(data.get('assets', []))

            if not asset:
                logging.warning("No compatible asset found for this platform")
                return None

            return {
                'version': latest_version,
                'download_url': asset['browser_download_url'],
                'changelog': data.get('body', 'No changelog available'),
                'published_at': data.get('published_at', ''),
                'asset_name': asset['name'],
                'asset_size': asset.get('size', 0)
            }
        else:
            logging.info("App is up to date")
            return None

    except HTTPError as e:
        if e.code == 404:
            logging.error("Repository or releases not found (404)")
            raise UpdateCheckError("Repository non trovato. Verifica GITHUB_REPO_OWNER e GITHUB_REPO_NAME.")
        else:
            logging.error(f"HTTP error checking updates: {e}")
            raise UpdateCheckError(f"Errore HTTP: {e.code}")

    except URLError as e:
        logging.error(f"Network error checking updates: {e}")
        raise UpdateCheckError("Errore di rete. Verifica la connessione internet.")

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON response: {e}")
        raise UpdateCheckError("Risposta non valida dal server.")

    except Exception as e:
        logging.error(f"Unexpected error checking updates: {e}")
        raise UpdateCheckError(f"Errore imprevisto: {str(e)}")


def download_update(
    download_url: str,
    asset_name: str,
    progress_callback: Optional[callable] = None
) -> str:
    """Scarica il file di update.

    Args:
        download_url: URL del file da scaricare
        asset_name: Nome del file
        progress_callback: Funzione chiamata con (bytes_downloaded, total_bytes)

    Returns:
        Path del file scaricato

    Raises:
        UpdateDownloadError: Se il download fallisce

    Example:
        >>> def on_progress(current, total):
        ...     print(f"{current}/{total} bytes")
        >>> path = download_update(url, "app.exe", on_progress)
    """
    try:
        # Directory temporanea per il download
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, asset_name)

        logging.info(f"Downloading update to {output_path}")

        # Download con progress tracking
        if progress_callback:
            def _report_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                progress_callback(downloaded, total_size)

            urlretrieve(download_url, output_path, reporthook=_report_hook)
        else:
            urlretrieve(download_url, output_path)

        logging.info(f"Update downloaded successfully to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Error downloading update: {e}")
        raise UpdateDownloadError(f"Download fallito: {str(e)}")


def apply_update(installer_path: str) -> None:
    """Applica l'update scaricato.

    Per .exe: Lancia installer e chiude l'app corrente
    Per .zip: Estrae e sostituisce files (richiede riavvio manuale)

    Args:
        installer_path: Path del file installer/update

    Raises:
        UpdateApplyError: Se l'applicazione fallisce

    Note:
        Questa funzione terminerà l'applicazione corrente dopo aver
        lanciato l'installer.
    """
    try:
        file_ext = Path(installer_path).suffix.lower()

        if file_ext == '.exe':
            _apply_exe_update(installer_path)
        elif file_ext == '.zip':
            _apply_zip_update(installer_path)
        else:
            raise UpdateApplyError(f"Tipo file non supportato: {file_ext}")

    except Exception as e:
        logging.error(f"Error applying update: {e}")
        raise UpdateApplyError(f"Applicazione update fallita: {str(e)}")


# ============================================================================
# FUNZIONI HELPER PRIVATE
# ============================================================================

def _is_newer_version(latest: str, current: str) -> bool:
    """Confronta due versioni in formato semantic versioning.

    Args:
        latest: Versione più recente (es: "0.5.0")
        current: Versione corrente (es: "0.4.1")

    Returns:
        True se latest > current

    Example:
        >>> _is_newer_version("0.5.0", "0.4.1")
        True
        >>> _is_newer_version("0.4.1", "0.4.1")
        False
    """
    try:
        # Converti a tuple di interi per confronto
        latest_parts = tuple(int(x) for x in latest.split('.'))
        current_parts = tuple(int(x) for x in current.split('.'))

        return latest_parts > current_parts

    except (ValueError, AttributeError):
        # Se parsing fallisce, usa confronto stringa
        logging.warning(f"Version comparison fallback for {latest} vs {current}")
        return latest > current


def _find_platform_asset(assets: list) -> Optional[Dict[str, Any]]:
    """Trova l'asset appropriato per la piattaforma corrente.

    Args:
        assets: Lista di assets dalla GitHub API

    Returns:
        Asset dict se trovato, None altrimenti
    """
    system = platform.system().lower()

    # Cerca pattern nel nome del file
    patterns = {
        'windows': ['.exe', '-windows', '-win'],
        'darwin': ['.dmg', '.app', '-macos', '-darwin'],
        'linux': ['.AppImage', '-linux', '.deb', '.rpm']
    }

    platform_patterns = patterns.get(system, [])

    for asset in assets:
        name = asset['name'].lower()
        if any(pattern in name for pattern in platform_patterns):
            return asset

    # Fallback: prendi il primo asset
    return assets[0] if assets else None


def _apply_exe_update(installer_path: str) -> None:
    """Applica update da file .exe (Windows).

    Lancia l'installer e termina l'applicazione corrente.
    """
    logging.info(f"Launching installer: {installer_path}")

    if platform.system() == 'Windows':
        # Windows: usa subprocess.Popen per non bloccare
        subprocess.Popen([installer_path], shell=True)
    else:
        # Unix: usa subprocess.run
        subprocess.Popen([installer_path])

    logging.info("Installer launched, exiting application")
    sys.exit(0)


def _apply_zip_update(zip_path: str) -> None:
    """Applica update da file .zip.

    Estrae i contenuti e li copia nella directory di installazione.
    Richiede riavvio manuale dell'applicazione.
    """
    import zipfile
    import shutil

    logging.info(f"Extracting update from {zip_path}")

    # Directory di installazione (dove si trova questo script)
    install_dir = Path(__file__).parent.parent.parent

    # Estrai in directory temporanea
    temp_extract = Path(tempfile.gettempdir()) / "mvd_update"
    temp_extract.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)

    # Copia files (sovrascrivi)
    for item in temp_extract.rglob('*'):
        if item.is_file():
            relative = item.relative_to(temp_extract)
            dest = install_dir / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            logging.info(f"Updated: {relative}")

    # Cleanup
    shutil.rmtree(temp_extract, ignore_errors=True)

    logging.info("Update extracted successfully. Please restart the application.")


# ============================================================================
# ECCEZIONI CUSTOM
# ============================================================================

class UpdateError(Exception):
    """Eccezione base per errori di update."""
    pass


class UpdateCheckError(UpdateError):
    """Errore durante il controllo degli aggiornamenti."""
    pass


class UpdateDownloadError(UpdateError):
    """Errore durante il download dell'aggiornamento."""
    pass


class UpdateApplyError(UpdateError):
    """Errore durante l'applicazione dell'aggiornamento."""
    pass


# ============================================================================
# TESTING / DEBUG
# ============================================================================

if __name__ == "__main__":
    # Test del sistema di update
    logging.basicConfig(level=logging.INFO)

    print(f"Current version: {get_current_version()}")
    print(f"Checking for updates at {RELEASES_URL}")

    try:
        update = check_for_updates()
        if update:
            print(f"\n✅ Update available!")
            print(f"Version: {update['version']}")
            print(f"File: {update['asset_name']}")
            print(f"Size: {update['asset_size'] / 1024 / 1024:.1f} MB")
            print(f"\nChangelog:\n{update['changelog']}")
        else:
            print("\n✅ App is up to date!")
    except UpdateCheckError as e:
        print(f"\n❌ Error: {e}")
