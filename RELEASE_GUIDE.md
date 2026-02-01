# 🚀 Guida Completa al Sistema di Auto-Update

## 📋 Indice

1. [Setup Iniziale](#setup-iniziale)
2. [Configurazione Repository GitHub](#configurazione-repository-github)
3. [Creare Release con Update](#creare-release-con-update)
4. [Come l'Utente Finale Riceve gli Update](#come-utente-finale-riceve-update)
5. [Workflow Completo](#workflow-completo)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Setup Iniziale

### 1. Configurare il Repository GitHub

Apri [`src/mvd/updater.py`](src/mvd/updater.py) e modifica le righe 22-23:

```python
# PRIMA (esempio):
GITHUB_REPO_OWNER = "TUO_USERNAME"  # es: "vegeta"
GITHUB_REPO_NAME = "modern-video-downloader"  # nome repository

# DOPO (con i tuoi dati):
GITHUB_REPO_OWNER = "Vegeta123"  # Il tuo username GitHub
GITHUB_REPO_NAME = "ModernVideoDownloader"  # Il nome del tuo repository
```

### 2. Creare Repository GitHub

Se non hai ancora un repository:

```bash
# 1. Inizializza git (se non fatto)
cd "c:\Users\Vegeta\Desktop\progetti xcode\modern_video_downloader"
git init

# 2. Aggiungi files
git add .
git commit -m "Initial commit - v0.4.1"

# 3. Crea repository su GitHub (vai su github.com e crea un nuovo repo)

# 4. Collega repository locale a GitHub
git remote add origin https://github.com/TUO_USERNAME/NOME_REPO.git
git branch -M main
git push -u origin main
```

---

## 📦 Configurazione Repository GitHub

### 1. Rendere il Repository Pubblico o Privato

**Opzione A: Repository Pubblico** ✅ RACCOMANDATO (Gratuito)
- Vai su `Settings` del repository
- Scroll down a "Danger Zone"
- Clicca "Change repository visibility"
- Seleziona "Public"

**Opzione B: Repository Privato** (Richiede GitHub Pro o account con Releases)
- Le GitHub Releases funzionano anche su repo privati
- Ma devi autenticare le richieste API (più complesso)

### 2. Abilitare GitHub Releases

- Le releases sono abilitate di default ✅
- Nessuna configurazione aggiuntiva necessaria

---

## 🎯 Creare Release con Update

### Passo 1: Preparare la Nuova Versione

#### A. Aggiorna il numero di versione

Modifica [`src/mvd/__init__.py`](src/mvd/__init__.py):

```python
# PRIMA:
__version__ = "0.4.1"

# DOPO (esempio per v0.5.0):
__version__ = "0.5.0"
```

#### B. Commit e push

```bash
git add src/mvd/__init__.py
git commit -m "Bump version to 0.5.0"
git push origin main
```

### Passo 2: Creare il Tag Git

```bash
# Crea tag per la versione
git tag v0.5.0

# Push tag a GitHub
git push origin v0.5.0
```

⚠️ **IMPORTANTE:** Il tag DEVE iniziare con `v` (es: `v0.5.0`, NON `0.5.0`)

### Passo 3: Creare l'Installer (.exe)

#### Opzione A: PyInstaller (RACCOMANDATO per Windows)

1. Installa PyInstaller:
```bash
pip install pyinstaller
```

2. Crea spec file (`build.spec`):
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ffmpeg', 'ffmpeg'),  # Include FFmpeg
    ],
    hiddenimports=['customtkinter', 'yt_dlp'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ModernVideoDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico'  # Tua icona (opzionale)
)
```

3. Build l'installer:
```bash
pyinstaller build.spec
```

4. L'exe sarà in `dist/ModernVideoDownloader.exe`

#### Opzione B: cx_Freeze (Alternativa)

```bash
pip install cx_Freeze
python setup.py build
```

### Passo 4: Creare la Release su GitHub

#### Metodo 1: Web UI (Più Semplice)

1. Vai su GitHub repository
2. Clicca su "Releases" (colonna destra)
3. Clicca "Draft a new release"
4. Compila i campi:

```
Tag version:    v0.5.0
Release title:  Modern Video Downloader v0.5.0
Description:    (Scrivi il changelog)
```

**Esempio Changelog:**
```markdown
## 🎉 Modern Video Downloader v0.5.0

### ✨ Nuove Features
- 🔄 Sistema auto-update integrato
- ⚡ Download 20% più veloci
- 🎨 Nuova UI per gestione queue

### 🐛 Bug Fixes
- Fixed crash quando URL non valido
- Fixed memory leak su download lunghi

### 📊 Miglioramenti
- Ottimizzata gestione memoria
- Migliorato logging

---

**Installazione:**
1. Scarica `ModernVideoDownloader-v0.5.0.exe`
2. Esegui il file
3. Segui l'installazione guidata
```

5. **IMPORTANTE:** Allega l'installer:
   - Clicca "Attach binaries" sotto la descrizione
   - Upload `ModernVideoDownloader.exe`
   - **Rinominalo** in: `ModernVideoDownloader-v0.5.0.exe`

6. Clicca "Publish release" ✅

#### Metodo 2: GitHub CLI (Avanzato)

```bash
# Installa GitHub CLI
# Scarica da: https://cli.github.com/

# Login
gh auth login

# Crea release con asset
gh release create v0.5.0 \
  --title "Modern Video Downloader v0.5.0" \
  --notes-file CHANGELOG.md \
  dist/ModernVideoDownloader.exe#ModernVideoDownloader-v0.5.0.exe
```

---

## 👤 Come l'Utente Finale Riceve gli Update

### 1. Utente Clicca "🔄 Check Update"

Nell'applicazione, in alto a destra accanto alla versione.

### 2. App Controlla GitHub

```
App chiama: https://api.github.com/repos/USER/REPO/releases/latest
Risposta JSON:
{
  "tag_name": "v0.5.0",
  "assets": [
    {
      "name": "ModernVideoDownloader-v0.5.0.exe",
      "browser_download_url": "https://github.com/.../ModernVideoDownloader-v0.5.0.exe",
      "size": 52428800
    }
  ],
  "body": "Changelog markdown..."
}
```

### 3. App Confronta Versioni

```python
Versione corrente: 0.4.1
Versione latest:   0.5.0
0.5.0 > 0.4.1? → SÌ → Update disponibile!
```

### 4. Dialog Mostrato

```
┌─────────────────────────────────────────┐
│  🎉 Nuova Versione Disponibile: v0.5.0  │
├─────────────────────────────────────────┤
│  📦 Dimensione: 50.0 MB                 │
│                                         │
│  📝 Novità:                             │
│  ┌─────────────────────────────────┐   │
│  │ - Auto-update system            │   │
│  │ - Download 20% più veloci       │   │
│  │ - Bug fixes                     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [⬇️ Scarica e Installa]  [❌ Più Tardi]│
└─────────────────────────────────────────┘
```

### 5. Download + Installazione

- Click su "Scarica e Installa"
- Progress bar durante download
- Conferma installazione
- App si chiude e installer parte
- Utente completa installazione
- Nuova versione installata! ✅

---

## 📈 Workflow Completo

### Scenario: Rilasciare v0.5.0

```bash
# 1. Sviluppa nuove features
git add .
git commit -m "Add auto-update system"

# 2. Aggiorna versione in __init__.py
# __version__ = "0.5.0"
git add src/mvd/__init__.py
git commit -m "Bump version to 0.5.0"

# 3. Push a GitHub
git push origin main

# 4. Crea tag
git tag v0.5.0
git push origin v0.5.0

# 5. Build .exe
pyinstaller build.spec

# 6. Crea release su GitHub
# - Vai su github.com/USER/REPO/releases
# - "Draft new release"
# - Tag: v0.5.0
# - Upload: dist/ModernVideoDownloader.exe
# - Rename: ModernVideoDownloader-v0.5.0.exe
# - Publish

# 7. Utenti ricevono notifica update! ✅
```

### Frequenza Release Raccomandata

- **Patch** (0.4.1 → 0.4.2): Bug fixes urgenti → Ogni 1-2 settimane
- **Minor** (0.4.x → 0.5.0): Nuove features → Ogni 1-2 mesi
- **Major** (0.x.x → 1.0.0): Breaking changes → Quando stabile

---

## 🎨 Naming Conventions

### ✅ Corretto:

```
Tag:     v0.5.0
Asset:   ModernVideoDownloader-v0.5.0.exe
Title:   Modern Video Downloader v0.5.0
```

### ❌ Sbagliato:

```
Tag:     0.5.0          (manca 'v')
Asset:   installer.exe  (non specifico)
Title:   New version    (non chiaro)
```

---

## 🐛 Troubleshooting

### Problema 1: "Repository non trovato (404)"

**Causa:** `GITHUB_REPO_OWNER` o `GITHUB_REPO_NAME` errati in `updater.py`

**Soluzione:**
```python
# Verifica che corrisponda esattamente al tuo repository
GITHUB_REPO_OWNER = "TuoUsername"  # Case-sensitive!
GITHUB_REPO_NAME = "nome-repo"     # Esatto come su GitHub
```

Test URL:
```
https://api.github.com/repos/TuoUsername/nome-repo/releases/latest
```
Aprilo nel browser - deve restituire JSON, non 404.

### Problema 2: "Nessun asset compatibile trovato"

**Causa:** File non ha `.exe` nel nome o non è allegato

**Soluzione:**
- Verifica che l'asset sia allegato alla release
- Nome deve contenere `.exe` per Windows
- Pattern riconosciuti: `.exe`, `-windows`, `-win`

### Problema 3: "Update check fallisce con network error"

**Causa:** Firewall blocca richieste GitHub API

**Soluzione:**
- Verifica connessione internet
- Whitelist: `api.github.com` nel firewall
- Test con: `curl https://api.github.com/repos/USER/REPO/releases/latest`

### Problema 4: ".exe non si avvia dopo update"

**Causa:** FFmpeg mancante o path non corretto

**Soluzione:**
In `build.spec` assicurati di includere FFmpeg:
```python
datas=[
    ('ffmpeg', 'ffmpeg'),  # Include FFmpeg directory
],
```

### Problema 5: "Versioni non confrontate correttamente"

**Causa:** Tag non inizia con 'v'

**Soluzione:**
```bash
# ❌ Sbagliato
git tag 0.5.0

# ✅ Corretto
git tag v0.5.0
```

---

## 🔐 Sicurezza

### Verifica Integrità Download

**Opzionale:** Aggiungi checksum SHA256 alle release:

```bash
# Genera checksum
certutil -hashfile ModernVideoDownloader-v0.5.0.exe SHA256

# Aggiungi al changelog
SHA256: a1b2c3d4e5f6...
```

Nel codice puoi verificare:
```python
import hashlib

def verify_checksum(file_path, expected_sha256):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_sha256
```

---

## 📊 Statistiche Download

GitHub fornisce statistiche automatiche:

- Vai su `Releases` del repository
- Ogni release mostra "X downloads" per ogni asset
- Puoi vedere quanti utenti hanno scaricato ogni versione

---

## 🚀 Distribuzione Avanzata

### Opzione 1: Windows Installer (NSIS)

Crea un vero installer con wizard:

```bash
# Usa NSIS (Nullsoft Scriptable Install System)
# Download: https://nsis.sourceforge.io/

# Script NSIS (installer.nsi):
!define APP_NAME "Modern Video Downloader"
!define APP_VERSION "0.5.0"
!define APP_PUBLISHER "YourName"

OutFile "ModernVideoDownloader-Setup-v0.5.0.exe"
InstallDir "$PROGRAMFILES\ModernVideoDownloader"

Section "Install"
    SetOutPath $INSTDIR
    File "dist\ModernVideoDownloader.exe"
    File /r "ffmpeg"
    CreateShortCut "$DESKTOP\Modern Video Downloader.lnk" "$INSTDIR\ModernVideoDownloader.exe"
SectionEnd

# Build con:
makensis installer.nsi
```

### Opzione 2: Auto-Updater con Delta Updates

Per file grandi, scarica solo le differenze:

```bash
# Usa bsdiff per delta patching
pip install bsdiff4

# Crea delta patch:
bsdiff4.file_diff("old.exe", "new.exe", "update.patch")

# Applica patch:
bsdiff4.file_patch("old.exe", "new.exe", "update.patch")
```

---

## ✅ Checklist Finale

Prima di rilasciare una nuova versione:

- [ ] ✅ Versione aggiornata in `__init__.py`
- [ ] ✅ Changelog scritto e completo
- [ ] ✅ Tests passati (quando aggiunti)
- [ ] ✅ Commit pushato a `main`
- [ ] ✅ Tag creato e pushato (`v0.x.x`)
- [ ] ✅ .exe buildato con PyInstaller
- [ ] ✅ .exe testato manualmente
- [ ] ✅ Release creata su GitHub
- [ ] ✅ .exe allegato e rinominato correttamente
- [ ] ✅ Release pubblicata (non draft)
- [ ] ✅ Testato "Check Update" dalla versione precedente

---

## 🎯 Best Practices

### 1. Semantic Versioning

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (1.0.0 → 2.0.0)
MINOR: New features backward-compatible (0.4.0 → 0.5.0)
PATCH: Bug fixes (0.4.1 → 0.4.2)
```

### 2. Changelog Format

```markdown
## v0.5.0 - 2026-02-01

### ✨ Added
- Auto-update system with GUI
- Keyboard shortcut Ctrl+U for update check

### 🔄 Changed
- Improved download speed by 20%
- Updated yt-dlp to latest version

### 🐛 Fixed
- Fixed crash on invalid URL
- Fixed memory leak in queue processing

### 🗑️ Removed
- Removed deprecated legacy format support
```

### 3. Pre-release Testing

```bash
# Crea pre-release per testing
git tag v0.5.0-beta.1
gh release create v0.5.0-beta.1 --prerelease
```

---

## 📚 Risorse Utili

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Semantic Versioning](https://semver.org/)
- [NSIS Documentation](https://nsis.sourceforge.io/Docs/)

---

**Fatto! 🎉**

Ora il tuo Modern Video Downloader ha un sistema di auto-update professionale!

Gli utenti riceveranno notifiche automatiche e potranno aggiornare con un click. 🚀
