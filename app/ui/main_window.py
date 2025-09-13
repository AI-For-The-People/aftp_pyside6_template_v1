from __future__ import annotations
from pathlib import Path
import os, webbrowser, shutil, subprocess, platform
from PySide6.QtCore import Qt, QProcess, QTimer, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QHBoxLayout,
    QComboBox, QRadioButton, QGroupBox, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QPlainTextEdit, QSplitter, QAbstractItemView, QStatusBar, QMenuBar, QMenu, QInputDialog, QProgressDialog, QTextEdit,
    QDialog, QDialogButtonBox, QFileDialog, QCheckBox
)
from app.core.theme import ThemeManager, SCHEMES
from app.core.venv_tools import EXPECTED, is_created, validate, details
from app.core.runtime_registry import rescan_and_update, read_registry
from app.core.ollama_tools import (
    server_ok, list_models, pull_model, delete_model, prompt,
    list_conversations, load_conversation, save_conversation,
    which_ollama, install_ollama_linux, install_ollama_windows, license_url
)
from app.core.shortcuts import ActionSpec, attach_actions
from app.core.command_palette import CommandPalette
from app.core.plugins import discover_actions
from app.ui.quick_model_dialog import QuickModelDialog
from app.ui.shortcuts_help import ShortcutsHelp
from app.ui.quick_tour import QuickTour
from app.ui.diagnostics_dialog import DiagnosticsDialog
from app.ui.ghost_complete import GhostCompleter

from app.ui.quick_llm_dialog import QuickLLMDialog
from app.ui.license_dialog import LicenseDialog
from app.core.settings import load_config, save_config
from app.core.licenses import fetch_and_cache_license

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
        self.resize(980, 700)
        self.theme = ThemeManager(); self.theme.apply()
        self._conv_name = "default"; self._current_model = None
        self.config = load_config()
        self._build_menu()

        # Status bar FIRST so _update_status is safe
        self._status = QStatusBar(self); self.setStatusBar(self._status)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._overview_tab(), "Overview")
        self.tabs.addTab(self._theme_tab(), "Theme")
        self.tabs.addTab(self._runtimes_tab(), "Runtimes")
        self.tabs.addTab(self._ollama_tab(), "Ollama")
        self.setCentralWidget(self.tabs)

        self._wire_shortcuts()
        self._update_status()

        if self.config.get("show_licenses_on_start", True):
            self._open_licenses()
            self.config["show_licenses_on_start"] = False
            save_config(self.config)

    def _build_menu(self):
        bar = QMenuBar(self); self.setMenuBar(bar)
        helpm: QMenu = bar.addMenu("&Help")
        act_short = helpm.addAction("Shortcuts…")
        act_short.setShortcut("F1")
        act_short.triggered.connect(lambda: ShortcutsHelp(self).exec())
        act_tour = helpm.addAction("Quick Tour…")
        act_tour.setShortcut("Shift+F1")
        act_tour.triggered.connect(self._open_quick_tour)
        helpm.addSeparator()
        helpm.addAction("Licenses & Notices").triggered.connect(self._open_licenses)

    # ---- Overview ----
    def _overview_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        t = QLabel("<b>Hub Template</b><br>Set theme and prepare runtimes; real apps reuse these.")
        t.setWordWrap(True); lay.addWidget(t)
        how = QLabel("• Theme tab → pick scheme.<br>• Runtimes → create/validate venvs.<br>• Ollama → switch models, manage, quick prompt.<br>• Help → Licenses.")
        how.setWordWrap(True); lay.addWidget(how)
        lay.addStretch(1); return w

    # ---- Theme ----
    def _theme_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        grp_mode = QGroupBox("Mode"); rlay = QHBoxLayout(grp_mode)
        r_dark = QRadioButton("Dark"); r_light = QRadioButton("Light")
        r_dark.setChecked(self.theme.mode()=="dark"); r_light.setChecked(self.theme.mode()=="light")
        r_dark.toggled.connect(lambda on: on and self.theme.set_mode("dark"))
        r_light.toggled.connect(lambda on: on and self.theme.set_mode("light"))
        rlay.addWidget(r_dark); rlay.addWidget(r_light); rlay.addStretch(1)

        grp_scheme = QGroupBox("Accent Scheme (two colors)"); s_lay = QHBoxLayout(grp_scheme)
        combo = QComboBox()
        for s in SCHEMES: combo.addItem(s.name, s.key)
        for i in range(combo.count()):
            if combo.itemData(i)==self.theme._data.get("scheme","aftp_signature"):
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

        lay.addWidget(grp_mode); lay.addWidget(grp_scheme); lay.addWidget(grp_custom); lay.addStretch(1); return w

    def _apply_custom(self, primary: str, secondary: str):
        primary = primary.strip(); secondary = secondary.strip()
        if not primary:
            QMessageBox.information(self, "Accent", "Enter at least primary color (e.g., #D64545)."); return
        self.theme.set_custom_accent(primary, secondary or None)

    # ---- Runtimes ----
    
    
    def _runtimes_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        desc = QLabel("Create/validate venvs. Progress/logs appear below. Use Details for per-module info.")
        desc.setWordWrap(True); toprow = QHBoxLayout(); toprow.addWidget(desc); helpbtn = QPushButton("?"); helpbtn.setFixedWidth(28); helpbtn.setToolTip("Quick Tour"); helpbtn.clicked.connect(self._open_quick_tour); toprow.addStretch(1); toprow.addWidget(helpbtn); lay.addLayout(toprow)

        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(["Name","Status","Backend","Create/Update","Validate","Details","Log"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._venv_table = table

        names = sorted(EXPECTED.keys()) + ["mamba2"]
        table.setRowCount(len(names))

        self._op_log = QTextEdit(); self._op_log.setReadOnly(True); self._op_log.hide()

        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import QProcess, Qt

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
            def finished(code, status):
                dlg.close()
                on_done(code)
            proc.finished.connect(finished)
            proc.start()

        def make_run(name, st_item):
            def _run():
                script = f"scripts/setup_venv_{name}.sh" if os.name != "nt" else f"scripts\\setup_venv_{name}.ps1"
                if not os.path.exists(script):
                    QMessageBox.warning(self, "Script missing", f"{script} not found."); return
                st_item.setText("installing…"); self._op_log.clear(); self._op_log.show()
                def done(code):
                    # refresh status cell by validating
                    ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
                    st_item.setText("created" if ok else ("missing" if missing == ["_venv_missing_"] else "missing: " + ", ".join(missing)))
                    QMessageBox.information(self, "Result",
                        f"{name}: {'OK' if ok else 'Missing: ' + ', '.join(missing)}")
                run_script(script, done)
            return _run

        def make_validate(name):
            def _val():
                ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
                if ok: QMessageBox.information(self, "Validate", f"{name}: OK")
                else:
                    if missing==["_venv_missing_"]: QMessageBox.warning(self,"Validate",f"{name}: venv not created yet.")
                    else: QMessageBox.warning(self,"Validate",f"{name}: missing imports: {', '.join(missing)}")
            return _val

        def make_details(name):
            def _det():
                info = details(name)
                txt = []
                for mod, d in info.items():
                    if d.get("ok"):
                        ver = d.get("version") or "(version unknown)"
                        txt.append(f"✔ {mod}  —  {ver}")
                    else:
                        txt.append(f"✖ {mod}  —  {d.get('error','import failed')}")
                if not txt:
                    txt = ["(no modules defined for this venv)"]
                dlg = _TextDialog(f"{name} — Import details", "\n".join(txt), self)
                dlg.exec()
            return _det

        for row, name in enumerate(names):
            # Backend selector where applicable
            backend_btn = QPushButton("Backend…")
            def _pick_backend(n=name):
                choices = ["cpu"]
                if n in ("image","ai_dev","stt"): choices += ["cuda","rocm","intel"]
                if n == "embeddings": choices += ["cuda"]
                choice, ok = QInputDialog.getItem(self, f"{n} backend", "Select:", choices, 0, False)
                if not ok: return
                # Map to script name
                script = None
                if choice == "cpu": script = f"scripts/setup_venv_{n}_cpu.sh"
                elif choice == "cuda": script = f"scripts/setup_venv_{n}_cuda.sh"
                elif choice == "rocm": script = f"scripts/setup_venv_{n}_rocm.sh"
                elif choice == "intel": script = f"scripts/setup_venv_{n}_intel.sh"
                if script and os.path.exists(script):
                    # Reuse existing runner to show progress & log
                    # Find status item in this row
                    st_item = table.item(row, 1)
                    def after(_code):
                        ok, missing = validate(n) if n in EXPECTED else (is_created(n), [])
                        st_item.setText("created" if ok else ("missing" if missing == ["_venv_missing_"] else "missing: " + ", ".join(missing)))
                    self._op_log.clear(); self._op_log.show()
                    # Run
                    from PySide6.QtCore import QProcess, Qt
                    from PySide6.QtWidgets import QProgressDialog
                    dlg = QProgressDialog("Installing backend…", "", 0, 0, self); dlg.setCancelButton(None); dlg.setWindowModality(Qt.ApplicationModal); dlg.show()
                    proc = QProcess(self)
                    proc.setProgram("bash"); proc.setArguments([script])
                    proc.setProcessChannelMode(QProcess.MergedChannels)
                    proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
                    proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
                    proc.finished.connect(lambda code, status: (dlg.close(), after(code)))
                    proc.start()
                else:
                    QMessageBox.information(self, "Backend", f"No installer for {n}:{choice} on this OS yet.")
            backend_btn.clicked.connect(_pick_backend)
            table.setCellWidget(row, 2, backend_btn)

            table.setItem(row, 0, QTableWidgetItem(name))
            ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
            status = "created" if ok else ("missing" if missing==["_venv_missing_"] else f"missing: {', '.join(missing)}")
            st_item = QTableWidgetItem(status); table.setItem(row, 1, st_item)

            btn_run = QPushButton("Create/Update"); btn_run.clicked.connect(make_run(name, st_item))
            table.setCellWidget(row, 3, btn_run)

            btn_val = QPushButton("Validate"); btn_val.clicked.connect(make_validate(name))
            table.setCellWidget(row, 4, btn_val)

            btn_det = QPushButton("Details"); btn_det.clicked.connect(make_details(name))
            table.setCellWidget(row, 5, btn_det)

            logbtn = QPushButton("Open Log"); logbtn.clicked.connect(lambda _=None: self._op_log.show())
            table.setCellWidget(row, 6, logbtn)

        table.resizeColumnsToContents()
        lay.addWidget(table, 1)

        # Bottom controls
        bottom = QHBoxLayout()
        btn_check_all = QPushButton("Check All")
        btn_refresh = QPushButton("Refresh Status")
        btn_check_all.clicked.connect(self._check_all_venvs)
        btn_refresh.clicked.connect(self._refresh_runtime_status)
        bottom.addWidget(btn_check_all); bottom.addStretch(1); bottom.addWidget(btn_refresh)
        lay.addLayout(bottom)

        lay.addWidget(self._op_log, 1)  # hidden until used
        return w
    
    

    # ---- Ollama ----
    def _ollama_tab(self) -> QWidget:
        w = QWidget(); outer = QVBoxLayout(w)

        top1 = QHBoxLayout()
        self.lbl_srv = QLabel("Server: (checking…)"); top1.addWidget(self.lbl_srv)
        btn_loc = QPushButton("Locate/Install"); btn_lic = QPushButton("License (Website)"); top1.addStretch(1)
        top1.addWidget(btn_loc); top1.addWidget(btn_lic)
        outer.addLayout(top1)
        # Models folder row
        row_dir = QHBoxLayout()
        row_dir.addWidget(QLabel("Models dir:"))
        self.lbl_models_dir = QLabel(self.config.get("ollama_models_dir", "(default ~/.ollama)"))
        self.lbl_models_dir.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        btn_dir = QPushButton("Change…")
        btn_start = QPushButton("Start Server with this folder")
        row_dir.addWidget(self.lbl_models_dir, 1)
        row_dir.addWidget(btn_dir)
        row_dir.addWidget(btn_start)
        btn_stop = QPushButton("Force Stop Server")
        row_dir.addWidget(btn_stop)
        btn_stop.clicked.connect(lambda _=None: (self._stop_ollama_server(True), self._refresh_server_state()))
        btn_un = QPushButton("Uninstall Ollama…")
        row_dir.addWidget(btn_un)
        btn_un.clicked.connect(self._uninstall_ollama_dialog)
        outer.addLayout(row_dir)
        # Port row
        row_port = QHBoxLayout()
        row_port.addWidget(QLabel("Port:"))
        self.edit_ollama_port = QLineEdit(self)
        self.edit_ollama_port.setFixedWidth(100)
        self.edit_ollama_port.setText(str(self.config.get("ollama_port", 11434)))
        row_port.addWidget(self.edit_ollama_port)
        row_port.addStretch(1)
        outer.addLayout(row_port)
        btn_dir.clicked.connect(self._choose_ollama_dir)
        btn_start.clicked.connect(self._start_ollama_with_dir)

        btn_loc.clicked.connect(self._locate_or_install_ollama)
        btn_lic.clicked.connect(self._open_ollama_license)

        top2 = QHBoxLayout()
        self.cmb_model = QComboBox(); self.btn_refresh_models = QPushButton("↻"); self.btn_delete_model = QPushButton("Delete")
        self.cmb_conv = QComboBox(); self.btn_new_conv = QPushButton("+")
        top2.addWidget(QLabel("Model:")); top2.addWidget(self.cmb_model, 1); top2.addWidget(self.btn_refresh_models); top2.addWidget(self.btn_delete_model)
        top2.addSpacing(12)
        top2.addWidget(QLabel("Conversation:")); top2.addWidget(self.cmb_conv, 1); top2.addWidget(self.btn_new_conv)
        outer.addLayout(top2)

        adv = QHBoxLayout()
        self.pull_edit = QLineEdit(); self.pull_edit.setPlaceholderText("Advanced: pull model (e.g., qwen2.5:7b)")
        self.btn_pull = QPushButton("Pull"); adv.addWidget(self.pull_edit, 1); adv.addWidget(self.btn_pull)
        outer.addLayout(adv)

        split = QSplitter(Qt.Orientation.Vertical)
        up = QWidget(); up_l = QVBoxLayout(up)
        \
self.inp = QPlainTextEdit(); self.inp.setPlaceholderText("Type a quick prompt to the current model…")
        # toggles: Stream + Markdown
        row_opts = QHBoxLayout()
        self.chk_stream = QCheckBox("Stream")
        self.chk_stream.setChecked(True)
        self.chk_md = QCheckBox("Markdown")
        self.chk_md.setChecked(True)
        row_opts.addWidget(self.chk_stream); row_opts.addWidget(self.chk_md); row_opts.addStretch(1)
        self.btn_send = QPushButton("Send (Ctrl+Enter)")
        row_opts.addWidget(self.btn_send)
        up_l.addWidget(self.inp, 1); up_l.addLayout(row_opts)
        # Attach ghost completer: Ctrl+Space (suggest), Tab/Right (accept), Esc (dismiss)
        try:
            self._ghost = GhostCompleter(
                self.inp,
                model_name_getter=lambda: (self._current_model or self.cmb_model.currentText()),
                config_getter=lambda: self.config,
            )
        except Exception:
            pass

        down = QWidget(); down_l = QVBoxLayout(down)
        self.out = QTextEdit(); self.out.setReadOnly(True)
        down_l.addWidget(self.out, 1)
        split.addWidget(up); split.addWidget(down)
        outer.addWidget(split, 1)

        self.btn_refresh_models.clicked.connect(self._load_models)
        self.btn_delete_model.clicked.connect(self._delete_selected_model)
        self.btn_new_conv.clicked.connect(self._new_conv)
        self.cmb_model.currentIndexChanged.connect(lambda _: self._on_model_changed())
        self.cmb_conv.currentIndexChanged.connect(lambda _: self._on_conv_changed())
        self.btn_pull.clicked.connect(self._pull_now)
        self.btn_send.clicked.connect(self._send_prompt)
        self.inp.keyPressEvent = self._prompt_keypress(self.inp.keyPressEvent)

        self._refresh_server_state(); self._refresh_tools_status(); self._load_models(); self._load_conversations()
        return w

    # ---- Streaming worker / markdown helpers ----
    class _StreamWorker(QObject):
        chunk = Signal(str)
        done = Signal(str)    # final text
        error = Signal(str)

        def __init__(self, model: str, text: str, config: dict | None):
            super().__init__()
            self.model, self.text, self.config = model, text, config

        def run(self):
            try:
                from app.core.ollama_tools import prompt_stream
                acc = []
                for ok, piece in prompt_stream(self.model, self.text, config=self.config, options={"num_predict": 256}):
                    if not ok:
                        self.error.emit(piece)
                        return
                    acc.append(piece)
                    self.chunk.emit(piece)
                self.done.emit("".join(acc))
            except Exception as e:
                self.error.emit(str(e))

    def _render_reply_markdown(self, text: str):
        if getattr(self, "chk_md", None) and self.chk_md.isChecked():
            try:
                self.out.setMarkdown(text)
                return
            except Exception:
                pass
        self.out.setPlainText(text)

    def _append_reply_markdown(self, piece: str):
        # append while preserving markdown; for QTextEdit, best is rebuild current text + piece
        cur = self.out.toMarkdown() if getattr(self, "chk_md", None) and self.chk_md.isChecked() else self.out.toPlainText()
        new = (cur or "") + piece
        self._render_reply_markdown(new)

    
    def _maybe_show_model_notice(self) -> bool:
        """
        Show a one-time notice that models have their own licenses.
        Returns True if user wants to continue with pulling, False otherwise.
        """
        try:
            from app.core.settings import load_config, save_config
            cfg = load_config()
            if not cfg.get("show_model_license_notice", True):
                return True
            # Build a custom message box with a third button
            box = QMessageBox(self)
            box.setWindowTitle("Model licenses")
            box.setText(
                "Models in the Ollama library have their own licenses and terms.\n"
                "You can review them on the Ollama website before pulling models."
            )
            yes = box.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
            open_site = box.addButton("Open Model Library", QMessageBox.ButtonRole.ActionRole)
            no = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            box.setIcon(QMessageBox.Icon.Information)
            box.exec()

            if box.clickedButton() is open_site:
                import webbrowser
                webbrowser.open("https://ollama.com/library")
                return False
            if box.clickedButton() is yes:
                # do not show again
                cfg["show_model_license_notice"] = False
                save_config(cfg)
                return True
            return False
        except Exception:
            # If anything weird happens, fail open but don't persist
            return True
# --- Ollama helpers ---
    def _refresh_server_state(self):
        ok = server_ok(self.config)
        self.lbl_srv.setText("Server: ✅ running" if ok else "Server: ❌ not reachable (127.0.0.1:11434)")
        self.cmb_model.setEnabled(ok); self.cmb_conv.setEnabled(ok)
        self.btn_refresh_models.setEnabled(ok); self.btn_pull.setEnabled(ok); self.btn_send.setEnabled(ok); self.btn_delete_model.setEnabled(ok)
        self._update_status()

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
            QMessageBox.information(self,"Delete","Pick a model to delete."); return
        if QMessageBox.question(self,"Delete model",f"Delete '{name}' from Ollama? This cannot be undone.") != QMessageBox.StandardButton.Yes:
            return
        ok, msg = delete_model(name)
        if ok: QMessageBox.information(self,"Delete",f"Deleted {name}."); self._load_models()
        else: QMessageBox.warning(self,"Delete",f"Failed: {msg}")

    def _load_conversations(self):
        names = list_conversations()
        if not names: names = ["default"]
        self.cmb_conv.clear()
        for n in names: self.cmb_conv.addItem(n)
        self._set_combo_current_text(self.cmb_conv, getattr(self, "_conv_name", "default"))
        self._update_status()

    def _new_conv(self):
        base = self._app_data_dir(); i = 1
        while True:
            nm = f"conv_{i}"
            if nm not in list_conversations(): break
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
        if not self._maybe_show_model_notice():
            return
        ok, msg = pull_model(name)
        QMessageBox.information(self, "Pull", f"{'OK' if ok else 'Failed'}: {msg}")
        self._load_models()

    def _send_prompt(self):
        if not server_ok(self.config): QMessageBox.warning(self, "Ollama", "Server not reachable at 127.0.0.1:11434"); return
        model = self._current_model or self.cmb_model.currentText().strip()
        if not model or model.startswith("("): QMessageBox.information(self, "Ollama", "Pick a model first."); return
        text = self.inp.toPlainText().strip()
        if not text: return
        ok, resp = prompt(model, text)
        self.out.setPlainText(resp if ok else f"[error] {resp}")
        data = load_conversation(self._conv_name)
        msgs = data.get("messages", []); msgs.append({"role":"user","content":text}); msgs.append({"role":"assistant","content":resp})
        data["messages"] = msgs; data["model"] = model; save_conversation(self._conv_name, data)

    def _prompt_keypress(self, super_impl):
        def handler(evt):
            if evt.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (evt.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self._send_prompt(); return
            return super_impl(evt)
        return handler

    def _set_combo_current_text(self, combo: QComboBox, text: str):
        for i in range(combo.count()):
            if combo.itemText(i) == text:
                combo.setCurrentIndex(i); return

    def _locate_or_install_ollama(self):
        path = which_ollama()
        if path and os.path.exists(path):
            QMessageBox.information(self, "Ollama", f"Found: {path}\nIf server isn't running, try 'ollama serve'.")
            self._open_ollama_license(); return
        if os.name == "nt":
            install_ollama_windows(Path("scripts") / "install_ollama.ps1")
            QMessageBox.information(self, "Ollama", "Attempted winget install or opened download page.")
        else:
            ok, out = install_ollama_linux(Path("scripts") / "install_ollama.sh")
            QMessageBox.information(self, "Ollama", "Installer finished." if ok else f"Install failed:\n{out}")
        self._refresh_server_state(); self._refresh_tools_status()

    def _open_ollama_license(self):
        webbrowser.open("https://ollama.com")




    # ---- Shortcuts / Help ----
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
            ("Runtimes",       lambda: self.tabs.setCurrentIndex(2)),
            ("Ollama",         lambda: self.tabs.setCurrentIndex(3)),
            ("Open Licenses",  self._open_licenses),
        ]
        dlg = CommandPalette(cmds, self); dlg.exec()

    def _open_licenses(self):
        dlg = LicenseDialog(self); dlg.exec()

    def _update_status(self):
        srv = "Ollama:OK" if server_ok(self.config) else "Ollama:OFF"
        model = self._current_model or "(none)"
        conv = getattr(self, "_conv_name", "default")
        self._status.showMessage(f"{srv} | Model: {model} | Conv: {conv} —  Ctrl+O switch, Ctrl+K commands")

    # helper
    def _app_data_dir(self):
        from app.core.paths import app_local_data_dir
        return app_local_data_dir()


    def _refresh_runtime_status(self):
        # Rescan registry and update venv table statuses
        try:
            from pathlib import Path
            rescan_and_update(EXPECTED, Path(".").resolve())
        except Exception:
            pass
        # Update table cells from local checks
        table = getattr(self, "_venv_table", None)
        if not table: return
        for row in range(table.rowCount()):
            name = table.item(row, 0).text()
            st_item = table.item(row, 1)
            if not st_item: continue
            st_item.setText("created" if is_created(name) else "missing")

    
    def _refresh_tools_status(self):
        # Update External Tools (Runtimes tab) label if it exists.
        try:
            from app.core.ollama_tools import which_ollama
            label = getattr(self, "_lbl_ollama", None)
            p = which_ollama()
            if label is not None:
                label.setText(f"Ollama: {'✅ ' + p if p else '❌ not found'}")
        except Exception:
            label = getattr(self, "_lbl_ollama", None)
            if label is not None:
                label.setText("Ollama: (error checking)")



    def _check_all_venvs(self):
        rows = getattr(self, "_venv_table", None).rowCount() if getattr(self, "_venv_table", None) else 0
        lines = []
        for r in range(rows):
            name = self._venv_table.item(r, 0).text()
            ok, missing = validate(name) if name in EXPECTED else (is_created(name), [])
            if ok:
                lines.append(f"{name}: OK")
            else:
                if missing==["_venv_missing_"]:
                    lines.append(f"{name}: venv not created yet")
                else:
                    lines.append(f"{name}: missing imports: {', '.join(missing)}")
        dlg = _TextDialog("Venv Check — Summary", "\n".join(lines) if lines else "(no rows)", self)
        dlg.exec()


    def _action_quick_llm(self):
        dlg = QuickLLMDialog(self)
        dlg.exec()


    def _action_palette(self):
        # Core + plugin actions
        base = [
            ("Quick LLM…", self._action_quick_llm if hasattr(self, "_action_quick_llm") else lambda: None),
            ("Quick Model…", self._action_quick_model),
            ("Refresh Runtimes", self._refresh_runtime_status if hasattr(self, "_refresh_runtime_status") else lambda: None),
            ("Toggle Dark/Light", self.theme.toggle if hasattr(self, "theme") else lambda: None),
        ]
        try:
            plugin_actions = discover_actions()
        except Exception:
            plugin_actions = []
        dlg = CommandPalette(base + plugin_actions, self)
        dlg.exec()

    def _action_quick_model(self):
        dlg = QuickModelDialog(self)
        dlg.exec()
        def log(msg: str):
            if not log_to_ui: return
            try:
                self._op_log.insertPlainText(msg + "\n")
                self._op_log.show()
            except Exception: pass
        try:
            from app.core.ollama_tools import server_ok
            if not server_ok(self.config): return True
        except Exception: return True
        log("[Ollama] Attempting to stop server…")
        # simplest killall fallback
        if os.name != "nt":
            os.system("pkill -f 'ollama serve' >/dev/null 2>&1")
        else:
            os.system("taskkill /IM ollama.exe /F >NUL 2>&1")
        for _ in range(12):
            try:
                from app.core.ollama_tools import server_ok
                if not server_ok(self.config):
                    log("[Ollama] Server appears to be stopped."); return True
            except Exception: return True
            time.sleep(0.5)
        log("[Ollama] Could not stop the server automatically.")
        return False

    def _open_quick_tour(self):
        dlg = QuickTour(self)
        dlg.exec()

    def _choose_ollama_dir(self):
        start = self.config.get("ollama_models_dir", str(Path.home() / ".ollama"))
        path = QFileDialog.getExistingDirectory(self, "Select Ollama models folder", start)
        if not path: return
        self.config["ollama_models_dir"] = path
        save_config(self.config)
        self.lbl_models_dir.setText(path)
        QMessageBox.information(self, "Ollama", "Models folder saved. Restart the server via 'Start Server with this folder' to apply.")
    def _start_ollama_with_dir(self):
        # Try to stop any running server first
        if not self._stop_ollama_server(log_to_ui=True):
            QMessageBox.warning(self, "Ollama", "Could not stop existing server.")
            return

        folder = self.config.get("ollama_models_dir")
        # Port
        try:
            port = int(self.edit_ollama_port.text()) if hasattr(self, 'edit_ollama_port') else int(self.config.get("ollama_port", 11434))
        except Exception:
            port = 11434
        self.config["ollama_port"] = port
        save_config(self.config)
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"127.0.0.1:{port}"

        from os import access, W_OK
        if folder:
            # use exactly what user selected, but ensure it is writable
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
                if access(folder, W_OK):
                    env["OLLAMA_MODELS"] = folder
                else:
                    QMessageBox.warning(self, "Ollama", f"Models folder not writable: {folder}. Using Ollama default (~/.ollama).")
            except Exception as e:
                QMessageBox.warning(self, "Ollama", f"Could not prepare models folder: {folder}\n{e}\nUsing Ollama default (~/.ollama).")

        proc = QProcess(self)
        proc.setProgram("ollama")
        proc.setArguments(["serve"])
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.setEnvironment([f"{k}={v}" for k,v in env.items()])
        proc.readyReadStandardOutput.connect(
            lambda: self._op_log.insertPlainText(
                proc.readAllStandardOutput().data().decode("utf-8","ignore")
            )
        )
        proc.readyReadStandardError.connect(
            lambda: self._op_log.insertPlainText(
                proc.readAllStandardError().data().decode("utf-8","ignore")
            )
        )
        proc.start()
        QTimer.singleShot(1500, self._refresh_server_state)
        self._op_log.show()
        QMessageBox.information(
            self, "Ollama",
            f"Attempted to start server{(' with '+folder) if folder else ''}."
        )

    def _stop_ollama_server(self, log_to_ui: bool = True) -> bool:
        import time, subprocess, shutil
        def log(msg: str):
            if not log_to_ui:
                return
            try:
                self._op_log.insertPlainText(msg + "\n")
                self._op_log.show()
            except Exception:
                pass

        try:
            from app.core.ollama_tools import server_ok
            if not server_ok(self.config):
                return True
        except Exception:
            return True

        log("[Ollama] Attempting to stop server…")

        if os.name != "nt":
            os.system("pkill -f 'ollama serve' >/dev/null 2>&1")
        else:
            os.system("taskkill /IM ollama.exe /F >NUL 2>&1")

        for _ in range(12):
            try:
                from app.core.ollama_tools import server_ok
                if not server_ok(self.config):
                    log("[Ollama] Server appears stopped.")
                    return True
            except Exception:
                return True
            time.sleep(0.5)

        log("[Ollama] Could not stop the server automatically.")
        return False



    def _uninstall_ollama_dialog(self):
        # Simple confirm dialog with "purge models" checkbox
        dlg = QDialog(self)
        dlg.setWindowTitle("Uninstall Ollama")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("This will stop services, remove the ollama binary, and kill running processes."))
        lay.addWidget(QLabel("You can also optionally delete the models folder."))
        purge = QCheckBox("Also delete models folder")
        lay.addWidget(purge)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
        lay.addWidget(btns)
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        if dlg.exec() != QDialog.Accepted:
            return
        # Build command
        script = str((Path(__file__).resolve().parent.parent.parent / "scripts" / "uninstall_ollama.sh"))
        if not os.path.exists(script):
            QMessageBox.warning(self, "Uninstall", "scripts/uninstall_ollama.sh not found.")
            return
        args = [script]
        if purge.isChecked():
            args.append("--purge-models")
            # If we have a custom folder saved, pass it explicitly
        folder = self.config.get("ollama_models_dir")
        if folder:
            args += ["--models-dir", folder]
        # Run with QProcess to show output in log
        from PySide6.QtCore import QProcess, Qt
        from PySide6.QtWidgets import QProgressDialog
        dlgp = QProgressDialog("Uninstalling Ollama…", "", 0, 0, self)
        dlgp.setCancelButton(None); dlgp.setWindowModality(Qt.ApplicationModal); dlgp.show()
        proc = QProcess(self)
        proc.setProgram("bash"); proc.setArguments(args)
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardOutput().data().decode("utf-8","ignore")))
        proc.readyReadStandardError.connect(lambda: self._op_log.insertPlainText(proc.readAllStandardError().data().decode("utf-8","ignore")))
        proc.finished.connect(lambda *_: (dlgp.close(), self._refresh_server_state()))
        self._op_log.clear(); self._op_log.show()
        proc.start()


    def _choose_model_placeholder(self, srv_ok: bool, models: list[str]) -> str:
        if not srv_ok:
            return "(no server)"
        return "(no models)" if not models else models[0]
