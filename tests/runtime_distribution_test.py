"""Exercise runtime updates, locked files, backups, and failure recovery."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import runtime_distribution as distribution


class RuntimeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.port = self.root/'work'
        self.native = self.port/'build/game'
        self.native.mkdir(parents=True)
        for name in distribution.REQUIRED:
            (self.native/name).write_bytes(b'old '+name.encode())
        game = self.port/'private/game'
        (game/'media').mkdir(parents=True)
        (game/'Default.xex').write_bytes(b'owned executable')
        (game/'media/asset').write_bytes(b'owned asset')
        self.output = self.root/'installed'
        distribution.install_runtime(self.port, self.output)
        for name in ('saves/title-storage.sqlite', 'mods/settings.json', 'custom-tool.exe', 'cache/shaders', 'HappyWars.ini'):
            path = self.output/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'preserve '+name.encode())

    def snapshot(self):
        return {p.relative_to(self.output).as_posix():p.read_bytes()
                for p in self.output.rglob('*') if p.is_file() and '.update-backups' not in p.parts}

    def test_update_preserves_profiles_assets_and_private_tools(self):
        before = self.snapshot()
        for name in distribution.REQUIRED:
            (self.native/name).write_bytes(b'new '+name.encode())
        distribution.install_runtime(self.port, self.output, update=True)
        after = self.snapshot()
        for name, data in before.items():
            if name not in (*distribution.REQUIRED, 'build-info.json'):
                self.assertEqual(after[name], data)
        backups = list((self.output/'.update-backups').iterdir())
        self.assertEqual(len(backups), 1)
        for name in distribution.REQUIRED:
            self.assertEqual((backups[0]/name).read_bytes(), before[name])
            self.assertEqual(after[name], b'new '+name.encode())
        manifest = json.loads(after['build-info.json'])
        self.assertEqual(manifest['files']['HappyWars.exe'], hashlib.sha256(after['HappyWars.exe']).hexdigest())

    def test_failed_replace_rolls_back_and_releases_lock(self):
        before = self.snapshot()
        for name in distribution.REQUIRED:
            (self.native/name).write_bytes(b'new')
        replace = os.replace
        count = 0
        def fail_second(source, target):
            nonlocal count
            count += 1
            if count == 2:
                raise PermissionError('simulated file becoming locked')
            return replace(source, target)
        with patch.object(distribution.os, 'replace', side_effect=fail_second):
            with self.assertRaises(PermissionError):
                distribution.install_runtime(self.port, self.output, update=True)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.root/'.installed.builder.lock').exists())

    def test_locked_runtime_leaves_all_files_unchanged(self):
        before = self.snapshot()
        with patch.object(distribution, 'check_replaceable', side_effect=RuntimeError('game running')):
            with self.assertRaises(RuntimeError):
                distribution.install_runtime(self.port, self.output, update=True)
        self.assertEqual(self.snapshot(), before)

    @unittest.skipUnless(os.name == 'nt', 'Windows file sharing semantics')
    def test_windows_open_file_is_rejected(self):
        with (self.output/'HappyWars.exe').open('rb'):
            with self.assertRaises(RuntimeError):
                distribution.check_replaceable([self.output/'HappyWars.exe'])

    def test_other_output_and_conflicting_directory_are_rejected(self):
        with self.assertRaises(ValueError):
            distribution.validate_destination(self.root, update=True)
        (self.native/'fonts').mkdir()
        (self.native/'fonts/fps.ttf').write_bytes(b'font')
        (self.output/'fonts/fps.ttf').mkdir(parents=True)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            distribution.install_runtime(self.port, self.output, update=True)
        self.assertEqual(self.snapshot(), before)

    def test_parallel_install_is_rejected(self):
        before = self.snapshot()
        with distribution.installation_lock(self.output):
            with self.assertRaises(RuntimeError):
                distribution.install_runtime(self.port, self.output, update=True)
        self.assertEqual(self.snapshot(), before)


class GPUOverrideTests(unittest.TestCase):
    def test_verified_plugin_stages_and_corruption_preserves_the_existing_plugin(self):
        from build_d3d12_gpu import PATCH_NAMES
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); port=root/'port'; payload=root/'payload'
            (port/'build/game').mkdir(parents=True); (port/'patches').mkdir(); (port/'config').mkdir()
            payload.mkdir(); (payload/'rexgpu-xenos.dll').write_bytes(b'verified GPU plugin')
            (payload/'licenses').mkdir(); (payload/'licenses/SDK.txt').write_text('SDK license')
            (port/'config/upstream-lock.json').write_text(json.dumps({'sdk':{'commit':'pinned'}}))
            patches={}
            for name in PATCH_NAMES:
                data=name.encode(); (port/'patches'/name).write_bytes(data)
                patches[name]=hashlib.sha256(data).hexdigest()
            info=dict(source_revision='pinned',backend='d3d12',patches=patches,
                plugin_sha256=hashlib.sha256((payload/'rexgpu-xenos.dll').read_bytes()).hexdigest())
            (payload/'gpu-build-info.json').write_text(json.dumps(info))
            distribution.apply_gpu_override(port,payload)
            self.assertEqual((port/'build/game/rexgpu-xenos.dll').read_bytes(),b'verified GPU plugin')
            self.assertEqual((port/'build/game/licenses/SDK.txt').read_text(),'SDK license')
            (payload/'rexgpu-xenos.dll').write_bytes(b'corrupt')
            with self.assertRaisesRegex(RuntimeError,'checksum'): distribution.apply_gpu_override(port,payload)
            self.assertEqual((port/'build/game/rexgpu-xenos.dll').read_bytes(),b'verified GPU plugin')
            (payload/'rexgpu-xenos.dll').write_bytes(b'verified GPU plugin')
            (port/'patches'/PATCH_NAMES[0]).write_bytes(b'wrong patch')
            with self.assertRaisesRegex(RuntimeError,'source patch'): distribution.apply_gpu_override(port,payload)


if __name__ == '__main__':
    unittest.main()
