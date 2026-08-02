import sys
from PySide6.QtWidgets import QApplication
from ui.enhanced_explorer import PremiumExplorer


def test_premium_explorer_accepts_root_path_keyword():
    app = QApplication.instance() or QApplication(sys.argv)
    explorer = PremiumExplorer(event_bus=None, parent=None, root_path='.')
    assert explorer is not None
