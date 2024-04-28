:: Batch render Maya scenes from the queue

set "MAYAPY=C:\Program Files\Autodesk\Maya2023\bin\mayapy"
set "SCRIPT=%~dp0rec\renderArgs.py"

:loop
"%MAYAPY%" "%SCRIPT%"
if errorlevel 1 goto :eof

"%CMD%"
goto :loop
