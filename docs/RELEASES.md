# Releases

Release titles use the version tag, such as `v0.1.0-alpha.1`. Notes use direct English descriptions with installation or update instructions, a changelog, validation and known issues.

Publish a release after a verified major milestone: entering gameplay, a measured performance improvement, completing a match, persistent equipment, working Happy Cards, or newly validated maps and modes. Small fixes remain commits until they form a demonstrated milestone.

Keep releases marked as prereleases until the game meets its gameplay requirements. A source release must say that it contains no playable binary. Do not describe unit-test success as working gameplay.

## Release contents

Each release identifies its source revision, reproducible build steps, checks performed and remaining limitations. Distributable build artifacts need hashes and a clear account of what changed from the previous milestone.

The public source excludes game executables, original assets, loaded images, translated game code, saves and local logs. The supplied README cover is included. Owners provide their own game package.

## Commit messages

Use short English imperative titles describing the change, for example `Fix service endpoint lookup` or `Add offline storage transport tests`. Include technical context in the body when it helps review. Do not add tool attribution or unrelated project history.
