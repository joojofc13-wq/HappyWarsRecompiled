# Native boot

This document records an earlier base-version investigation. See [current status](../STATUS.md) for TU46 gameplay and remaining issues.

The native build reaches the intro and a 3D title scene. A coherent virtual LIVE profile passes the account gate. The local-service build now sends storage GET and PUT requests, then encounters a guest access violation. The mode menu and gameplay remain unverified.

## Function discovery

| Address | Original behavior and correction |
|---|---|
| 0x83393258 | Compare, conditional return, tail branch and return; explicit shared-register boundary |
| 0x8342DA20 | Leaf comparator, 0x88 bytes; explicit boundary |
| 0x83353380 | A single blr; registered only after checking its original opcode |
| 0x830613E0 | Audio-thread routine, 0x100 bytes, ending before the next PDATA function |
| 0x83066CA0 | Six-instruction virtual tail call; 0x18-byte boundary |
| 0x830697E8 | Subtracts 36 from r3 and branches to 0x83069388 |
| 0x8327D108 | Virtual adapter in a consecutive family; original arguments and flags preserved |
| 0x83329250 | Four-instruction virtual tail call |
| 0x82B67950 | Indexed virtual dispatcher using the original destination table |
| 0x82D1D0A0 | Sets r5 to 6, then branches to 0x82D1B380 |
| 0x82BA52B8 | Five-instruction closure adapter; 0x14-byte boundary |

`prepare_thunk_boundaries.py` declares 238 short adapters from constrained instruction patterns and code references. It excludes existing manual and PDATA intervals and requires a preceding terminator or padding. The SDK translates the original instructions; these declarations do not replace their behavior.

Supplemental immediate-return callbacks must match the original blr opcode. They are not a fallback for unknown functions.

## Build checks

The preflight rejects missing labels and explicit translation traps. Cached audit results are reused only when generated-source and verifier hashes match.

The SDK emits both an ordered mapping array and individual registration calls. `verify_registration.py` requires exact ordered equality before the application uses a loop over that array. The current table contains 237,086 pairs.

The diagnostic code generator is selected through the project-owned CMake override. Regeneration cannot silently replace this choice. Runtime libraries still come from the pinned SDK.

Translated code now uses `-O1`. The observed executable size decreased from 210,965,504 to 118,457,856 bytes in the optimization comparison. No FPS comparison has been recorded, and later builds can have different sizes.

## Reproducing a boot test

```powershell
py scripts/recompile.py
py scripts/build.py --diagnostics
py scripts/build.py --game --opt-level 1 --jobs 6
py scripts/runtime_smoke.py --seconds 120 --visible --keyboard
```

The smoke runner archives the preceding log and records the executable hash, exit code, timeout and observed runtime markers. A forced stop at the time limit is not classified as a crash. Runtime initialization markers do not prove menu or match functionality.

Native fixture tests cover a leaf search, pointer-adjusting tail calls, virtual adapters and indexed dispatch. They preserve the selected translated instructions while replacing callees with test observers. They do not validate the real callee's gameplay behavior.
