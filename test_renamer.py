import importlib.util
import json
import os
from pathlib import Path
import plistlib
import tempfile
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('renamer', Path(__file__).with_name('renamer.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        r.DESTINATION = self.root / 'Screenshots'; r.DESTINATION.mkdir()
        r.STATE = self.root / 'state'; r.STATE.mkdir()
        self.history = []

    def screenshot(self, name='Screenshot test.png'):
        p = r.DESTINATION / name; p.write_bytes(b'image fixture')
        subprocess.run(['/usr/bin/xattr', '-wx', r.MARKER, plistlib.dumps(True, fmt=plistlib.FMT_BINARY).hex(), str(p)], check=True)
        return p

    def run_file(self, p, title='Workshop checklist'):
        with patch.object(r, 'ready', side_effect=r.identity):
            return r.process(p, self.history, lambda _: title)

    def test_rename_preserves_bytes_metadata_and_creation_date(self):
        p = self.screenshot(); old = p.read_bytes()
        created = p.stat().st_birthtime
        self.assertEqual(self.run_file(p), 'renamed')
        dest = next(r.DESTINATION.iterdir())
        self.assertEqual(dest.read_bytes(), old); self.assertTrue(r.is_screenshot(dest))
        self.assertEqual(dest.stat().st_birthtime, created)
        self.assertEqual(self.run_file(dest), 'already-processed')
        stored = json.loads((r.STATE / 'processed.json').read_text())
        self.assertTrue(all(isinstance(value, int) for row in stored for value in row))
        self.assertFalse((r.STATE / 'history.json').exists())

    def test_collision_does_not_overwrite(self):
        a=self.screenshot('Screenshot a.png'); b=self.screenshot('Screenshot b.png')
        with patch.object(r.datetime, 'datetime', wraps=r.datetime.datetime) as dt:
            dt.fromtimestamp.return_value.strftime.return_value='2026-09-15 12.00.00'
            self.run_file(a); self.run_file(b)
        names=list(r.DESTINATION.iterdir())
        self.assertNotEqual(*names); self.assertTrue(all(x.exists() for x in names))

    def test_ordinary_image_is_not_screenshot(self):
        p=r.DESTINATION/'photo.png'; p.write_bytes(b'ordinary')
        self.assertFalse(r.is_screenshot(p))
        with patch.object(r.time, 'sleep'):
            with self.assertRaises(ValueError): r.process(p,self.history,lambda _:self.fail('model called'))
        self.assertTrue(p.exists())

    def test_model_error_keeps_original(self):
        p=self.screenshot()
        with patch.object(r,'ready',side_effect=r.identity):
            with self.assertRaises(RuntimeError):
                r.process(p,self.history,lambda _: (_ for _ in ()).throw(RuntimeError()))
        self.assertTrue(p.exists()); self.assertEqual(self.history,[])

    def test_symlink_and_outside_desktop_ignored(self):
        p=self.screenshot(); link=r.DESTINATION/'Screenshot link.png'; link.symlink_to(p)
        self.assertEqual(self.run_file(link),'ignored')
        other=self.root/'Screenshot outside.png'; other.write_bytes(b'x')
        self.assertEqual(self.run_file(other),'ignored')

    def test_changed_file_not_renamed(self):
        p=self.screenshot()
        def generate(q): q.write_bytes(b'changed'); return 'Title'
        with patch.object(r,'ready',side_effect=r.identity):
            self.assertEqual(r.process(p,self.history,generate),'changed-during-generation')
        self.assertTrue(p.exists())

    def test_existing_files_require_explicit_batch_opt_in(self):
        p=self.screenshot()
        with patch.object(r.time, 'time', return_value=p.stat().st_birthtime+600):
            self.assertEqual(self.run_file(p), 'old-file-ignored')
            with patch.object(r, 'ready', side_effect=r.identity):
                self.assertEqual(r.process(p,self.history,lambda _: 'Workshop checklist',allow_existing=True),'renamed')

    def test_title_sanitization(self):
        self.assertEqual(r.sanitize('../../Hello\nWorld: /test'), 'Hello World test')
        with self.assertRaises(ValueError): r.sanitize('///')

if __name__=='__main__': unittest.main()
