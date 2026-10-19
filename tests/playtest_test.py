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

    def test_direct_runs_and_standalone_launcher_preserve_failure_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'game').mkdir();(root/'game/Default.xex').touch()
            (root/'HappyWars.exe').write_bytes(b'fixture')
            def process(command,**kwargs):
                self.assertIn('--user_data_root='+str(root/'saves'),command)
                log=Path(next(a.split('=',1)[1] for a in command if a.startswith('--log_file=')))
                log.write_text('D3D12 device removed: DEVICE_HUNG\n')
                result=unittest.mock.Mock(pid=321);result.wait.return_value=7
                return result
            with patch.object(playtest.subprocess,'Popen',side_effect=process):
                session=playtest.launch('standalone',root)
            self.assertEqual(session['exit_code'],7)
            directory=root/'logs/playtests'
            (directory/'run-123.log').write_text('[critical] Call to invalid or unregistered function at guest address 0x834bd2f8\n')
            (directory/'run-123.guest-fault.log').write_text('fault details')
            report=playtest.summarize(root)
            self.assertEqual(len(report['sessions']),2)
            self.assertEqual(report['missing_functions'][0]['address'],'0x834BD2F8')
    def test_render_path_trial_is_applied_and_invalid_values_do_not_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'game').mkdir();(root/'private').mkdir()
            (root/'game/Default.xex').touch();(root/'HappyWars.exe').write_bytes(b'fixture')
            config=root/'private/gpu-settings.json'
            config.write_text(json.dumps({'render_target_path_d3d12':'rov'}))
            def process(command,**kwargs):
                self.assertIn('--render_target_path_d3d12=rov',command)
                result=unittest.mock.Mock(pid=987);result.wait.return_value=0;return result
            with patch.object(playtest.subprocess,'Popen',side_effect=process):
                session=playtest.launch('ROV',root)
            self.assertEqual(session['gpu_settings']['render_target_path_d3d12'],'rov')
            config.write_text(json.dumps({'render_target_path_d3d12':'unsupported'}))
            with patch.object(playtest.subprocess,'Popen') as launch:
                session=playtest.launch('bad config',root)
                launch.assert_not_called()
            self.assertEqual(session['state'],'launch_failed')
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
