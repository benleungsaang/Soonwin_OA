@echo off
setlocal

cd /d "%~dp0.."

echo [1/2] Stopping Soonwin OA production tray and backend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root = [IO.Path]::GetFullPath('%~dp0..'); $tray = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like ('*' + ($root + '\windows-tools\oa_tray.py') + '*') }; foreach ($process in $tray) { taskkill.exe /PID $process.ProcessId /T /F | Out-Host }"

echo [2/2] Stopping Soonwin OA production Nginx...
if exist "%~dp0..\nginx-1.28.1\nginx.exe" (
    "%~dp0..\nginx-1.28.1\nginx.exe" -s stop -c "%~dp0..\nginx-1.28.1\conf\nginx.conf"
) else (
    echo Nginx executable not found, skipped.
)

echo.
echo Checking production ports...
powershell -NoProfile -Command "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @(5000,5183) } | Select-Object LocalAddress,LocalPort,OwningProcess"
echo.
pause
exit /b 0
