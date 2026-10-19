# GPU hang investigation

Gameplay has failed with D3D12 device removal, `0x887A0006`
(`DEVICE_HUNG`), on a Radeon RX 6650 XT. This is distinct from the earlier
unregistered-function crashes. The final PM4 draw errors follow device removal
and do not establish which earlier GPU command caused the hang.

Disabling bindless resources did not resolve the failure. DRED reported a GPU
page fault at virtual address `0x0000000350CC0000`. Its allocation has not yet
been identified, so the address alone does not establish the responsible resource.

The committed-memory trial also failed with `DEVICE_HUNG`, while retaining the
original 30 FPS pacing. DRED reported another page fault, at
`0x0000000344140000`. This does not identify the allocation or prove that the
same resource caused the earlier fault. Disabling sparse shared-memory mappings
is not a confirmed fix.

The local diagnostic GPU plugin applies `patches/rexglue-dred-allocations.patch`
to the pinned SDK. It logs DRED matching live/recently freed allocation names and
types, names guest textures and shared/EDRAM buffers, and records their buffer
address ranges. These changes add diagnostics and do not claim to fix the hang.
They do not require the optional Windows debug layer for DRED output.
See Microsoft's [DRED allocation output](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_dred_page_fault_output).

`scripts/playtest.py` accepts the optional boolean keys `d3d12_bindless`,
`d3d12_debug`, and `d3d12_tiled_shared_memory` from `private/gpu-settings.json`.
Each session manifest records these settings alongside the executable hash.
Removing the file restores SDK defaults. Existing logs are retained for
comparison. Sustained gameplay must be tested before reporting a fix.

## Queue-operation fence correction

The pinned backend wrapped a logical AND in SUCCEEDED instead of checking the
HRESULT returned by each API separately. With S_OK (zero) from Signal, the old
condition skipped SetEventOnCompletion and still entered the wait. Failure
HRESULTs could also enter that branch after boolean conversion.

`patches/rexglue-queue-fence-order.patch` checks Signal first, then registers the
event only on success, and waits only if both calls succeeded. A local compiled
regression compared the exact old and corrected conditions with successful and
failed HRESULT values: the old expression failed and the corrected one passed.
The diagnostic log records when this path is exercised. Whether this defect
causes the observed gameplay GPU fault still requires a matching playtest.

The named-allocation trial faulted at `0x0000000343E00000`, outside the logged
shared-memory and EDRAM buffer ranges. DRED returned no matching live or recently
freed allocations. This does not establish a resource-lifetime bug by itself.

## Render-path isolation

The fence-correction trial still faulted on the RTV path. The correction fixes a
real error in fence handling, but is not a verified fix for the observed GPU
fault. A new isolated trial selects `render_target_path_d3d12=rov`, retaining
30 FPS pacing, the same profile, committed shared memory and DRED diagnostics.
The plugin logs the effective path, rather than relying only on requested flags.

ROV uses a different render-target implementation; it can trade performance for
accuracy. Early shader compilation caused very low frame rates in this trial.
A live process or a few rendered frames do not establish stable gameplay.
See the [Xenia render-path options](https://github.com/xenia-canary/xenia-canary/wiki/Options).
