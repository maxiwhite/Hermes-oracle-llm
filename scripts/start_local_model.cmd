@echo off
call "%~dp0..\start-hermes.cmd" --doctor
exit /b %ERRORLEVEL%
