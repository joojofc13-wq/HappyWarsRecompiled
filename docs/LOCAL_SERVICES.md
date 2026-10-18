# Local Xbox services

The port uses ReXGlue for the console runtime and adds title-specific services
inside the game process. The local HTTP dispatcher starts during `OnPostSetup`
and stores title data under the configured user-data directory. It does not
need a separate server, open a listening port or contact Xbox Live.

The intended scope is the Xbox functionality needed by Happy Wars, including
the services needed to reach and play its modes. Full Xbox 360 system software
and the public Xbox Live network are not implemented.

| Area | Current behavior | Remaining work |
| --- | --- | --- |
| Identity | One local profile, stable XUID and sign-in information | Profile selection and additional users |
| Network identity | Loopback address, local online status | Sessions and peer communication |
| Title storage | SQLite-backed payloads, slots, dated backups, quota and transactions | Validate all gameplay save paths and recovery |
| Service discovery | Synchronous `services` endpoint resolves locally | Other service names and asynchronous lookup |
| HTTP | In-process handles, requests, responses and queued callbacks | Catalog protocols and remaining title requests |
| Statistics | Requested views with empty rows, real enumerator handles and closure | Persistent local scores and writes |
| Marketplace | Warning still occurs | Identify its failing request and supply a valid local catalog |
| Achievements | No additional title-specific service established | Audit SDK behavior, persist unlocks and validate notifications |
| Matchmaking | No local matchmaking service validated | Session creation, search, joins and teardown |
| Voice | Observed microphone-array SDK stub | Voice capture, routing and lifecycle |

An API returning success does not establish that a service works. Validation
must include initialized outputs, owned handles, completion callbacks, error
paths and persistence where applicable. Runtime warnings record unsupported
service boundaries so they can be implemented from the actual caller contract.

TU46 reaches Game Home and plays Skirmish. Several missing original-function boundaries have been repaired.
The latest blocker is a GPU page fault; full match completion is unverified.
See [TU46 startup](TU46_STARTUP.md).
