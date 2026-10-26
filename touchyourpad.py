"""
touchpad_touch.py  -  Use your laptop touchpad as a touchscreen (absolute mapping).

Touch the top-left of the touchpad  -> taps the top-left of the screen.
Touch the middle                    -> taps the middle. Multi-finger works (up to 10).

Requirements: Windows 10/11, Python 3 (64-bit), a Precision Touchpad. No pip installs.
Run:          python touchpad_touch.py

Hotkey:       Ctrl+`  = turn ON / OFF   (close this window to quit)
While ON, normal mouse/touchpad cursor movement is blocked (so the cursor
doesn't fight with your touches). Turn OFF with the hotkey to get it back.
Works in any screen orientation, even if you rotate the screen while it runs.
"""
import ctypes
import struct
import sys
from ctypes import wintypes as w, byref, c_void_p, POINTER, Structure, WINFUNCTYPE

if sys.platform != "win32":
    sys.exit("This only runs on Windows.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
hid = ctypes.WinDLL("hid", use_last_error=True)

user32.SetProcessDPIAware()  # so coordinates are real pixels
SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)

LRESULT = ctypes.c_ssize_t
WNDPROC = WINFUNCTYPE(LRESULT, w.HWND, w.UINT, w.WPARAM, w.LPARAM)
HOOKPROC = WINFUNCTYPE(LRESULT, ctypes.c_int, w.WPARAM, w.LPARAM)

# ----------------------------------------------------------------- structures
class WNDCLASSW(Structure):
    _fields_ = [("style", w.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", w.HINSTANCE), ("hIcon", w.HANDLE),
                ("hCursor", w.HANDLE), ("hbrBackground", w.HANDLE), ("lpszMenuName", w.LPCWSTR),
                ("lpszClassName", w.LPCWSTR)]

class RAWINPUTDEVICE(Structure):
    _fields_ = [("usUsagePage", w.USHORT), ("usUsage", w.USHORT), ("dwFlags", w.DWORD), ("hwndTarget", w.HWND)]

class RAWINPUTHEADER(Structure):
    _fields_ = [("dwType", w.DWORD), ("dwSize", w.DWORD), ("hDevice", c_void_p), ("wParam", w.WPARAM)]

class HIDP_CAPS(Structure):
    _fields_ = [("Usage", w.USHORT), ("UsagePage", w.USHORT), ("InputReportByteLength", w.USHORT),
                ("OutputReportByteLength", w.USHORT), ("FeatureReportByteLength", w.USHORT),
                ("Reserved", w.USHORT * 17), ("NumberLinkCollectionNodes", w.USHORT),
                ("NumberInputButtonCaps", w.USHORT), ("NumberInputValueCaps", w.USHORT),
                ("NumberInputDataIndices", w.USHORT), ("NumberOutputButtonCaps", w.USHORT),
                ("NumberOutputValueCaps", w.USHORT), ("NumberOutputDataIndices", w.USHORT),
                ("NumberFeatureButtonCaps", w.USHORT), ("NumberFeatureValueCaps", w.USHORT),
                ("NumberFeatureDataIndices", w.USHORT)]

class HIDP_VALUE_CAPS(Structure):
    _fields_ = [("UsagePage", w.USHORT), ("ReportID", ctypes.c_ubyte), ("IsAlias", ctypes.c_ubyte),
                ("BitField", w.USHORT), ("LinkCollection", w.USHORT), ("LinkUsage", w.USHORT),
                ("LinkUsagePage", w.USHORT), ("IsRange", ctypes.c_ubyte), ("IsStringRange", ctypes.c_ubyte),
                ("IsDesignatorRange", ctypes.c_ubyte), ("IsAbsolute", ctypes.c_ubyte),
                ("HasNull", ctypes.c_ubyte), ("Reserved", ctypes.c_ubyte), ("BitSize", w.USHORT),
                ("ReportCount", w.USHORT), ("Reserved2", w.USHORT * 5), ("UnitsExp", w.ULONG),
                ("Units", w.ULONG), ("LogicalMin", ctypes.c_long), ("LogicalMax", ctypes.c_long),
                ("PhysicalMin", ctypes.c_long), ("PhysicalMax", ctypes.c_long), ("U", w.USHORT * 8)]

class MSLLHOOKSTRUCT(Structure):
    _fields_ = [("pt", w.POINT), ("mouseData", w.DWORD), ("flags", w.DWORD), ("time", w.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]

class POINTER_INFO(Structure):
    _fields_ = [("pointerType", w.DWORD), ("pointerId", w.UINT), ("frameId", w.UINT),
                ("pointerFlags", w.DWORD), ("sourceDevice", w.HANDLE), ("hwndTarget", w.HWND),
                ("ptPixelLocation", w.POINT), ("ptHimetricLocation", w.POINT),
                ("ptPixelLocationRaw", w.POINT), ("ptHimetricLocationRaw", w.POINT),
                ("dwTime", w.DWORD), ("historyCount", w.UINT), ("InputData", ctypes.c_int),
                ("dwKeyStates", w.DWORD), ("PerformanceCount", ctypes.c_uint64),
                ("ButtonChangeType", ctypes.c_int)]

class POINTER_TOUCH_INFO(Structure):
    _fields_ = [("pointerInfo", POINTER_INFO), ("touchFlags", w.DWORD), ("touchMask", w.DWORD),
                ("rcContact", w.RECT), ("rcContactRaw", w.RECT), ("orientation", w.UINT),
                ("pressure", w.UINT)]

class DEVMODEW(Structure):
    _fields_ = [("dmDeviceName", w.WCHAR * 32), ("dmSpecVersion", w.WORD), ("dmDriverVersion", w.WORD),
                ("dmSize", w.WORD), ("dmDriverExtra", w.WORD), ("dmFields", w.DWORD),
                ("dmPositionX", ctypes.c_long), ("dmPositionY", ctypes.c_long),
                ("dmDisplayOrientation", w.DWORD), ("dmDisplayFixedOutput", w.DWORD),
                ("dmColor", ctypes.c_short), ("dmDuplex", ctypes.c_short), ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short), ("dmCollate", ctypes.c_short), ("dmFormName", w.WCHAR * 32),
                ("dmLogPixels", w.WORD), ("dmBitsPerPel", w.DWORD), ("dmPelsWidth", w.DWORD),
                ("dmPelsHeight", w.DWORD), ("dmDisplayFlags", w.DWORD), ("dmDisplayFrequency", w.DWORD),
                ("dmICMMethod", w.DWORD), ("dmICMIntent", w.DWORD), ("dmMediaType", w.DWORD),
                ("dmDitherType", w.DWORD), ("dmReserved1", w.DWORD), ("dmReserved2", w.DWORD),
                ("dmPanningWidth", w.DWORD), ("dmPanningHeight", w.DWORD)]

# ------------------------------------------------------------- function types
user32.DefWindowProcW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.CallNextHookEx.argtypes = [c_void_p, ctypes.c_int, w.WPARAM, w.LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, w.HINSTANCE, w.DWORD]
user32.SetWindowsHookExW.restype = c_void_p
user32.UnhookWindowsHookEx.argtypes = [c_void_p]
user32.GetRawInputData.argtypes = [c_void_p, w.UINT, c_void_p, POINTER(w.UINT), w.UINT]
user32.GetRawInputData.restype = w.UINT
user32.GetRawInputDeviceInfoW.argtypes = [c_void_p, w.UINT, c_void_p, POINTER(w.UINT)]
user32.GetRawInputDeviceInfoW.restype = w.UINT
user32.RegisterRawInputDevices.argtypes = [POINTER(RAWINPUTDEVICE), w.UINT, w.UINT]
user32.RegisterRawInputDevices.restype = w.BOOL
user32.RegisterClassW.argtypes = [POINTER(WNDCLASSW)]
user32.CreateWindowExW.argtypes = [w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, w.HWND, w.HMENU, w.HINSTANCE, c_void_p]
user32.CreateWindowExW.restype = w.HWND
user32.RegisterHotKey.argtypes = [w.HWND, ctypes.c_int, w.UINT, w.UINT]
user32.RegisterHotKey.restype = w.BOOL
user32.GetMessageW.argtypes = [POINTER(w.MSG), w.HWND, w.UINT, w.UINT]
user32.InitializeTouchInjection.argtypes = [w.UINT, w.DWORD]
user32.InitializeTouchInjection.restype = w.BOOL
user32.InjectTouchInput.argtypes = [w.UINT, c_void_p]
user32.InjectTouchInput.restype = w.BOOL
user32.EnumDisplaySettingsW.argtypes = [w.LPCWSTR, w.DWORD, POINTER(DEVMODEW)]
user32.EnumDisplaySettingsW.restype = w.BOOL
kernel32.GetModuleHandleW.argtypes = [w.LPCWSTR]
kernel32.GetModuleHandleW.restype = w.HMODULE

hid.HidP_GetCaps.argtypes = [c_void_p, POINTER(HIDP_CAPS)]
hid.HidP_GetCaps.restype = w.ULONG
hid.HidP_GetValueCaps.argtypes = [ctypes.c_int, c_void_p, POINTER(w.USHORT), c_void_p]
hid.HidP_GetValueCaps.restype = w.ULONG
hid.HidP_GetUsageValue.argtypes = [ctypes.c_int, w.USHORT, w.USHORT, w.USHORT, POINTER(w.ULONG),
                                   c_void_p, ctypes.c_char_p, w.ULONG]
hid.HidP_GetUsageValue.restype = w.ULONG
hid.HidP_GetUsages.argtypes = [ctypes.c_int, w.USHORT, w.USHORT, POINTER(w.USHORT), POINTER(w.ULONG),
                               c_void_p, ctypes.c_char_p, w.ULONG]
hid.HidP_GetUsages.restype = w.ULONG

# ------------------------------------------------------------------ constants
WM_INPUT, WM_HOTKEY, WM_DESTROY = 0x00FF, 0x0312, 0x0002
RID_INPUT, RIM_TYPEHID = 0x10000003, 2
RIDI_PREPARSEDDATA = 0x20000005
RIDEV_INPUTSINK = 0x00000100
HIDP_INPUT, HIDP_OK = 0, 0x00110000
HDR_SIZE = ctypes.sizeof(RAWINPUTHEADER)

PT_TOUCH = 2
F_NEW, F_INRANGE, F_INCONTACT, F_FIRSTBTN = 0x1, 0x2, 0x4, 0x10
F_DOWN, F_UPDATE, F_UP = 0x10000, 0x20000, 0x40000
FLAGS_DOWN = F_INRANGE | F_INCONTACT | F_DOWN
FLAGS_UPDATE = F_INRANGE | F_INCONTACT | F_UPDATE
FLAGS_UP = F_UP

# Touchpads have a thin unresponsive strip around the physical edge, so the
# raw coordinate range never quite reaches min/max. EDGE_MARGIN "shrinks" the
# usable range by this fraction on each side before scaling, so touches near
# the edge reach the screen's actual edge instead of stopping short.
# Raise it (e.g. 0.12) if corners still feel hard to reach; lower it if the
# edges feel too twitchy/sensitive.
EDGE_MARGIN = 0.03

DEBUG = False        # set True temporarily if something breaks and you need to see why
_dbg_count = 0

HOTKEY_TOGGLE, HOTKEY_QUIT, HOTKEY_RESET = 1, 2, 3

# ---------------------------------------------------------------------- state
enabled = True
devices = {}      # hDevice -> parsed touchpad info (or None if not a usable touchpad)
active = {}       # touchpad contact id -> (px, py, slot)
free_slots = list(range(10))
mouse_hook_handle = None
mouse_hook_proc = None
main_hinst = None
suppressed = set()   # contact ids that were down during a rotation; ignored until lifted

# If touches come out mirrored/backwards after rotating the screen to portrait,
# set this to True to swap the two portrait directions.
FLIP_ROTATION = True
WM_DISPLAYCHANGE = 0x007E
orientation = 0      # 0 = normal, 1 = rotated 90, 2 = 180, 3 = 270


def refresh_screen():
    """Re-read screen size and rotation. Called at start and on every display change."""
    global SCREEN_W, SCREEN_H, orientation
    SCREEN_W = user32.GetSystemMetrics(0)
    SCREEN_H = user32.GetSystemMetrics(1)
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if user32.EnumDisplaySettingsW(None, 0xFFFFFFFF, byref(dm)):  # ENUM_CURRENT_SETTINGS
        orientation = int(dm.dmDisplayOrientation) & 3
    else:
        orientation = 0
    print(f"[*] Screen {SCREEN_W}x{SCREEN_H}, rotation code {orientation}")


def map_to_screen(u, v):
    """u, v = touch position on the touchpad, 0..1 (left->right, top->bottom).
    Returns pixel position on the screen, rotated to match the screen's orientation."""
    o = orientation
    if FLIP_ROTATION and o in (1, 3):
        o = 4 - o
    if o == 1:
        cx, cy = v, 1 - u
    elif o == 2:
        cx, cy = 1 - u, 1 - v
    elif o == 3:
        cx, cy = 1 - v, u
    else:
        cx, cy = u, v
    px = min(max(int(cx * (SCREEN_W - 1)), 0), SCREEN_W - 1)
    py = min(max(int(cy * (SCREEN_H - 1)), 0), SCREEN_H - 1)
    return px, py


# ------------------------------------------------------------ touch injection
def inject(events):
    """events: list of (slot, px, py, flags)"""
    if not events:
        return
    arr = (POINTER_TOUCH_INFO * len(events))()
    for i, (slot, px, py, flags) in enumerate(events):
        t = arr[i]
        pi = t.pointerInfo
        pi.pointerType = PT_TOUCH
        pi.pointerId = slot
        pi.pointerFlags = flags
        pi.ptPixelLocation.x = px
        pi.ptPixelLocation.y = py
        t.touchMask = 0x1 | 0x2 | 0x4  # contact area, orientation, pressure
        t.orientation = 90
        t.pressure = 32000
        t.rcContact.left, t.rcContact.right = px - 2, px + 2
        t.rcContact.top, t.rcContact.bottom = py - 2, py + 2
    ok = user32.InjectTouchInput(len(events), arr)
    if not ok:
        if DEBUG:
            print(f"[!] InjectTouchInput failed (error {ctypes.get_last_error()}), resetting touch state")
        recover()


def recover():
    """Forget all touches and restart touch injection (fixes 'stuck' state after gestures)."""
    active.clear()
    free_slots[:] = list(range(10))
    user32.InitializeTouchInjection(10, 2)


def release_all():
    events = []
    for cid, (px, py, slot) in list(active.items()):
        events.append((slot, px, py, FLAGS_UP))
        free_slots.append(slot)
    active.clear()
    free_slots.sort()
    inject(events)


def process_contacts(dev, contacts):
    events = []
    (xmin, xmax), (ymin, ymax) = dev["xrange"], dev["yrange"]
    xspan, yspan = xmax - xmin, ymax - ymin
    ex0, ex1 = xmin + xspan * EDGE_MARGIN, xmax - xspan * EDGE_MARGIN
    ey0, ey1 = ymin + yspan * EDGE_MARGIN, ymax - yspan * EDGE_MARGIN
    for cid, x, y, tip in contacts:
        if cid in suppressed:
            if not tip:
                suppressed.discard(cid)
            continue
        u = min(max((x - ex0) / max(1, ex1 - ex0), 0.0), 1.0)
        v = min(max((y - ey0) / max(1, ey1 - ey0), 0.0), 1.0)
        px, py = map_to_screen(u, v)
        if tip:
            if cid in active:
                slot = active[cid][2]
                active[cid] = (px, py, slot)
                events.append((slot, px, py, FLAGS_UPDATE))
            elif free_slots:
                slot = free_slots.pop(0)
                active[cid] = (px, py, slot)
                events.append((slot, px, py, FLAGS_DOWN))
        elif cid in active:
            _, _, slot = active.pop(cid)
            free_slots.append(slot)
            free_slots.sort()
            events.append((slot, px, py, FLAGS_UP))
    # Windows expects every active finger in every frame. Touchpads often send one
    # finger per report, so re-send the other fingers at their last position.
    in_event = {e[0] for e in events}
    for cid, (apx, apy, aslot) in active.items():
        if aslot not in in_event:
            events.append((aslot, apx, apy, FLAGS_UPDATE))
    inject(events)


# ------------------------------------------------------------ HID / raw input
def load_device(hdev):
    """Read the touchpad's HID layout once per device."""
    size = w.UINT(0)
    user32.GetRawInputDeviceInfoW(hdev, RIDI_PREPARSEDDATA, None, byref(size))
    if size.value == 0:
        return None
    prep = ctypes.create_string_buffer(size.value)
    if user32.GetRawInputDeviceInfoW(hdev, RIDI_PREPARSEDDATA, prep, byref(size)) == 0xFFFFFFFF:
        return None
    caps = HIDP_CAPS()
    if hid.HidP_GetCaps(prep, byref(caps)) != HIDP_OK:
        return None
    n = caps.NumberInputValueCaps
    if n == 0:
        return None
    vcaps = (HIDP_VALUE_CAPS * n)()
    cnt = w.USHORT(n)
    if hid.HidP_GetValueCaps(HIDP_INPUT, vcaps, byref(cnt), prep) != HIDP_OK:
        return None

    links = {}  # link collection -> {x, y, id}
    for i in range(cnt.value):
        c = vcaps[i]
        if c.IsRange:
            continue
        usage = c.U[0]
        d = links.setdefault(c.LinkCollection, {})
        if c.UsagePage == 0x01 and usage == 0x30:
            d["x"] = (c.LogicalMin, c.LogicalMax)
        elif c.UsagePage == 0x01 and usage == 0x31:
            d["y"] = (c.LogicalMin, c.LogicalMax)
        elif c.UsagePage == 0x0D and usage == 0x51:
            d["id"] = True
    links = {lc: d for lc, d in links.items() if "x" in d and "y" in d and "id" in d}
    if not links:
        return None
    first = links[sorted(links)[0]]
    print(f"[+] Touchpad found: {len(links)} contact slots, X range {first['x']}, Y range {first['y']}")
    return {"prep": prep, "links": sorted(links), "xrange": first["x"], "yrange": first["y"]}


def parse_report(dev, report):
    prep = dev["prep"]
    out = []
    for lc in dev["links"]:
        vals = {}
        ok = True
        for name, page, usage in (("x", 0x01, 0x30), ("y", 0x01, 0x31), ("id", 0x0D, 0x51)):
            v = w.ULONG(0)
            st = hid.HidP_GetUsageValue(HIDP_INPUT, page, lc, usage, byref(v), prep, report, len(report))
            if st != HIDP_OK:
                ok = False
                break
            vals[name] = v.value
        if not ok:
            continue
        ul = (w.USHORT * 16)()
        ln = w.ULONG(16)
        st = hid.HidP_GetUsages(HIDP_INPUT, 0x0D, lc, ul, byref(ln), prep, report, len(report))
        tip = st == HIDP_OK and 0x42 in list(ul)[:ln.value]
        if not tip and vals["x"] == 0 and vals["y"] == 0:
            continue  # unused slot in a hybrid report
        out.append((vals["id"], vals["x"], vals["y"], tip))
    return out


def on_raw_input(lparam):
    size = w.UINT(0)
    user32.GetRawInputData(lparam, RID_INPUT, None, byref(size), HDR_SIZE)
    if size.value == 0:
        return
    buf = ctypes.create_string_buffer(size.value)
    if user32.GetRawInputData(lparam, RID_INPUT, buf, byref(size), HDR_SIZE) != size.value:
        return
    hdr = RAWINPUTHEADER.from_buffer(buf)
    if hdr.dwType != RIM_TYPEHID:
        return
    hdev = hdr.hDevice or 0
    if hdev not in devices:
        devices[hdev] = load_device(hdev)
        if DEBUG:
            print(f"[dbg] raw input from device {hdev}: usable touchpad = {devices[hdev] is not None}")
    dev = devices[hdev]
    if dev is None or not enabled:
        return
    size_hid, count = struct.unpack_from("<II", buf, HDR_SIZE)
    base = HDR_SIZE + 8
    for i in range(count):
        report = bytes(buf[base + i * size_hid: base + (i + 1) * size_hid])
        contacts = parse_report(dev, report)
        global _dbg_count
        if DEBUG and _dbg_count < 40:
            _dbg_count += 1
            print(f"[dbg] report len={len(report)} contacts(id,x,y,tip)={contacts}")
        if contacts:
            process_contacts(dev, contacts)
        elif active:
            release_all()


# ------------------------------------------------------------ mouse blocking
def reinstall_mouse_hook():
    """Fully remove and re-add the low-level mouse hook. A stale/unresponsive
    hook is what causes the cursor to lag or stop reacting after toggling."""
    global mouse_hook_handle
    if mouse_hook_handle:
        user32.UnhookWindowsHookEx(mouse_hook_handle)
        mouse_hook_handle = None
    mouse_hook_handle = user32.SetWindowsHookExW(14, mouse_hook_proc, main_hinst, 0)  # WH_MOUSE_LL
    return mouse_hook_handle is not None


def mouse_hook(ncode, wparam, lparam):
    if ncode >= 0 and enabled:
        info = ctypes.cast(lparam, POINTER(MSLLHOOKSTRUCT)).contents
        injected = info.flags & 0x1
        from_touch = (info.dwExtraInfo & 0xFFFFFF00) == 0xFF515700
        if not injected and not from_touch:
            return 1  # swallow real mouse/touchpad cursor input
    return user32.CallNextHookEx(None, ncode, wparam, lparam)


# ------------------------------------------------------------------- window
def wnd_proc(hwnd, msg, wparam, lparam):
    global enabled, mouse_hook_handle
    try:
        if msg == WM_INPUT:
            on_raw_input(lparam)
        elif msg == WM_HOTKEY:
            if wparam == HOTKEY_TOGGLE:
                enabled = not enabled
                if not enabled:
                    release_all()
                else:
                    recover()
                print("[*] Touchpad-touchscreen:", "ON" if enabled else "OFF (normal mouse restored)")
            elif wparam == HOTKEY_QUIT:
                user32.PostQuitMessage(0)
        elif msg == WM_DISPLAYCHANGE:
            # Screen rotated or resolution changed: drop current touches, re-read size/rotation.
            suppressed.update(active.keys())
            release_all()
            refresh_screen()
            recover()
        elif msg == WM_DESTROY:
            user32.PostQuitMessage(0)
    except Exception as e:  # never crash inside a callback
        print("[!] error:", e)
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def main():
    if not user32.InitializeTouchInjection(10, 2):  # 2 = TOUCH_FEEDBACK_INDIRECT (shows the dots)
        sys.exit("Touch injection unavailable (need Windows 8 or newer).")

    global mouse_hook_proc, main_hinst, mouse_hook_handle
    hinst = kernel32.GetModuleHandleW(None)
    main_hinst = hinst
    proc = WNDPROC(wnd_proc)
    wc = WNDCLASSW()
    wc.lpfnWndProc = proc
    wc.hInstance = hinst
    wc.lpszClassName = "TouchpadTouchWnd"
    user32.RegisterClassW(byref(wc))
    hwnd = user32.CreateWindowExW(0, wc.lpszClassName, "TouchpadTouch", 0, 0, 0, 0, 0,
                                  None, None, hinst, None)

    rid = RAWINPUTDEVICE(0x0D, 0x05, RIDEV_INPUTSINK, hwnd)  # Precision Touchpad
    if not user32.RegisterRawInputDevices(byref(rid), 1, ctypes.sizeof(rid)):
        sys.exit("Could not register for touchpad input.")

    MOD_CONTROL = 0x2
    VK_OEM_3 = 0xC0  # the ` / ~ key
    user32.RegisterHotKey(hwnd, HOTKEY_TOGGLE, MOD_CONTROL, VK_OEM_3)        # Ctrl+`

    mouse_hook_proc = HOOKPROC(mouse_hook)
    mouse_hook_handle = user32.SetWindowsHookExW(14, mouse_hook_proc, hinst, 0)  # WH_MOUSE_LL

    refresh_screen()
    print("Running. Touch the touchpad. Ctrl+` = on/off. Close this window to quit.")
    print("Waiting for the first touchpad touch to detect it...")

    msg = w.MSG()
    try:
        while user32.GetMessageW(byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))
    finally:
        release_all()
        if mouse_hook_handle:
            user32.UnhookWindowsHookEx(mouse_hook_handle)
        print("Bye.")


if __name__ == "__main__":
    main()
