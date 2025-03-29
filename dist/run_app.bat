@echo off
echo Starting Interest Calendar Ledger...
cd %~dp0
InterestCalendarLedger.exe
if %ERRORLEVEL% neq 0 pause
