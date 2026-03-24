Set WinScriptHost = CreateObject("WScript.Shell")
' Replace the path below with the actual one where you saved ai.py
WinScriptHost.Run "PATH", 0
Set WinScriptHost = Nothing