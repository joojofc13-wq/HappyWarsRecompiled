# Title updates

Updates must match the source executable's Title ID, Media ID, version and
signature hash. Update numbers alone do not establish compatibility.

## Import local packages

```powershell
py scripts/import_title_update.py "PATH_TO_UPDATE_ZIPS"
```

The input may be a ZIP, an extracted STFS package or a directory. The importer
checks each candidate against `private/game/Default.xex`, removes duplicates and
selects the highest compatible target version. It verifies extracted files
against their container and stores them under `private/title-updates/`.
The report is written to `logs/title-update-import.json`.

Importing stages files only. Updated PowerPC instructions require new code
generation, reviewed hook addresses and a native rebuild. The normal launcher
continues using the base build until an updated build has been tested.

## Inspected packages

| Package | Required source | Target | Media ID |
|---|---|---|---|
| TU3 | 0.0.0.2 | 0.0.3.2 | 061F2D01 |
| TU7 | 0.0.0.2 | 0.0.7.2 | 061F2D01 |
| TU23 | 0.0.8.5 | 0.0.23.5 | 4005211B |
| TU36 | 0.0.24.7 | 0.0.36.7 | 5CEC066D |
| TU46 | 0.0.24.7 | 0.0.46.7 | 5CEC066D |

TU3 and TU7 both patch the original 0.0.0.2 executable. TU7 can be applied
directly; TU3 is not a prerequisite. These packages do not provide a path from
0.0.7.2 to the source required by TU23, TU36 or TU46.

TU7 has passed local extraction checks and the SDK's executable-delta loader.
Its patched header reports version 0.0.7.2 and entry point 0x831F2748. Updated
gameplay validation is still pending.

Updates, extracted assets, generated game code and font files remain private.
The importer uses local inputs; an automatic download source is not configured.

## TU46 development port

A complete owned TU46 installation has reached Game Home and Skirmish in the
native port. Its project-owned configuration is preserved under
[`ports/tu46`](../ports/tu46/README.md). This does not establish that TU46 can
patch a TU7 executable or that the public setup has been validated end to end.
