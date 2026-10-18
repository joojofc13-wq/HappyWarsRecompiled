# Windows builder

Download **HappyWarsBuilder.exe** from the project's prereleases. Select your
**Game folder** and an empty **Output folder**, accept the Microsoft build-tools
license, then click **Build**. Those are the only folder fields.

Use your own extracted Xbox 360 copy from **Happy Wars Revival**: TU46,
version **0.0.46.7**, Media ID **5CEC066D**. The builder verifies the executable
hash before preparing the output. Earlier versions are not guaranteed to work.

## Requirements

- Windows x64 and an internet connection for the first build.
- Your own complete extracted TU46 copy containing `Default.xex` and `media`.
- Space for the copied game, portable tools, generated C++ and object files.

Python, Git, LLVM, Microsoft headers, Windows SDK and the pinned ReXGlue tools
are downloaded and prepared automatically. You do not need to install or locate
them first. Downloads are pinned in `config/upstream-lock.json`; executable-tool
archives and the SDK are checked against recorded hashes. The Microsoft installer
is used to extract headers and libraries locally, not to install Visual Studio.

Tools stay under the output's `tools` directory. A short temporary directory is
used during Microsoft SDK extraction to avoid Windows Installer path limits.
No system PATH change is made. Game files and updates are never downloaded.

## Build and play

1. Select the game folder and a new or empty output folder.
2. Read the **License** link and accept the Microsoft build-tools license.
3. Click **Build** and wait for completion. Downloads and native compilation can take time.
4. Click **Open game folder**, then double-click **HappyWars.exe**.

The original input is unchanged. Nonempty output folders are rejected. Failed
builds retain their files and logs for diagnosis; use a new empty output for
another attempt. The main log is `logs/builder.log`.

The result is `build/game/HappyWars.exe`, runtime libraries and the save-reset
helper. Playing does not require LLVM or Python installed separately.

The FPS counter uses an optional compatible original Scaleform font. TU46 uses
different font resources, so a build without that optional base-game font keeps
the FPS overlay disabled. Maintainers can supply their owned font through
`fps_font_source` in ignored `config/local-tools.json`.

## Saves

Saves use `private/smoke-user/title-storage.sqlite`. Backups and SQLite journal
files stay in that profile directory. Close the game and use **ResetSaves.cmd** to reset this
port's saves after typing **RESET**. Game files, shader caches, tool downloads,
settings and unrelated games are preserved. The next launch starts a new save.

## Packaging and validation

Maintainers use the pinned PyInstaller 6.22.3 and run
`scripts/package_builder.py --output build/release-public`. It embeds the audited
Git index and emits the builder, a source/hash manifest and `SHA256SUMS.txt`.
No original game executable, asset, translated game code, font or save is included.

The portable Python, pip, Git and LLVM downloads were exercised. Microsoft SDK
extraction, SDK/tool setup and native recompiler-tool compilation passed using
those portable tools with external developer tools removed from the test PATH.
The earlier staged TU46 native game build and direct executable startup passed.
This is not a clean Windows VM test and does not establish stable gameplay.

The UI uses Python/Tk and PyInstaller; see the
[PyInstaller license](https://pyinstaller.org/en/stable/license.html). Subprocess
handling follows its [Windows guidance](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html).

The progress bar estimates overall progress from 0 to 100%. Native compilation
updates from completed Ninja tasks. Tool setup and code generation advance at
stage boundaries, so the percentage can remain unchanged while work continues.
100% means the executable and runtime files are ready.
