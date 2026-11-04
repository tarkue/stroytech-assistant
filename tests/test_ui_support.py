"""Shared isolated Streamlit fixture; contains no test cases itself."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class StreamlitCase(unittest.TestCase):
    def setUp(self):
        from streamlit.testing.v1 import AppTest
        from stroytech.storage import Repository
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.db=Path(temporary.name)/'ui.sqlite3'
        environ=patch.dict(os.environ,{'STROYTECH_DB':str(self.db)})
        environ.start()
        self.addCleanup(environ.stop)
        self.repository=Repository(self.db)
        self.repository.initialize()
        self.app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=15).run()
        self.assertFalse(self.app.exception)

    def button(self,key):
        return self.app.button(key=key)
