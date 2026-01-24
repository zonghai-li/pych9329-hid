# keymap.py
# @author zonghai@gmail.com
# @description Cross-platform HID key mapping (US QWERTY).
# Maps ASCII characters and special keys to USB HID Scan Codes.

# -------------------------------------------------
# USB HID Modifier Bits (Standard)
# -------------------------------------------------
MOD_NONE = 0x00
MOD_LCTRL = 0x01
MOD_LSHFT = 0x02
MOD_LALT = 0x04
MOD_LGUI = 0x08  # Windows Key / Command Key
MOD_RCTRL = 0x10
MOD_RSHFT = 0x20
MOD_RALT = 0x40
MOD_RGUI = 0x80

# Human-readable mapping for hotkeys
MOD_MAP = {
    "ctrl": MOD_LCTRL,
    "control": MOD_LCTRL,
    "shift": MOD_LSHFT,
    "alt": MOD_LALT,
    "option": MOD_LALT,
    "gui": MOD_LGUI,
    "win": MOD_LGUI,
    "cmd": MOD_LGUI,
    "command": MOD_LGUI,
    "meta": MOD_LGUI,
    "super": MOD_LGUI,
}

# -------------------------------------------------
# HID Usage ID (Key Codes)
# -------------------------------------------------
# Base ASCII Mapping (Lower Case & Digits)
KEY = {
    # Letters a-z (0x04 - 0x1D)
    **{chr(c): 0x04 + c - ord("a") for c in range(ord("a"), ord("z") + 1)},
    # Digits 1-0 (0x1E - 0x27)
    "1": 0x1E,
    "2": 0x1F,
    "3": 0x20,
    "4": 0x21,
    "5": 0x22,
    "6": 0x23,
    "7": 0x24,
    "8": 0x25,
    "9": 0x26,
    "0": 0x27,
    # Basic Control
    "\n": 0x28,  # Enter
    "\b": 0x2A,  # Backspace
    "\t": 0x2B,  # Tab
    " ": 0x2C,  # Space
    # Punctuation (US Layout)
    "-": 0x2D,
    "=": 0x2E,
    "[": 0x2F,
    "]": 0x30,
    "\\": 0x31,
    ";": 0x33,
    "'": 0x34,
    "`": 0x35,
    ",": 0x36,
    ".": 0x37,
    "/": 0x38,
}

# -------------------------------------------------
# Shifted Characters (Requires MOD_LSHFT)
# -------------------------------------------------
# Maps a character to its base key and the shift modifier
SHIFTED = {
    "!": ("1", MOD_LSHFT),
    "@": ("2", MOD_LSHFT),
    "#": ("3", MOD_LSHFT),
    "$": ("4", MOD_LSHFT),
    "%": ("5", MOD_LSHFT),
    "^": ("6", MOD_LSHFT),
    "&": ("7", MOD_LSHFT),
    "*": ("8", MOD_LSHFT),
    "(": ("9", MOD_LSHFT),
    ")": ("0", MOD_LSHFT),
    "_": ("-", MOD_LSHFT),
    "+": ("=", MOD_LSHFT),
    "{": ("[", MOD_LSHFT),
    "}": ("]", MOD_LSHFT),
    "|": ("\\", MOD_LSHFT),
    ":": (";", MOD_LSHFT),
    '"': ("'", MOD_LSHFT),
    "~": ("`", MOD_LSHFT),
    "<": (",", MOD_LSHFT),
    ">": (".", MOD_LSHFT),
    "?": ("/", MOD_LSHFT),
}


NUMPAD_KEYS = {
    # Numpad keys
    "num0": 0x62,
    "num1": 0x59,
    "num2": 0x5A,
    "num3": 0x5B,
    "num4": 0x5C,
    "num5": 0x5D,
    "num6": 0x5E,
    "num7": 0x5F,
    "num8": 0x60,
    "num9": 0x61,
    "numlock": 0x53,
    "numenter": 0x58,
    "num\n": 0x58,
    "num/": 0x54,
    "num*": 0x55,
    "num-": 0x56,
    "num+": 0x57,
    "num.": 0x63,
}


SPECIAL_KEYS = {
    "f1": 0x3A,
    "f2": 0x3B,
    "f3": 0x3C,
    "f4": 0x3D,
    "f5": 0x3E,
    "f6": 0x3F,
    "f7": 0x40,
    "f8": 0x41,
    "f9": 0x42,
    "f10": 0x43,
    "f11": 0x44,
    "f12": 0x45,
    "printscreen": 0x46,
    "scrolllock": 0x47,
    "pause": 0x48,
    "insert": 0x49,
    "home": 0x4A,
    "pageup": 0x4B,
    "delete": 0x4C,
    "end": 0x4D,
    "pagedown": 0x4E,
    "right": 0x4F,
    "left": 0x50,
    "down": 0x51,
    "up": 0x52,
    "enter": 0x28,
    "backspace": 0x2A,
    "tab": 0x2B,
    "esc": 0x29,
    "space": 0x2C,

    **NUMPAD_KEYS,
}


def char_to_hid(ch: str):
    """
    Translates a single character to (modifier, keycode).

    Example:
        'a' -> (MOD_NONE, 0x04)
        'A' -> (MOD_LSHFT, 0x04)
        '!' -> (MOD_LSHFT, 0x1E)
    """
    # 1. Handle Uppercase A-Z
    if len(ch) == 1 and "A" <= ch <= "Z":
        return MOD_LSHFT, KEY[ch.lower()]

    # 2. Handle Shifted symbols (!, @, #, etc.)
    if ch in SHIFTED:
        base_char, mod = SHIFTED[ch]
        return mod, KEY[base_char]

    # 3. Handle Standard Keys (Lower case, digits, space, etc.)
    if ch in KEY:
        return MOD_NONE, KEY[ch]

    # 4. Handle Special Keys (f1, up, etc.) if passed as strings
    if ch.lower() in SPECIAL_KEYS:
        return MOD_NONE, SPECIAL_KEYS[ch.lower()]

    return MOD_NONE, None
