# Collecting playtest crashes

Open `LaunchHappyWars.cmd` for each run. The launcher creates a separate runtime
log and session record under `logs/playtests/`. After the game exits, it updates
`logs/playtest-summary.json`, grouping missing functions by address while keeping
each original log. Each session records the executable hash and process exit code.

Try different maps, difficulty settings and menu actions. A crash stops that run;
reopen the launcher to test another path. Repeating the same crash remains useful
for reproduction, but it does not identify another missing function. A function
that blocks all paths must be fixed before testing beyond it.

For a named session, run `py scripts/playtest.py --label "Skirmish difficulty"`.
To refresh the report without opening the game, run
`py scripts/playtest.py --summarize`. Logs stay on the local PC and are excluded
from publication. HTTP request logging omits query strings.

The report identifies observed missing functions. Other failures remain in each
session's critical log lines and exit status; a run without a missing-function
message is not automatically classified as successful gameplay.

For standalone installations, use `Playtest.exe` beside `HappyWars.exe` when
provided, or run `py scripts/playtest.py --root PATH_TO_GAME_FOLDER`. Each launch
records its own log, executable hash, process exit code and failure summary.
The launcher waits for you to finish playing and does not stop tests on a timer.

Direct standalone launches now write unique `logs/playtests/run-*.log` files.
Guest-fault traces use the same session prefix. The summary includes these runs
without claiming an exit code when no launcher supervised the process.
