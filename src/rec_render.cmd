:: Batch render Maya scenes from the queue

@echo off
set "MAYAPY=C:\Program Files\Autodesk\Maya2023\bin\mayapy"
set "SCRIPT=%~dp0rec\renderNoArnold.py"

@echo on
"%MAYAPY%" "%SCRIPT%"
