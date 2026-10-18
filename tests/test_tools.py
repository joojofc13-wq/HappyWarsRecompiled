import pathlib
import struct
import sys
import unittest
import zlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from stfs import safe_relative,PackageError
from resources import decode_zres
from analyze import xex_report,word
from data_audit import read_json_export
import tempfile


class ToolTests(unittest.TestCase):
    def test_unsafe_paths(self):
        for value in ('.','../escape','C:/escape','/absolute','dir/../escape','CON','dir/file:stream','a./b'):
            with self.subTest(value=value), self.assertRaises(PackageError):
                safe_relative(value)
        self.assertEqual(safe_relative('media\\stage\\map.bres'),'media/stage/map.bres')

    def test_zres_exact_length_and_truncation(self):
        payload=b'unit-test-only\x00\xff'*30
        data=b'ZRES'+struct.pack('<I',len(payload))+zlib.compress(payload)
        self.assertEqual(decode_zres(data),payload)
        with self.assertRaises(ValueError):
            decode_zres(data[:-2])
        with self.assertRaises(ValueError):
            decode_zres(data+b'trailing data')
        with self.assertRaises(ValueError):
            decode_zres(b'ZRES'+struct.pack('<I',1)+zlib.compress(payload))

    def test_bounded_fields(self):
        with self.assertRaises(ValueError):
            word(b'ab',0)
        with self.assertRaises(ValueError):
            word(b'abcd',-1)

    def test_json_comments_preserve_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/'unit.json'
            path.write_text('// comment\n{"url":"https://example.invalid/a//b",/* comment */"x":4}')
            self.assertEqual(read_json_export(path),{'url':'https://example.invalid/a//b','x':4})

    def test_real_xex_identity(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        path=root/'private/game/Default.xex'
        if not path.exists():
            self.skipTest('User-provided XEX absent')
        report=xex_report(path)
        self.assertEqual(report['execution']['title_id'],'0x58410ae9')
        self.assertEqual(report['entry_point'],'0x830f23c8')
        self.assertEqual(report['sha256'],'0e4dde7ac8c1e81d6f7ec5dee62cc623e693e905a471232d1b0b28d6f0e8f548')


if __name__=='__main__':
    unittest.main()
