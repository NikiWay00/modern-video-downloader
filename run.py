import sys
from pathlib import Path

def setup_paths_or_die():
    base_dir = Path(__file__).resolve().parent
    src_dir = base_dir / "src"
    pkg_dir = src_dir / "mvd"

    print("[run.py] FILE :", Path(__file__).resolve())
    print("[run.py] CWD  :", Path.cwd())
    print("[run.py] BASE :", base_dir)
    print("[run.py] SRC  :", src_dir, "exists=", src_dir.exists())
    print("[run.py] MVD  :", pkg_dir, "exists=", pkg_dir.exists())

    if not src_dir.exists():
        raise RuntimeError(f"ERRORE: cartella 'src' non trovata in: {src_dir}")

    if not pkg_dir.exists():
        raise RuntimeError(f"ERRORE: cartella package 'mvd' non trovata in: {pkg_dir}")

    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    print("[run.py] sys.path[0] =", sys.path[0])

def main():
    setup_paths_or_die()
    from mvd.main import main as app_main
    app_main()

if __name__ == "__main__":
    main()
