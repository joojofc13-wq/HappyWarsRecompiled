# Executable and resource analysis

## Package identity

| Field | Value |
|---|---|
| Container | LIVE |
| Title ID | `58410AE9` |
| Package size | 467,415,040 bytes |
| Package SHA-256 | `c70f6f0b979dad72cd54c0d912163686bcebd09ba114aa4bd35495825e2bee33` |
| Extracted content | 402 files, 34 directories, 463,663,802 file bytes |
| Executable | `Default.xex`, 7,258,112 bytes |
| XEX SHA-256 | `0e4dde7ac8c1e81d6f7ec5dee62cc623e693e905a471232d1b0b28d6f0e8f548` |
| Version | `0.0.0.2` |
| Media ID | `061F2D01` |

Extract-STFS extracts the package. An independent implementation checks referenced SHA-1 blocks and compares each extracted file with the package byte stream. These checks do not verify the RSA signature or upper STFS hash tree. Alternate-table resilient STFS formats are rejected because their selection logic is not implemented.

## Loaded image

The SDK loader exposes a big-endian PowerPC PE image with machine value `0x01F2`, base `0x82000000`, entry `0x830F23C8`, XEX header size `0x6000` and loaded-image size 38,469,632 bytes. Encryption and compression enum values are 1 and 2.

`scripts/capture_image.py` captures the loaded image with ReadProcessMemory for local analysis. The snapshot stays in `private/loaded-image.bin`.

| Section | RVA | Virtual size |
|---|---|---:|
| .rdata | 0x400 | 2,036,628 |
| .pdata | 0x1F1800 | 614,200 |
| .text | 0x290000 | 20,948,316 |
| .data | 0x1690000 | 14,434,172 |
| .tls | 0x2454000 | 9 |
| .XBMOVIE | 0x2454200 | 12 |
| .idata | 0x2460000 | 1,828 |
| .XBLD | 0x2470000 | 336 |
| .reloc | 0x2470200 | 1,940,164 |

PDATA contains 76,775 entries. That count does not establish the number of correctly translated functions. The PE declares SizeOfImage 41,224,704, larger than the loaded snapshot; the full relocation section has not been examined. No export table was found in the inspected XEX security field or PE export directory. TLS declares 64 slots and eight bytes of data; the default stack is 524,288 bytes.

## Imported services

The import records reference `xboxkrnl.exe` and `xam.xex`. Type-1 thunks identify 412 functions: 175 kernel and 237 XAM imports. Values patched by the loader are not reinterpreted as original ordinals.

| Area | Imported examples | Validation |
|---|---|---|
| Memory | NtAllocateVirtualMemory, MmAllocatePhysicalMemoryEx, ExAllocatePool | SDK runtime used during native boot |
| Threads and timers | ExCreateThread, NtSetTimerEx, NtCreateTimer, KeDelayExecutionThread | Startup runs; full gameplay behavior unverified |
| Graphics | Vd family and statically linked D3D9/XGRAPHC | Xenos/D3D12 renders the title |
| Audio | XAudioRegisterRenderDriverClient, XAudioSubmitRenderDriverFrame | Audio runtime initializes; complete playback unverified |
| Input | XamInputGetState, XamInputSetState, XamInputGetCapabilities | SDL backend; keyboard and controller support |
| Profile and content | XamContentCreateEx, XamContentFlush, XamUserReadProfileSettings, XamUserWriteProfileSettings | Virtual identity works; inventory format still under investigation |
| Network | XampXAuthStartup, XamGetToken, NetDll_XHttpSendRequest, NetDll_XNetStartup | Local replacements under development |

The initial SDK macro audit found 270 implemented declarations, 137 stubs and five unmatched imports. An implemented declaration can still contain incomplete behavior. Dynamically resolved exports, including XamGetServiceEndpoint, require separate analysis.

## Resources and offline behavior

The resource audit decompresses 362 ZRES files using zlib and their little-endian declared sizes. It parses 102 JSON exports and finds 1,516 item definitions, excluding version markers. Definitions contain IDs, classes, rarity, slots, levels, attributes and buff references. They are not instantiated inventory objects.

`ItemSpinner.json` contains category, lottery, multiple-draw, point and cost references. The complete Happy Cards reward distribution has not been recovered. No replacement probabilities are presented as original.

The resources contain Warrior, Mage, Cleric, bot, co-op and campaign data. `media/stage/stageFileList.nut` lists 12 resource names, including two test names. The executable contains OFFLINE_NORMAL, OFFLINE_HANDICAP_MATCH, OFFLINE_REPEL, OFFLINE_SUBJUGATION, OFFLINE_RELIEF and OFFLINE_TREASURE_HUNT. Presence does not prove that each mode can run offline.

Progression exports include OfflineExp, OfflineBoxRankUpRate and OfflineBoxRankUpLimit. The port should reuse the original logic where available.

## Investigation points

| Address | Evidence |
|---|---|
| 0x8269A5C8, 0x8269A648, 0x8269A6C8, 0x8269A740 | References to savedata/%s.txt; possibly development utilities |
| 0x829245D8 | Reference to unlock_; role unresolved |
| 0x8292AEA0 | Reference to RewardBuffLotteryTable |
| 0x82932C78 | Reference to OfflineBoxRankUpLimit |
| 0x82BC2AD8, 0x82BC2B50 | equipItem/deleteItem interface calls |
| 0x832C0900 | Dynamic service-endpoint lookup |
| 0x82AF54C8 | Token and URL initialization |
| 0x82AF56D0 | HTTP request state machine |

The short string-reference scan is not full data-flow analysis. Indirect calls and base-relative string construction require manual tracing. See [save-service analysis](SAVE_SERVICE_ANALYSIS.md) for the current startup boundary.
