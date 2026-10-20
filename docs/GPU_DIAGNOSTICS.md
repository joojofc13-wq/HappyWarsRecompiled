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

The first ROV session survived the previously failing sections according to the
tester, but frame rates were poor. The next ROV session, with validation disabled,
failed with the same DEVICE_HUNG result. ROV is therefore not a confirmed fix.

## GPU access validation

The earlier debug-enabled runs reported that the D3D12 debug layer could not be
loaded. DRED was active, but shader-access validation was not. The local
development machine now has the Windows Graphics Tools capability installed.

`patches/rexglue-gpu-validation.patch` adds an opt-in
`d3d12_gpu_based_validation` flag to the diagnostic plugin. Apply it after the
allocation and queue-fence patches. It enables validation before device creation
and reads the D3D12 information queue into the game log. Queue polling supports
Windows 10, where the newer message-callback interface is unavailable.

The current local diagnostic executable selects Agility SDK 619 with matching
app-local core and debug-layer binaries. The playtest manifest records their
hashes. Both validation activation and log capture were verified at startup.
Shader compilation and execution can be much slower under this instrumentation;
these runs must not be used as performance benchmarks. This is a diagnostic
configuration, not a public gameplay default or a verified crash fix.

See Microsoft's [GPU-based validation documentation](https://learn.microsoft.com/en-us/windows/win32/direct3d12/using-d3d12-debug-layer-gpu-based-validation)
and [Agility SDK setup](https://devblogs.microsoft.com/directx/gettingstarted-dx12agility/).

Full shader instrumentation stalled after the third submitted frame on this
machine, with a black screen and no useful access errors. The local trial now
uses RTV with GPU-based validation disabled. Ordinary CPU-side D3D12 validation
and DRED remain enabled, and the diagnostic plugin captures their messages too.
The title resumed submitting frames at approximately 30 FPS during startup.
This verifies recovery from the diagnostic black screen, not match stability.

## Presentation-side device loss

The CPU-validation trial exited during a match with the generic graphics-device
loss message, but no command-processor device-removal details. The presenter can
report loss first; its callback aborted immediately before the other thread
reached the diagnostic path.

`patches/rexglue-present-loss-diagnostics.patch` queries the device-removal reason
and captures the information queue and DRED output from that callback before
flushing the logs and aborting. Breadcrumbs with zero completed operations are
included because the first operation may be the one that failed. Apply this
patch after the preceding three patches. This closes a diagnostic gap and does
not fix the device loss itself.

## Submission resource lifetime

The personal test build is back on D3D12 RTV with original 30 FPS pacing.
CPU and GPU validation are disabled for gameplay; DRED logging is retained.
The Vulkan experiment did not render the match scene correctly.

Apply `rexglue-submission-lifetime.patch` after the four D3D12 patches above.
It prevents a failed frame-fence wait from retiring resources still referenced
by the GPU. It also handles the device-removal fence sentinel without treating
it as completion, checks allocator/list reset and list close results, and only
advances the submission number after a successful queue signal. Failed OS waits
now stop with an explicit error instead of continuing with unsafe resource reuse.

`py scripts/test_submission_lifetime.py` compiles the actual patched fence-read
and frame-admission blocks with injected pending, completed and removed-device
states. The diagnostic plugin builds successfully and the regression passes.
These checks cover error handling, not the original GPU fault: sustained match
stability and performance still require a gameplay test. The prior DEVICE_HUNG
page fault remains unresolved until that test provides evidence.

## Frame overlap comparison

The RTV lifetime-guard trial still failed during a match with DEVICE_HUNG.
It held approximately 30 FPS before the failure. The guard is not a verified
fix for the original GPU hang. DRED was not enabled in that session because
validation was disabled, so no allocation or breadcrumb evidence was captured.

`rexglue-frame-overlap-diagnostics.patch` applies after the lifetime patch. It
adds an optional `d3d12_max_frames_in_flight` setting (1 to 3, default 3). The
comparison build uses 1 to wait for the preceding frame before reusing frame
resources. This isolates overlap without changing the guest's 30 FPS timing.
The default preserves the SDK's existing frame queue.

The separate `d3d12_dred` option enables breadcrumbs and page fault tracking
before device creation, independently of CPU/GPU validation. This restores
crash evidence without enabling the slow shader-access instrumentation.
Both options are recorded by the playtest launcher. Stability of the one-frame
comparison remains unverified until tested in a match.
