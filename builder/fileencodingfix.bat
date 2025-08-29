@echo off
setlocal

REM === Folder containing files to convert ===
set "srcfolder=%cd%"

REM === Process all text files (change *.filter to *.* if needed) ===
for %%F in ("%srcfolder%\..\*.filter") do (
    echo Converting "%%~nxF" to Windows-1252...

    powershell -Command ^
        "$tmp = '%%~fF.tmp'; " ^
        "Get-Content -Raw -Encoding UTF8 '%%~fF' | Set-Content -Encoding Default $tmp; " ^
        "Move-Item -Force $tmp '%%~fF'"
)

for %%F in ("%srcfolder%\*.filter") do (
    echo Converting "%%~nxF" to Windows-1252...

    powershell -Command ^
        "$tmp = '%%~fF.tmp'; " ^
        "Get-Content -Raw -Encoding UTF8 '%%~fF' | Set-Content -Encoding Default $tmp; " ^
        "Move-Item -Force $tmp '%%~fF'"
)

echo.
echo Conversion complete. Files are now Windows-1252 encoded.
pause
