from __future__ import annotations
from pathlib import Path
import os, time, webbrowser
from typing import Optional
from PySide6.QtCore import Qt, QProcess, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QHBoxLayout,
    QComboBox, QRadioButton, QGroupBox, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QPlainTextEdit, QSplitter, QAbstractItemView, QStatusBar, QMenuBar, QMenu, QInputDialog,
    QProgressDialog, QTextEdit, QDialog, QDialogButtonBox, QFileDialog, QCheckBox
)

# Theme / Runtimes
from app.core.theme import ThemeManager, SCHEMES
from app.core.venv_tools import EXPECTED, is_created, validate, details
from app.core.runtime_registry import rescan_and_update

# Ollama client (stream + non-stream)
from app.core.ollama_tools import (
    server_ok, list_models, pull_model, delete_model, prompt, prompt_stream_iter,
    list_conversations, load_conversation, save_conversation,
    which_ollama, install_ollama_linux, install_ollama_windows
)

# UI utilities & dialogs
from app.core.shortcuts import ActionSpec, attach_actions
from app.core.command_palette import CommandPalette
from app.core.plugins import discover_actions
from app.ui.quick_model_dialog import QuickModelDialog
from app.ui.shortcuts_help import ShortcutsHelp
from app.ui.quick_tour import QuickTour
from app.ui.diagnostics_dialog import DiagnosticsDialog
from app.ui.quick_llm_dialog import QuickLLMDialog
from app.ui.license_dialog import LicenseDialog

# Config
from app.core.settings import load_config, save_config


class _TextDialog(QDialog):
    def __init__(self, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(820, 600)
        lay = QVBoxLayout(self)
        view = QPlainTextEdit(self); view.setReadOnly(True); view.setPlainText(text)
        lay.addWidget(view, 1)
        btns = QDialogButtonBox(QDialogButtonBox.Close, self)
        btns.rejected.connect(self.reject); btns.clicked.connect(self.close)
        lay.addWidget(btns)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI For The People — Hub")
        self.resize(1000, 720)

        self.theme = ThemeManager(); self.theme.apply()
        self.config = load_config()

        self._conv_name = "default"
        self._current_model: Optional[str] = None

        self._status = QStatusBar(self); self.setStatusBar(self._status)
        self._build_menu()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._overview_tab(), "Overview")
        self.tabs.addTab(self._theme_tab(), "Theme")
        self.tabs.addTab(self._runtimes_tab(), "Runtimes")
        self.tabs.addTab(self._ollama_tab(), "Ollama")
        self.setCentralWidget(self.tabs)

        self._wire_shortcuts()
        self._update_status()

        self._stream_thread: Optional[QThread] = None
        self._stream_worker: Optional[MainWindow._StreamWorker] = None

        if self.config.get("show_licenses_on_start", True):
            self._open_licenses()
            self.config["show_licenses_on_start"] = False
            save_config(self.config)

    # ===== Menu =====
    def _build_menu(self):
        bar = QMenuBar(self); self.setMenuBar(bar)

        filem: QMenu = bar.addMenu("&File")
        act_quit = QAction("Quit", self); act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close); filem.addAction(act_quit)

        toolsm: QMenu = bar.addMenu("&Tools")
        act_diag = QAction("Diagnostics…", self)
        act_diag.triggered.connect(lambda: DiagnosticsDialog(self).exec())
        toolsm.addAction(act_diag)

        helpm: QMenu = bar.addMenu("&Help")
        act_short = helpm.addAction("Shortcuts…"); act_short.setShortcut("F1")
        act_short.triggered.connect(lambda: ShortcutsHelp(self).exec())
        act_tour = helpm.addAction("Quick Tour…"); act_tour.setShortcut("Shift+F1")
        act_tour.triggered.connect(self._open_quick_tour)
        helpm.addSeparator()
        helpm.addAction("Licenses & Notices").triggered.connect(self._open_licenses)

    # ===== Overview =====
    def _overview_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        t = QLabel("<b>Hub Template</b><br>Set theme and prepare runtimes; real apps reuse these.")
        t.setWordWrap(True); lay.addWidget(t)
        how = QLabel(
            "• Theme → pick scheme.<br>"
            "• Runtimes → create/validate venvs.<br>"
            "• Ollama → set models dir/port, start/stop, manage models, ask questions.<br>"
            "• Help → Licenses."
        )
        how.setWordWrap(True); lay.addWidget(how); lay.addStretch(1)
        return w

    # ===== Theme =====
    def _theme_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)

        grp_mode = QGroupBox("Mode"); rlay = QHBoxLayout(grp_mode)
        r_dark = QRadioButton("Dark"); r_light = QRadioButton("Light")
        r_dark.setChecked(self.theme.mode() == "dark")
        r_light.setChecked(self.theme.mode() == "light")
        r_dark.toggled.connect(lambda on: on and self.theme.set_mode("dark"))
        r_light.toggled.connect(lambda on: on and self.theme.set_mode("light"))
        rlay.addWidget(r_dark); rlay.addWidget(r_light); rlay.addStretch(1)

        grp_scheme = QGroupBox("Accent Scheme (two colors)"); s_lay = QHBoxLayout(grp_scheme)
        combo = QComboBox()
        for s in SCHEMES: combo.addItem(s.name, s.key)
        for i in range(combo.count()):
            if combo.itemData(i) == self.theme._data.get("scheme", "aftp_signature"):
                combo.setCurrentIndex(i); break
        combo.currentIndexChanged.connect(lambda i: self.theme.set_scheme(combo.itemData(i)))
        s_lay.addWidget(combo); s_lay.addStretch(1)

        grp_custom = QGroupBox("Custom Accent (optional)"); f = QFormLayout(grp_custom)
        p1 = QLineEdit(); p2 = QLineEdit()
        p1.setPlaceholderText("#RRGGBB for primary"); p2.setPlaceholderText("#RRGGBB for secondary")
        btn_apply = QPushButton("Apply"); btn_clear = QPushButton("Clear")
        btn_apply.clicked.connect(lambda: self._apply_custom(p1.text(), p2.text()))
        btn_clear.clicked.connect(self.theme.clear_custom_accent)
        f.addRow("Primary", p1); f.addRow("Secondary", p2); f.addRow(btn_apply, btn_clear)

        lay.addWidget(grp_mode); lay.addWidget(grp_scheme); lay.addWidget(grp_custom); lay.addStretch(1)
        return w

    def _apply_custom(self, primary: str, secondary: str):
        primary = primary.strip(); secondary = secondary.strip()
        if not primary:
            QMessageBox.information(self, "Accent", "Enter at least primary color (e.g., #D64545)."); return
        self.theme.set_custom_accent(primary, secondary or None)

    # ===== Runtimes =====
    def _runtimes_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)

        desc = QLabel("Create/validate venvs. Progress/logs appear below. Use Details for per-module info.")
        desc.setWordWrap(True)
        toprow = QHBoxLayout(); toprow.addWidget(desc)
        helpbtn = QPushButton("?"); helpbtn.setFixedWidth(28); helpbtn.setToolTip("Quick Tour")
        helpbtn.clicked.connect(self._open_quick_tour)
        toprow.addStretch(1); toprow.addWidget(helpbtn); lay.addLayout(toprow)

        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(["Name", "Status", "Backend", "Create/Update", "Validate", "Details", "Log"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._venv_table = table

        names = sorted(EXPECTED.keys()) + ["mamba2"]
        table.setRowCount(len(names))

        self._op_log = QTextEdit(); self._op_log.setReadOnly(True); self._op_log.hide()

        def run_script(script_path: str, on_done):
            dlg = QProgressDialog("Working…", "", 0, 0, self)
            dlg.setWindowTitle("Installing / Updating")
            dlg.setCancelButton(None)
            dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
            dlg.show()
            proc = QProcess(self)
            proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            if os.name == "nt":
                proc.setProgram("powershell"); proc.setArguments(["-ExecutionPolicy","Bypass","-File", script_path])
            else:
                proc.setProgram("bash"); proc.setArguments([script_path])
            proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
            proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
            def finished(code, status): dlg.close(); on_done(code)
            proc.finished.connect(finished); proc.start()

        def make_run(name, st_item):
            def _run():
                script = f"scripts/setup_venv_{name}.sh" if os.name != "nt" else f"scripts\\setup_venv_{name}.ps1"
                if not os.path.exists(script):
                    QMessageBox.warning(self, "Script missing", f"{script} not found."); return
                st_item.setText("installing…"); self._op_log.clear(); self._op_log.show()
                def done(_code):
                    ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
                    st_item.setText("created" if ok else ("missing" if missing == ["_venv_missing_"] else "missing: " + ", ".join(missing)))
                    QMessageBox.information(self, "Result", f"{name}: {'OK' if ok else 'Missing: ' + ', '.join(missing)}")
                run_script(script, done)
            return _run

        def make_validate(name):
            def _val():
                ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
                if ok: QMessageBox.information(self, "Validate", f"{name}: OK")
                else:
                    if missing == ["_venv_missing_"]: QMessageBox.warning(self, "Validate", f"{name}: venv not created yet.")
                    else: QMessageBox.warning(self, "Validate", f"{name}: missing imports: {', '.join(missing)}")
            return _val

        def make_details(name):
            def _det():
                info = details(name); txt=[]
                for mod, d in info.items():
                    if d.get("ok"): txt.append(f"✔ {mod}  —  {d.get('version') or '(version unknown)'}")
                    else: txt.append(f"✖ {mod}  —  {d.get('error','import failed')}")
                if not txt: txt=["(no modules defined for this venv)"]
                _TextDialog(f"{name} — Import details", "\n".join(txt), self).exec()
            return _det

        for row, name in enumerate(names):
            backend_btn = QPushButton("Backend…")
            def _pick_backend(n=name, row=row):
                choices = ["cpu"]
                if n in ("image","ai_dev","stt"): choices += ["cuda","rocm","intel"]
                if n == "embeddings": choices += ["cuda"]
                choice, ok = QInputDialog.getItem(self, f"{n} backend", "Select:", choices, 0, False)
                if not ok: return
                if os.name == "nt":
                    script = {"cpu":f"scripts\\setup_venv_{n}_cpu.ps1","cuda":f"scripts\\setup_venv_{n}_cuda.ps1","rocm":f"scripts\\setup_venv_{n}_rocm.ps1","intel":f"scripts\\setup_venv_{n}_intel.ps1"}.get(choice)
                else:
                    script = {"cpu":f"scripts/setup_venv_{n}_cpu.sh","cuda":f"scripts/setup_venv_{n}_cuda.sh","rocm":f"scripts/setup_venv_{n}_rocm.sh","intel":f"scripts/setup_venv_{n}_intel.sh"}.get(choice)
                if script and os.path.exists(script):
                    st_item = table.item(row, 1)
                    def after(_code):
                        ok, missing = validate(n) if n in EXPECTED else (is_created(n), [])
                        st_item.setText("created" if ok else ("missing" if missing == ["_venv_missing_"] else "missing: " + ", ".join(missing)))
                    self._op_log.clear(); self._op_log.show()
                    dlg = QProgressDialog("Installing backend…", "", 0, 0, self); dlg.setCancelButton(None); dlg.setWindowModality(Qt.ApplicationModal); dlg.show()
                    proc = QProcess(self)
                    if os.name == "nt": proc.setProgram("powershell"); proc.setArguments(["-ExecutionPolicy","Bypass","-File", script])
                    else: proc.setProgram("bash"); proc.setArguments([script])
                    proc.setProcessChannelMode(QProcess.MergedChannels)
                    proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
                    proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
                    proc.finished.connect(lambda *_: (dlg.close(), after(0))); proc.start()
                else:
                    QMessageBox.information(self, "Backend", f"No installer for {n}:{choice} on this OS yet.")
            backend_btn.clicked.connect(_pick_backend); table.setCellWidget(row, 2, backend_btn)

            table.setItem(row, 0, QTableWidgetItem(name))
            ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
            status = "created" if ok else ("missing" if missing == ["_venv_missing_"] else f"missing: {', '.join(missing)}")
            st_item = QTableWidgetItem(status); table.setItem(row, 1, st_item)

            btn_run = QPushButton("Create/Update"); btn_run.clicked.connect(make_run(name, st_item)); table.setCellWidget(row, 3, btn_run)
            btn_val = QPushButton("Validate"); btn_val.clicked.connect(make_validate(name)); table.setCellWidget(row, 4, btn_val)
            btn_det = QPushButton("Details"); btn_det.clicked.connect(make_details(name)); table.setCellWidget(row, 5, btn_det)
            logbtn = QPushButton("Open Log"); logbtn.clicked.connect(lambda _=None: self._op_log.show()); table.setCellWidget(row, 6, logbtn)

        table.resizeColumnsToContents(); lay.addWidget(table, 1)

        bottom = QHBoxLayout(); btn_check_all = QPushButton("Check All"); btn_refresh = QPushButton("Refresh Status")
        btn_check_all.clicked.connect(self._check_all_venvs); btn_refresh.clicked.connect(self._refresh_runtime_status)
        bottom.addWidget(btn_check_all); bottom.addStretch(1); bottom.addWidget(btn_refresh); lay.addLayout(bottom)

        lay.addWidget(self._op_log, 1)
        return w

    # ===== Ollama =====
    def _ollama_tab(self) -> QWidget:
        w = QWidget(); outer = QVBoxLayout(w)

        top1 = QHBoxLayout(); self.lbl_srv = QLabel("Server: (checking…)"); top1.addWidget(self.lbl_srv)
        btn_loc = QPushButton("Locate/Install"); btn_lic = QPushButton("License (Website)")
        top1.addStretch(1); top1.addWidget(btn_loc); top1.addWidget(btn_lic); outer.addLayout(top1)

        row_dir = QHBoxLayout()
        row_dir.addWidget(QLabel("Models dir:"))
        self.lbl_models_dir = QLabel(self.config.get("ollama_models_dir", "(default ~/.ollama)"))
        self.lbl_models_dir.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        btn_dir = QPushButton("Change…"); btn_start = QPushButton("Start Server with this folder"); btn_stop = QPushButton("Force Stop Server"); btn_un = QPushButton("Uninstall Ollama…")
        row_dir.addWidget(self.lbl_models_dir, 1); row_dir.addWidget(btn_dir); row_dir.addWidget(btn_start); row_dir.addWidget(btn_stop); row_dir.addWidget(btn_un)
        outer.addLayout(row_dir)

        row_port = QHBoxLayout(); row_port.addWidget(QLabel("Port:"))
        self.edit_ollama_port = QLineEdit(self); self.edit_ollama_port.setFixedWidth(100); self.edit_ollama_port.setText(str(self.config.get("ollama_port", 11434)))
        row_port.addWidget(self.edit_ollama_port); row_port.addStretch(1); outer.addLayout(row_port)

        top2 = QHBoxLayout()
        self.cmb_model = QComboBox(); self.btn_refresh_models = QPushButton("↻"); self.btn_delete_model = QPushButton("Delete")
        self.cmb_conv = QComboBox(); self.btn_new_conv = QPushButton("+")
        top2.addWidget(QLabel("Model:")); top2.addWidget(self.cmb_model, 1); top2.addWidget(self.btn_refresh_models); top2.addWidget(self.btn_delete_model)
        top2.addSpacing(12)
        top2.addWidget(QLabel("Conversation:")); top2.addWidget(self.cmb_conv, 1); top2.addWidget(self.btn_new_conv)
        outer.addLayout(top2)

        adv = QHBoxLayout(); self.pull_edit = QLineEdit(); self.pull_edit.setPlaceholderText("Advanced: pull model (e.g., qwen2.5:7b)")
        self.btn_pull = QPushButton("Pull"); adv.addWidget(self.pull_edit, 1); adv.addWidget(self.btn_pull); outer.addLayout(adv)

        split = QSplitter(Qt.Orientation.Vertical)
        up = QWidget(); up_l = QVBoxLayout(up)
        self.inp = QPlainTextEdit(); self.inp.setPlaceholderText("Type a quick prompt to the current model…")

        row_opts = QHBoxLayout()
        self.chk_stream = QCheckBox("Stream"); self.chk_stream.setChecked(True)
        self.chk_md = QCheckBox("Markdown"); self.chk_md.setChecked(True)
        row_opts.addWidget(self.chk_stream); row_opts.addWidget(self.chk_md); row_opts.addStretch(1)
        self.btn_send = QPushButton("Send (Ctrl+Enter)"); row_opts.addWidget(self.btn_send)

        up_l.addWidget(self.inp, 1); up_l.addLayout(row_opts)

        down = QWidget(); down_l = QVBoxLayout(down)
        self.out = QTextEdit(); self.out.setReadOnly(True); down_l.addWidget(self.out, 1)

        split.addWidget(up); split.addWidget(down); outer.addWidget(split, 1)

        btn_dir.clicked.connect(self._choose_ollama_dir)
        btn_start.clicked.connect(self._start_ollama_with_dir)
        btn_stop.clicked.connect(lambda _=None: (self._stop_ollama_server(True), self._refresh_server_state()))
        btn_un.clicked.connect(self._uninstall_ollama_dialog)
        btn_loc.clicked.connect(self._locate_or_install_ollama)
        btn_lic.clicked.connect(lambda: webbrowser.open("https://ollama.com"))

        self.btn_refresh_models.clicked.connect(self._load_models)
        self.btn_delete_model.clicked.connect(self._delete_selected_model)
        self.btn_new_conv.clicked.connect(self._new_conv)
        self.cmb_model.currentIndexChanged.connect(lambda _: self._on_model_changed())
        self.cmb_conv.currentIndexChanged.connect(lambda _: self._on_conv_changed())
        self.btn_pull.clicked.connect(self._pull_now)
        self.btn_send.clicked.connect(self._send_prompt)
        self.inp.keyPressEvent = self._prompt_keypress(self.inp.keyPressEvent)

        self._refresh_server_state(); self._load_models(); self._load_conversations()
        return w

    # ===== streaming worker =====
    class _StreamWorker(QObject):
        chunk = Signal(str); done = Signal(str); error = Signal(str)
        def __init__(self, model: str, text: str, config: dict | None):
            super().__init__(); self.model, self.text, self.config = model, text, config
        def run(self):
            try:
                acc: list[str] = []
                for piece in prompt_stream_iter(self.model, self.text, config=self.config, options=None, timeout=600):
                    if piece: acc.append(piece); self.chunk.emit(piece)
                self.done.emit("".join(acc))
            except Exception as e:
                self.error.emit(str(e))

    # ===== helpers =====
    def _render_reply_markdown(self, text: str):
        if getattr(self, "chk_md", None) and self.chk_md.isChecked():
            try: self.out.setMarkdown(text); return
            except Exception: pass
        self.out.setPlainText(text)

    def _refresh_server_state(self):
        ok = server_ok(self.config)
        self.lbl_srv.setText("Server: ✅ running" if ok else "Server: ❌ not reachable (127.0.0.1:11434)")
        enabled = bool(ok)
        for w in (self.cmb_model, self.cmb_conv, self.btn_refresh_models, self.btn_pull, self.btn_send, self.btn_delete_model): w.setEnabled(enabled)
        self._update_status(); return ok

    def _load_models(self):
        self.cmb_model.clear()
        if not server_ok(self.config): self.cmb_model.addItem("(no server)"); return
        models = list_models(self.config)
        if not models: self.cmb_model.addItem("(no models yet)")
        else:
            for m in models: self.cmb_model.addItem(m)
        if self._current_model is None and models:
            self._current_model = models[0]; self._set_combo_current_text(self.cmb_model, self._current_model)
        self._update_status()

    def _delete_selected_model(self):
        name = self.cmb_model.currentText().strip()
        if not name or name.startswith("("):
            QMessageBox.information(self, "Delete", "Pick a model to delete."); return
        if QMessageBox.question(self, "Delete model", f"Delete '{name}' from Ollama? This cannot be undone.") != QMessageBox.StandardButton.Yes: return
        ok, msg = delete_model(name, self.config)
        if ok: QMessageBox.information(self, "Delete", f"Deleted {name}."); self._load_models()
        else: QMessageBox.warning(self, "Delete", f"Failed: {msg}")

    def _load_conversations(self):
        names = list_conversations() or ["default"]
        self.cmb_conv.clear()
        for n in names: self.cmb_conv.addItem(n)
        self._set_combo_current_text(self.cmb_conv, getattr(self, "_conv_name", "default"))
        self._update_status()

    def _new_conv(self):
        i = 1; existing = set(list_conversations())
        while True:
            nm = f"conv_{i}"
            if nm not in existing: break
            i += 1
        self._conv_name = nm
        save_conversation(nm, {"id": nm, "model": self._current_model, "messages": []})
        self._load_conversations()

    def _on_model_changed(self):
        self._current_model = self.cmb_model.currentText()
        data = load_conversation(getattr(self, "_conv_name", "default"))
        data["model"] = self._current_model; save_conversation(self._conv_name, data); self._update_status()

    def _on_conv_changed(self):
        self._conv_name = self.cmb_conv.currentText()
        data = load_conversation(self._conv_name)
        if data.get("model"): self._set_combo_current_text(self.cmb_model, data["model"])
        self._update_status()

    def _pull_now(self):
        name = self.pull_edit.text().strip()
        if not name: return
        if not self._maybe_show_model_notice(): return
        ok, msg = pull_model(name, self.config)
        QMessageBox.information(self, "Pull", f"{'OK' if ok else 'Failed'}: {msg}")
        self._load_models()

    def _send_prompt(self):
        if not server_ok(self.config):
            QMessageBox.warning(self, "Ollama", "Server not reachable at 127.0.0.1:11434 (or configured host)."); return
        model = (self._current_model or self.cmb_model.currentText()).strip()
        if not model or model.startswith("("):
            QMessageBox.information(self, "Ollama", "Pick a model first."); return
        text = self.inp.toPlainText().strip()
        if not text: return

        # save user message immediately
        try:
            data = load_conversation(getattr(self, "_conv_name", "default"))
            msgs = data.get("messages", []); msgs.append({"role":"user","content":text})
            data["messages"] = msgs; data["model"] = model; save_conversation(getattr(self, "_conv_name", "default"), data)
        except Exception: pass

        self.out.clear()
        if not (getattr(self, "chk_stream", None) and self.chk_stream.isChecked()):
            ok, resp = prompt(model, text, config=self.config)
            out = resp if ok else f"[error] {resp}"
            self._render_reply_markdown(out)
            try:
                data = load_conversation(getattr(self, "_conv_name", "default"))
                msgs = data.get("messages", []); msgs.append({"role":"assistant","content":out})
                data["messages"] = msgs; data["model"] = model; save_conversation(getattr(self, "_conv_name", "default"), data)
            except Exception: pass
            return

        # stream
        self._stop_stream_thread()
        self._stream_thread = QThread(self)
        self._stream_worker = MainWindow._StreamWorker(model, text, self.config)
        self._stream_worker.moveToThread(self._stream_thread)
        self._stream_thread.started.connect(self._stream_worker.run)
        self._stream_worker.chunk.connect(self._on_stream_chunk)
        self._stream_worker.done.connect(self._on_stream_done)
        self._stream_worker.error.connect(self._on_stream_error)
        self._stream_thread.start()

    def _on_stream_chunk(self, piece: str):
        try:
            cur = self.out.textCursor(); cur.movePosition(QTextCursor.End)
            cur.insertText(piece.replace("\r\n","\n")); self.out.setTextCursor(cur)
        except Exception:
            self.out.setPlainText((self.out.toPlainText() or "") + piece)

    def _on_stream_done(self, final_text: str):
        try:
            if getattr(self, "chk_md", None) and self.chk_md.isChecked():
                self.out.clear(); self.out.setMarkdown(final_text)
            else:
                self.out.setPlainText(final_text)
        except Exception:
            self.out.setPlainText(final_text)
        self._stop_stream_thread()
        try:
            data = load_conversation(getattr(self, "_conv_name", "default"))
            msgs = data.get("messages", []); msgs.append({"role":"assistant","content":final_text})
            data["messages"] = msgs; data["model"] = self._current_model or self.cmb_model.currentText().strip()
            save_conversation(getattr(self, "_conv_name", "default"), data)
        except Exception: pass

    def _on_stream_error(self, err: str):
        try: self.out.append(f"\n[error] {err}")
        except Exception: pass
        self._stop_stream_thread()

    def _stop_stream_thread(self):
        try:
            if self._stream_thread is not None:
                self._stream_thread.quit(); self._stream_thread.wait(2000)
        except Exception: pass
        self._stream_thread = None; self._stream_worker = None

    def _maybe_show_model_notice(self) -> bool:
        try:
            cfg = load_config()
            if not cfg.get("show_model_license_notice", True): return True
            box = QMessageBox(self); box.setWindowTitle("Model licenses")
            box.setText("Models in the Ollama library have their own licenses and terms.\nYou can review them on the Ollama website before pulling models.")
            yes = box.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
            open_site = box.addButton("Open Model Library", QMessageBox.ButtonRole.ActionRole)
            no = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            box.setIcon(QMessageBox.Icon.Information); box.exec()
            if box.clickedButton() is open_site: webbrowser.open("https://ollama.com/library"); return False
            if box.clickedButton() is yes: cfg["show_model_license_notice"] = False; save_config(cfg); return True
            return False
        except Exception:
            return True

    # ===== Runtimes helpers =====
    def _refresh_runtime_status(self):
        try: rescan_and_update(EXPECTED)
        except Exception: pass
        table = getattr(self, "_venv_table", None)
        if not table: return
        for row in range(table.rowCount()):
            name = table.item(row, 0).text(); st_item = table.item(row, 1)
            if not st_item: continue
            ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
            st_item.setText("created" if ok else ("missing" if missing == ["_venv_missing_"] else f"missing: {', '.join(missing)}"))

    def _check_all_venvs(self):
        rows = getattr(self, "_venv_table", None).rowCount() if getattr(self, "_venv_table", None) else 0
        lines = []
        for r in range(rows):
            name = self._venv_table.item(r, 0).text()
            ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
            if ok: lines.append(f"{name}: OK")
            else:
                if missing == ["_venv_missing_"]: lines.append(f"{name}: venv not created yet")
                else: lines.append(f"{name}: missing imports: {', '.join(missing)}")
        _TextDialog("Venv Check — Summary", "\n".join(lines) if lines else "(no rows)", self).exec()

    # ===== Shortcuts / Help =====
    def _wire_shortcuts(self):
        def show_theme_tab(): self.tabs.setCurrentIndex(1)
        def show_runtimes_tab(): self.tabs.setCurrentIndex(2)
        def show_ollama_tab(): self.tabs.setCurrentIndex(3)
        def open_palette(): self._open_palette()
        specs = [
            ActionSpec("Quick LLM", "Ctrl+J", self._action_quick_llm),
            ActionSpec("Open Command Palette", "Ctrl+K", open_palette),
            ActionSpec("Open Command Palette (Alt)", "Ctrl+Shift+P", open_palette),
            ActionSpec("Theme / Settings", "Ctrl+,", show_theme_tab),
            ActionSpec("Runtimes", None, show_runtimes_tab),
            ActionSpec("Ollama", "Ctrl+O", show_ollama_tab),
            ActionSpec("Licenses & Notices", None, self._open_licenses),
        ]
        self._actions = attach_actions(self, specs)

    def _open_palette(self):
        cmds = [
            ("Theme / Settings", lambda: self.tabs.setCurrentIndex(1)),
            ("Runtimes",         lambda: self.tabs.setCurrentIndex(2)),
            ("Ollama",           lambda: self.tabs.setCurrentIndex(3)),
            ("Open Licenses",    self._open_licenses),
        ]
        CommandPalette(cmds, self).exec()

    def _open_licenses(self):
        LicenseDialog(self).exec()

    def _update_status(self):
        srv = "Ollama:OK" if server_ok(self.config) else "Ollama:OFF"
        model = self._current_model or "(none)"
        conv = getattr(self, "_conv_name", "default")
        self._status.showMessage(f"{srv} | Model: {model} | Conv: {conv} —  Ctrl+O switch, Ctrl+K commands")

    def _action_quick_llm(self):
        QuickLLMDialog(self).exec()

    def _action_quick_model(self):
        QuickModelDialog(self).exec()

    def _open_quick_tour(self):
        QuickTour(self).exec()

    # ===== Ollama processes =====
    def _locate_or_install_ollama(self):
        path = which_ollama()
        if path and os.path.exists(path):
            QMessageBox.information(self, "Ollama", f"Found: {path}\nIf server isn't running, try 'ollama serve'.")
            webbrowser.open("https://ollama.com"); self._refresh_server_state(); return
        if os.name == "nt":
            install_ollama_windows(Path("scripts") / "install_ollama.ps1")
            QMessageBox.information(self, "Ollama", "Attempted winget install or opened download page.")
        else:
            ok, out = install_ollama_linux(Path("scripts") / "install_ollama.sh")
            QMessageBox.information(self, "Ollama", "Installer finished." if ok else f"Install failed:\n{out}")
        self._refresh_server_state()

    def _choose_ollama_dir(self):
        start = self.config.get("ollama_models_dir", str(Path.home() / ".ollama"))
        path = QFileDialog.getExistingDirectory(self, "Select Ollama models folder", start)
        if not path: return
        self.config["ollama_models_dir"] = path; save_config(self.config)
        self.lbl_models_dir.setText(path)
        QMessageBox.information(self, "Ollama", "Models folder saved. Restart the server via 'Start Server with this folder' to apply.")

    def _start_ollama_with_dir(self):
        if not self._stop_ollama_server(log_to_ui=True):
            QMessageBox.warning(self, "Ollama", "Could not stop existing server."); return
        folder = self.config.get("ollama_models_dir")
        try:
            port = int(self.edit_ollama_port.text()) if hasattr(self, 'edit_ollama_port') else int(self.config.get("ollama_port", 11434))
        except Exception: port = 11434
        self.config["ollama_port"] = port; save_config(self.config)
        env = os.environ.copy(); env["OLLAMA_HOST"] = f"127.0.0.1:{port}"
        if folder:
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
                if os.access(folder, os.W_OK): env["OLLAMA_MODELS"] = folder
                else: QMessageBox.warning(self, "Ollama", f"Models folder not writable: {folder}. Using default (~/.ollama).")
            except Exception as e:
                QMessageBox.warning(self, "Ollama", f"Could not prepare models folder: {folder}\n{e}\nUsing default (~/.ollama).")
        proc = QProcess(self); proc.setProgram("ollama"); proc.setArguments(["serve"]); proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.setEnvironment([f"{k}={v}" for k,v in env.items()])
        proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
        proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
        proc.start(); QTimer.singleShot(1500, self._refresh_server_state); self._op_log.show()
        QMessageBox.information(self, "Ollama", f"Attempted to start server{(' with '+folder) if folder else ''}.")

    def _uninstall_ollama_dialog(self):
        """
        Stop Ollama if running and call scripts/uninstall_ollama.sh (Linux/macOS)
        or try winget on Windows. Optionally purge models folder.
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox, QMessageBox, QProgressDialog
        from PySide6.QtCore import QProcess, Qt
        from pathlib import Path
        import os, sys

        # Confirm dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Uninstall Ollama")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("This will attempt to stop Ollama and uninstall its binary."))
        lay.addWidget(QLabel("Optional: also delete your models folder (can be large)."))
        purge = QCheckBox("Also delete models folder")
        lay.addWidget(purge)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
        lay.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() != QDialog.Accepted:
            return

        # Best-effort stop
        try:
            if os.name != "nt":
                os.system("pkill -f 'ollama serve' >/dev/null 2>&1")
            else:
                os.system("taskkill /IM ollama.exe /F >NUL 2>&1")
        except Exception:
            pass

        # Build command per OS
        models_dir = self.config.get("ollama_models_dir")
        if os.name == "nt":
            # Windows: try winget; no model purge here (users should delete folder manually)
            proc = QProcess(self)
            proc.setProgram("powershell")
            proc.setArguments(["-NoProfile","-ExecutionPolicy","Bypass","-Command","winget uninstall -e --id Ollama.Ollama"])
            proc.setProcessChannelMode(QProcess.MergedChannels)
            # progress UI
            pd = QProgressDialog("Uninstalling Ollama (Windows)…", "", 0, 0, self)
            pd.setCancelButton(None); pd.setWindowModality(Qt.ApplicationModal); pd.show()
            proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
            proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
            proc.finished.connect(lambda *_: (pd.close(), self._refresh_server_state()))
            self._op_log.clear(); self._op_log.show()
            proc.start()
            return

        # Linux/macOS: call uninstall script if present
        script = Path(__file__).resolve().parent.parent.parent / "scripts" / "uninstall_ollama.sh"
        if not script.exists():
            QMessageBox.warning(self, "Uninstall", f"Script not found: {script}\\nOpen https://ollama.com for manual uninstall instructions.")
            return

        args = [str(script)]
        if purge.isChecked():
            args.append("--purge-models")
            if models_dir:
                args += ["--models-dir", models_dir]

        pd = QProgressDialog("Uninstalling Ollama…", "", 0, 0, self)
        pd.setCancelButton(None); pd.setWindowModality(Qt.ApplicationModal); pd.show()
        proc = QProcess(self)
        proc.setProgram("bash")
        proc.setArguments(args)
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
        proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
        proc.finished.connect(lambda *_: (pd.close(), self._refresh_server_state()))
        self._op_log.clear(); self._op_log.show()
        proc.start()
    
    def _stop_ollama_server(self, log_to_ui: bool = True) -> bool:
        def log(msg: str):
            if log_to_ui:
                try: self._op_log.insertPlainText(msg + "\n"); self._op_log.show()
                except Exception: pass
        try:
            if not server_ok(self.config): return True
        except Exception: return True
        log("[Ollama] Attempting to stop server…")
        if os.name != "nt": os.system("pkill -f 'ollama serve' >/dev/null 2>&1")
        else: os.system("taskkill /IM ollama.exe /F >NUL 2>&1")
        for _ in range(12):
            try:
                if not server_ok(self.config): log("[Ollama] Server appears stopped."); return True
            except Exception: return True
            time.sleep(0.5)
        log("[Ollama] Could not stop the server automatically."); return False


    def _prompt_keypress(self, super_impl):
        """Return a keypress handler that sends on Ctrl+Enter."""
        def handler(evt):
            try:
                if (
                    evt.key() in (Qt.Key_Return, Qt.Key_Enter)
                    and (evt.modifiers() & Qt.ControlModifier)
                ):
                    self._send_prompt()
                    return
            except Exception:
                pass
            return super_impl(evt)
        return handler


    def _set_combo_current_text(self, combo: QComboBox, text: str):
        """Set the current index of a QComboBox by visible text, if present."""
        try:
            for i in range(combo.count()):
                if combo.itemText(i) == text:
                    combo.setCurrentIndex(i)
                    return
        except Exception:
            pass
