# Offline progression and Premium

The owned TU46 data includes offline progression parameters. Its original
`PlayerLevelUpParam.json` has offline experience values and separate normal and
Premium reward-box rank-up rates and limits. The `GameWin` entry includes offline
experience and box progress. Item lottery and reward-set tables are also present.

This establishes that the game has data for offline rewards. It does not establish
that the port completes every match-result and inventory-grant path. A reliable
completed Skirmish match, resulting item award and restart with that item preserved
still need validation. The current GPU crash prevents claiming full progression.
If the original award path remains blocked, a local fallback should use the owned
reward tables and existing serializer; its rules should be agreed first.

## Permanent local Premium

TU46 builds enable local Premium membership by default, including a fresh normal
profile. The original predicate
at `0x82F5C320` compares the current FILETIME against the expiration returned by
`0x82BAC790`, which reads the profile timestamp at offset `0x14438`.

The local policy supplies an expiration horizon renewed on every read and an
active result for the four supported user indices. It applies on every launch,
including after a save reset, so membership never counts down to expiration.
It preserves the save payload and issues no remote purchase or subscription.
Complete Premium reward and UI effects still need gameplay validation.

Native tests check valid and invalid users, timestamp range, null and out-of-range
objects, and register preservation. Premium consumable tickets remain optional
inventory items; their activation is not required by the local policy.
