# Vulkan development build

The local TU46 build now uses a Vulkan-only Xenos plugin and Vulkan presentation.
The pinned Windows runtime stays in place; the plugin includes the Vulkan UI
implementation that the original runtime package did not provide. Guest timing
remains at its original 30 FPS target. The FPS counter and per-run logs remain.

The local test selected the Radeon RX 6650 XT and rendered the menus, but match
scenes appeared black while the HUD remained visible. A fix for invalid Vulkan
structure headers in unused color attachment slots is installed for testing.
Its effect on match rendering remains unverified. The public Builder has not yet
been updated to distribute this experimental plugin.

## Build the plugin

Use the Windows development toolchain described in BUILDING.md. In
`config/local-tools.json`, set `rexglue_source` to a checkout of the revision
pinned in `config/upstream-lock.json`, alongside the existing SDK and tool paths.

```powershell
py scripts/build_vulkan_gpu.py --jobs 2
```

The helper applies the Vulkan attachment patch, initializes missing Vulkan
submodules at their pinned revisions, and builds
`build/gpu-vulkan/rexgpu-xenos.dll`. Conflicting source edits stop the build
without resetting the checkout. It does not rebuild translated game
code or change an installed game. Close the game and back up its existing plugin
before replacing that DLL.

For a direct launch, place `happywars.toml` beside HappyWars.exe:

```toml
gpu = "vulkan"
vulkan_validation_enabled = false
```

Device selection is automatic unless `vulkan_device` is specified. In the local
test, index 0 was the RX 6650 XT and index 1 was the integrated GPU. Device indices
can differ on another PC. Playtest also accepts these settings in its optional
`private/gpu-settings.json` and records them in each session manifest.
