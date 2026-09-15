from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock
import install


def ok(*args, **kwargs):
    return subprocess.CompletedProcess(args, 0, stdout='Model is available\n', stderr='')


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fm = Path(self.temp.name) / 'fm'

    def test_missing_fm_names_the_running_version(self):
        problems = install.preflight(run=Mock(), fm=self.fm, version='26.6.2')
        self.assertEqual(len(problems), 1)
        self.assertIn('/usr/bin/fm is missing', problems[0])
        self.assertIn('this Mac runs 26.6.2', problems[0])

    def test_fm_available_failure_is_reported(self):
        self.fm.write_text('')
        run = Mock(return_value=subprocess.CompletedProcess([], 1, stdout='', stderr='Model not ready'))
        problems = install.preflight(run=run, fm=self.fm)
        self.assertEqual(len(problems), 1)
        self.assertIn('Model not ready', problems[0])
        run.assert_called_once_with([str(self.fm), 'available'], text=True, capture_output=True)

    def test_healthy_mac_has_no_problems(self):
        self.fm.write_text('')
        self.assertEqual(install.preflight(run=ok, fm=self.fm), [])
