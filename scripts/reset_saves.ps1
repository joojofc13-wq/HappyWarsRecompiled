param([switch]$Yes)
$ErrorActionPreference = 'Stop'
$scriptFolder = Split-Path -Parent $MyInvocation.MyCommand.Path
if ((Split-Path -Leaf $scriptFolder) -eq 'scripts') {
    $portRoot = Split-Path -Parent $scriptFolder
} elseif ((Split-Path -Leaf $scriptFolder) -eq 'game' -and (Split-Path -Leaf (Split-Path -Parent $scriptFolder)) -eq 'build') {
    $portRoot = Split-Path -Parent (Split-Path -Parent $scriptFolder)
} else { throw 'Run this helper from scripts or build/game.' }
$portRoot = [IO.Path]::GetFullPath($portRoot)
if (-not (Test-Path -LiteralPath (Join-Path $portRoot 'happywars_manifest.toml'))) { throw 'Project marker missing.' }
$running = Get-CimInstance Win32_Process -Filter "Name='HappyWars.exe'" | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($portRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}
if ($running) { throw 'Close this game before resetting saves.' }
if (-not $Yes) {
    Write-Host 'Permanently delete saves, database backups for this port?'
    Write-Host 'Game files, shader caches, settings and unrelated games are preserved.'
    if ((Read-Host 'Type RESET to continue') -cne 'RESET') { exit 0 }
}
$files = @()
foreach ($relative in @('private/smoke-user')) {
    $directory = [IO.Path]::GetFullPath((Join-Path $portRoot $relative))
    if (-not $directory.StartsWith($portRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe profile path.' }
    if (Test-Path -LiteralPath $directory) {
        if ((Get-Item -LiteralPath $directory).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked profile directory rejected.' }
        $children = Get-ChildItem -LiteralPath $directory -Recurse -Force
        if ($children | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Linked save path rejected.' }
        $files += $children | Where-Object { -not $_.PSIsContainer -and $_.Name -like '*.sqlite*' }
    }
}
foreach ($file in $files) {
    if (-not $file.FullName.StartsWith($portRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe save path.' }
    Remove-Item -LiteralPath $file.FullName -Force
}
Write-Host ('Removed {0} save files. The next launch creates a new profile.' -f $files.Count)
