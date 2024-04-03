@echo off

SETLOCAL
set /A MAYA_VER=2023
set "mayapy=C:\Program Files\Autodesk\Maya%MAYA_VER%\bin\mayapy"
ENDLOCAL

"%mayapy%" "%~dp0\rec\export_cachesCamera_queue.py" "%*"
