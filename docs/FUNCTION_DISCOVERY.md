# Function discovery

ReXGlue combines PDATA, direct calls, RTTI and virtual tables, control-flow analysis and gap filling. A static pass can miss destinations constructed at runtime. See the [pipeline overview](https://github.com/rexglue/rexglue-sdk/wiki/Codegen-Pipeline-Overview) and [generated-code structure](https://github.com/rexglue/rexglue-sdk/wiki/Generated-Code-Structure).

## Changes in this project

The gap scanner did not treat canonical bctr as a terminator. The patch adds that case while preserving bctrl calls, control-flow discovery and cleanup of absorbed regions.

The resulting analysis found 832 additional entries after correcting the full 0x188-byte boundary of the switch function at 0x830FBEB8. Labels and explicit translation traps are checked before compilation.

Manual declarations and constrained adapter scans use original instructions and PDATA boundaries. A reference in data is only a candidate: it can point to an internal label or exception structure.

```powershell
py scripts/build.py --diagnostics
```

The report separates missing PDATA starts, destinations observed in runtime logs and speculative data references. It does not count every candidate as a missing function.

## Related work

[XenonRecomp issue 114](https://github.com/hedge-dev/XenonRecomp/issues/114) describes exception data mistaken for instructions. [PR 98](https://github.com/hedge-dev/XenonRecomp/pull/98) proposes importing boundaries from an external analysis export. Both illustrate why recovered boundaries need review.

[Unleashed Recompiled's configuration](https://github.com/hedge-dev/UnleashedRecomp/blob/main/UnleashedRecompLib/config/SWA.toml) contains title-specific declarations. Those addresses cannot be reused for Happy Wars.

The [Xenia Happy Wars report](https://github.com/xenia-project/game-compatibility/issues/1239) describes slow intros and a LIVE requirement after the title. It is a separate execution and does not verify this port.
