# Local patches

## rexglue-gap-cleanup.patch

Base revision: `bd833a2ab69d305f99ddf57418fc38ffec8af93d`.

A reverse index records callers waiting for each branch destination. Function insertion checks those callers while preserving the original resolution rules. Differential tests compare the original and indexed states across 20,000 operations, including removal, replacement and stale records.

Gap cleanup limits its search to candidate gap entries inside each function's bounds while retaining containsAddress. Differential tests compare both loops across 300 overlapping and discontinuous graphs.

The measured analysis completed validation in 13.3 seconds, following an earlier attempt interrupted after more than 20 minutes of CPU time. This is a generator measurement, not an in-game performance result.

The patch also prevents exception-metadata inference from extending a function through another PDATA start. The change resolved missing labels in six generated bodies while preserving metadata parsing. It does not establish full C++/SEH compatibility.

Tests and build definitions are in `tools/diagnostic/`. The runtime remains the pinned official SDK; only the CLI is rebuilt locally.

## rexglue-indirect-tail-branches.patch

Apply after the analysis patch. Canonical bctr terminates a gap segment. bctrl remains a call. Control-flow discovery and cleanup remain enabled.

The game's switch function at 0x830FBEB8 needs its full 0x188-byte boundary. See [function discovery](../docs/FUNCTION_DISCOVERY.md).

## msvc-wine-required-sdk-only.patch

Base revision: `514f8ea34842cd6d831804d0e9658d3a32870ae1`.

Limit administrative Windows SDK extraction to the headers, libraries and tools required by the x64 build, including shared OnecoreUap headers. Payloads still come from official manifests and are checked by the downloader. Microsoft files remain local.

## Build integration

Project-owned CMake selects the patched CLI through `REXGLUE_CODEGEN_EXECUTABLE`, so code generation cannot overwrite the selection.

`HAPPYWARS_RECOMP_OPT_LEVEL` controls optimization of translated C++; host code and runtime remain Release. The application output is HappyWars.exe. CMake stages the SDK Xenos plugin alongside it.

