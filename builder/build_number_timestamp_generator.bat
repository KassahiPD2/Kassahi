@echo off
setlocal ENABLEDELAYEDEXPANSION

rem === CONFIGURATION ===
set "TEMPLATE_FILE=01-version.source.filter"
set "OUTPUT_FILE=01-version.filter"
set "BUILDNUM_FILE=buildnum.txt"

rem === GET CURRENT BUILD NUMBER (PERSISTENT) ===
if not exist "%BUILDNUM_FILE%" (
    echo 0>"%BUILDNUM_FILE%"
)

set /p CURRENT_BUILDNUM=<"%BUILDNUM_FILE%"
if "%CURRENT_BUILDNUM%"=="" set CURRENT_BUILDNUM=0

set /a NEW_BUILDNUM=CURRENT_BUILDNUM+1

rem Save the new build number for next run
> "%BUILDNUM_FILE%" echo %NEW_BUILDNUM%

rem === GET FORMATTED TIMESTAMP LIKE Nov/25th/25 ===
for /f "usebackq delims=" %%T in (`
    powershell -NoLogo -NoProfile -Command ^
      "$now = Get-Date; " ^
      "$day = $now.Day; " ^
      "if ($day -ge 11 -and $day -le 13) { $suffix = 'th' } " ^
      "else { " ^
      "  switch ($day %% 10) { " ^
      "    1 { $suffix = 'st'; break } " ^
      "    2 { $suffix = 'nd'; break } " ^
      "    3 { $suffix = 'rd'; break } " ^
      "    default { $suffix = 'th' } " ^
      "  } " ^
      "} " ^
      "$month = $now.ToString('MMM'); " ^
      "$year = $now.ToString('yy'); " ^
      "Write-Output ('{0}/{1}{2}/{3}' -f $month, $day, $suffix, $year)"
`) do (
    set "TIMESTAMP=%%T"
)

rem === DO REPLACEMENT AND WRITE OUTPUT ===
if not exist "%TEMPLATE_FILE%" (
    echo Template file "%TEMPLATE_FILE%" not found.
    exit /b 1
)

(
    for /f "usebackq delims=" %%L in ("%TEMPLATE_FILE%") do (
        set "LINE=%%L"
        set "LINE=!LINE:--timestamp--=%TIMESTAMP%!"
        set "LINE=!LINE:--buildnum--=%NEW_BUILDNUM%!"
        echo(!LINE!
    )
) > "%OUTPUT_FILE%"

echo Done.
echo Timestamp: %TIMESTAMP%
echo Build #:   %NEW_BUILDNUM%

endlocal
