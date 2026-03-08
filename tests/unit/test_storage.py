import tempfile
import unittest
from pathlib import Path

from nuvola.adapters.storage.file_session_store import FileSessionStore
from nuvola.domain.models import SessionContext


class FileSessionStoreTest(unittest.TestCase):
    def test_save_and_load_session(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = FileSessionStore(Path(tmp_dir) / ".nuvola-session.json")
            session = SessionContext(backend="legacy_student", token="TOKEN", student_id="42")
            store.save(session)
            loaded = store.load()
            self.assertEqual(loaded, session)

    def test_save_without_student_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = FileSessionStore(Path(tmp_dir) / ".nuvola-session.json")
            session = SessionContext(backend="legacy_student", token="TOKEN", tenant="demo")
            store.save(session)
            loaded = store.load()
            self.assertEqual(loaded.token, "TOKEN")
            self.assertIsNone(loaded.student_id)
            self.assertEqual(loaded.tenant, "demo")


if __name__ == "__main__":
    unittest.main()
