> [!NOTE]
> Experimental Windows builder and project sources. Supply a compatible owned Happy Wars TU46 copy from Happy Wars Revival. No playable binary or game assets are distributed.

## Build or update

Download **HappyWarsBuilder.exe**. For a new build, select your game files and an empty output folder. To update a standalone installation, select **Update existing build**, choose its output folder and leave the game folder empty. Close the game before updating. Read the [builder guide](https://github.com/joojofc13-wq/HappyWarsRecompiled/blob/v0.1/docs/BUILDER.md).

## Changes

- Update existing builds while preserving owned game files, saves, caches, settings and extra files.
- Back up replaced runtime files and restore them if replacement fails.
- Show estimated overall progress from 0 to 100% and live native compilation counts.
- Export a standalone game folder without compiler tools or source files.
- Add native TU46 copy/fill fast paths, with fallbacks for overlapping copies and non-RAM ranges.
- Enable an experimental 60 FPS target. Set FrameRate=30 in HappyWars.ini to restore original pacing.
- Include the FPS counter in every build, with an F6 toggle and built-in font fallback.
- Fix asynchronous HTTP write-completion data lifetime and response cursor resets.
- Preserve permanent local Premium membership and local title-storage saves.

## Validation

Sixteen native service/translation tests passed, including HTTP callback data and repeated response reads. Native CRT comparisons passed for sizes, alignment, byte values, overlapping copies and return values. A 4 KiB memset microbenchmark measured 42.4 ms for translated code and 4.9 ms for the native path; this is not a whole-game benchmark.

Updater tests cover file preservation, backup contents, Windows file locks, concurrent installers and rollback after a simulated replacement failure. Short boot trials reached a 61.5 FPS sample at 120 Hz guest refresh. Full gameplay speed and sustained 60 FPS remain unverified.

## Known issues

- Gameplay may fail with D3D12 DEVICE_HUNG and a GPU page fault on the tested Radeon RX 6650 XT. No confirmed GPU-hang fix is included.
- Disabling bindless resources did not fix that failure. Committed shared memory remains an unverified diagnostic trial.
- The Marketplace warning persists; local catalog responses are unfinished.
- Full match completion, all maps and modes, rewards and complete progression persistence remain unverified.
- Ticket display/spending and complete Premium reward/UI effects need further checks.
- Experimental 60 FPS timing needs validation for animations, physics and match timers.
