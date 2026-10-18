> [!NOTE]
> Experimental prerelease with a Windows builder and project sources. No playable game binary or game content is included. You must provide your own compatible Happy Wars Xbox 360 files.

## How to Build

Follow the [build guide](https://github.com/joojofc13-wq/HappyWarsRecompiled/blob/v0.1.0-alpha.2/docs/BUILDING.md).
The root configuration targets the base game. The
[TU46 development profile](https://github.com/joojofc13-wq/HappyWarsRecompiled/blob/v0.1.0-alpha.2/ports/tu46/README.md)
preserves version-specific configuration and hook sources. Download
`HappyWarsBuilder.exe` to compile the supported TU46 copy through a simple Windows
interface. Python, Git and LLVM remain prerequisites; see the
[builder guide](https://github.com/joojofc13-wq/HappyWarsRecompiled/blob/v0.1.0-alpha.2/docs/BUILDER.md).

## Changelog

- Add a Windows builder for an owned TU46 copy, with exact executable validation.
- Start HappyWars.exe directly with automatic game and save paths.
- Include a save-reset helper that preserves game files and shader caches.
- Enable permanent local Premium membership from the first launch.

- Reach Game Home, the tutorial and short Skirmish gameplay sessions in the local TU46 development port.
- Add local network identity and real statistics-enumerator handles.
- Preserve original save payloads, including dated title-storage backups.
- Repair missing original callback and adapter boundaries found in playtests.
- Add an FPS counter using the owned game's font, with an F6 toggle.
- Add compatible local title-update inspection and import tools.
- Keep separate crash logs and record GPU diagnostic settings for each run.

## Validation

The builder completed a new staged native build using the existing tested
toolchain, and the packaged Windows UI passed its startup check. Clean-machine
dependency installation remains unverified. Direct executable startup also passed.
Interactive testing confirmed menu access, Skirmish gameplay, the FPS counter,

## Known Issues

- Gameplay can fail with D3D12 `DEVICE_HUNG` and a GPU page fault on the tested Radeon RX 6650 XT.
- Disabling bindless resources did not fix that failure. Disabling tiled shared memory is an unverified diagnostic trial.
- The Marketplace warning persists; local catalog responses are unfinished.
- Full match completion, all maps and modes, rewards and complete progression persistence remain unverified.
- Inventory capacity remains 1024 entries. Performance still needs measurement and optimization.

See [project status](https://github.com/joojofc13-wq/HappyWarsRecompiled/blob/v0.1.0-alpha.2/STATUS.md) for the current validation scope.
