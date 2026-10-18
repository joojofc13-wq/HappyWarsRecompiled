# Offline services and progression

The target is local play with the original combat, bots, maps and progression. No external backend is required by the design. Only content present in the user's copy can be supported.

## Local identity

The XAM replacements expose one synthetic LIVE profile with coherent sign-in state, XUIDs, name, membership tier and privileges. They use no real account or credentials. The original account gate has been passed in an interactive run.

## Storage service

The port dispatches selected XHTTP requests in process. The local endpoint does not bind a TCP port or perform DNS. Title-storage routes use SQLite to preserve opaque binary payloads from the game.

The route and HTTP ABI tests verify binary reads and writes, slot isolation, restart, replacement, deletion, invalid routes and backup replacement. The original game has not yet created and restored a valid player through this service. Metadata field selection has been traced, but complete parser compatibility remains unverified.

See [save-service analysis](SAVE_SERVICE_ANALYSIS.md) for endpoint, token, URL, header and callback contracts.

## SQLite backend

`OfflineStore` uses schema version 1. It creates a local profile identifier on first open and stores records as a key, codec version and binary payload.

Snapshots use BEGIN IMMEDIATE/COMMIT, WAL and synchronous=FULL. Revisions reject conflicting writes. Errors roll back the transaction. Backup and restore use sqlite3_backup; opening checks integrity and rejects unsupported future schema versions.

The backend tests include process restart and abrupt exit before commit. This establishes database behavior, not correct serialization of the original inventory.

## Gameplay requirements

The remaining work includes first-run player creation, restoration of original objects, match setup, bot teams, objectives, rewards and progression. Equipment must retain IDs, attributes, buffs, upgrades and selections across process restarts.

Happy Cards need local results based on recovered behavior or clearly documented replacement rules. The available lottery exports do not establish a complete original probability distribution.

The acceptance path is: create a profile, reach the menu, start Skirmish, complete a match, receive rewards, equip and upgrade an item, close the process, reopen it and recover the same item with its attributes. Repeat without a network connection and validate supported maps and modes individually.
