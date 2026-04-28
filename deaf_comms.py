"""
Deaf Players Quick Communication Overlay
Sağır Oyuncular İçin Hızlı İletişim

Requirements:
    pip install websockets

Tuşlar / Keys:
  V          → EMERGENCY menü  (çift tap ≤500ms = ENEMY HERE! direkt)
  Z          → URGENT menü     (çift tap ≤500ms = GO NOW! direkt)
  Z          → TACTICS menü    (çift tap ≤500ms = 3,2,1 countdown)
  ` (0xC0)   → URGENT menü     (çift tap ≤500ms = GO NOW!)
  F1         → AAA             (direkt)
  F2         → BBB             (direkt)
  F3         → CCC             (direkt)
  F4         → Slow play       (direkt)
  F5         → Look at Discord!(direkt)
  1-6        → Navigasyon (sadece menü açıkken)
"""

import tkinter as tk
import threading
import json
import time
import os
import asyncio
import ctypes
import ctypes.wintypes
from collections import OrderedDict

# ─────────────────────────────────────────────────────────────
# WINDOWS API
# ─────────────────────────────────────────────────────────────
_user32      = ctypes.windll.user32
WM_HOTKEY    = 0x0312
MOD_NOREPEAT = 0x4000

WM_APP_REG_NAV   = 0x8001
WM_APP_UNREG_NAV = 0x8002

# Virtual key codes
VK_V   = 0x56
VK_Z   = 0x5A
VK_F   = 0x46
VK_C0  = 0xC0   # backtick / grave `
VK_F1  = 0x70
VK_F2  = 0x71
VK_F3  = 0x72
VK_F4  = 0x73
VK_F5  = 0x74
VK_NAV = [0x31, 0x32, 0x33, 0x34, 0x35, 0x36]  # 1-6

# Hotkey IDs
HK_V        = 1
HK_Z        = 2
HK_F        = 3
HK_C0       = 4
HK_F1       = 5
HK_F2       = 6
HK_F3       = 7
HK_F4       = 8
HK_F5       = 9
HK_NAV_BASE = 20   # 20-25 → keys 1-6

# ─────────────────────────────────────────────────────────────
# TIMING / COLORS
# ─────────────────────────────────────────────────────────────
DOUBLE_TAP_MS   = 500
MENU_TIMEOUT_MS = 4000
DISPLAY_TIME_MS = 1500
COUNTDOWN_DELAY = 0.8

BG_DARK      = "#0f1923"
BG_PANEL     = "#1a2634"
BG_ITEM      = "#243447"
ACCENT       = "#ff4655"
ACCENT2      = "#00e5a0"
TEXT_WHITE   = "#ece8e1"
TEXT_DIM     = "#768a96"
BORDER_COLOR = "#2d4a5e"
FONT_FAMILY  = "Segoe UI"

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "deafcomms_config.json")

# ─────────────────────────────────────────────────────────────
# MESSAGES
# ─────────────────────────────────────────────────────────────

def make_root_menus():
    return {

        # ── V — EMERGENCY ────────────────────────────────────
        "V": {
            "double_tap": {"en": "ENEMY HERE!", "tr": "BURADA!!", "show_self": False},
            "title_en": "🔴 EMERGENCY",
            "title_tr": "🔴 ACİL",
            "items": OrderedDict([
                ("1", {"en": "ALL HERE!",      "tr": "TÜM BURADA!!!",       "show_self": False}),
                ("2", {"en": "BEHIND/FLANK!",  "tr": "ARKANDA/ARKALIYOR!!", "show_self": False}),
                ("3", {"en": "LEFT!",           "tr": "SOL!",                "show_self": False}),
                ("4", {"en": "RIGHT!",          "tr": "SAĞ!",                "show_self": False}),
                ("5", {"en": "ROTATE!",         "tr": "DÖN DÖN DÖN",        "show_self": False}),
                ("6", {"en": "Rotating",        "tr": "Dönüyorlar",          "show_self": False}),
            ])
        },

        # ── 0xC0 — URGENT (menu) ─────────────────────────────
        "C0": {
            "double_tap": {"en": "GO NOW!", "tr": "Giriyoruz Şimdi!", "show_self": False},
            "title_en": "⚡ URGENT",
            "title_tr": "⚡ ACİL",
            "items": OrderedDict([
                ("1", {"en": "Flashing",      "tr": "Kör atıyorum Şimdi", "show_self": False}),
                ("2", {"en": "Swing with me", "tr": "Benimle oyna",       "show_self": False}),
                ("3", {"en": "Wait",          "tr": "Bekle",              "show_self": False}),
                ("4", {"en": "No peek",       "tr": "Peeklemeyin",        "show_self": False}),
                ("5", {"en": "Yes",           "tr": "Evet",               "show_self": False}),
                ("6", {"en": "No",            "tr": "Hayır",              "show_self": False}),
            ])
        },

        # ── F1-F5 — direct ───────────────────────────────────
        "F1": {"direct": {"en": "AAAAAAAAAAAAAAA", "tr": "AAAAAAAAAAAAAAA", "show_self": False}},
        "F2": {"direct": {"en": "BBBBBBBBBBBBBBB", "tr": "BBBBBBBBBBBBBBB", "show_self": False}},
        "F3": {"direct": {"en": "CCCCCCCCCCCCCCC", "tr": "CCCCCCCCCCCCCCC", "show_self": False}},
        "F4": {"direct": {"en": "SLOW PLAY",       "tr": "Yavaş oynayalım", "show_self": False}},
        "F5": {"direct": {"en": "Look at Discord!","tr": "Discord'a bak",  "show_self": True}},

        # ── Z — TACTICS / STRATEGY ───────────────────────────
        "Z": {
            "double_tap": {
                "en": "Swing Together 3,2,1 NOW!",
                "tr": "Beraber gireceğiz 3,2,1 ŞİMDİ!",
                "show_self": True,
                "countdown": True,
            },
            "title_en": "🧠 TACTICS / STRATEGY",
            "title_tr": "🧠 TAKTİK / STRATEJİ",
            "items": OrderedDict([
                ("1", {
                    "label_en": "📢 Info", "label_tr": "📢 Bilgi",
                    "submenu": OrderedDict([
                        ("1", {"en": "Back",   "tr": "Arka/Dip", "show_self": False}),
                        ("2", {"en": "CT",     "tr": "CT",       "show_self": False}),
                        ("3", {"en": "Site",   "tr": "Side",     "show_self": False}),
                        ("4", {"en": "Heaven", "tr": "Heaven",   "show_self": False}),
                        ("5", {"en": "Mid!!",  "tr": "Mid!!",    "show_self": False}),
                        ("6", {"en": "Hell",   "tr": "Hell",     "show_self": False}),
                    ])
                }),
                ("2", {
                    "label_en": "ℹ Info 2", "label_tr": "ℹ Bilgi 2",
                    "submenu": OrderedDict([
                        ("1", {"en": "Short",          "tr": "Kısa",           "show_self": False}),
                        ("2", {"en": "Main",           "tr": "Ana",            "show_self": False}),
                        ("3", {"en": "Long",           "tr": "Uzun",           "show_self": False}),
                        ("4", {"en": "Link/Connector", "tr": "Link/Connector", "show_self": False}),
                        ("5", {"en": "Smoke in",       "tr": "Smoke içinde",   "show_self": False}),
                        ("6", {"en": "Cubby",          "tr": "Köşe",           "show_self": False}),
                    ])
                }),
                ("3", {
                    "label_en": "💨 Smoke/Spike", "label_tr": "💨 Smoke/Spike",
                    "submenu": OrderedDict([
                        ("1", {
                            "label_en": "Smoke  ▶", "label_tr": "Smoke  ▶",
                            "submenu": OrderedDict([
                                ("1", {"en": "Smoke A",      "tr": "A Smoke at",     "show_self": False}),
                                ("2", {"en": "Smoke B",      "tr": "B Smoke at",     "show_self": False}),
                                ("3", {"en": "Smoke C/Mid",  "tr": "C/Mid Smoke at", "show_self": False}),
                                ("4", {"en": "Smoke CT",     "tr": "CT Smoke at",    "show_self": False}),
                                ("5", {"en": "Smoke Heaven", "tr": "Heaven Smoke",   "show_self": False}),
                            ])
                        }),
                        ("2", {"en": "Smoke my sign",   "tr": "İşaretlediğime smoke at", "show_self": False}),
                        ("3", {"en": "Smoke here",      "tr": "Buraya smoke at",          "show_self": False}),
                        ("4", {"en": "Open plant",      "tr": "Açık Kur",                 "show_self": False}),
                        ("5", {"en": "Safe plant",      "tr": "Güvenli Kur",              "show_self": False}),
                        ("6", {"en": "Defusing/Defuse", "tr": "Çözüyor/Çöz",             "show_self": False}),
                    ])
                }),
                ("4", {
                    "label_en": "⚡ Abilities", "label_tr": "⚡ Yetenekler",
                    "submenu": OrderedDict([
                        ("1", {"en": "I have flash",      "tr": "Kör bende var",                "show_self": False}),
                        ("2", {"en": "I'll use ulti",    "tr": "Ulti kullanacağım",            "show_self": False}),
                        ("3", {"en": "Trap tripped",      "tr": "Tuzak geldi!!",                "show_self": False}),
                        ("4", {"en": "Play off my flash", "tr": "Beraber girecez kör atacağım", "show_self": True}),
                        ("5", {"en": "Use ulti",          "tr": "Ulti kullan!!",                "show_self": False}),
                        ("6", {"en": "Heal me",           "tr": "Can lazım",                    "show_self": True}),
                    ])
                }),
                ("5", {
                    "label_en": "🤝 Teamwork", "label_tr": "🤝 Takım Oyunu",
                    "submenu": OrderedDict([
                        ("1", {"en": "Come here",  "tr": "Buraya gel",            "show_self": False}),
                        ("2", {"en": "One stay",   "tr": "Orada bir kişi kalsın", "show_self": False}),
                        ("3", {"en": "Cover me",   "tr": "Beni koru",             "show_self": True}),
                        ("4", {"en": "Trade me",   "tr": "Beni takasla",          "show_self": False}),
                        ("5", {"en": "Need help",  "tr": "Yardım lazım",          "show_self": True}),
                        ("6", {"en": "Fast Push",  "tr": "Hızlı girelim",         "show_self": False}),
                    ])
                }),
                ("6", {
                    "label_en": "🧠 Strategy", "label_tr": "🧠 Strateji",
                    "submenu": OrderedDict([
                        ("1", {
                            "label_en": "Fake Y, Go X  ▶", "label_tr": "Fake Y, Git X  ▶",
                            "submenu": OrderedDict([
                                ("1", {"en": "Fake A, Go B!", "tr": "Önce Fake A sonra B gidelim", "show_self": False}),
                                ("2", {"en": "Fake B, Go A!", "tr": "Önce Fake B sonra A gidelim", "show_self": False}),
                                ("3", {"en": "Fake A, Go C!", "tr": "Önce Fake A sonra C gidelim", "show_self": False}),
                                ("4", {"en": "Fake C, Go A!", "tr": "Önce Fake C sonra A gidelim", "show_self": False}),
                            ])
                        }),
                        ("2", {
                            "label_en": "Mid to X  ▶", "label_tr": "Mid'den X'e  ▶",
                            "submenu": OrderedDict([
                                ("1", {"en": "Mid to A!", "tr": "Mid to A!", "show_self": False}),
                                ("2", {"en": "Mid to B!", "tr": "Mid to B!", "show_self": False}),
                                ("3", {"en": "Mid to C!", "tr": "Mid to C!", "show_self": False}),
                            ])
                        }),
                        ("3", {"en": "Flank/Flanking", "tr": "Lurkla/Lurklayım",   "show_self": False}),
                        ("4", {"en": "Lurk/Lurking",   "tr": "Arkala/Arkalıyorum", "show_self": False}),
                        ("5", {
                            "label_en": "Going...  ▶", "label_tr": "Gidiyorum...  ▶",
                            "submenu": OrderedDict([
                                ("1", {"en": "Going A!",   "tr": "A'ya gidiyorum/gidiyoruz",  "show_self": False}),
                                ("2", {"en": "Going B!",   "tr": "B'ye gidiyorum/gidiyoruz",  "show_self": False}),
                                ("3", {"en": "Going C!",   "tr": "C'ye gidiyorum/gidiyoruz",  "show_self": False}),
                                ("4", {"en": "Going Mid!", "tr": "Mid'e gidiyorum/gidiyoruz", "show_self": False}),
                            ])
                        }),
                        ("6", {"en": "Play default", "tr": "Dağınık oynayalım", "show_self": False}),
                    ])
                }),
            ])
        },
    }


SPECIAL = {
    "en": {"countdown_3": "⏱ 3...", "countdown_2": "⏱ 2...",
           "countdown_1": "⏱ 1...", "countdown_go": "🔥 GO GO GO!"},
    "tr": {"countdown_3": "⏱ 3...", "countdown_2": "⏱ 2...",
           "countdown_1": "⏱ 1...", "countdown_go": "🔥 BAŞLA!"},
}

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────────────────────
# WEBSOCKET CLIENT
# ─────────────────────────────────────────────────────────────

class WebSocketClient:
    def __init__(self, app, server_url, room_id, player_name):
        self.app         = app
        self.server_url  = server_url
        self.room_id     = room_id
        self.player_name = player_name
        self.ws          = None
        self.running     = True
        self.loop        = None
        self.connected   = False

    def start(self):
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        try:
            import websockets
        except ImportError:
            self.app.root.after(0, lambda: self.app.update_status("❌ pip install websockets", ACCENT))
            return
        retry = 0
        while self.running:
            try:
                url = self.server_url
                if not url.startswith("ws"):
                    url = "wss://" + url
                self.app.root.after(0, lambda: self.app.update_status("Connecting...", "#ffaa00"))
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    self.ws = ws
                    self.connected = True
                    retry = 0
                    await ws.send(json.dumps({"type": "join", "room": self.room_id, "name": self.player_name}))
                    self.app.root.after(0, lambda: self.app.update_status(
                        f"✅ Connected | Room: {self.room_id}", ACCENT2))
                    async for raw in ws:
                        try:
                            data = json.loads(raw)
                            t = data.get("type")
                            if t == "message":
                                self.app.root.after(0, lambda d=data: self.app.on_network_message(d))
                            elif t == "system":
                                self.app.root.after(0, lambda d=data: self.app.show_system_message(d))
                        except json.JSONDecodeError:
                            continue
            except Exception:
                self.connected = False
                self.ws = None
                retry += 1
                wait = min(retry * 2, 10)
                self.app.root.after(0, lambda w=wait: self.app.update_status(
                    f"⚠ Disconnected — retry in {w}s", "#ff6600"))
                await asyncio.sleep(wait)

    def send(self, payload: dict):
        if not (self.ws and self.connected and self.loop):
            return
        payload.setdefault("sender", self.player_name)
        payload.setdefault("time", time.time())
        asyncio.run_coroutine_threadsafe(self.ws.send(json.dumps(payload)), self.loop)

    def stop(self):
        self.running = False

# ─────────────────────────────────────────────────────────────
# HOTKEY MANAGER
# ─────────────────────────────────────────────────────────────

class HotkeyManager:
    """
    RegisterHotKey(None) only — no SetWindowsHookEx.
    Nav keys 1-6 registered/unregistered via PostThreadMessage
    so they only suppress gameplay keys while the menu is open.
    """

    def __init__(self, app):
        self.app     = app
        self._thread = None
        self._tid    = None
        self._nav_on = False

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()

        always_on = [
            (HK_V,   VK_V),
            (HK_Z,   VK_Z),
            (HK_C0,  VK_C0),
            (HK_F1,  VK_F1),
            (HK_F2,  VK_F2),
            (HK_F3,  VK_F3),
            (HK_F4,  VK_F4),
            (HK_F5,  VK_F5),
        ]
        for hid, vk in always_on:
            _user32.RegisterHotKey(None, hid, MOD_NOREPEAT, vk)

        msg = ctypes.wintypes.MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                hid = msg.wParam
                if   hid == HK_V:   self.app.root.after(0, lambda: self.app.on_root_key("V"))
                elif hid == HK_Z:   self.app.root.after(0, lambda: self.app.on_root_key("Z"))
                elif hid == HK_C0:  self.app.root.after(0, lambda: self.app.on_root_key("C0"))
                elif hid == HK_F1:  self.app.root.after(0, lambda: self.app.on_direct_key("F1"))
                elif hid == HK_F2:  self.app.root.after(0, lambda: self.app.on_direct_key("F2"))
                elif hid == HK_F3:  self.app.root.after(0, lambda: self.app.on_direct_key("F3"))
                elif hid == HK_F4:  self.app.root.after(0, lambda: self.app.on_direct_key("F4"))
                elif hid == HK_F5:  self.app.root.after(0, lambda: self.app.on_direct_key("F5"))
                elif HK_NAV_BASE <= hid <= HK_NAV_BASE + 5:
                    k = str(hid - HK_NAV_BASE + 1)
                    self.app.root.after(0, lambda key=k: self.app.on_nav(key))

            elif msg.message == WM_APP_REG_NAV and not self._nav_on:
                for i, vk in enumerate(VK_NAV):
                    _user32.RegisterHotKey(None, HK_NAV_BASE + i, MOD_NOREPEAT, vk)
                self._nav_on = True

            elif msg.message == WM_APP_UNREG_NAV and self._nav_on:
                for i in range(6):
                    _user32.UnregisterHotKey(None, HK_NAV_BASE + i)
                self._nav_on = False

        for hid, _ in always_on:
            _user32.UnregisterHotKey(None, hid)
        if self._nav_on:
            for i in range(6):
                _user32.UnregisterHotKey(None, HK_NAV_BASE + i)

    def register_nav(self):
        if self._tid:
            _user32.PostThreadMessageW(self._tid, WM_APP_REG_NAV, 0, 0)

    def unregister_nav(self):
        if self._tid:
            _user32.PostThreadMessageW(self._tid, WM_APP_UNREG_NAV, 0, 0)

    def stop(self):
        if self._tid:
            _user32.PostThreadMessageW(self._tid, 0x0012, 0, 0)

# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────

class DeafCommsApp:
    def __init__(self):
        self.lang        = "en"
        self.player_name = "Player"
        self.room_id     = "takim1"
        self.server_url  = "wss://deafcomms-server.onrender.com"
        self.network     = None
        self.hotkeys     = None
        self.root_menus  = make_root_menus()

        # Menu state
        self.menu_open        = False
        self.active_root_key  = None
        self.menu_stack       = []
        self.key_path_parts   = []
        self.current_level    = None
        self.current_title    = ""
        self._menu_timeout_id = None

        # Double-tap tracking
        self._last_key_ms = {}

        # Popup slots
        self._slots          = []
        self._queue          = []
        self._countdown_slot = None

        self.root = tk.Tk()
        self.root.title("Deaf Players Quick Communication Overlay")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.config = load_config()
        self._show_setup_screen()

    # ────────────────────────────────────────────────────────
    # SETUP SCREEN
    # ────────────────────────────────────────────────────────

    def _show_setup_screen(self):
        self.root.deiconify()
        self.root.attributes("-alpha", 0.95)
        ww, wh = 500, 460
        self.root.geometry(f"{ww}x{wh}+{(self.screen_w-ww)//2}+{(self.screen_h-wh)//2}")

        frame = tk.Frame(self.root, bg=BG_DARK,
                         highlightbackground=ACCENT, highlightthickness=2)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Deaf Players Quick Communication Overlay",
                 font=(FONT_FAMILY, 15, "bold"), fg=ACCENT, bg=BG_DARK,
                 wraplength=450).pack(pady=(22, 2))
        tk.Label(frame,
                 text="Sağır ve işitme engelli oyuncular için erişilebilir iletişim aracı",
                 font=(FONT_FAMILY, 9), fg=TEXT_DIM, bg=BG_DARK,
                 wraplength=450).pack(pady=(0, 14))

        form = tk.Frame(frame, bg=BG_DARK)
        form.pack(padx=40, fill="x")

        # Language
        tk.Label(form, text="Language / Dil:", font=(FONT_FAMILY, 11, "bold"),
                 fg=TEXT_WHITE, bg=BG_DARK, anchor="w").pack(fill="x", pady=(0, 4))
        lang_row = tk.Frame(form, bg=BG_PANEL,
                            highlightbackground=BORDER_COLOR, highlightthickness=1)
        lang_row.pack(fill="x", pady=(0, 14), ipady=6)
        self._lang_var = tk.StringVar(value=self.config.get("lang", "en"))

        rb_en = tk.Radiobutton(lang_row, text="  🇬🇧  English",
            variable=self._lang_var, value="en",
            font=(FONT_FAMILY, 12, "bold"), fg=TEXT_WHITE, bg=BG_PANEL,
            selectcolor=BG_DARK, activebackground=BG_PANEL,
            indicatoron=0, relief="flat", padx=12, pady=4, cursor="hand2")
        rb_en.pack(side="left", expand=True, fill="x")

        rb_tr = tk.Radiobutton(lang_row, text="  🇹🇷  Türkçe",
            variable=self._lang_var, value="tr",
            font=(FONT_FAMILY, 12, "bold"), fg=TEXT_WHITE, bg=BG_PANEL,
            selectcolor=BG_DARK, activebackground=BG_PANEL,
            indicatoron=0, relief="flat", padx=12, pady=4, cursor="hand2")
        rb_tr.pack(side="left", expand=True, fill="x")

        def _tint(*_):
            v = self._lang_var.get()
            rb_en.config(bg=BG_DARK if v == "en" else BG_PANEL,
                         fg=ACCENT  if v == "en" else TEXT_WHITE)
            rb_tr.config(bg=BG_DARK if v == "tr" else BG_PANEL,
                         fg=ACCENT  if v == "tr" else TEXT_WHITE)
        self._lang_var.trace_add("write", _tint)
        _tint()

        # Player name
        tk.Label(form, text="Player Name / Oyuncu Adın:",
                 font=(FONT_FAMILY, 11, "bold"), fg=TEXT_WHITE, bg=BG_DARK,
                 anchor="w").pack(fill="x", pady=(0, 3))
        self.name_entry = tk.Entry(form, font=(FONT_FAMILY, 13), bg=BG_PANEL,
            fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief="flat",
            highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.name_entry.pack(fill="x", ipady=6, pady=(0, 12))
        self.name_entry.insert(0, self.config.get("name", ""))

        # Room code
        tk.Label(form, text="Room Code / Oda Kodu:",
                 font=(FONT_FAMILY, 11, "bold"), fg=TEXT_WHITE, bg=BG_DARK,
                 anchor="w").pack(fill="x", pady=(0, 3))
        self.room_entry = tk.Entry(form, font=(FONT_FAMILY, 13), bg=BG_PANEL,
            fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief="flat",
            highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.room_entry.pack(fill="x", ipady=6, pady=(0, 12))
        self.room_entry.insert(0, self.config.get("room", "takim1"))

        # Server
        tk.Label(form, text="Server / Sunucu:",
                 font=(FONT_FAMILY, 11, "bold"), fg=TEXT_WHITE, bg=BG_DARK,
                 anchor="w").pack(fill="x", pady=(0, 3))
        self.server_entry = tk.Entry(form, font=(FONT_FAMILY, 13), bg=BG_PANEL,
            fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief="flat",
            highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.server_entry.pack(fill="x", ipady=6, pady=(0, 18))
        self.server_entry.insert(0, self.config.get("server", "ws://34.141.78.151:10000"))

        btn = tk.Frame(form, bg=ACCENT, cursor="hand2")
        btn.pack(fill="x", ipady=11)
        lbl = tk.Label(btn, text="▶   START / BAŞLAT",
                       font=(FONT_FAMILY, 14, "bold"), fg=TEXT_WHITE,
                       bg=ACCENT, cursor="hand2")
        lbl.pack(expand=True)
        btn.bind("<Button-1>", lambda e: self._start_app())
        lbl.bind("<Button-1>", lambda e: self._start_app())
        self.root.bind("<Return>", lambda e: self._start_app())

    # ────────────────────────────────────────────────────────
    # START
    # ────────────────────────────────────────────────────────

    def _start_app(self):
        self.player_name = self.name_entry.get().strip()   or "Player"
        self.room_id     = self.room_entry.get().strip()   or "takim1"
        self.server_url  = self.server_entry.get().strip() or "wss://deafcomms-server.onrender.com"
        self.lang        = self._lang_var.get()

        save_config({"name": self.player_name, "room": self.room_id,
                     "server": self.server_url, "lang": self.lang})

        for w in self.root.winfo_children():
            w.destroy()
        self.root.withdraw()

        self._setup_overlay()
        self.network = WebSocketClient(self, self.server_url, self.room_id, self.player_name)
        self.network.start()
        self.hotkeys = HotkeyManager(self)
        self.hotkeys.start()

    # ────────────────────────────────────────────────────────
    # OVERLAY SETUP
    # ────────────────────────────────────────────────────────

    def _click_through(self, win):
        try:
            win.update_idletasks()
            hwnd   = _user32.GetParent(win.winfo_id())
            GWL    = -20
            styles = _user32.GetWindowLongW(hwnd, GWL)
            styles |= 0x00080000 | 0x00000020 | 0x00000080
            _user32.SetWindowLongW(hwnd, GWL, styles)
        except Exception as e:
            print(f"[WARN] click-through: {e}")

    def _setup_overlay(self):
        self.root.attributes("-alpha", 0.93)
        self.root.attributes("-toolwindow", True)
        self.main_frame = tk.Frame(self.root, bg=BG_DARK,
                                   highlightbackground=ACCENT, highlightthickness=2)
        self.main_frame.pack(fill="both", expand=True)
        self.root.after(100, lambda: self._click_through(self.root))

        # Status bar — bottom right
        self.status_win = tk.Toplevel(self.root)
        self.status_win.attributes("-topmost", True)
        self.status_win.attributes("-alpha", 0.80)
        self.status_win.overrideredirect(True)
        sw, sh = 400, 30
        self.status_win.geometry(
            f"{sw}x{sh}+{self.screen_w - sw - 10}+{self.screen_h - sh - 50}")
        sf = tk.Frame(self.status_win, bg=BG_DARK,
                      highlightbackground=BORDER_COLOR, highlightthickness=1)
        sf.pack(fill="both", expand=True)
        self.status_label = tk.Label(
            sf, text=f"🎮 {self.player_name} | Connecting...",
            font=(FONT_FAMILY, 9), fg="#ffaa00", bg=BG_DARK)
        self.status_label.pack(expand=True)
        self.root.after(200, lambda: self._click_through(self.status_win))

        # 2 popup slots
        self._slots = []
        for i in range(2):
            win = tk.Toplevel(self.root)
            win.attributes("-topmost", True)
            win.attributes("-alpha", 0.95)
            win.overrideredirect(True)
            mw, mh = 800, 76
            win.geometry(f"{mw}x{mh}+{(self.screen_w-mw)//2}+{8 + i*(mh+4)}")
            mf = tk.Frame(win, bg=BG_DARK,
                          highlightbackground=ACCENT, highlightthickness=2)
            mf.pack(fill="both", expand=True)
            lbl = tk.Label(mf, text="", font=(FONT_FAMILY, 22, "bold"),
                           fg=TEXT_WHITE, bg=BG_DARK, wraplength=760)
            lbl.pack(expand=True)
            win.withdraw()
            self.root.after(200 + i*10, lambda w=win: self._click_through(w))
            self._slots.append({"win": win, "label": lbl, "active": False, "timer": None})

    # ────────────────────────────────────────────────────────
    # STATUS
    # ────────────────────────────────────────────────────────

    def update_status(self, text, color=TEXT_DIM):
        try:
            self.status_label.config(
                text=f"🎮 {self.player_name} | {text}", fg=color)
        except Exception:
            pass

    # ────────────────────────────────────────────────────────
    # HOTKEY ENTRY POINTS
    # ────────────────────────────────────────────────────────

    def on_root_key(self, root_key: str):
        """V / Z / F — single tap opens menu, double tap sends quick message."""
        now_ms = int(time.time() * 1000)
        last   = self._last_key_ms.get(root_key, 0)

        if (now_ms - last) <= DOUBLE_TAP_MS:
            self._last_key_ms[root_key] = 0
            self._close_menu()
            self._do_double_tap(root_key)
        else:
            self._last_key_ms[root_key] = now_ms
            if self.active_root_key == root_key:
                self._close_menu()
            else:
                self._close_menu()
                if self.root_menus.get(root_key, {}).get("items"):
                    self._open_menu(root_key)

    def on_direct_key(self, root_key: str):
        """C0 / F1-F5 — send immediately, no menu."""
        item = self.root_menus.get(root_key, {}).get("direct")
        if not item:
            return
        self._send_texts(item.get("en", ""), item.get("tr", ""),
                         item.get("show_self", False), key_path=root_key)

    def on_nav(self, key: str):
        if not self.menu_open or not self.current_level:
            return
        if key not in self.current_level:
            return
        self._set_timeout(MENU_TIMEOUT_MS)  # extend to 4s once navigating
        item = self.current_level[key]

        if "submenu" in item:
            self.menu_stack.append((self.current_level, self.current_title))
            self.key_path_parts.append(key)
            self.current_level = item["submenu"]
            lbl = item.get(f"label_{self.lang}") or item.get("label_en", "…")
            self.current_title = lbl.replace("  ▶", "").strip()
            self._render_menu()
        elif "en" in item:
            sub_path = ".".join(self.key_path_parts + [key])
            self._close_menu()
            self._send_texts(
                item.get("en", ""), item.get("tr", ""),
                item.get("show_self", False),
                key_path=f"{self.active_root_key}.{sub_path}")

    # ────────────────────────────────────────────────────────
    # MENU OPEN / RENDER / CLOSE
    # ────────────────────────────────────────────────────────

    def _open_menu(self, root_key: str):
        self.active_root_key = root_key
        self.menu_open       = True
        self.menu_stack      = []
        self.key_path_parts  = []
        root = self.root_menus[root_key]
        self.current_level   = root["items"]
        self.current_title   = root.get(f"title_{self.lang}") or root.get("title_en", "MENU")
        self.hotkeys.register_nav()
        self._render_menu()
        # Menu stays open 4s for navigation
        self._set_timeout(MENU_TIMEOUT_MS)

    def _close_menu(self):
        if self._menu_timeout_id:
            self.root.after_cancel(self._menu_timeout_id)
            self._menu_timeout_id = None
        self.menu_open       = False
        self.active_root_key = None
        self.menu_stack      = []
        self.key_path_parts  = []
        self.current_level   = None
        if self.hotkeys:
            self.hotkeys.unregister_nav()
        self.root.withdraw()

    def _set_timeout(self, ms: int):
        if self._menu_timeout_id:
            self.root.after_cancel(self._menu_timeout_id)
        self._menu_timeout_id = self.root.after(ms, self._close_menu)

    def _render_menu(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

        depth = len(self.menu_stack)
        bar   = ACCENT if depth == 0 else (ACCENT2 if depth == 1 else "#ffaa00")

        badges = {"V": "[V]", "Z": "[Z]", "C0": "[`]"}
        badge  = badges.get(self.active_root_key, "")

        tk.Frame(self.main_frame, bg=bar, height=3).pack(fill="x")

        crumbs = " › ".join(t for _, t in self.menu_stack)
        title  = f"{badge} {crumbs} › {self.current_title}" if crumbs else f"{badge} {self.current_title}"
        tk.Label(self.main_frame, text=title,
                 font=(FONT_FAMILY, 13, "bold"), fg=bar, bg=BG_DARK).pack(pady=(8, 4))

        dt = self.root_menus[self.active_root_key].get("double_tap", {})
        dt_text = dt.get(self.lang) or dt.get("en", "")
        if dt_text and depth == 0:
            tk.Label(self.main_frame,
                     text=f"⚡ {badge}+{badge} → {dt_text}",
                     font=(FONT_FAMILY, 9), fg="#ffaa00", bg=BG_DARK).pack(pady=(0, 3))

        for key, item in self.current_level.items():
            has_sub   = "submenu" in item
            show_self = item.get("show_self", False)

            row = tk.Frame(self.main_frame, bg=BG_ITEM, padx=12, pady=5)
            row.pack(fill="x", padx=14, pady=2)

            tk.Label(row, text=f"[{key}]",
                     font=(FONT_FAMILY, 12, "bold"), fg=bar, bg=BG_ITEM).pack(side="left")

            if has_sub:
                label = (item.get(f"label_{self.lang}") or item.get("label_en", "?")).replace("  ▶", "").strip()
                icon, fg = "  ▶ ", TEXT_WHITE
            else:
                label = item.get(self.lang) or item.get("en", "?")
                icon  = "  📍 " if show_self else "  → "
                fg    = ACCENT2 if show_self else TEXT_WHITE

            tk.Label(row, text=f"{icon}{label}",
                     font=(FONT_FAMILY, 12), fg=fg, bg=BG_ITEM).pack(side="left")

        hint = ("📍=sende görünür  ▶=alt menü  (4s timeout)"
                if self.lang == "tr" else
                "📍=shown to you  ▶=sub-menu  (4s timeout)")
        tk.Label(self.main_frame, text=hint,
                 font=(FONT_FAMILY, 9), fg=TEXT_DIM, bg=BG_DARK).pack(pady=(4, 6))

        dt_row = 1 if (dt_text and depth == 0) else 0
        win_h  = 18 + 34 + dt_row * 22 + len(self.current_level) * 38 + 32
        self.root.geometry(f"490x{win_h}+{(self.screen_w-490)//2}+20")
        self.root.deiconify()

    # ────────────────────────────────────────────────────────
    # DOUBLE TAP ACTION
    # ────────────────────────────────────────────────────────

    def _do_double_tap(self, root_key: str):
        item = self.root_menus.get(root_key, {}).get("double_tap")
        if not item:
            return
        en_text   = item.get("en", "")
        tr_text   = item.get("tr", "")
        show_self = item.get("show_self", False)

        if item.get("countdown"):
            # Guard: don't re-trigger while countdown is already running
            if self._countdown_slot is not None:
                return
            payload = self._make_payload(en_text, tr_text, countdown=True)
            self.network.send(payload)
            if show_self:
                text = tr_text if self.lang == "tr" else en_text
                slot = self._claim_slot()
                self._countdown_slot = slot
                if slot:
                    self._update_slot(slot, f"📤 {text}", ACCENT2)
                else:
                    self._push_popup(f"📤 {text}", ACCENT2)
            threading.Thread(target=self._countdown_broadcast,
                             args=(show_self,), daemon=True).start()
        else:
            self._send_texts(en_text, tr_text, show_self, key_path=f"{root_key}.__dt__")

    # ────────────────────────────────────────────────────────
    # SEND HELPERS
    # ────────────────────────────────────────────────────────

    def _make_payload(self, en_text, tr_text, countdown=False, special=None) -> dict:
        meta = {}
        if countdown: meta["countdown"] = True
        if special:   meta["special"]   = special
        dc = {"en": en_text, "tr": tr_text, **meta}
        payload = {"type": "message", "text": "__dc__" + json.dumps(dc, ensure_ascii=False)}
        if special: payload["special"] = special
        return payload

    def _send_texts(self, en_text, tr_text, show_self, key_path=""):
        payload = self._make_payload(en_text, tr_text)
        if key_path:
            payload["key_path"] = key_path
        self.network.send(payload)
        text = tr_text if self.lang == "tr" else en_text
        if show_self:
            self._push_popup(f"📤 {text}", ACCENT2)
        else:
            short = text[:32] + "…" if len(text) > 32 else text
            self.update_status(f"✅ {short}", ACCENT2)
            lbl = (f"✅ Bağlı | Oda: {self.room_id}" if self.lang == "tr"
                   else f"✅ Connected | Room: {self.room_id}")
            self.root.after(2200, lambda: self.update_status(lbl, ACCENT2))

    # ────────────────────────────────────────────────────────
    # COUNTDOWN BROADCAST
    # ────────────────────────────────────────────────────────

    def _countdown_broadcast(self, show_self: bool):
        slot = self._countdown_slot if show_self else None
        for step in ("countdown_3", "countdown_2", "countdown_1"):
            time.sleep(COUNTDOWN_DELAY)
            en = SPECIAL["en"][step]; tr = SPECIAL["tr"][step]
            self.network.send(self._make_payload(en, tr, special=step))
            if show_self:
                txt = tr if self.lang == "tr" else en
                if slot and slot["active"]:
                    self.root.after(0, lambda t=txt, s=slot: self._update_slot(s, t, "#ffaa00"))
                else:
                    self.root.after(0, lambda t=txt: self._push_popup(t, "#ffaa00"))
        time.sleep(COUNTDOWN_DELAY)
        en = SPECIAL["en"]["countdown_go"]; tr = SPECIAL["tr"]["countdown_go"]
        self.network.send(self._make_payload(en, tr, special="countdown_go"))
        if show_self:
            txt = tr if self.lang == "tr" else en
            if slot and slot["active"]:
                self.root.after(0, lambda s=slot, t=txt: self._update_slot(
                    s, t, ACCENT, hold_ms=DISPLAY_TIME_MS))
            else:
                self.root.after(0, lambda t=txt: self._push_popup(t, ACCENT))
        self._countdown_slot = None

    # ────────────────────────────────────────────────────────
    # INCOMING MESSAGES
    # ────────────────────────────────────────────────────────

    def on_network_message(self, data: dict):
        sender = data.get("sender", "?")
        # Skip own messages — already shown locally when sent
        if sender == self.player_name:
            return
        raw  = data.get("text", "")
        both = {}

        if raw.startswith("__dc__"):
            try:
                both = json.loads(raw[6:])
            except Exception:
                pass
            text = both.get(self.lang) or both.get("en", "")
        else:
            text = raw

        if not text:
            return

        display = f"💬 {sender}: {text}"
        special = both.get("special") or data.get("special", "")
        COUNTDOWN_STEPS = {"countdown_3", "countdown_2", "countdown_1"}

        if both.get("countdown"):
            if self._countdown_slot and self._countdown_slot["active"]:
                # Duplicate message — update existing slot, don't open a new one
                self._update_slot(self._countdown_slot, display, TEXT_WHITE)
            else:
                slot = self._claim_slot()
                self._countdown_slot = slot
                if slot:
                    self._update_slot(slot, display, TEXT_WHITE)
                else:
                    self._push_popup(display, TEXT_WHITE)
        elif special in COUNTDOWN_STEPS:
            slot = self._countdown_slot
            if slot and slot["active"]:
                self._update_slot(slot, display, "#ffaa00")
            else:
                self._push_popup(display, "#ffaa00")
        elif special == "countdown_go":
            slot = self._countdown_slot
            if slot and slot["active"]:
                self._update_slot(slot, display, ACCENT, hold_ms=DISPLAY_TIME_MS)
            else:
                self._push_popup(display, ACCENT)
            self._countdown_slot = None
        else:
            self._push_popup(display, TEXT_WHITE)

    def show_system_message(self, data: dict):
        self._push_popup(data.get("text", ""), "#ffaa00")

    # ────────────────────────────────────────────────────────
    # POPUP SLOTS
    # ────────────────────────────────────────────────────────

    def _claim_slot(self):
        for slot in self._slots:
            if not slot["active"]:
                slot["active"] = True
                return slot
        return None

    def _update_slot(self, slot, text, color, hold_ms=None):
        slot["label"].config(text=text, fg=color)
        slot["win"].deiconify()
        if slot["timer"]:
            slot["win"].after_cancel(slot["timer"])
            slot["timer"] = None
        if hold_ms is not None:
            slot["timer"] = slot["win"].after(hold_ms, lambda: self._clear_slot(slot))

    def _push_popup(self, text, color):
        for slot in self._slots:
            if not slot["active"]:
                self._show_in_slot(slot, text, color)
                return
        self._queue.append((text, color))

    def _show_in_slot(self, slot, text, color):
        slot["active"] = True
        slot["label"].config(text=text, fg=color)
        slot["win"].deiconify()
        if slot["timer"]:
            slot["win"].after_cancel(slot["timer"])
        slot["timer"] = slot["win"].after(DISPLAY_TIME_MS, lambda: self._clear_slot(slot))

    def _clear_slot(self, slot):
        slot["active"] = False
        slot["label"].config(text="")
        slot["timer"] = None
        slot["win"].withdraw()
        if self._queue:
            text, color = self._queue.pop(0)
            self._show_in_slot(slot, text, color)

    # ────────────────────────────────────────────────────────
    # RUN
    # ────────────────────────────────────────────────────────

    def run(self):
        print("=" * 56)
        print("  Deaf Players Quick Communication Overlay")
        print("  pip install websockets")
        print("=" * 56)
        try:
            self.root.mainloop()
        finally:
            if self.network: self.network.stop()
            if self.hotkeys: self.hotkeys.stop()


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    DeafCommsApp().run()
