# touchmypad

![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-2a3bff)

**Use your laptop touchpad as a touchscreen.**

Touch the top-left of your touchpad and the top-left of your screen gets tapped. Touch the middle and the middle gets tapped. It uses absolute mapping instead of a moving cursor and supports up to 10 fingers. Good for everyday use, games that support touch, and drawing with your finger.

## Download (easiest, no Python needed)

1. Open the [latest release](https://github.com/skykartik/touchmypad/releases/latest) and download **touchmypad.exe**.
2. Double-click it. The touchmypad window opens with touch mode **off**.
3. Click the big switch to turn touch mode on, then touch your touchpad once. The window shows "Touchpad connected".

> **"Windows protected your PC"?** The app is new and unsigned, so Windows may show this blue box. Click **More info**, then **Run anyway**. Some antivirus tools are also cautious about apps that inject touch input. You can read the source here or run the Python version below.

## Features

- **Live preview** of where your fingers land on the screen.
- **Small fixed window**, so everything is visible at once with no scrolling.
- **Shortcut you can change:** `Ctrl` + `` ` `` turns touch mode on or off from anywhere. Click the keys in the app to pick your own.
- **Tray icon** with a quick on/off, open and quit menu.
- **Advanced settings (off by default):** switch it on to unlock corner reach, swap portrait direction, start with touch mode on, keep running in the tray when the window is closed, open when Windows starts, and a shortcut to show or hide the window. Switching Advanced off puts all of these back to normal.
- **Reset all settings** button in the Settings tab.
- Works in any screen orientation, even if you rotate the screen while it runs.

Touch mode always starts **off**. While it's on, normal cursor movement is paused so it doesn't fight your touches. Turn it off with the switch, the tray menu or your shortcut to get your cursor back.

## Requirements

- Windows 10 or 11
- A **Precision Touchpad**, which most modern laptops have. To check, open Windows Settings, search for "Touchpad", and look for "Your PC has a precision touchpad".
- Microsoft Edge WebView2 (already on Windows 11 and up-to-date Windows 10).

## Run from source (Python)

1. Install Python 3.10 to 3.12 (64-bit). Download it from <https://www.python.org/downloads/> and tick **Add python.exe to PATH**, or get it from the Microsoft Store.
2. Click the green **Code** button, then **Download ZIP**, and extract it. Or run `git clone https://github.com/skykartik/touchmypad.git`.
3. Open a terminal in the folder and run:

```
pip install -r requirements.txt
python touchmypad_app.py
```

`touchmypad.py` is the engine and `ui.html` is the window. Keep all files together. `python touchmypad.py` still runs the engine alone in a terminal.

## Build the exe yourself

**On your PC:** keep `build.bat`, `touchmypad_app.py`, `touchmypad.py`, `ui.html`, `touchmypad.ico` and `requirements.txt` together and double-click `build.bat`. Your app appears at `dist\touchmypad.exe`.

**Automatically on GitHub:** the workflow in `.github/workflows/release.yml` builds the exe and attaches it to a release. Create a release tagged like `v1.0.0` and wait a couple of minutes. You can also run it from the Actions tab.

## How it works

1. **Read the pad:** it reads each finger's position from your touchpad.
2. **Map to the screen:** positions are scaled to the screen, adjusted for corner reach, and rotated to match the display.
3. **Inject touch:** the points go to Windows as real touch input.

## Troubleshooting

- **The cursor won't move.** Touch mode is on. Turn it off with the switch, the tray menu or your shortcut.
- **Nothing happens.** Check you have a Precision Touchpad, and touch it once so the app can find it.
- **Touches are mirrored in portrait.** Turn on Advanced settings and switch "Swap portrait direction".
- **Corners are hard to reach.** Turn on Advanced settings and raise "Corner reach".
- **A shortcut shows in red.** Another app already uses it. Pick different keys.
- **Games ignore it.** Only games and apps that accept touch input will react.

## Limitations

- Windows only.
- It can't sense how hard you press, so drawing has no pressure sensitivity.

## Contributing

Issues and pull requests are welcome. Include your Windows version and laptop model when reporting a bug.

## License

Add a `LICENSE` file to choose how others can use this project (MIT is a common choice).
