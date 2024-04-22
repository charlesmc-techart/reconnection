@echo off
:: Batch render Maya scenes from the queue

set "MAYAPY=C:\Program Files\Autodesk\Maya2023\bin\mayapy"
set "SCRIPT=%~dp0\rec\renderArgs.py"
set "CMD=%~dp0\__render_args.cmd"

:loop
"%MAYAPY%" "%SCRIPT%" "%CMD%"
if errorlevel 1 goto :eof

call "%CMD%"
goto :loop
