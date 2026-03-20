Dim shell
Set shell = CreateObject("WScript.Shell")

' Open Edge minimized — this activates the extension which fetches usage data
shell.Run """C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"" --window-state=minimized ""https://claude.ai/settings/usage""", 1, False

' Wait a moment for Edge to start
WScript.Sleep 2000

' Start the widget silently, hidden in tray
shell.Run """C:\Users\User\AppData\Local\Programs\Python\Python313\pythonw.exe"" ""C:\ClaudeZone\claude-widget\claude_widget.py"" --hidden", 0, False
