# Project status

**The game is not playable yet.** The native build renders the intro and 3D title screen. The virtual profile passes the account check. The last observed startup stops at the network-save warning.

The current source corrects the service lookup, local URL and token boundaries, HTTP work result, header queries and storage response codes. Eleven native tests pass. The latest interactive run logs real storage GET and PUT requests through the local service, then a guest access violation reading address 0x00000004. No successful menu transition or full player-state restoration has been verified.

| Component | Evidence and remaining work |
|---|---|
| Original package | LIVE package, Title ID 58410AE9; original preserved |
| Extraction | 402 files, 34 directories; file sizes, SHA-256 and 113,431 referenced SHA-1 blocks checked |
| Package authenticity | RSA signature and upper STFS hash-tree verification are not implemented |
| Resources | 362 ZRES files decoded; 102 JSON files and 1,516 item definitions examined |
| Static recompilation | 326 generated C++ files; no PowerPC JIT; generation runs without `--force` |
| Function registration | 237,086 address/function pairs checked; no missing PDATA starts in the inspected table |
| Translation audits | No missing labels or explicit translation traps within the audit scope |
| Windows build | Native x64 executable using Clang with the MSVC ABI and the pinned ReXGlue runtime |
| Graphics, audio and input | Runtime initializes D3D12, audio and SDL; intro and 3D title observed |
| Performance | Translated code uses `-O1`; FPS improvement has not been measured |
| Profile | Synthetic LIVE identity, XUIDs, name, tier and privileges; account gate passed |
| Local services | In-process XHTTP and SQLite route tests pass; startup GET/PUT requests observed; later guest access violation remains |
| Saves | Transactions, revisions, backup and restart tested; original player data creation and restoration remain unverified |
| Mode menu and Skirmish | No successful entry observed |
| Maps and modes | Original resources and identifiers found; unlocks and mode flows remain pending |
| Happy Cards and equipment | Original definitions examined; rewards, upgrades and in-game persistence remain pending |

## Validation

The current CTest suite has 11 passing tests. It covers storage, selected translated routines, profile consistency, XAuth, endpoint lookup and the local HTTP guest ABI. The HTTP test writes binary bytes, reopens the database, reads in chunks, replaces a blob and deletes it.

These tests do not cover complete HTTP callback behavior, the game's JSON parsers, first-run player initialization, the mode menu or gameplay. The earlier five Python tool tests also passed.

## Next milestones

1. Verify real startup requests against the original save parsers.
2. Reach the mode menu with a valid local player.
3. Start and complete Skirmish with the original bots and objectives.
4. Verify rewards, equipment changes and restoration after restarting.
5. Validate each available map and mode, then measure performance.
6. Provide a builder for owners to extract and compile their own copies after the menu works.

Releases follow [verified milestones](docs/RELEASES.md).
