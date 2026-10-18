# Startup statistics result

This document records an earlier base-version investigation. See [current status](../STATUS.md) for TU46 gameplay and remaining issues.

The null-range crash after Start occurred in the original function at
0x82AAA650. Its caller was 0x82AAB20C. The consumer loaded a result structure,
then dereferenced its null views pointer at offset 4.

The original XUserReadStats wrapper is 0x830EFE38. It dispatches XGI message
0x000B0021. The pinned SDK's handler returned success without populating the
result. The game assumes at least one requested view is represented even when
there are no ranked users.

## Local result

The port initializes the result before invoking the original wrapper. Each
requested view gets its original view ID, zero total rows, zero returned rows
and a null row pointer. The outer view array is present and count matches the
request. This describes an empty local leaderboard; it does not invent ranks,
rewards or inventory.

The original wrapper retains request dispatch and overlapped completion. Buffer
sizing follows its reserve formula, including the per-user row and column
space. Short buffers return 122 with the required size. Invalid spec counts and
column counts are rejected.

The fixture test extracts both original consumers, 0x82AAA650 and 0x82AAA518,
plus their original register-save helpers without editing instructions. They
accept the initialized empty views and preserve the checked nonvolatile
registers and return address. The full native suite has 12 passing tests.

## Runtime observations

The corrected build logs the local stats result and advances beyond the previous
null access. It then displays an update-service notice. Confirming that notice
loads tutorial resources.

A later indirect call to 0x8275D0F8 exposed a missing registration. Its original
0x30-byte leaf body checks a 3-by-3 index and stores the supplied value. Its full
boundary is now declared, ending at the original return at 0x8275D124.

The rebuilt executable passes translation and registration checks. The latest
run continues loading tutorial resources beyond that call. A mode-menu
transition still requires confirmation; the update-service notice is not the
menu.

SQLite contains original game-generated save payloads. The player payloads are
base64-encoded zlib streams and decompress successfully to 29,752 bytes in the
observed local profiles. This establishes readable persisted payloads, not
complete equipment or progression compatibility.
