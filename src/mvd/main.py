from .utils import setup_ffmpeg, setup_logger
from .gui import VideoDownloaderGUI


def main():
    """
    Entry point dell'applicazione
    """
    setup_logger()
    setup_ffmpeg()

    app = VideoDownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
