import os
import unittest

from context import APP_DIR, LOG_DIR, PATCHING_RECORD


class TestCredentials(unittest.TestCase):
    def test_app_dir(self):
        self.assertEqual(APP_DIR, os.path.join(os.environ["LOCALAPPDATA"], "Overload"))

    def test_log_dir(self):
        self.assertEqual(
            LOG_DIR, os.path.join(os.environ["LOCALAPPDATA"], "Overload\\changesLog")
        )

    def test_patching_record(self):
        self.assertEqual(
            PATCHING_RECORD,
            os.path.join(
                os.environ["LOCALAPPDATA"], "Overload\\changesLog\\patching_record.txt"
            ),
        )


if __name__ == "__main__":
    unittest.main()
