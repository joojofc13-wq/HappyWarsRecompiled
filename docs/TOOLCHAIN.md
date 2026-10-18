# Toolchain

Dependency revisions, package hashes and versions are pinned in `config/upstream-lock.json`.

| Project | Use |
|---|---|
| [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk) | Static PowerPC translation, kernel services, memory, filesystem, input, audio and Xenos GPU plugin |
| [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) | Static recompilation reference; it does not supply the runtime needed by this port |
| [Xenia](https://github.com/xenia-project/xenia) | XEX, STFS and kernel implementation reference |
| [XBLA-Extract](https://github.com/ryzendew/XBLA-Extract) | Extraction implementation reviewed; not used for the verified extraction |
| [Extract-STFS](https://github.com/jasonulbright/Extract-STFS) | Package extraction with separate integrity checks in this project |
| [Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp) | Reference for integration, project presentation and game-specific patches |

The pinned ReXGlue package is `0.10.0.24-dev.gbd833a2`. Its CLI and runtime are experimental; successful translation does not establish full game support.

## Compiler and CLI

The tested compiler is raw Clang 23.1.3 using `--target=x86_64-pc-windows-msvc -fms-runtime-lib=dll`, with MSVC 14.44.35207 headers and libraries and Windows SDK 10.0.26100.0. CMake 4.4.4 and Ninja 1.13.2 drive the build.

Use the executable's `--help` for CLI arguments. The pinned SDK uses `--project-name`, `--xex-path`, `--game-root` and `--project-root`; older wiki examples use different names. The generated project name is `happywars`.

The project builds a patched diagnostic CLI while retaining the official runtime libraries. See [patches](../patches/README.md) and [building](BUILDING.md).

## Licenses

Extract-STFS is included with its MIT license. ReXGlue patches target a BSD-3-Clause revision; its license is included. The SDK contains dependencies with their own notices.

Microsoft installers, headers, libraries, extracted game files and translated game code stay local. The public repository includes project sources, configuration, tests, patches and the supplied README cover.
