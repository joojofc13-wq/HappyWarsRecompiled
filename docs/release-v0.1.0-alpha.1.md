> [!NOTE]
> This prerelease contains source code and patches. It does not include a playable game binary. Building requires your own Happy Wars Xbox 360 package.

## How to Build

Follow the [build guide](https://github.com/joojofc13-wq/HappyWarsRecompiled/blob/main/docs/BUILDING.md). Extracted game files, generated code and saves remain local.

## Changelog

- Add the native Windows x64 static-recompilation pipeline.
- Render the intro and 3D title screen through the ReXGlue Xenos backend.
- Add a virtual LIVE profile that passes the title's account check.
- Fix missing indirect-tail-call boundaries found during startup.
- Add SQLite storage with transaction, revision, backup and restart tests.
- Add an in-process title-storage service and local endpoint, URL and token handling.
- Match the game's HTTP header queries and storage success codes.
- Add a launcher that supplies the required game and user-data paths.
- Compile translated code with optimization enabled.

## Validation

Generation completed without `--force`. Registration checks covered 237,086 address/function pairs with no missing PDATA starts in the inspected table. Eleven native CTest tests pass. Five Python tool tests passed. Intro and title rendering were observed during interactive runs; the latest run sends storage GET and PUT requests through the local service.

## Known Issues

- Startup previously stopped at the network-save warning. The local-service build sends requests, then encounters a guest access violation.
- The mode menu and Skirmish have not been reached.
- Happy Cards, map and mode unlocks, and in-game equipment persistence remain pending.
- FPS improvement has not been measured.

This remains a source-only development release.
