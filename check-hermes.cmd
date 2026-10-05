@echo off
call "%~dp0start-hermes.cmd" --doctor
exit /b %ERRORLEVEL%
