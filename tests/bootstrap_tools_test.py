"""Validate download integrity and archive containment before tool extraction."""
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from bootstrap_tools import download,extract_archive

class BootstrapTests(unittest.TestCase):
    def test_cached_tool_requires_matching_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'tool.zip').write_bytes(b'checked')
            spec={'url':'https://example.invalid/tool.zip','sha256':hashlib.sha256(b'checked').hexdigest()}
            with patch('bootstrap_tools.urllib.request.urlopen',side_effect=AssertionError('unexpected network')):
                self.assertEqual(download(spec,folder),folder/'tool.zip')
    def test_download_hash_mismatch_does_not_replace_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);cached=folder/'tool.zip';cached.write_bytes(b'previous')
            spec={'url':'https://example.invalid/tool.zip','sha256':hashlib.sha256(b'expected').hexdigest()}
            response=io.BytesIO(b'wrong');response.headers={}
            with patch('bootstrap_tools.urllib.request.urlopen',return_value=response):
                with self.assertRaises(ValueError):download(spec,folder,lambda message:None)
            self.assertEqual(cached.read_bytes(),b'previous')
    def test_zip_traversal_is_rejected_before_extracting_files(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            with zipfile.ZipFile(folder/'tool.zip','w') as archive:
                archive.writestr('valid.txt','keep out');archive.writestr('../outside','blocked')
            with self.assertRaises(ValueError):extract_archive(folder/'tool.zip',folder/'output')
            self.assertFalse((folder/'output/valid.txt').exists())
            self.assertFalse((folder/'outside').exists())

if __name__=='__main__':unittest.main()
