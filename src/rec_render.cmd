@echo off
:: Batch render Maya scenes from the queue

set "SCRIPT_DIR=%~dp0"
set "SCRIPT=%SCRIPT_DIR%\rec\construct_renderArgs.py"
set "CMD=%SCRIPT_DIR%\__render.cmd"

set "MAYAPY=C:\Program Files\Autodesk\Maya2023\bin\mayapy"

:loop
"%MAYAPY%" "%SCRIPT%" "%CMD%"
if errorlevel 1 goto :eof

call "%CMD%"
goto :loop
