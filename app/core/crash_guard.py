from __future__ import annotations
import sys, os, time, traceback, pathlib

LOG_DIR = pathlib.Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / f"app_{time.strftime('%Y%m%d_%H%M%S')}.log"

def _write_log(prefix: str, msg: str):
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {prefix}: {msg}\n")
    except Exception:
        pass

def install():
    # 1) Python exceptions
    def excepthook(exc_type, exc, tb):
        details = "".join(traceback.format_exception(exc_type, exc, tb))
        _write_log("EXC", details)
        try:
            from PySide6.QtWidgets import QMessageBox
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:  # show a dialog if we have a GUI
                QMessageBox.critical(None, "AFTP Hub — Crash",
                    f"An unhandled error occurred.\n\nLog:\n{LOG_PATH}\n\nDetails:\n{details[:2000]}")
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = excepthook

    # 2) Route Qt messages to the log
    try:
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType
        def qt_handler(mode, ctx, msg):
            level = {QtMsgType.QtDebugMsg:"DBG", QtMsgType.QtInfoMsg:"INF",
                     QtMsgType.QtWarningMsg:"WRN", QtMsgType.QtCriticalMsg:"CRT",
                     QtMsgType.QtFatalMsg:"FTL"}.get(mode, "QT")
            _write_log(level, msg)
        qInstallMessageHandler(qt_handler)
    except Exception:
        pass

    # 3) Optional: disable fatal Qt warnings that can kill the process
    os.environ.setdefault("QT_FATAL_WARNINGS", "0")
