# Windows builder

Download **HappyWarsBuilder.exe** from the project's prereleases. It uses the
Windows system theme and builds native game code from your own files. It contains
no Happy Wars executable, assets, translated game code, fonts or saves.

Use your own extracted Xbox 360 copy from **Happy Wars Revival**: TU46,
version **0.0.46.7**, Media ID **5CEC066D**. The builder verifies its executable
SHA-256 before preparing the destination. Other versions are rejected.

## Requirements

- Windows x64, Python 3.11 or newer with pip, Git for Windows and LLVM/Clang.
- An LLVM `bin` folder containing `clang.exe` or `clang-<major>.exe` and `lld-link.exe`.
- Portable Microsoft headers and Windows SDK, or acceptance of their license for local download.
- Your own complete extracted TU46 game folder containing `Default.xex` and `media`.
- Optional: the original `media/scaleform/Font_en.bres` from your own base game enables the FPS overlay. TU46 uses different font resources; without the compatible font, the game builds and runs with the FPS overlay disabled.
- Space for a copy of the game, dependencies, generated C++ and object files. Build duration has not been measured.

The builder includes its UI runtime. Compiler scripts require an external Python
installation. It downloads pinned SDK/build dependencies and retrieves pinned
tool sources. LLVM, Git and Python must already be installed.

## Build

1. Select the game folder, a new or empty build folder and your LLVM `bin` folder.
2. Select a portable Microsoft SDK, or check the license box to download it.
3. Supply the owned base-game font if needed, then click **Build**.
4. Click **Open game folder** and double-click **HappyWars.exe**.

The original input remains unchanged. Nonempty output folders are rejected.
A failed build retains its files and `logs/builder.log`; select a new empty
folder for another attempt. Output is `build/game/HappyWars.exe` with its runtime
libraries and locally extracted font.

## Saves and reset

The game resolves local paths automatically when opened from Explorer.
Normal saves use `private/smoke-user/title-storage.sqlite`; mod saves use
in those profile directories.

Compilation places **ResetSaves.cmd** beside the game. Close the game, run the
helper and type **RESET** to permanently clear this port's save databases,
backups and decoded analysis save. Game resources, shader caches, mod settings
and other games are preserved. The next launch creates a fresh profile.
Linked profile directories and active game processes are rejected.

## Packaging

Maintainers run `scripts/package_builder.py` with PyInstaller 6.22.3 installed.
It audits and embeds the exact Git index and emits the builder, a source/hash
manifest and `SHA256SUMS.txt` under `build/builder-release`.

The UI uses Python/Tk and PyInstaller. The latter's bootloader exception permits
distribution; see the [PyInstaller license](https://pyinstaller.org/en/stable/license.html).
Toolchains and game resources remain separate inputs.

## Validation scope

A new staging directory completed image loading, code generation and native
compilation with the existing tested toolchain. The separate packaged UI startup
check passed with the Windows `vista` theme. Direct game startup from an unrelated
working directory also succeeded. This does not validate a clean machine with
fresh tool downloads or establish stable matches.
