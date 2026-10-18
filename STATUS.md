# Project status

**The TU46 development port reaches Game Home, the tutorial and Skirmish.**
Short gameplay sessions have been confirmed by interactive testing. A full match
has not been completed reliably. The latest blocker is a D3D12 `DEVICE_HUNG`
with a GPU page fault on a Radeon RX 6650 XT. The Marketplace warning remains.

The public repository contains project-owned source, tooling and the
[TU46 development profile](ports/tu46/README.md). It does not include a playable
binary, game assets, translated game code, extracted fonts or saves. The root
configuration still targets the original base version; TU46 has separate hook
addresses and boundary declarations. The Windows builder completed a new staged native build with the existing tested toolchain; clean-machine dependency setup still needs validation.

| Component | Evidence and remaining work |
| --- | --- |
| Recompilation | Native Windows x64, ahead-of-time PowerPC translation through the pinned ReXGlue SDK |
| TU46 input | Version 0.0.46.7, Media ID 5CEC066D, Title ID 58410AE9; exact executable hash recorded in the version profile |
| Original behavior | Missing callback and adapter boundaries are declared and compiled from the owned executable |
| Graphics and input | Intro, 3D scenes and gameplay observed; SDL keyboard/controller support |
| Performance | Translated code uses `-O1`; low FPS reported; no measured optimization improvement claimed |
| FPS counter | Original game font extracted locally; counter observed; F6 toggle implemented, user toggle check pending |
| Profile and services | Local identity, loopback network status, in-process HTTP and empty statistics views |
| Saves | Original payloads stored in SQLite with slots, revisions, transactions and dated backups; complete progression recovery unverified |
| Menu and Skirmish | Game Home, tutorial and short Skirmish gameplay confirmed |
| Marketplace | Warning persists; a valid local catalog protocol remains unfinished |
| Inventory | 1024-entry capacity retained; crossover grants prioritized; corrected visibility still needs confirmation |
| Tickets and Premium | Local ticket hooks and permanent Premium policy implemented; ticket spending and Premium reward/UI effects need validation |
| Maps and modes | Full coverage, match completion and rewards remain unverified |
| GPU stability | Disabling bindless resources did not fix the crash; committed shared memory is the current unverified trial |
| Distribution | Windows builder and public sources; no playable game binary or assets |

## Validation

The last full native CTest run passed 16 tests covering storage, selected
translated routines, profile/authentication contracts, HTTP, network identity,
statistics enumeration and local ticket accounting. Python checks cover save
and adapter-pattern recognition. These checks do not establish stable gameplay.

The current GPU trial changes resource allocation without modifying Windows
settings. Logs remain local and retain per-run executable hashes and selected
GPU settings. See [GPU diagnostics](docs/GPU_DIAGNOSTICS.md) and
[playtesting](docs/PLAYTESTING.md).

## Next milestones

1. Resolve the GPU page fault and complete a sustained Skirmish match.
2. Implement the remaining local Marketplace responses.
3. Verify rewards, ticket spending and progression after restarting.
4. Validate maps, modes and optional mods.
5. Measure performance and validate the public TU46 build workflow.

Releases follow [verified milestones](docs/RELEASES.md).
