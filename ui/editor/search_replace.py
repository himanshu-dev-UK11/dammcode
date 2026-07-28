"""
Search and Replace Widget.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextDocument

class SearchReplaceWidget(QFrame):
    find_requested = Signal(str, bool, bool, bool) # text, forward, case, regex
    replace_requested = Signal(str, str, bool, bool, bool) # find, replace, forward, case, regex
    replace_all_requested = Signal(str, str, bool, bool)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.hide() # Hidden by default
        
    def setup_ui(self):
        from ui.design_system import get_design_system
        p = get_design_system().palette
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.bg};
                border: 1px solid {p.border};
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {p.editor_bg};
                color: {p.text};
                border: 1px solid {p.border};
                padding: 4px;
            }}
            QPushButton {{
                background-color: {p.border};
                color: {p.text};
                border: none;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {p.surface_hover};
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Top row: Find
        find_layout = QHBoxLayout()
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        self.find_input.returnPressed.connect(self.on_find_next)
        
        self.btn_next = QPushButton("Next")
        self.btn_prev = QPushButton("Prev")
        self.btn_close = QPushButton("X")
        
        self.btn_next.clicked.connect(self.on_find_next)
        self.btn_prev.clicked.connect(self.on_find_prev)
        self.btn_close.clicked.connect(self.hide)
        
        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.btn_prev)
        find_layout.addWidget(self.btn_next)
        find_layout.addWidget(self.btn_close)
        
        # Bottom row: Replace
        replace_layout = QHBoxLayout()
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace...")
        
        self.btn_replace = QPushButton("Replace")
        self.btn_replace_all = QPushButton("Replace All")
        
        self.btn_replace.clicked.connect(self.on_replace)
        self.btn_replace_all.clicked.connect(self.on_replace_all)
        
        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.btn_replace)
        replace_layout.addWidget(self.btn_replace_all)
        
        # Options row
        options_layout = QHBoxLayout()
        self.chk_case = QCheckBox("Match Case")
        self.chk_word = QCheckBox("Whole Word")
        self.chk_regex = QCheckBox("Regex")
        
        options_layout.addWidget(self.chk_case)
        options_layout.addWidget(self.chk_word)
        options_layout.addWidget(self.chk_regex)
        options_layout.addStretch()
        
        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addLayout(options_layout)

    def on_find_next(self):
        self.find_requested.emit(self.find_input.text(), True, self.chk_case.isChecked(), self.chk_regex.isChecked())

    def on_find_prev(self):
        self.find_requested.emit(self.find_input.text(), False, self.chk_case.isChecked(), self.chk_regex.isChecked())

    def on_replace(self):
        self.replace_requested.emit(self.find_input.text(), self.replace_input.text(), True, self.chk_case.isChecked(), self.chk_regex.isChecked())
        
    def on_replace_all(self):
        self.replace_all_requested.emit(self.find_input.text(), self.replace_input.text(), self.chk_case.isChecked(), self.chk_regex.isChecked())
