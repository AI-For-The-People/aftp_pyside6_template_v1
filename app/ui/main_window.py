from __future__ import annotations
import os, webbrowser
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QHBoxLayout,
    QComboBox, QRadioButton, QGroupBox, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QPlainTextEdit, QSplitter, QAbstractItemView, QStatusBar, QMenuBar, QMenu,
    QDialog, QDialogButtonBox
)
from app.core.theme import ThemeManager, SCHEMES
from app.core.venv_tools import EXPECTED, is_created, validate
from app.core.ollama_tools import (
    server_ok, list_models, pull_model, delete_model, prompt,
    list_conversations, load_conversation, save_conversation,
    which_ollama, install_ollama_linux, install_ollama_windows, license_url
)
from app.core.shortcuts import ActionSpec, attach_actions
from app.ui.command_palette import CommandPalette
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
        desc = QLabel("Create/validate venvs. Buttons run scripts under <code>scripts/</code>.")
        desc.setWordWrap(True); lay.addWidget(desc)

        table = QTableWidget(0, 4); table.setHorizontalHeaderLabels(["Name","Status","Create/Update","Validate"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        names = list(EXPECTED.keys()) + ["mamba2"]; table.setRowCount(len(names))
        def mk_btn(label, fn): b = QPushButton(label); b.clicked.connect(fn); return b

        for row, name in enumerate(names):
            table.setItem(row, 0, QTableWidgetItem(name))
            st_item = QTableWidgetItem("created" if is_created(name) else "missing")
            table.setItem(row, 1, st_item)

            def make_run(n=name):
                def _run():
                    script = f"scripts/setup_venv_{n}.sh"
                    if os.name == "nt": script = f"scripts\\setup_venv_{n}.ps1"
                    if not os.path.exists(script):
                        QMessageBox.warning(self, "Script missing", f"{script} not found."); return
                    from subprocess import run, CalledProcessError
                    try:
                        if os.name=="nt": run(["powershell","-ExecutionPolicy","Bypass","-File",script], check=True)
                        else: run(["bash", script], check=True)
                        QMessageBox.information(self, "Done", f"{n} venv created/updated."); st_item.setText("created")
                    except CalledProcessError:
                        QMessageBox.critical(self,"Error",f"Script failed for {n}.")
                return _run

            def make_val(n=name):
                def _val():
                    ok, missing = validate(n) if n in EXPECTED else (is_created(n), [] if is_created(n) else ["_venv_missing_"])
                    if ok: QMessageBox.information(self, "Validate", f"{n}: OK")
                    else:
                        if missing==["_venv_missing_"]: QMessageBox.warning(self,"Validate",f"{n}: venv not created yet.")
                        else: QMessageBox.warning(self,"Validate",f"{n}: missing imports: {', '.join(missing)}")
                return _val

            table.setCellWidget(row, 2, mk_btn("Create/Update", make_run()))
            table.setCellWidget(row, 3, mk_btn("Validate", make_val()))

        table.resizeColumnsToContents()
        lay.addWidget(table, 1)
        return w

    # ---- Ollama ----
    def _ollama_tab(self) -> QWidget:
        w = QWidget(); outer = QVBoxLayout(w)

        top1 = QHBoxLayout()
        self.lbl_srv = QLabel("Server: (checking…)"); top1.addWidget(self.lbl_srv)
        btn_loc = QPushButton("Locate/Install"); btn_lic = QPushButton("License (Website)"); top1.addStretch(1)
        top1.addWidget(btn_loc); top1.addWidget(btn_lic)
        outer.addLayout(top1)
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
        self.inp = QPlainTextEdit(); self.inp.setPlaceholderText("Type a quick prompt to the current model…")
        self.btn_send = QPushButton("Send (Ctrl+Enter)")
        up_l.addWidget(self.inp, 1); up_l.addWidget(self.btn_send, 0)
        down = QWidget(); down_l = QVBoxLayout(down)
        self.out = QPlainTextEdit(); self.out.setReadOnly(True)
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

        self._refresh_server_state(); self._load_models(); self._load_conversations()
        return w

    
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
        ok = server_ok()
        self.lbl_srv.setText("Server: ✅ running" if ok else "Server: ❌ not reachable (127.0.0.1:11434)")
        self.cmb_model.setEnabled(ok); self.cmb_conv.setEnabled(ok)
        self.btn_refresh_models.setEnabled(ok); self.btn_pull.setEnabled(ok); self.btn_send.setEnabled(ok); self.btn_delete_model.setEnabled(ok)
        self._update_status()

    def _load_models(self):
        self.cmb_model.clear()
        if not server_ok(): self.cmb_model.addItem("(no server)"); return
        models = list_models()
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
        names = list_conversations(self._app_data_dir())
        if not names: names = ["default"]
        self.cmb_conv.clear()
        for n in names: self.cmb_conv.addItem(n)
        self._set_combo_current_text(self.cmb_conv, getattr(self, "_conv_name", "default"))
        self._update_status()

    def _new_conv(self):
        base = self._app_data_dir(); i = 1
        while True:
            nm = f"conv_{i}"
            if nm not in list_conversations(base): break
            i += 1
        self._conv_name = nm
        save_conversation(base, {"name": nm, "model": self._current_model, "messages": []})
        self._load_conversations()

    def _on_model_changed(self):
        self._current_model = self.cmb_model.currentText()
        data = load_conversation(self._app_data_dir(), getattr(self, "_conv_name", "default"))
        data["model"] = self._current_model; save_conversation(self._app_data_dir(), data); self._update_status()

    def _on_conv_changed(self):
        self._conv_name = self.cmb_conv.currentText()
        data = load_conversation(self._app_data_dir(), self._conv_name)
        if data.get("model"): self._set_combo_current_text(self.cmb_model, data["model"])
        self._update_status()

    def _pull_now(self):
        name = self.pull_edit.text().strip()
        if not name: return
        if not self._maybe_show_model_notice():
            return
        if not self._maybe_show_model_notice():
            return
        ok, msg = pull_model(name)
        QMessageBox.information(self, "Pull", f"{'OK' if ok else 'Failed'}: {msg}")
        self._load_models()

    def _send_prompt(self):
        if not server_ok(): QMessageBox.warning(self, "Ollama", "Server not reachable at 127.0.0.1:11434"); return
        model = self._current_model or self.cmb_model.currentText().strip()
        if not model or model.startswith("("): QMessageBox.information(self, "Ollama", "Pick a model first."); return
        text = self.inp.toPlainText().strip()
        if not text: return
        ok, resp = prompt(model, text)
        self.out.setPlainText(resp if ok else f"[error] {resp}")
        data = load_conversation(self._app_data_dir(), self._conv_name)
        msgs = data.get("messages", []); msgs.append({"role":"user","content":text}); msgs.append({"role":"assistant","content":resp})
        data["messages"] = msgs; data["model"] = model; save_conversation(self._app_data_dir(), data)

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
        self._refresh_server_state()

    def _open_ollama_license(self):
        webbrowser.open("https://ollama.com")




    # ---- Shortcuts / Help ----
    def _wire_shortcuts(self):
        def show_theme_tab(): self.tabs.setCurrentIndex(1)
        def show_runtimes_tab(): self.tabs.setCurrentIndex(2)
        def show_ollama_tab(): self.tabs.setCurrentIndex(3)
        def open_palette(): self._open_palette()
        specs = [
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
        dlg = CommandPalette(self); dlg.set_commands(cmds); dlg.exec()

    def _open_licenses(self):
        dlg = LicenseDialog(self); dlg.exec()

    def _update_status(self):
        srv = "Ollama:OK" if server_ok() else "Ollama:OFF"
        model = self._current_model or "(none)"
        conv = getattr(self, "_conv_name", "default")
        self._status.showMessage(f"{srv} | Model: {model} | Conv: {conv} —  Ctrl+O switch, Ctrl+K commands")

    # helper
    def _app_data_dir(self):
        from app.core.paths import app_local_data_dir
        return app_local_data_dir()
