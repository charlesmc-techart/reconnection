@echo off

set "MAYAPY=C:\Program Files\Autodesk\Maya2023\bin\mayapy"
set "SCRIPT=%~dp0rec\export_cachesCamera_queue.py" "%*"

"%MAYAPY%" "%SCRIPT%"