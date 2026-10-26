# touch-my-pad

![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-2a3bff)
![Python](https://img.shields.io/badge/python-3%20(64--bit)-2a3bff)
![Dependencies](https://img.shields.io/badge/dependencies-none-2a3bff)

**Use your laptop touchpad as a touchscreen.**

Touch the top-left of your touchpad and the top-left of your screen gets tapped. Touch the middle and the middle gets tapped. It's absolute mapping instead of a moving cursor, with multi-touch for up to 10 fingers, in a single Python file with no pip installs.

## Features

- **Absolute mapping:** the touchpad surface maps 1:1 onto the screen.
- **Multi-touch:** up to 10 simultaneous fingers, sent to Windows as real touch input.
- **Hotkey toggle:** `Ctrl` + `` ` `` turns it on and off.
- **Rotation-aware:** works in any screen orientation, even if you rotate the screen while it runs.
- **Edge compensation:** an adjustable margin so you can reach the screen corners.
- **Zero dependencies:** only Python's standard library (`ctypes`).

## Requirements

- Windows 10 or 11
- Python 3, **64-bit**
- A **Precision Touchpad** (most modern laptops have one)

## Setup

### 1. Install Python

1. Download Python 3 (64-bit) from <https://www.python.org/downloads/>.
2. Run the installer and **tick "Add python.exe to PATH"** on the first screen.
3. Open a new terminal (Command Prompt or PowerShell) and check it worked:

   ```
   python --version
   ```

### 2. Get the script

With Git:

```
git clone https://github.com/skykartik/touch-your-pad.git
cd touch-my-pad
```

Without Git: open the repo on GitHub, click **Code**, then **Download ZIP**, and unzip it.

### 3. Run it

```
python touchmypad.py
```

Touch the touchpad once so the script can detect it. You should see something like:

```
[+] Touchpad found: 5 contact slots, X range (0, 3000), Y range (0, 1800)
[*] Screen 1920x1080, rotation code 0
Running. Touch the touchpad. Ctrl+` = on/off. Close this window to quit.
```

(The numbers will differ on your machine.)

### 4. Use it

- Touch the pad to tap the matching spot on the screen.
- Press `Ctrl` + `` ` `` to turn it **off** and **on**.
- Close the terminal window to quit.

## Hotkeys

| Keys | Action |
| --- | --- |
| `Ctrl` + `` ` `` | Turn touch mode on or off |

## Settings

Open `touchmypad.py` in any text editor and change these near the top of the file.

| Setting | Default | What it does |
| --- | --- | --- |
| `EDGE_MARGIN` | `0.03` | Shrinks the usable pad area by this fraction on each side so edges and corners are reachable. Raise it (for example `0.12`) if corners are hard to reach. Lower it if edges feel twitchy. |
| `FLIP_ROTATION` | `True` | If touches come out mirrored after rotating to portrait, set this to `False`. |
| `DEBUG` | `False` | Set to `True` temporarily to print what the script sees if something isn't working. |

## How it works

1. **Read the pad:** the script registers for raw HID input from the Precision Touchpad and reads each finger's absolute position.
2. **Map to the screen:** positions are scaled to the screen size, adjusted for the edge margin, and rotated to match the display orientation.
3. **Inject touch:** the points are sent to Windows through the touch injection API, so apps receive genuine touch events.

While it's on, a low-level mouse hook blocks normal cursor movement so the cursor doesn't fight your touches.

## Troubleshooting

**The cursor won't move.** That's expected while touch mode is on. Press `Ctrl` + `` ` `` to turn it off and get your cursor back, or close the terminal window.

**Nothing happens when I touch the pad.** Make sure you have a Precision Touchpad and 64-bit Python. Set `DEBUG = True` and run it again to see what it prints.

**Touches are mirrored in portrait.** Set `FLIP_ROTATION = False`.

**Corners are hard to reach.** Raise `EDGE_MARGIN`.

**`python` isn't recognized.** Reinstall Python and tick "Add python.exe to PATH", then open a new terminal.

## Limitations

- Windows only. It uses Windows touch injection.
- Needs a Precision Touchpad. Older non-precision touchpads aren't supported.

## Contributing

Issues and pull requests are welcome. If you report a bug, include your Windows version, your laptop model, and the output with `DEBUG = True`.

## License

Add a `LICENSE` file to choose how others can use this project (MIT is a common choice).
