param(
    [switch]$WhatIfOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$startupDir = [Environment]::GetFolderPath('Startup')
$entryPath = Join-Path $startupDir 'SoonwinOA-Startup.vbs'
$launcher = Join-Path $repoRoot 'windows-tools\oa_startup.py'
$launcherEscaped = $launcher.Replace('"', '""')
$content = @"
Set shell = CreateObject("WScript.Shell")
shell.Run "py -3 ""$launcherEscaped""", 0, False
"@

if ($WhatIfOnly) {
    Write-Output "Would create: $entryPath"
    Write-Output $content
    exit 0
}

[IO.File]::WriteAllText($entryPath, $content, [Text.Encoding]::Unicode)
Write-Output "Created user Startup entry: $entryPath"
