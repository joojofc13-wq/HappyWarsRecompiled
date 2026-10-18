# Building from Source

For the two-folder Windows interface with automatic tool downloads, use the
[builder](BUILDER.md). The commands below describe manual developer setup.

You need your own game package, Python, Git, Clang, MSVC headers and libraries, and the Windows SDK. Dependency versions and hashes are pinned in `config/upstream-lock.json`.

```powershell
py scripts/install_msvc.py --accept-license
py scripts/setup.py --llvm-bin "C:\path\to\llvm\bin" --msvc tools/msvc --diagnostic-source
py scripts/build_diagnostic.py
py scripts/extract.py "C:\path\to\your\game-package"
py scripts/analyze.py
py scripts/resources.py
py scripts/data_audit.py
py scripts/recompile.py
py scripts/build.py --game --opt-level 1 --jobs 6
```

The raw Clang executable must use the MSVC ABI to link with the SDK. Setup writes local paths to the ignored `config/local-tools.json`. LLVM itself is not installed by these scripts. The tested compiler is Clang 23.1.3, with CMake 4.4.4 and Ninja 1.13.2.

The executable is written to `build/game/HappyWars.exe`. CMake stages its runtime DLLs. Extracted game files stay under `private/game`.

```powershell
py scripts/runtime_smoke.py --seconds 120 --visible --keyboard
```

This command closes the process when the test limit expires. Its report distinguishes a timeout from a crash. Keyboard mappings include Enter for Start, Space for A, Backspace for B, and WASD for the left stick. Controllers use SDL.

The default configuration targets the base game. For the tested updated version,
see the [TU46 development profile](../ports/tu46/README.md). The experimental [Windows builder](BUILDER.md) automates this profile.
A clean-machine setup with freshly downloaded dependencies still needs validation.
The FPS font step requires `fonttools`, pinned in `config/upstream-lock.json`,
and derives its font from your owned game files.

## Tests

```powershell
py -m unittest discover -s tests -p test_tools.py
py scripts/build.py
py scripts/prepare_translation_test.py
py scripts/prepare_thunk_test.py
py scripts/prepare_indexed_dispatch_test.py
py scripts/build.py --translation-test
py scripts/build.py --diagnostics
```

The default build tests SQLite storage. Translation tests run selected original routines with fixture memory. Other tests cover the virtual profile, authentication and local storage boundaries. They do not establish that a match works.

Generation does not use `--force`. The build rejects missing labels and explicit translation traps. After changing the generator itself, use `py scripts/recompile.py --regenerate`. Do not run two generators against the same output directory.

## Running the local build

Double-click `build/game/HappyWars.exe` after building. It resolves game, save
and cache paths from the project folder. `LaunchHappyWars.cmd` remains available
for separate playtest logs. `ResetSaves.cmd` clears only this port's save data
after confirmation.

The [builder guide](BUILDER.md) describes the Windows interface, requirements
and save locations. Gameplay stability remains under investigation.
