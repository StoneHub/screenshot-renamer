from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock
from doctor import doctor


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.folder = self.home / 'Shots'
        self.folder.mkdir()
        self.state = self.home / 'Library/Application Support/Screenshot Renamer'
        self.script = self.home / 'Library/Scripts/Folder Action Scripts/Screenshot Renamer.scpt'
        self.fm = self.home / 'fm'
        self.answers = {'fm': 'Model is available\n', 'osascript': 'true,true,true\n', 'defaults': str(self.folder) + '\n'}

    def run_command(self, args, **kwargs):
        name = Path(args[0]).name
        if name == 'osascript':
            self.assertEqual(args[-1], str(self.folder))
            self.assertIn('folder action', kwargs['input'])
        return subprocess.CompletedProcess(args, 0, stdout=self.answers[name], stderr='')

    def install_fixture(self):
        self.state.mkdir(parents=True)
        (self.state / 'config.py').write_text('SCREENSHOT_DIRECTORY = ' + repr(str(self.folder)) + '\n')
        (self.state / 'status.log').write_text('\n'.join('line%d ok' % n for n in range(7)) + '\n')
        self.script.parent.mkdir(parents=True)
        self.script.write_text('fixture')

    def report(self):
        out = StringIO()
        code = doctor(self.home, self.run_command, self.fm, '27.0', out)
        return code, out.getvalue().splitlines()

    def test_healthy(self):
        self.fm.write_text('')
        self.install_fixture()
        code, lines = self.report()
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], 'macOS 27.0: /usr/bin/fm present, fm available ok')
        self.assertEqual(lines[1], 'Screenshot folder: ' + str(self.folder) + ' exists')
        self.assertEqual(lines[2], 'Compiled script: ' + str(self.script) + ' exists')
        self.assertEqual(lines[3], 'Folder action: attached to ' + str(self.folder)
                         + '; action enabled true; script enabled true; Folder Actions switch true')
        self.assertEqual(lines[4], 'status.log, last 5 lines:')
        self.assertEqual(lines[5:10], ['  line%d ok' % n for n in range(2, 7)])
        self.assertEqual(lines[10], 'Result: healthy')

    def test_disabled_script_is_unhealthy(self):
        self.fm.write_text('')
        self.install_fixture()
        self.answers['osascript'] = 'true,true,false\n'
        code, lines = self.report()
        self.assertEqual(code, 1)
        self.assertIn('script enabled false', lines[3])

    def test_fm_missing(self):
        self.install_fixture()
        code, lines = self.report()
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], 'macOS 27.0: /usr/bin/fm is missing. Apple ships it with macOS 27; this Mac runs 27.0.')
        self.assertEqual(lines[-1], 'Result: not working; see above')

    def test_not_installed_skips_system_events(self):
        self.fm.write_text('')
        run = Mock(side_effect=self.run_command)
        out = StringIO()
        code = doctor(self.home, run, self.fm, '27.0', out)
        lines = out.getvalue().splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[1], 'Screenshot folder: ' + str(self.folder) + ' exists')
        self.assertEqual(lines[2], 'Compiled script: ' + str(self.script) + ' missing')
        self.assertEqual(lines[3], 'Folder action: not checked because the compiled script is missing')
        self.assertEqual(lines[4], 'status.log: none at ' + str(self.state / 'status.log'))
        self.assertNotIn('osascript', [Path(call.args[0][0]).name for call in run.call_args_list])

    def test_falls_back_to_desktop_when_defaults_is_unset(self):
        self.fm.write_text('')
        run = Mock(return_value=subprocess.CompletedProcess([], 1, stdout='', stderr='does not exist'))
        out = StringIO()
        doctor(self.home, run, self.fm, '27.0', out)
        self.assertIn('Screenshot folder: ' + str(self.home / 'Desktop') + ' missing', out.getvalue())
