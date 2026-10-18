# GPU hang investigation

Gameplay has failed with D3D12 device removal, `0x887A0006`
(`DEVICE_HUNG`), on a Radeon RX 6650 XT. This is distinct from the earlier
unregistered-function crashes. The final PM4 draw errors follow device removal
and do not establish which earlier GPU command caused the hang.

Disabling bindless resources did not resolve the failure. DRED reported a GPU
page fault at virtual address `0x0000000350CC0000`. Its allocation has not yet
been identified, so the address alone does not establish the responsible resource.

The current trial also disables `d3d12_tiled_shared_memory`. The SDK then creates
a fully committed 512 MiB shared-memory buffer instead of a reserved buffer with
sparse tile mappings. This tests whether missing tile backing contributes to the
fault. It increases video-memory use and remains an unverified workaround.
Bound descriptors and DRED remain enabled as in the preceding failed run.
No Windows timeout or driver settings are changed.

`scripts/playtest.py` accepts the optional boolean keys `d3d12_bindless`,
`d3d12_debug`, and `d3d12_tiled_shared_memory` from `private/gpu-settings.json`.
Each session manifest records these settings alongside the executable hash.
Removing the file restores SDK defaults. Existing logs are retained for
comparison. Sustained gameplay must be tested before reporting a fix.
