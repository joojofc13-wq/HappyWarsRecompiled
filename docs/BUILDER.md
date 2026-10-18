# Windows builder

Download **HappyWarsBuilder.exe** from the project's prereleases. Select your
**Game folder** and an empty **Output folder**, accept the Microsoft build-tools
license, then click **Build / Update**. Those are the only folder fields.

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

Sources and tools stay in a separate Windows temporary build workspace. A short temporary directory is
used during Microsoft SDK extraction to avoid Windows Installer path limits.
No system PATH change is made. Game files and updates are never downloaded.

## Build and play

1. Select the game folder and a new or empty output folder.
2. Read the **License** link and accept the Microsoft build-tools license.
3. Click **Build / Update** and wait for completion. Downloads and native compilation can take time.
4. Click **Open game folder**, then double-click **HappyWars.exe**.

The original input is unchanged. New builds require an empty output folder. Failed
builds retain their files and logs for diagnosis; use a new empty output for
another attempt. The workspace path is shown during setup; its main log is `logs/builder.log`.

The output contains `HappyWars.exe`, runtime DLLs, the owned files in `game/`,
and the save-reset helper. It contains no source tree, compiler or object files. Playing does not require LLVM or Python installed separately.

The FPS counter is included in every build and toggles with **F6**. It uses the
original game font when available and a built-in font otherwise.

## Update an installed build

1. Select **Update existing build**.
2. Set **Output folder** to the folder containing `HappyWars.exe` and `game/`.
3. Leave **Game folder** empty to reuse that installation's owned game files.
4. Close the game, accept the tool license and click **Build / Update**.

The builder compiles the current sources in a separate workspace, then replaces
runtime files. It preserves `game/`, `saves/`, `cache/`, user settings and extra
files. Replaced runtime files are retained in `.update-backups/`. Replacement
failures trigger rollback; locked files stop installation before replacement.
Do not launch the game while an update is being installed.

## Frame rate

TU46 builds enable an **experimental 60 FPS target**. Edit `HappyWars.ini` beside
the executable and set `[Graphics] FrameRate=30` to restore original pacing.
Restart after changing it. Existing INI settings are preserved during updates.
Explicit video-refresh command-line or environment settings take precedence.

This changes guest presentation refresh without changing the guest clock. Short
boot trials reached a 61.5 FPS sample, and a user reported 60 FPS after menu
access. Sustained gameplay, animation timing, physics and match timers still
need validation. It does not guarantee 60 FPS on every PC or resolve GPU hangs.

## Saves

Exported games use `saves/title-storage.sqlite` beside the executable.
Development workspaces use `private/smoke-user/title-storage.sqlite`. Backups and SQLite journal
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
