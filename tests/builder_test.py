"""Protect original inputs and nonempty destinations in the public builder."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import builder

class BuilderTests(unittest.TestCase):
    def test_native_build_progress_is_streamed_and_errors_propagate(self):
        import contextlib
        import io
        import build
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'logs').mkdir()
            console=io.StringIO()
            command=[sys.executable,'-u','-c',
                     "print('[1/2] Compile'); print('compiler details'); print('[2/2] Link'); raise SystemExit(7)"]
            with patch.object(build,'ROOT',root), contextlib.redirect_stdout(console):
                with self.assertRaises(SystemExit) as failure:
                    build.run(command,'native.log',dict(__import__('os').environ))
            self.assertEqual(failure.exception.code,7)
            self.assertIn('[1/2] Compile',console.getvalue())
            self.assertIn('[2/2] Link',console.getvalue())
            self.assertIn('compiler details',(root/'logs/native.log').read_text())
    def test_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp); original=folder/'keep.txt'; original.write_text('keep')
            with self.assertRaises(ValueError): builder.prepare_sources(folder)
            self.assertEqual(original.read_text(),'keep')
    def test_source_archive_cannot_escape_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            with zipfile.ZipFile(folder/'source.zip','w') as archive:
                archive.writestr('../escaped.txt','rejected')
            with patch.object(builder.sys,'_MEIPASS',str(folder),create=True):
                with self.assertRaises(ValueError): builder.prepare_sources(folder/'output')
            self.assertFalse((folder/'escaped.txt').exists())
    def test_wrong_executable_is_rejected_without_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'media').mkdir();executable=folder/'Default.xex'
            executable.write_bytes(b'not a supported game')
            with self.assertRaises(ValueError):builder.validate_game(folder)
            self.assertEqual(executable.read_bytes(),b'not a supported game')

if __name__=='__main__':unittest.main()
