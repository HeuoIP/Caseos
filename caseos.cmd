@echo off
rem CaseOS CLI wrapper -- Windows.
rem Sets PYTHONPATH so python -m caseos.cli.caseos resolves.
setlocal
set "PYTHONPATH=%~dp0backend;%PYTHONPATH%"
python -m caseos.cli.caseos %*
exit /b %ERRORLEVEL%