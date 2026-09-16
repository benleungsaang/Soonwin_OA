$ErrorActionPreference = 'Stop'
$startupDir = [Environment]::GetFolderPath('Startup')
$entryPath = Join-Path $startupDir 'SoonwinOA-Startup.vbs'
if (Test-Path -LiteralPath $entryPath) {
    Remove-Item -LiteralPath $entryPath -Force
    Write-Output "Removed user Startup entry: $entryPath"
} else {
    Write-Output "Startup entry not found: $entryPath"
}
