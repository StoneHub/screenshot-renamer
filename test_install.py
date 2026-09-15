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

    def test_permission_notice_is_two_lines(self):
        out = StringIO()
        with redirect_stdout(out):
            install.announce()
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn('System Events', lines[0])
        self.assertIn('screenshot folder', lines[0])


class InstalledCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.state = self.home / 'Library/Application Support/Screenshot Renamer'

    def install_fixture(self):
        self.state.mkdir(parents=True)
        (self.state / 'config.py').write_text('SCREENSHOT_DIRECTORY = "/tmp/fixture"\n')
        (self.state / 'disable.applescript').write_text('fixture')
        (self.state / 'uninstall.py').write_text('fixture')

    def test_not_installed_says_so(self):
        for command in [install.uninstall_installed, install.disable_installed]:
            run = Mock()
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(command(self.home, run), 1)
            self.assertEqual(out.getvalue(), 'Screenshot Renamer is not installed.\n')
            run.assert_not_called()

    def test_uninstall_runs_the_installed_script(self):
        self.install_fixture()
        run = Mock()
        with redirect_stdout(StringIO()):
            self.assertEqual(install.uninstall_installed(self.home, run), 0)
        run.assert_called_once_with(['/usr/bin/python3', str(self.state / 'uninstall.py')], check=True)

    def test_disable_passes_the_configured_folder(self):
        self.install_fixture()
        run = Mock()
        with redirect_stdout(StringIO()):
            self.assertEqual(install.disable_installed(self.home, run), 0)
        run.assert_called_once_with(['/usr/bin/osascript', str(self.state / 'disable.applescript'), '/tmp/fixture'], check=True)
