@echo off

SETLOCAL
set /A MAYA_VER=2023
ENDLOCAL

"C:\Program Files\Autodesk\Maya%MAYA_VER%\bin\mayapy" "%~dp0\rec\export_cachesCamera_queue.py" "%*"
