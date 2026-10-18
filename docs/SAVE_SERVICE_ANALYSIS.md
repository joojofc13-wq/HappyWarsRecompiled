# Save-service boundary

The account check passes. The latest interactive run resolves the local endpoint
and sends GET and PUT storage requests through the in-process transport. It later
encounters a guest access violation reading address 0x00000004. Full player-state
restoration and a mode-menu transition remain unverified.

## Corrections applied after analysis

The current source replaces the actual endpoint wrapper, provides a local-only
URL/token policy, returns nonzero from successful HTTP work, supports the observed
header queries and matches the storage helpers' success codes. Metadata now uses
blobs and pagingInfo members. Eleven native tests pass, including HTTP guest-ABI
binary writes, reopen, chunked reads, replacement and deletion.

The contract findings below describe the prototype defects identified before
these corrections. They remain evidence for the changes, not a claim that the
same defects are still present.

## Call sequence found in the original code

1. Query the signed-in user's XUID, LIVE flags, subscription tier and privileges.
2. Initialize XAuth with an eight-byte settings structure.
3. Open an XHTTP session.
4. Resolve the `services` endpoint.
5. Construct the title-storage URL and request.
6. Send it and advance the HTTP state machine through callbacks.
7. Parse status, metadata and payload before creating or restoring player state.

The latest runtime log reaches endpoint resolution and real storage requests.
Successful completion of player initialization has not been observed.

## Endpoint lookup

The game calls `sub_832C0900` with four arguments:

| Register | Meaning | Evidence |
|---|---|---|
| r3 | Service-name string | Callers use the `services` string |
| r4 | Output character buffer | Callers pass stack or object buffers |
| r5 | Buffer capacity | The inspected callers pass 384 |
| r6 | Optional asynchronous argument | The inspected callers pass zero |

The wrapper opens `xam.xex`, resolves ordinal `0x577` through
`XexGetProcedureAddress`, then invokes the resulting function with these four
arguments. That ordinal is `XamGetServiceEndpoint` in the pinned SDK export table.
The caller requires return value zero before formatting the storage URL.

This lookup is dynamic. Adding a normal import override alone would not replace
the SDK's cached dynamic thunk. The local implementation should either replace
this reviewed wrapper or explicitly replace that thunk in the dispatcher.

An earlier adapter for `sub_82E669D8` converted a different XAuth directory layout.
Its unit tests passed, but no call was observed during the storage failure. It
must not be cited as a working endpoint lookup.

## Storage routes

The original strings use this title group:

`/users/xuid(<id>)/storage/titlestorage/titlegroups/be554af1-2afa-4168-b64f-bdcb9ce7ac7b`

The code contains GET, PUT and DELETE routes under
`/data/hw201209/slot<slot>/<name>,binary`, a group-level GET, and a metadata path
without the binary suffix. Parser keys include `fileName`, `size`,
`UsedBytesInVerifiedStorage`, `QuotaBytesForVerifiedStorage`,
`UsedBytesInUnverifiedStorage` and `QuotaBytesForUnverifiedStorage`.

These strings identify the transport boundary. They do not prove the complete
JSON response shape or the binary save layout. The local storage prototype
preserves opaque bytes and returns missing-file errors instead of inventing an
inventory. Its JSON metadata still needs validation against the original parser.

## HTTP callback contract

The callback installed by the game is `sub_82AF4BE8`. Its inspected branches map:

| Status | Effect in the original callback |
|---|---|
| 0x400000 | Advance request state to 3 |
| 0x20000 | Advance request state to 5 |
| 0x80000 | Store r7 as received byte count, advance to 8 |
| 0x100000 | Advance to completion state 11 |
| 0x200000 | Record an error and advance to 11 |
| 0x8000 | Advance to 11 |

The callback arguments are handle, request context, status, status-information
pointer and information length. The original code reads the request context from
r4 and byte count from r7. Windows WinHTTP documentation is a reference for this
shape; Xbox-specific status and closing behavior must be checked in the game.

## Implemented and still unverified

The SQLite route handler passes tests for binary bytes, slot isolation, restart,
replacement, deletion, invalid paths and backup replacement. This proves storage
behavior in the test contract, not compatibility with the game parser.

An in-process XHTTP prototype has typed session, connection and request handles,
queued callbacks and local storage dispatch. It performs no DNS or socket I/O.
The latest run reaches its route handler for storage reads and writes. A later
guest access violation still prevents confirmation of player initialization.

Before claiming save support, verify endpoint-buffer behavior, the exact JSON
shape, missing-save handling, token structure and ownership, URL parsing,
callback ordering and cancellation, numeric/header buffer sizes, and player-state
creation. Then test a real write and read after restarting the game.

The account warning is gone. The earlier network-save warning has now been
followed by actual local requests and a later guest access violation.

## Parser contracts recovered from the original functions

The following results come from following direct calls and resolving virtual
tables in the loaded image. No game flow has been changed to obtain them.

| Operation | Original functions | Observed contract |
|---|---|---|
| Gamercard | `82AF7FC0`, `82AF4130`, `82AF9000` | Parse a JSON document, select `tier`, then look up its string in an enum registry |
| Tier registry | `82AF3A40` | `Unknown=0`, `FamilyGold=1`, `Gold=2`, `Silver=3` |
| Quota fields | `82AF38F0` | Four named fields at result offsets 0, 4, 8 and 12 |
| Blob listing | `82AF66F8`, `82AF86F8`, `82AF87B8` | Select the named members `blobs` and `pagingInfo` from the parsed document |
| Blob entry | `82AF39C0` | Select `fileName` and `size`; size is stored at result offset 128 |
| Paging | `82AF77D0` | Select `continuationToken` and `totalItems`; totalItems is stored at result offset 64 |

The quota keys, in result-offset order, are `UsedBytesInVerifiedStorage`,
`QuotaBytesForVerifiedStorage`, `UsedBytesInUnverifiedStorage` and
`QuotaBytesForUnverifiedStorage`. Each uses the same scalar adapter. Its accepted
numeric types and overflow behavior still need inspection.

The gamercard path supports the proposed `{"tier":"Gold"}` response at the
field-selection and enum-registration levels. This is static evidence only;
the complete response has not passed through the running game.

The metadata prototype currently returns a bare array. The original parser
instead selects `blobs` and `pagingInfo` from its input. The prototype therefore
needs revision before it can be treated as compatible. The precise element
container, filename convention, empty-list behavior and continuation-token
rules still require validation. Merely returning HTTP 200 would hide these
incompatibilities.

`82AF41C8` closes the request and its associated handle. It is cleanup, not the
request pump. Its presence in a caller does not prove a completed request.

## Imported HTTP surface

The generated import wrappers expose 22 XHTTP functions. The local transport
implements 14 of them. The remaining imported functions are `CrackUrl`,
`CrackUrlW`, `CreateUrl`, `CreateUrlW`, `QueryOption`, `QueryAuthSchemes` and
`SetCredentials`. There is also an unimplemented `OpenRequestUsingMemory`
wrapper. These eight functions are included in the total of 22.
Import presence alone does not establish that a startup path executes them.
Their callers must be traced before deciding which implementations are needed.

`XamGetToken` is exposed through `82E66FA8`. Its output structure, ownership and
completion semantics remain unverified. A successful return without initializing
the expected outputs would be unsafe.

Direct-call tracing identifies both `XamGetToken` and ANSI `XHttpCrackUrl` in
`82AF54C8`, the request initializer used by `82AF5998`. The other seven missing
XHTTP wrappers have no direct callers in the generated functions inspected;
indirect uses are not excluded by that search.

The token call supplies user index, URL pointer, URL length, an output-pointer
address at request offset 28, and a zero asynchronous argument. Cleanup
`82AF4B30` loads that pointer, calls `XamFreeToken` when nonzero, then clears it.
The request pump reads a token member at offset 8 as a header string when the
pointer is nonzero. Allocation, layout and matching release must therefore be
handled together. The reference netplay implementation returns failure here;
copying it would not satisfy this game's initializer.

The URL-components buffer has size 60 at request offset 44. The initializer
provides a hostname buffer at request offset 140 with capacity 128, and sets
the path-length member at components offset 48 to `0xffffffff`. The consumer
reads scheme at components offset 12, hostname pointer at 16, port as a 16-bit
value at 24, and path pointer at 44. Scheme value 2 enables request flag
`0x00800000`. The CrackUrl call passes flags `0x90000000`. Pointer and length
semantics must be checked before implementing this boundary.

The actual pump is `82AF56D0`, called by the synchronous loop `82AF6010`.
It treats `XHttpDoWork` returning zero as failure, transitions to state 11 and
reads the last error. The prototype currently returns zero unconditionally;
this is a confirmed incompatibility independent of endpoint resolution.
Successful work must follow the caller's nonzero convention. The loop exits
at state 10 or 11 and sleeps between iterations.

Header queries also differ from the Windows constants assumed by the prototype:

| Original helper | Query passed to XHTTP | Output |
|---|---|---|
| `82AF4D00` | `0x2000fffe` | Four-byte numeric HTTP status |
| `82AF4C90` | `0x20000009` | Four-byte numeric response length |
| `82AF4D70` | `0x0000ffff`, name `ETag` | Caller-provided character buffer |

The prototype recognizes status query 19 and length query 5 instead, and has no
named ETag query. All three actual queries would currently fail. Their output
buffers and lengths must follow the guest's big-endian numeric convention.

Storage helper `82AF3388` accepts HTTP 200, copies the response length to its
output and returns zero. HTTP 404 clears that length and returns internal result
4; other unsuccessful responses return result 2 after the retry policy. This
proves that missing blobs have a distinct result. Whether the higher-level
player loader turns result 4 into first-run profile creation remains unverified.

The write helper `82AF3568` requires exactly HTTP 201. Returning 200 for a
replacement, as the prototype does, would make that helper report failure.
Helper `82AF3730` requires exactly HTTP 200. Response codes must be based on
these callers rather than generic REST conventions.

The XHTTP wrappers insert caller value 1 in r3 and shift their incoming
arguments by one register. For example, `82E67208` passes the send-request
context in r10 after shifting. `XamGetToken` uses its original registers and
converts positive error codes to HRESULTs in `82E66FA8`.

The current callback prototype also needs checks for callback-mask filtering,
close/cancel ordering, handle kinds, request reuse, header buffer conventions
and write-completion information lifetime. These checks should precede another
interactive boot attempt.

## Scope after storage initialization

Passing storage initialization is a prerequisite for the menu. It does not prove
Skirmish initialization, bot execution, match completion, unlocks, Happy Cards,
equipment persistence or all-mode support. Those remain separate requirements.
The intended next validation is a first-run profile created by the original
game code, followed by an opaque save write and a successful read after restart.
The user-facing builder remains scheduled after reaching the mode menu.
