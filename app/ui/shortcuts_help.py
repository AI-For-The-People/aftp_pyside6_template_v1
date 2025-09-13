from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
class ShortcutsHelp(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcuts")
        self.setMinimumSize(520, 420)
        lay = QVBoxLayout(self)
        t = QTextEdit(self); t.setReadOnly(True)
        t.setPlainText(
            "Global\n"
            "  Ctrl+K  Command Palette\n"
            "  Ctrl+J  Quick LLM\n"
            "  Ctrl+M  Quick Model\n"
            "  Ctrl+Shift+L  Toggle Log\n"
            "  Ctrl+Shift+R  Refresh Runtimes\n"
            "Navigation\n"
            "  Ctrl+Tab / Ctrl+Shift+Tab  Switch Tabs\n"
            "Edit\n"
            "  Ctrl+Z / Ctrl+Shift+Z  Undo / Redo\n"
            "  Ctrl+C / Ctrl+V / Ctrl+X  Copy / Paste / Cut\n"
            "Theme & View\n"
            "  Ctrl+Shift+D  Toggle Dark/Light\n"
            "  Ctrl++ / Ctrl+- / Ctrl+0  Zoom In/Out/Reset\n"
        )
        lay.addWidget(t,1)
        b = QPushButton("Close", self); b.clicked.connect(self.accept)
        lay.addWidget(b)
