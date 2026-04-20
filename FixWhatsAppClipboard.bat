@echo off
:: Self-elevate to admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================
echo  WhatsApp Clipboard Fix
echo ============================================
echo.
echo This will change your UAC (User Account Control)
echo setting temporarily to fix WhatsApp clipboard.
echo.
echo Current setting will be saved so you can revert.
echo.

:: Read current value and save it
for /f "tokens=3" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v ConsentPromptBehaviorAdmin 2^>nul') do set CURRENT=%%a
for /f "tokens=3" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v PromptOnSecureDesktop 2^>nul') do set CURRENT_DESK=%%a

echo Current UAC value: %CURRENT%
echo.

:: Save current values to a restore file
echo %CURRENT% > "%~dp0uac_restore_value.txt"
echo %CURRENT_DESK% >> "%~dp0uac_restore_value.txt"

:: Set to "Always notify" (highest level)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 2 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v PromptOnSecureDesktop /t REG_DWORD /d 1 /f >nul

echo UAC set to "Always Notify" (highest).
echo.
echo ============================================
echo  YOU MUST REBOOT FOR THIS TO TAKE EFFECT
echo ============================================
echo.
echo After rebooting, test WhatsApp paste.
echo If it works, run RevertUAC.bat to restore
echo your original UAC setting.
echo.
choice /c YN /m "Reboot now?"
if %errorlevel%==1 shutdown /r /t 5 /c "Rebooting to fix WhatsApp clipboard..."

pause
