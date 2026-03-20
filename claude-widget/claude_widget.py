#!/usr/bin/env python3
"""Claude Usage Desktop Widget

Receives usage data POSTed by the Edge/Chrome extension on localhost:7899.
No browser automation, no Cloudflare — the extension runs inside your real
logged-in browser.

Usage:
  python claude_widget.py           # start visible
  python claude_widget.py --hidden  # start hidden in tray
"""

import sys
import tkinter as tk
import threading
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

PORT       = 7899
CACHE_PATH = Path.home() / ".claude_widget" / "last_usage.json"

BG      = "#1e1e2e"
SURFACE = "#313244"
TEXT    = "#cdd6f4"
MUTED   = "#a6adc8"
SUBTLE  = "#585b70"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
YELLOW  = "#f9e2af"
RED     = "#f38ba8"


# ══════════════════════════════════════════════════════════════════════════════
#  HTTP server — receives POST from extension
# ══════════════════════════════════════════════════════════════════════════════

class UsageHandler(BaseHTTPRequestHandler):
    widget: "ClaudeWidget | None" = None

    def do_OPTIONS(self):           # CORS preflight
        self._send_cors(200)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body)
            if self.widget:
                self.widget.root.after(0, self.widget.on_data, data)
            self._send_cors(200)
        except Exception:
            self._send_cors(400)

    def _send_cors(self, code):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *_):
        pass   # silence server logs


def start_server(widget: "ClaudeWidget"):
    UsageHandler.widget = widget
    server = HTTPServer(("localhost", PORT), UsageHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

class ClaudeWidget:
    def __init__(self, start_hidden: bool = False):
        self.root = tk.Tk()
        self._drag_x = self._drag_y = 0
        self._setup_window()
        self._build_ui()
        self._setup_tray()
        start_server(self)
        self._load_cache()
        if start_hidden:
            self.root.after(200, self._hide_window)

    def _setup_window(self):
        r = self.root
        r.title("Claude Usage")
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.93)
        r.wm_attributes("-toolwindow", True)
        r.configure(bg=BG)
        sw = r.winfo_screenwidth()
        r.geometry(f"275x240+{sw - 300}+20")
        r.bind("<Button-1>",  self._drag_start)
        r.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        r = self.root

        hdr = tk.Frame(r, bg=SURFACE, height=34)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Claude Usage", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(side="left", pady=6)

        btns = tk.Frame(hdr, bg=SURFACE)
        btns.pack(side="right", padx=6, pady=4)

        # Minimize → hide to tray
        min_btn = tk.Label(btns, text=" — ", bg=SURFACE, fg=MUTED,
                           font=("Segoe UI", 9), cursor="hand2")
        min_btn.pack(side="left")
        min_btn.bind("<Button-1>", lambda e: self._hide_window())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=TEXT))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=MUTED))

        # Close → quit
        x_btn = tk.Label(btns, text=" ✕ ", bg=SURFACE, fg=RED,
                         font=("Segoe UI", 9), cursor="hand2")
        x_btn.pack(side="left")
        x_btn.bind("<Button-1>", lambda e: self._quit())
        x_btn.bind("<Enter>", lambda e: x_btn.config(bg="#4a1a2a"))
        x_btn.bind("<Leave>", lambda e: x_btn.config(bg=SURFACE))

        self._body = tk.Frame(r, bg=BG)
        self._body.pack(fill="both", expand=True, padx=14, pady=10)

        self._waiting_lbl = tk.Label(
            self._body,
            text="Waiting for extension data…\n\nMake sure the extension is\ninstalled and Edge is open.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9), justify="center"
        )
        self._waiting_lbl.pack(pady=20)

        self._footer = tk.Label(r, text=f"Listening on localhost:{PORT}",
                                bg=BG, fg=SUBTLE, font=("Segoe UI", 7))
        self._footer.pack(side="bottom", pady=3)

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _make_tray_image(self):
        img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Blue-ish rounded background
        draw.rounded_rectangle([2, 2, 62, 62], radius=14, fill="#89b4fa")
        # "C" arc
        draw.arc([12, 10, 52, 54], start=50, end=310, fill="white", width=9)
        return img

    def _setup_tray(self):
        if not HAS_TRAY:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_window, default=True),
            pystray.MenuItem("Quit", self._quit),
        )
        self._tray = pystray.Icon(
            "claude_usage", self._make_tray_image(), "Claude Usage", menu
        )
        threading.Thread(target=self._tray.run, daemon=True).start()

    # ── Show / Hide ───────────────────────────────────────────────────────────

    def _hide_window(self):
        self.root.withdraw()

    def _show_window(self, icon=None, item=None):
        self.root.after(0, self._do_show)

    def _do_show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)

    def _quit(self, icon=None, item=None):
        if HAS_TRAY and hasattr(self, "_tray"):
            self._tray.stop()
        self.root.after(0, self.root.destroy)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()

    def on_data(self, raw: dict):
        """Called on main thread when extension POSTs data."""
        rows = parse_payload(raw)
        if not rows:
            return
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps({"rows": rows,
                                          "at": datetime.now().isoformat()}))
        self._render(rows)

    def _load_cache(self):
        try:
            cached = json.loads(CACHE_PATH.read_text())
            rows   = cached.get("rows", {})
            at     = cached.get("at", "")
            if rows:
                self._render(rows, stale_since=at)
        except Exception:
            pass

    def _render(self, rows: dict, stale_since: str = ""):
        self._clear_body()

        for label, value in rows.items():
            ll = label.lower()
            color = (GREEN  if any(x in ll for x in ("remain", "left", "available")) else
                     YELLOW if any(x in ll for x in ("reset", "renew", "next"))      else
                     TEXT)
            row = tk.Frame(self._body, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=BG, fg=MUTED,
                     font=("Segoe UI", 8), anchor="w").pack(side="left")
            tk.Label(row, text=str(value), bg=BG, fg=color,
                     font=("Segoe UI", 8, "bold"), anchor="e").pack(side="right")

        now = datetime.now().strftime("%H:%M")
        if stale_since:
            try:
                dt  = datetime.fromisoformat(stale_since)
                now = dt.strftime("%H:%M") + " (cached)"
            except Exception:
                pass
        self._footer.config(text=f"Updated {now}  ·  auto via extension")

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  Parse the payload sent by the extension
# ══════════════════════════════════════════════════════════════════════════════

_WANTED = {
    "messages_used":      "Messages Used",
    "messages_limit":     "Message Limit",
    "messages_remaining": "Messages Remaining",
    "message_count":      "Messages Used",
    "usage_count":        "Usage",
    "remaining":          "Remaining",
    "reset_at":           "Resets At",
    "reset_date":         "Reset Date",
    "renews_at":          "Renews At",
    "next_reset":         "Next Reset",
    "plan_name":          "Plan",
    "plan_type":          "Plan",
    "tokens_used":        "Tokens Used",
    "tokens_limit":       "Token Limit",
}


def parse_payload(raw: dict) -> dict:
    result: dict = {}

    api = raw.get("api", {})
    if api:
        flat = {}
        for data in api.values():
            flat.update(flatten(data))

        for raw_key, value in flat.items():
            kl = raw_key.lower().replace(".", "_").replace("-", "_").replace(" ", "_")
            for fragment, label in _WANTED.items():
                if fragment in kl and label not in result:
                    if isinstance(value, str) and re.search(r"\d{4}-\d{2}-\d{2}T", value):
                        try:
                            dt    = datetime.fromisoformat(value.rstrip("Z"))
                            value = dt.strftime("%b %d %H:%M")
                        except Exception:
                            pass
                    result[label] = value
                    break

    dom = raw.get("dom", {})
    for label, value in dom.items():
        if label not in result:
            result[label] = value

    return result


def flatten(obj, prefix="", sep=".") -> dict:
    items: dict = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = f"{prefix}{sep}{k}" if prefix else str(k)
            items.update(flatten(v, nk, sep) if isinstance(v, (dict, list)) else {nk: v})
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:10]):
            items.update(flatten(v, f"{prefix}[{i}]", sep))
    return items


if __name__ == "__main__":
    start_hidden = "--hidden" in sys.argv
    widget = ClaudeWidget(start_hidden=start_hidden)
    widget.run()
