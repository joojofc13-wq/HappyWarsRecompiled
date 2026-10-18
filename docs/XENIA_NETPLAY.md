# Local profile and Xenia references

The port exposes a virtual LIVE identity entirely in process. It does not connect to Netplay or import a real Xbox account.

## References

- [Xenia's Happy Wars report](https://github.com/xenia-project/game-compatibility/issues/1239) reaches the title and encounters a LIVE requirement. It is historical compatibility evidence for another execution.
- [Xenia XAM user implementation](https://github.com/xenia-project/xenia/blob/master/src/xenia/kernel/xam/xam_user.cc) provides the baseline profile and privilege behavior.
- [Netplay XAM user implementation](https://github.com/Nexia360/xenia-canary/blob/netplay_canary_experimental/src/xenia/kernel/xam/xam_user.cc) checks profile state and LIVE eligibility when answering privilege requests.
- [Netplay session API](https://github.com/Nexia360/xenia-canary/blob/netplay_canary_experimental/src/xenia/kernel/XLiveAPI.cpp) uses external registration and session requests. It does not supply Happy Wars' offline save service.
- [Netplay network implementation](https://github.com/Nexia360/xenia-canary/blob/netplay_canary_experimental/src/xenia/kernel/xam/xam_net.cc) documents the XAuth boundary used for comparison.

## Implementation

The profile API returns sign-in state 2, distinct synthetic online and offline XUIDs, the LIVE flag, LocalPlayer and consistent privileges. Membership-tier lookup returns 6 for the synthetic identities. Other users and invalid outputs follow explicit failure paths.

Runtime logs show the original title gate reaching zero restrictions, and the subsequent screen reports a network-save error rather than the previous profile warning.

XAuth startup validates an eight-byte structure. Shutdown writes completion. GetTitleBuffer returns an explicit null because the port has no remote title-authentication blob. This avoids interpreting a stale argument as a pointer.

The local token policy accepts only the in-process origin and initializes the token output to null. The original request pump permits a null token. No remote authorization header is generated. This policy passes its ABI tests but still requires startup validation in the game.
