# TU46 development profile

This directory preserves the project-owned configuration used by the local TU46
port. It contains function-boundary declarations, three version-specific runtime
sources, the manifest and CMake target settings. It contains no translated game
instructions, executable, assets, font or player data.

The tested executable is version **0.0.46.7**, Media ID **5CEC066D**, Title ID
**58410AE9**. Its SHA-256 is recorded in `profile.json`. Other executables must
not use these addresses without analysis.

## Manual setup

Use a separate checkout for TU46. Follow the root build guide to install and
configure the pinned dependencies. Supply your own complete TU46 game directory
as `private/game`, including `Default.xex` and its matching resources. Do not
mix base and updated files. The update importer stages compatible local packages;
it does not manufacture the missing source version or download game content.

Copy this directory's `CMakeLists.txt`, `happywars_manifest.toml`, `config/`
files and `runtime/` files over their counterparts at the checkout root. Keep
the other project sources and scripts. The CMake override enables
`HAPPYWARS_TU46` and the runtime files select TU46 hook addresses.

Run code generation and the normal native build from the build guide. The FPS
font step needs the original `media/scaleform/Font_en.bres`; if your updated
copy omits it, supply that resource from your own base game via the
`fps_font_source` setting in ignored `config/local-tools.json`.

The [Windows builder](../../docs/BUILDER.md) applies this profile automatically.
The original development workspace completed the manual process. A clean-machine
setup with freshly downloaded dependencies still needs validation. Generated
code, loaded images and runtime logs stay local.

## Observed behavior

Game Home, tutorial and Skirmish gameplay have been reached. Sustained gameplay
still crashes on the tested AMD GPU, and the Marketplace warning persists.
and [GPU diagnostics](../../docs/GPU_DIAGNOSTICS.md).
