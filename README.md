# ClaudeTools

A pair of tools that show your Claude.ai usage stats in a floating desktop widget — no browser automation, no API keys required.

## How it works

```
claude.ai/settings/usage
        │
        │  (browser extension intercepts API responses + DOM)
        ▼
  claude-extension  ──POST──►  claude-widget (localhost:7899)
                                      │
                                      ▼
                              floating desktop widget
```

1. The **browser extension** runs inside your real logged-in browser, intercepts usage data from `claude.ai/settings/usage`, and POSTs it to localhost.
2. The **desktop widget** listens on `localhost:7899`, displays the data in a small always-on-top window, and caches the last result so it survives restarts.

---

## claude-widget

A lightweight Python/Tkinter desktop widget. Always-on-top, draggable, minimises to system tray.

### Requirements

- Python 3.9+
- Windows (uses `pystray` for tray icon; other OSes work but without tray support)

### Setup

```bat
cd claude-widget
setup.bat          # installs dependencies + registers auto-start on Windows login
```

Or manually:

```bash
pip install pystray Pillow
python claude_widget.py          # start visible
python claude_widget.py --hidden # start hidden in tray
```

`setup.bat` registers `launch.vbs` in the Windows Startup folder so the widget starts silently on every login.

---

## claude-extension

A Manifest V3 browser extension for Chrome / Edge.

### Install (unpacked)

1. Open `chrome://extensions` (or `edge://extensions`)
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `claude-extension/` folder
4. Navigate to `https://claude.ai/settings/usage` — data will be sent to the widget automatically

### Regenerating icons

If you want to rebuild the PNG icons from scratch:

```bash
cd claude-extension
python make_icons.py
```

---

## Usage

1. Start the widget (`launch.vbs` or `python claude_widget.py`)
2. Open `https://claude.ai/settings/usage` in your browser
3. The widget updates automatically and caches the last result

The widget color-codes values:
- **Green** — messages remaining / available
- **Yellow** — reset / renewal times
- **White** — other stats

---

## Security & Privacy

- The extension **only runs on `claude.ai/settings/usage`** — it has no access to your conversations or any other pages.
- **No credentials are read or stored.** It reads usage numbers (message count, reset time, plan name) from the page you're already viewing.
- All data stays **local to your machine** — it is POSTed to `localhost:7899` only, never to any external server.
- The widget caches the last result in `~/.claude_widget/last_usage.json` on your local disk.
- The full source code is in this repo — load it as an unpacked extension so your browser shows you exactly what runs.
