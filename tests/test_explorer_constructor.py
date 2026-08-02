import sys
import unittest
from PySide6.QtWidgets import QApplication
from ui.enhanced_explorer import PremiumExplorer


class PremiumExplorerConstructorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_premium_explorer_accepts_root_path_keyword(self):
        explorer = PremiumExplorer(event_bus=None, parent=None, root_path='.')
        self.assertIsNotNone(explorer)


if __name__ == '__main__':
    unittest.main()
