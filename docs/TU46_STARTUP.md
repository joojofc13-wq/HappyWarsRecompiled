# TU46 startup investigation

The native TU46 build uses version 0.0.46.7, Media ID 5CEC066D. Interactive
testing now confirms that the connection wait ends and Game Home opens.
The Marketplace warning remains. After repairing the tutorial transition,
interactive testing reached Skirmish and played a match for several minutes.
The session then stopped at an unregistered original function, `0x829286A0`.

## Repaired contracts

The game writes dated backups under
`/data/hw201209/backup/YYYY/MM/DD/savedata/game_data.txt,binary`.
The local storage router previously accepted only numbered slots and returned
HTTP 400 for these writes. It now accepts that backup namespace, preserves the
original payload bytes and keeps backups separate from active slots. The same
quota, transaction and database-backup behavior applies to both namespaces.

`XamUserCreateStatsEnumerator` previously reached the SDK stub, which returned
success without creating a handle. The local implementation creates a real
SDK enumerator. Its first result contains the requested view IDs and zero
ranked rows. The next read returns `ERROR_NO_MORE_FILES`. The original SDK
continues handling `XamEnumerate`, deferred completion and handle closure.

`XNetLogonGetTitleID` also reached a stub and returned zero. It now reads the
current title ID from the runtime's loaded executable metadata.

`XNetGetTitleXnAddr` now supplies a loopback identity and the `ONLINE` status
bit required by the original game's connection state machine. This represents
the in-process service, not a connection to Microsoft's Xbox Live servers.

The tutorial crash identified two adjacent member-access adapters at
`0x83422490` and `0x83422498`. Their original load and tail-branch instructions
are retained and compiled as explicit entries. The boundary scanner also
recognizes this pattern when backed by data-pointer evidence and a known target.

The next Skirmish crash identified argument adapters at `0x829286A0` and
`0x829286B0`. Each retains its original four instructions, including its tail
branch to `0x82980E38`. These entries require another gameplay test.

Changing difficulty later reached an unregistered nested-object virtual-call
adapter at `0x834BD2F8`. The boundary scanner now recognizes its complete
six-instruction pattern and verifies the adjusted object and target register
dependencies. The original function is translated unchanged; this is not a
replacement difficulty implementation. Fresh playtest runs now get separate
logs and a report grouping repeated missing-function addresses.

Mod testing later reached `0x833C13C8`, an argument specialization adjacent to
the registered `0x833C13C0`. It and `0x833C13D0` load different constants into
`r5` and tail-call `0x833C0D48`. The boundary scanner now recognizes such
adjacent families using a registered anchor and matching argument register and
destination. Both original entries are compiled without replacing their logic.

The Marketplace investigation found an original URL rejected by
`XHttpCrackUrl`, called from `0x830AEBD0`. The parser now accepts HTTP and HTTPS
origins, explicit ports and separate query outputs. The transport remains
in-process. This removes a parsing restriction; it does not establish that
catalog responses are implemented or that the Marketplace warning is resolved.

## Validation

The last full native suite passed 16 tests, including local ticket accounting. The new enumerator test initializes a real
tool-mode runtime, creates a handle, reads both views through the SDK's
`XamEnumerate`, checks end-of-enumeration, closes the handle through `NtClose`
and confirms that further reads reject the closed handle. This test covers
synchronous enumeration; asynchronous completion remains delegated to the SDK.

The storage test checks backup writes and reads across a database reopen,
replacement, deletion, slot isolation and malformed backup paths.

The network test checks the status flags, loopback addresses, output bounds and
invalid-pointer return. The connection transition has also been tested in game.
Skirmish entry and short gameplay have been confirmed interactively. Full match
completion, Marketplace handling and sustained gameplay remain unverified.

## Current gameplay blocker

The listed adapter boundaries have been added. Later gameplay failures report
D3D12 device removal and a GPU page fault rather than a new missing function.
Full match completion remains unverified; see [GPU diagnostics](GPU_DIAGNOSTICS.md).
