<p align="center">
  <img src="assets/happy-wars-cover.png" alt="Happy Wars" width="360">
</p>

# Happy Wars Recompiled

> Use the Xbox 360 copy from **Happy Wars Revival**. This is the most up-to-date copy tested with this project: **TU46, version 0.0.46.7, Media ID 5CEC066D**. Earlier versions are not guaranteed to work. The builder verifies the executable hash before compiling.

An unofficial native Windows x64 port of the Xbox 360 version of Happy Wars, built using static PowerPC recompilation with ReXGlue.

The goal is to preserve the original campaign and offline Skirmish modes, including the original bots, maps, equipment, Happy Cards, and persistent progression.

**You must provide the game files from your own copy of Happy Wars.**

**Experimental:** the TU46 development port reaches Game Home, the tutorial and Skirmish gameplay. Matches remain unstable: a D3D12 GPU crash is under investigation, and the Marketplace warning persists. There is no ready-to-play public binary.

[Latest prerelease](https://github.com/joojofc13-wq/HappyWarsRecompiled/releases) · [Project status](STATUS.md) · [Build guide](docs/BUILDING.md)

## Table of Contents

- [Requirements](#requirements)
- [How to Run](#how-to-run)
- [Implemented Features](#implemented-features)
- [Roadmap](#roadmap)
- [Known Issues](#known-issues)
- [FAQ](#faq)
- [Building](#building)
- [Credits](#credits)

## Requirements

Development currently targets Windows x64 and a Direct3D 12 GPU supported by the pinned ReXGlue Xenos backend. Minimum hardware and performance requirements have not been measured.

Building requires Python, Git, Clang, MSVC headers and libraries, the Windows SDK, and your own Happy Wars Xbox 360 package. See the [tested toolchain](docs/TOOLCHAIN.md).

## How to Run

Download **HappyWarsBuilder.exe** from the [prereleases](https://github.com/joojofc13-wq/HappyWarsRecompiled/releases) to compile your supported TU46 copy through a simple Windows interface. See the [builder guide](docs/BUILDER.md) for Python, Git, LLVM and Microsoft SDK requirements. No game binary or assets are included.

After building, open `build/game` and double-click **HappyWars.exe**. It finds the game and save paths automatically. **ResetSaves.cmd** beside it resets only this port's saves after confirmation. The development launcher remains available for separate playtest logs.

Keyboard controls: Enter for Start, Space for A, Backspace for B, and WASD for the left stick. F6 toggles the FPS counter. The SDK also supports controllers through SDL.


## Implemented Features

- Native Windows x64 executable from statically translated PowerPC code.
- Intro, title, tutorial and Skirmish rendering through the Xenos backend in the TU46 development port.
- Virtual local LIVE profile that passes the account check.
- In-process HTTP transport, SQLite title storage, dated backups and local statistics views.
- FPS counter using a font extracted locally from the owned game, with an F6 toggle.
- Permanent local Premium membership from the first launch in TU46.
- Windows builder, direct executable startup and a save-reset helper.
- Separate playtest logs with grouped missing-function and GPU failures.
- Repeatable extraction, integrity checks, code generation and build scripts.

Menu and short gameplay sessions have been confirmed interactively. Full match completion, rewards and complete progression persistence remain unverified.

## Roadmap

- [x] Extract and inspect the original game package.
- [x] Compile a native executable and render the title.
- [x] Pass the original account check with a local profile.
- [x] Load local player data and reach the mode menu in TU46.
- [x] Enter Skirmish and play with the original bots in TU46.
- [x] Store local player and equipment data.
- [ ] Verify rewards, upgrades and Happy Cards across complete matches and restarts.
- [x] Begin map and mode playtesting.
- [ ] Complete validation of all available maps and modes.
- [ ] Measure and improve performance.
- [x] Provide an experimental Windows builder for owners of the supported TU46 copy.

## Known Issues

The tested TU46 port can crash during gameplay with D3D12 `DEVICE_HUNG` and a GPU page fault. The latest memory-allocation workaround is a diagnostic trial, not a confirmed fix. The Marketplace warning remains, performance needs work, and all maps and modes have not been validated.

See [STATUS.md](STATUS.md) for validation and [GPU diagnostics](docs/GPU_DIAGNOSTICS.md) for the current crash investigation.

See [offline progression](docs/OFFLINE_PROGRESSION.md) for reward analysis and the local Premium policy.

## FAQ

**Is this a Xenia launcher?**

No. The game CPU code is translated to C++ ahead of time and compiled for Windows x64. The port uses ReXGlue runtime components and its Xenos GPU backend.

**Does it require Xbox Live?**

The target is fully local play. The current code uses a synthetic profile and an in-process service, with no real account credentials.

**Are all maps and modes unlocked?**

Skirmish has been tested, but the full set of maps and modes has not been validated. Inventory grants also retain the original 1024-entry capacity.

**Will I need my own game files?**

Yes. Original game files and translated game code are excluded from this repository. The cover above was supplied for the project page.

## Building

Follow [Building from Source](docs/BUILDING.md). Dependency revisions and hashes are pinned in `config/upstream-lock.json`.

Technical references: [executable analysis](docs/TECHNICAL_ANALYSIS.md), [native boot](docs/BOOT.md), [offline services](docs/OFFLINE.md), [function discovery](docs/FUNCTION_DISCOVERY.md), [account handling](docs/XENIA_NETPLAY.md) and [release policy](docs/RELEASES.md).

## Credits

- [ReXGlue](https://github.com/rexglue/rexglue-sdk) for the recompilation pipeline and runtime.
- [Xenia](https://github.com/xenia-project/xenia) and [Xenia Netplay](https://github.com/Nexia360/xenia-canary) for implementation references.
- [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) for static recompilation references.
- [Extract-STFS](https://github.com/jasonulbright/Extract-STFS) for package extraction.
- [Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp) for project structure, presentation and release references.

Happy Wars belongs to its respective rights holders. Third-party notices are included with the relevant tools and patches.
