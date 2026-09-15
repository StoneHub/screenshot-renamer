from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock
from uninstall import uninstall


class UninstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.state = self.home / 'Library/Application Support/Screenshot Renamer'
        self.state.mkdir(parents=True)
        (self.state / 'disable.applescript').write_text('fixture')
        (self.state / 'config.py').write_text('SCREENSHOT_DIRECTORY = "/tmp/fixture"\n')
        (self.state / 'history.json').write_text('private undo fixture')
        self.script = self.home / 'Library/Scripts/Folder Action Scripts/Screenshot Renamer.scpt'
        self.script.parent.mkdir(parents=True)
        self.script.write_text('fixture')
        self.other = self.script.with_name('Other Action.scpt')
        self.other.write_text('leave alone')

    def test_removes_utility_and_preserves_unrelated_script(self):
        runner = Mock()
        uninstall(self.home, runner)
        runner.assert_called_once()
        self.assertFalse(self.state.exists())
        self.assertFalse(self.script.exists())
        self.assertEqual(self.other.read_text(), 'leave alone')
        self.assertFalse((self.home / 'Library/Application Support/Screenshot Renamer Backups').exists())
        self.assertIsNone(uninstall(self.home, runner))

    def test_failed_disable_leaves_installation_intact(self):
        runner = Mock(side_effect=subprocess.CalledProcessError(1, 'osascript'))
        with self.assertRaises(subprocess.CalledProcessError):
            uninstall(self.home, runner)
        self.assertTrue(self.script.exists())
        self.assertTrue((self.state / 'history.json').exists())

    def test_symlink_refused(self):
        self.script.unlink()
        self.script.symlink_to(self.other)
        runner = Mock()
        with self.assertRaises(RuntimeError):
            uninstall(self.home, runner)
        runner.assert_not_called()
        self.assertEqual(self.other.read_text(), 'leave alone')
