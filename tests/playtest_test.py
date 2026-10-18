"""Check that repeated crashes retain separate logs and a deduplicated summary."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import playtest


class PlaytestTests(unittest.TestCase):
    def test_separate_runs_group_the_same_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'build/game').mkdir(parents=True)
            (root/'private/game').mkdir(parents=True)
            (root/'build/game/HappyWars.exe').write_bytes(b'fixture')
            (root/'private/game/Default.xex').touch()
            def process(command, **kwargs):
                log = Path(next(a.split('=', 1)[1] for a in command if a.startswith('--log_file=')))
                log.write_text('[critical] [FATAL] Call to invalid or unregistered function at guest address 0x834bd2f8\n')
                result = unittest.mock.Mock(pid=123)
                result.wait.return_value = 1
                return result
            with patch.object(playtest.subprocess, 'Popen', side_effect=process):
                first = playtest.launch('difficulty', root)
                second = playtest.launch('another map', root)
            self.assertNotEqual(first['log'], second['log'])
            self.assertTrue((root/first['log']).is_file())
            report = playtest.summarize(root)
            self.assertEqual(len(report['sessions']), 2)
            self.assertEqual(report['missing_functions'][0]['address'], '0x834BD2F8')
            self.assertEqual(report['missing_functions'][0]['occurrences'], 2)

    def test_exit_without_missing_function_is_not_classified_as_one(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root/'logs/playtests'
            directory.mkdir(parents=True)
            (directory/'normal.log').write_text('normal shutdown\n')
            (directory/'normal.json').write_text(json.dumps({'log': 'logs/playtests/normal.log'}))
            self.assertEqual(playtest.summarize(root)['missing_functions'], [])


if __name__ == '__main__':
    unittest.main()
