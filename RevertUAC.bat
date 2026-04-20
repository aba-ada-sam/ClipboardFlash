@echo off
:: Self-elevate to admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================
echo  Revert UAC to Original Setting
echo ============================================
echo.

set RESTORE_FILE=%~dp0uac_restore_value.txt

if not exist "%RESTORE_FILE%" (
    echo ERROR: No saved UAC value found.
    echo Run FixWhatsAppClipboard.bat first.
    pause
    exit /b 1
)

:: Read saved values
set /p SAVED_VAL=<"%RESTORE_FILE%"
for /f "skip=1" %%a in (%RESTORE_FILE%) do set SAVED_DESK=%%a

echo Restoring UAC to original value: %SAVED_VAL%
echo.

reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d %SAVED_VAL% /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v PromptOnSecureDesktop /t REG_DWORD /d %SAVED_DESK% /f >nul

echo UAC restored successfully.
echo.
echo The WhatsApp fix should remain in effect.
echo You do NOT need to reboot after reverting.
echo.
pause
