:: Batch render Maya scenes from the queue

set "MAYAPY=C:\Program Files\Autodesk\Maya2023\bin\mayapy"
set "SCRIPT=%~dp0rec\renderArgs.py"
set "CMD=%~dp0__render_args.cmd"

:loop
"%MAYAPY%" "%SCRIPT%"
if errorlevel 1 goto :eof

"%CMD%"
goto :loop
