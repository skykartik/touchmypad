"""
touchmypad_app.py - the touchmypad app (window, tray, shortcuts).

Keep touchmypad.py (the engine) and ui.html (the look) in the same folder.
Run:  pip install -r requirements.txt   then   python touchmypad_app.py
"""
import ctypes
import json
import os
import sys
import threading
import time
import webbrowser
from ctypes import byref

import pystray
import webview
from PIL import Image, ImageDraw

import touchmypad as eng  # the engine: your original script

REPO = "https://github.com/skykartik/touchmypad"
WM_HOTKEY, WM_CLOSE, WM_APP_HK, WM_APP_PAUSE = 0x0312, 0x0010, 0x8001, 0x8002
ID_SHOW = 4
NOREPEAT = 0x4000
DEFAULTS = {
    "advanced": False, "margin": 0.03, "swap": False, "tray": False, "autostart": False, "start_on": False,
    "hotkeys": {"toggle": {"mod": 2, "vk": 0xC0, "label": "Ctrl + `"},
                "show": {"mod": 0, "vk": 0, "label": "Not set"}},
}
IDS = {"toggle": eng.HOTKEY_TOGGLE, "show": ID_SHOW}
SETTINGS = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "touchmypad", "settings.json")
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

S = {"pad": False, "error": None, "hwnd": None, "visible": True, "quitting": False,
     "window": None, "icon": None, "told": False, "ok": {"toggle": True, "show": True}}


def load():
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(SETTINGS) as fh:
            d = json.load(fh)
        for k in ("advanced", "swap", "tray", "autostart", "start_on"):
            if k in d:
                cfg[k] = bool(d[k])
        if "margin" in d:
            cfg["margin"] = min(max(float(d["margin"]), 0.0), 0.12)
        for n in cfg["hotkeys"]:
            h = d.get("hotkeys", {}).get(n)
            if isinstance(h, dict) and isinstance(h.get("mod"), int) and isinstance(h.get("vk"), int) and isinstance(h.get("label"), str):
                cfg["hotkeys"][n] = {"mod": h["mod"], "vk": h["vk"], "label": h["label"][:30]}
    except Exception:
        pass
    if not cfg["advanced"]:  # extras only count while Advanced settings is on
        cfg.update(margin=0.03, swap=False, tray=False, autostart=False, start_on=False)
        cfg["hotkeys"]["show"] = dict(DEFAULTS["hotkeys"]["show"])
    return cfg


cfg = load()


def save():
    try:
        os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
        with open(SETTINGS, "w") as fh:
            json.dump(cfg, fh)
    except Exception:
        pass


class Sink:
    """Catches the engine's print() output so the app can react to it."""
    def __init__(self, old):
        self.old = old

    def write(self, t):
        if "Touchpad found" in t:
            S["pad"] = True
        if self.old:
            self.old.write(t)

    def flush(self):
        if self.old:
            self.old.flush()


# ------------------------------------------------------------------ hotkeys
def register_all(hwnd):
    for n, hid in IDS.items():
        eng.user32.UnregisterHotKey(hwnd, hid)
        h = cfg["hotkeys"][n]
        S["ok"][n] = True if not h["vk"] else bool(eng.user32.RegisterHotKey(hwnd, hid, h["mod"] | NOREPEAT, h["vk"]))


def unregister_all(hwnd):
    for hid in IDS.values():
        eng.user32.UnregisterHotKey(hwnd, hid)


_pm = None


def post(msg, wp=0):
    global _pm
    if not S["hwnd"]:
        return
    if _pm is None:
        _pm = ctypes.WinDLL("user32").PostMessageW
        _pm.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
    _pm(S["hwnd"], msg, wp, 0)


def toggle():
    post(WM_HOTKEY, eng.HOTKEY_TOGGLE)


# ------------------------------------------------------------------- engine
def engine_thread():
    """Same setup as the engine's main(), but the app can control it."""
    u, k = eng.user32, eng.kernel32
    try:
        if not u.InitializeTouchInjection(10, 2):
            raise RuntimeError("Touch injection isn't available on this PC.")
        hinst = k.GetModuleHandleW(None)
        eng.main_hinst = hinst

        def proc(hwnd, msg, wp, lp):
            try:
                if msg == WM_HOTKEY and wp == ID_SHOW:
                    toggle_window()
                    return 0
                if msg == WM_APP_HK:
                    register_all(hwnd)
                    return 0
                if msg == WM_APP_PAUSE:
                    (unregister_all if wp else register_all)(hwnd)
                    return 0
            except Exception:
                pass
            return eng.wnd_proc(hwnd, msg, wp, lp)

        wproc = eng.WNDPROC(proc)
        wc = eng.WNDCLASSW()
        wc.lpfnWndProc = wproc
        wc.hInstance = hinst
        wc.lpszClassName = "TouchMyPadWnd"
        u.RegisterClassW(byref(wc))
        hwnd = u.CreateWindowExW(0, wc.lpszClassName, "TouchMyPadEngine", 0, 0, 0, 0, 0, None, None, hinst, None)
        rid = eng.RAWINPUTDEVICE(0x0D, 0x05, eng.RIDEV_INPUTSINK, hwnd)
        if not u.RegisterRawInputDevices(byref(rid), 1, ctypes.sizeof(rid)):
            raise RuntimeError("Couldn't connect to your touchpad.")
        register_all(hwnd)
        eng.mouse_hook_proc = eng.HOOKPROC(eng.mouse_hook)
        eng.mouse_hook_handle = u.SetWindowsHookExW(14, eng.mouse_hook_proc, hinst, 0)
        eng.refresh_screen()
        S["hwnd"] = hwnd
        msg = eng.w.MSG()
        try:
            while u.GetMessageW(byref(msg), None, 0, 0) > 0:
                u.TranslateMessage(byref(msg))
                u.DispatchMessageW(byref(msg))
        finally:
            eng.release_all()
            if eng.mouse_hook_handle:
                u.UnhookWindowsHookEx(eng.mouse_hook_handle)
    except Exception as e:
        S["error"] = str(e) or "Something went wrong."


# ------------------------------------------------------------ window + tray
def show_window():
    w = S["window"]
    if w:
        try:
            w.show()
            w.restore()
        except Exception:
            pass
    S["visible"] = True


def hide_window():
    w = S["window"]
    if w:
        try:
            w.hide()
        except Exception:
            pass
    S["visible"] = False
    if not S["told"] and S["icon"]:
        S["told"] = True
        try:
            S["icon"].notify("Still running here. Click the tray icon to open it.", "touchmypad")
        except Exception:
            pass


def toggle_window():
    hide_window() if S["visible"] else show_window()


def shutdown():
    S["quitting"] = True
    try:
        S["icon"].stop()
    except Exception:
        pass
    post(WM_CLOSE)


def quit_app():
    shutdown()
    time.sleep(0.25)
    try:
        S["window"].destroy()
    except Exception:
        pass


def make_icon(on):
    N = 256
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (127, 141, 255, 255) if on else (140, 150, 175, 255)
    d.rounded_rectangle((14, 46, 242, 210), radius=44, fill=(14, 20, 42, 255), outline=col, width=16)
    d.ellipse((146, 112, 200, 166), fill=col)
    return im.resize((64, 64), Image.LANCZOS)


def build_tray():
    menu = pystray.Menu(
        pystray.MenuItem("Open touchmypad", lambda i, it: show_window(), default=True),
        pystray.MenuItem(lambda it: "Turn touch mode off" if eng.enabled else "Turn touch mode on", lambda i, it: toggle()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda i, it: quit_app()),
    )
    icon = pystray.Icon("touchmypad", make_icon(eng.enabled), "touchmypad", menu)
    S["icon"] = icon
    icon.run_detached()

    def watch():
        last = None
        while not S["quitting"]:
            cur = bool(eng.enabled)
            if cur != last:
                last = cur
                try:
                    icon.icon = make_icon(cur)
                    icon.title = "touchmypad: touch mode " + ("ON" if cur else "OFF")
                    icon.update_menu()
                except Exception:
                    pass
            time.sleep(0.25)

    threading.Thread(target=watch, daemon=True).start()


def set_autostart(on):
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    try:
        if on:
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}" --tray'
            else:
                pyw = sys.executable.replace("python.exe", "pythonw.exe")
                cmd = f'"{pyw}" "{os.path.abspath(__file__)}" --tray'
            winreg.SetValueEx(key, "touchmypad", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "touchmypad")
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def apply_cfg():
    eng.EDGE_MARGIN = cfg["margin"]
    eng.FLIP_ROTATION = not cfg["swap"]
    post(WM_APP_HK)


def reset_advanced():
    cfg.update(margin=DEFAULTS["margin"], swap=False, tray=False, autostart=False, start_on=False)
    cfg["hotkeys"]["show"] = dict(DEFAULTS["hotkeys"]["show"])
    try:
        set_autostart(False)
    except Exception:
        pass


def reset_all():
    cfg.clear()
    cfg.update(json.loads(json.dumps(DEFAULTS)))
    reset_advanced()
    apply_cfg()
    save()


def apply_window_icon():
    """Puts the touchmypad icon on the window and taskbar button."""
    path = os.path.join(HERE, "touchmypad.ico")
    if not os.path.exists(path):
        return
    u = ctypes.WinDLL("user32")
    u.FindWindowExW.restype = ctypes.c_void_p
    u.FindWindowExW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p]
    u.LoadImageW.restype = ctypes.c_void_p
    u.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    u.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p]
    u.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    for _ in range(40):
        hwnd = None
        while True:
            hwnd = u.FindWindowExW(None, hwnd, None, "touchmypad")
            if not hwnd:
                break
            pid = ctypes.c_ulong(0)
            u.GetWindowThreadProcessId(hwnd, byref(pid))
            if pid.value == os.getpid():
                for kind, size in ((0, 16), (1, 32)):  # small and big icon
                    icon = u.LoadImageW(None, path, 1, size, size, 0x10)
                    if icon:
                        u.SendMessageW(hwnd, 0x0080, kind, icon)
                return
        time.sleep(0.25)


# ---------------------------------------------------------------------- API
class Api:
    def state(self):
        try:
            pts = [(p[0] / max(1, eng.SCREEN_W), p[1] / max(1, eng.SCREEN_H)) for p in list(eng.active.values())]
        except RuntimeError:
            pts = []
        return {"on": bool(eng.enabled), "pad": S["pad"], "error": S["error"], "w": eng.SCREEN_W, "h": eng.SCREEN_H,
                "pts": pts, "cfg": {k: cfg[k] for k in ("advanced", "margin", "swap", "tray", "autostart", "start_on")},
                "hk": {n: {"label": cfg["hotkeys"][n]["label"], "ok": S["ok"][n]} for n in IDS}}

    def toggle(self):
        if not S["error"]:
            toggle()

    def set_margin(self, v, final):
        if not cfg["advanced"]:
            return
        cfg["margin"] = eng.EDGE_MARGIN = min(max(float(v), 0.0), 0.12)
        if final:
            save()

    def set_flag(self, key, val):
        val = bool(val)
        if key == "advanced":
            cfg["advanced"] = val
            if not val:
                reset_advanced()
                apply_cfg()
        elif key in ("swap", "tray", "autostart", "start_on") and cfg["advanced"]:
            cfg[key] = val
            if key == "swap":
                eng.FLIP_ROTATION = not val
            if key == "autostart":
                try:
                    set_autostart(val)
                except Exception:
                    cfg[key] = False
        else:
            return
        save()

    def reset_all(self):
        reset_all()

    def capture(self, on):
        post(WM_APP_PAUSE, 1 if on else 0)

    def set_hotkey(self, name, mod, vk, label):
        if name not in IDS:
            return {"ok": False, "msg": "Unknown shortcut"}
        if name == "show" and not cfg["advanced"]:
            return {"ok": False, "msg": "Turn on Advanced settings first"}
        other = cfg["hotkeys"]["show" if name == "toggle" else "toggle"]
        if other["mod"] == mod and other["vk"] == vk:
            return {"ok": False, "msg": "That shortcut is already used here"}
        cfg["hotkeys"][name] = {"mod": int(mod), "vk": int(vk), "label": str(label)[:30]}
        save()
        post(WM_APP_HK)
        return {"ok": True, "msg": ""}

    def reset_hotkey(self, name):
        if name in IDS:
            cfg["hotkeys"][name] = dict(DEFAULTS["hotkeys"][name])
            save()
            post(WM_APP_HK)

    def hide(self):
        hide_window()

    def quit(self):
        threading.Thread(target=quit_app, daemon=True).start()

    def open_repo(self):
        webbrowser.open(REPO)


def main():
    eng.kernel32.CreateMutexW(None, False, "touchmypad-single-instance")
    if ctypes.get_last_error() == 183:  # already running
        sys.exit(0)
    sys.stdout, sys.stderr = Sink(sys.stdout), Sink(sys.stderr)
    eng.EDGE_MARGIN, eng.FLIP_ROTATION = cfg["margin"], not cfg["swap"]
    eng.enabled = cfg["start_on"]  # off unless the person asked for it
    threading.Thread(target=engine_thread, daemon=True).start()

    hidden = "--tray" in sys.argv
    with open(os.path.join(HERE, "ui.html"), encoding="utf-8") as fh:
        html = fh.read()
    win = webview.create_window("touchmypad", html=html, js_api=Api(), width=880, height=540, resizable=False,
                                background_color="#080c19", hidden=hidden)
    S["window"], S["visible"] = win, not hidden

    def closing():
        if S["quitting"]:
            return True
        if cfg["tray"]:
            hide_window()
            return False
        shutdown()
        return True

    win.events.closing += closing
    build_tray()
    threading.Thread(target=apply_window_icon, daemon=True).start()
    webview.start()
    shutdown()
    time.sleep(0.2)
    os._exit(0)


if __name__ == "__main__":
    main()
