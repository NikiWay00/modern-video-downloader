# 🚀 Quick Start - Sistema Auto-Update

Guida rapida per configurare e testare il sistema di auto-update in **5 minuti**.

---

## ⚡ Setup Veloce

### 1️⃣ Configura Repository (30 secondi)

Apri [`src/mvd/updater.py`](src/mvd/updater.py) e modifica le righe 22-23:

```python
GITHUB_REPO_OWNER = "TuoUsername"      # ← Il tuo username GitHub
GITHUB_REPO_NAME = "nome-tuo-repo"    # ← Il nome del repository
```

**Esempio:**
```python
GITHUB_REPO_OWNER = "Vegeta123"
GITHUB_REPO_NAME = "ModernVideoDownloader"
```

### 2️⃣ Crea Repository GitHub (2 minuti)

```bash
# Nella directory del progetto:
cd "c:\Users\Vegeta\Desktop\progetti xcode\modern_video_downloader"

# Inizializza git
git init
git add .
git commit -m "Initial commit - v0.4.1"

# Crea repository su GitHub:
# 1. Vai su github.com
# 2. Click "New repository"
# 3. Nome: "ModernVideoDownloader" (o quello che preferisci)
# 4. Public
# 5. Create repository

# Collega locale a GitHub (sostituisci con il tuo URL)
git remote add origin https://github.com/NikiWay00/ModernVideoDownloader.git
git branch -M main
git push -u origin main
```

### 3️⃣ Testa il Bottone (10 secondi)

```bash
# Avvia l'app
python run.py
```

In alto a destra vedrai: **"🔄 Check Update"**

Click! Dovrebbe dire: **"✅ Stai già usando l'ultima versione! Versione corrente: 0.4.1"**

✅ **Sistema configurato!**

---

## 🎯 Test Completo: Simulare un Update

Vogliamo testare l'intero flusso come se stessimo rilasciando v0.5.0:

### Step 1: Crea una "fake" v0.5.0

```bash
# 1. Aggiorna versione
# Apri src/mvd/__init__.py e cambia:
__version__ = "0.5.0"

# 2. Commit
git add src/mvd/__init__.py
git commit -m "Bump version to 0.5.0"
git push origin main

# 3. Crea tag
git tag v0.5.0
git push origin v0.5.0
```

### Step 2: Crea Release su GitHub

1. Vai su `https://github.com/TuoUsername/ModernVideoDownloader/releases`
2. Click **"Draft a new release"**
3. Compila:

```
Choose a tag:     v0.5.0
Release title:    Modern Video Downloader v0.5.0
Description:      ## Test Release

                  ### ✨ New Features
                  - 🔄 Auto-update system
                  - ⚡ Faster downloads

                  ### 🐛 Fixes
                  - Various bug fixes
```

4. **IMPORTANTE:** Allega un file .exe
   - Se non hai ancora buildato .exe, crea un file dummy:
     ```bash
     echo "test" > ModernVideoDownloader-v0.5.0.exe
     ```
   - Drag & drop nella sezione "Attach binaries"

5. Click **"Publish release"** ✅

### Step 3: Testa Update dalla v0.4.1

```bash
# 1. Torna alla versione 0.4.1
# Apri src/mvd/__init__.py e cambia:
__version__ = "0.4.1"

# 2. Riavvia app (NON fare commit!)
python run.py

# 3. Click "🔄 Check Update"
```

**Aspettato:**

```
┌─────────────────────────────────────────┐
│  🎉 Nuova Versione Disponibile: v0.5.0  │
├─────────────────────────────────────────┤
│  📦 Dimensione: 0.0 MB                  │
│                                         │
│  📝 Novità:                             │
│  ┌─────────────────────────────────┐   │
│  │ ## Test Release                 │   │
│  │                                 │   │
│  │ ### ✨ New Features              │   │
│  │ - Auto-update system            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [⬇️ Scarica e Installa]  [❌ Più Tardi]│
└─────────────────────────────────────────┘
```

✅ **Funziona!**

---

## 🏗️ Build .exe per Release Vera

Quando sei pronto per una release vera:

### 1. Installa PyInstaller

```bash
pip install pyinstaller
```

### 2. Build

```bash
# Usa il file build.spec che ho creato
pyinstaller build.spec
```

**Output:** `dist/ModernVideoDownloader.exe`

### 3. Test .exe

```bash
# Testa che funzioni
dist\ModernVideoDownloader.exe
```

### 4. Upload a Release

- Vai sulla release GitHub
- Upload `ModernVideoDownloader.exe`
- **Rinomina** in: `ModernVideoDownloader-v0.5.0.exe`

---

## 🎨 Personalizzazioni Opzionali

### Cambiare Colore Bottone Update

In [`src/mvd/gui.py`](src/mvd/gui.py), cerca `_build_header()`:

```python
# Cambia colore bottone
fg_color=COLORS.BTN_PRIMARY,        # ← Colore principale
hover_color=COLORS.BTN_PRIMARY_HOVER # ← Colore hover
```

### Aggiungere Shortcut Keyboard

In [`src/mvd/config.py`](src/mvd/config.py):

```python
@dataclass(frozen=True)
class KeyboardShortcuts:
    CHECK_UPDATE: str = "<Control-u>"  # ← Aggiungi questa riga
    # ...
```

In [`src/mvd/gui.py`](src/mvd/gui.py), nel metodo `_setup_keyboard_shortcuts()`:

```python
self.bind(KEYBOARD.CHECK_UPDATE, lambda e: self._check_for_updates())
```

Ora **Ctrl+U** controlla update!

---

## 📊 Verifica Checklist

- [ ] ✅ `updater.py` configurato con USERNAME e REPO corretti
- [ ] ✅ Repository GitHub creato e pushato
- [ ] ✅ Tag `v0.4.1` creato e pushato
- [ ] ✅ Bottone "Check Update" visibile nell'app
- [ ] ✅ Click su "Check Update" funziona (nessun errore)
- [ ] ✅ Test con release fake v0.5.0 completato
- [ ] ✅ Dialog update mostrato correttamente
- [ ] ✅ (Opzionale) .exe buildato con PyInstaller

---

## 🐛 Problemi Comuni

### "Repository non trovato (404)"

**Fix:** Verifica USERNAME e REPO in `updater.py`

Test URL nel browser:
```
https://api.github.com/repos/TuoUsername/TuoRepo/releases/latest
```

Deve restituire JSON, non errore.

### "Nessun asset compatibile"

**Fix:** Rinomina file allegato in `...v0.x.x.exe` con `.exe` visibile.

### "Errore di rete"

**Fix:** Controlla connessione internet. Testa:
```bash
curl https://api.github.com
```

---

## 🎉 Completato!

Ora hai:

✅ Sistema auto-update funzionante
✅ Bottone "Check Update" nell'app
✅ Dialog professionale con changelog
✅ Download e installazione automatica
✅ GitHub Releases configurato

**Gli utenti potranno aggiornare con un click!** 🚀

---

**Next Steps:**

1. ✅ Leggi [`RELEASE_GUIDE.md`](RELEASE_GUIDE.md) per workflow completo
2. ✅ Crea primo vero .exe con PyInstaller
3. ✅ Rilascia v0.5.0 ufficiale con nuove features
4. ✅ Condividi il tuo progetto! 🎊
