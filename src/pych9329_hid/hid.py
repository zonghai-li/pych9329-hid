# hid.py
# @author zonghai@gmail.com
# @description High-level HID automation layer for CH9329 with
# smooth, human-like interpolation for movement and dragging.

import math
import time
import warnings

from .ch9329 import CH9329, MOUSE_BUTTON_LEFT, MOUSE_BUTTON_MIDDLE, MOUSE_BUTTON_RIGHT
from .keymap import MOD_MAP, NUMPAD_KEYS, char_to_hid


# Mapping for mouse buttons to CH9329 bitmask
MOUSE_BUTTON_MAP = {
    "left": MOUSE_BUTTON_LEFT,
    "right": MOUSE_BUTTON_RIGHT,
    "middle": MOUSE_BUTTON_MIDDLE,
}


class HIDController:
    """
    High-level HID Controller
    Ensures hardware-software synchronization via CH9329 protocol.

    Error Handling:
    - Failures from CH9329 layer propagate to caller
    - CH9329 returns False for soft errors (timeout, ACK error) with warning
    - CH9329 raises SerialTransportError for hard errors (transport failure)
    """

    def __init__(self, transport, screen_width=1920, screen_height=1080):
        """
        Args:
            transport: Initialized SerialTransport instance.
            screen_width (int): Logical width of the target display.
            screen_height (int): Logical height of the target display.
        """
        self._protocol = CH9329(transport)
        self._width = screen_width
        self._height = screen_height

        # --- Global Timing Configuration ---
        # Interval between atomic reports to prevent hardware buffer overflow
        self.dwelling_time = 0.0  # 0 ms default

        # Specific delay for multi-click actions (e.g., double clicks)
        self.double_click_interval = 0.08

        self.keypress_hold_time = 0.05  # Time to hold a key down during press()

        # Interval for smooth mouse movement steps
        self.move_interval = 0.04

        # Scroll sensitivity multiplier (physical detents per logical click)
        # Recommended: macOS 3-5, Windows 1-2
        self.scroll_multiplier = 3

        # --- Internal State Tracking ---
        self._mouse_btn_mask = 0x00
        self._mouse_x = 0
        self._mouse_y = 0
        self._held_modifiers = 0x00

        self._pressed_keys = []  # Tracks currently pressed non-modifier HID keycodes (ordered for deterministic reports)

        self.reset()  # Anchor cursor to (0,0)

    # -------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------

    def _clamp(self, val, min_val, max_val):
        """Restricts a value within a specified range."""
        return max(min_val, min(max_val, val))

    def _safe_delay(self, duration=None):
        """Unified sleep mechanism for hardware pacing."""
        t = duration if duration is not None else self.dwelling_time
        if t > 0:
            time.sleep(t)

    def _map_coords(self, x, y):
        """
        Maps logical pixel coordinates to HID Absolute range (0-4095).
        macOS requires precise mapping for the cursor to land on UI elements.
        
        """
       
        OFFSET = 0.5  # Half-pixel offset to avoid edge issues
        
        nx = int(self._clamp(x + OFFSET, 0, self._width - 1) * 4095 / (self._width - 1))
        ny = int(self._clamp(y + OFFSET, 0, self._height - 1) * 4095 / (self._height - 1))
        return nx, ny

    def _commit_mouse_state(self):
        """
        The Source of Truth: Synchronizes internal X, Y, and Button states
        to the hardware via the ABSOLUTE MOUSE command (0x04).
        """
        # print(self._mouse_x, self._mouse_y, self._mouse_btn_mask)

        ax, ay = self._map_coords(self._mouse_x, self._mouse_y)
        self._protocol.send_mouse_abs(ax, ay, buttons=self._mouse_btn_mask)

    # -------------------------------------------------
    # Keyboard Operations (Improved)
    # -------------------------------------------------
    def keyDown(self, key: str):
        """Presses and holds a keyboard key."""
        key_l = key.lower()

        # 1. If an explicit modifier key, persist it in `_held_modifiers`
        if key_l in MOD_MAP:
            self._held_modifiers |= MOD_MAP[key_l]
            # send the full current state
            self._protocol.send_keyboard(
                self._held_modifiers, list(self._pressed_keys)[:6]
            )
            self._safe_delay()
        else:
            # Preserve original `key` when converting to HID so we don't lose case
            mod, code = char_to_hid(key)
            if code:
                # Append ordinary key to the pressed list in order (avoid duplicates)
                if code not in self._pressed_keys:
                    self._pressed_keys.append(code)
                # When sending: combine persistent modifiers with this key's temporary modifier (e.g., Shift for uppercase)
                # Note: `mod` is not stored in `self._held_modifiers`
                self._protocol.send_keyboard(
                    self._held_modifiers | mod, list(self._pressed_keys)[:6]
                )
                self._safe_delay()

    def keyUp(self, key: str):
        """Releases only the specified key."""
        key_l = key.lower()

        if key_l in MOD_MAP:
            # Remove explicit persistent modifier
            self._held_modifiers &= ~MOD_MAP[key_l]
        else:
            mod, code = char_to_hid(key)
            if code in self._pressed_keys:
                self._pressed_keys.remove(code)

        # Regardless of what was released, sync the accurate persistent state
        self._protocol.send_keyboard(self._held_modifiers, list(self._pressed_keys)[:6])
        self._safe_delay()

    def releaseAllKey(self):
        """Emergency reset for all keyboard states."""
        self._held_modifiers = 0x00
        self._pressed_keys.clear()
        self._protocol.send_keyboard(0x00, [])
        self._safe_delay()

    def press(self, key: str):
        """Simulates a full key press: Down -> Wait -> Up."""
        self.keyDown(key)
        self._safe_delay(self.keypress_hold_time)
        self.keyUp(key)

    def write(self, text: str):
        """Types a string character by character with hardware pacing."""
        start = time.time()
        for char in text:
            self.press(char)
        elapsed = time.time() - start
        print(f"[HID] write() consumed {elapsed:.3f}s")
       

    def hotkey(self, *keys):
        """
        Simulates simultaneous key combination (e.g., cmd+space).
        """
        final_mod = 0
        final_codes = []

        for k in keys:
            k_orig = str(k)
            k_l = k_orig.lower()
            if k_l in MOD_MAP:
                final_mod |= MOD_MAP[k_l]
            else:
                # Preserve original casing for char_to_hid
                mod, code = char_to_hid(k_orig)
                # 'mod' can be 0 (MOD_NONE) which is valid!
                if code is not None:
                    if mod:
                        final_mod |= mod
                    # avoid duplicate keycodes in the final report
                    if code not in final_codes:
                        final_codes.append(code)

        if final_codes or final_mod:
            # Step 1: Send the modifiers first (macOS stability)
            if final_mod:
                self._protocol.send_keyboard(final_mod, [])
                self._safe_delay()

            # Step 2: Send modifiers + key codes
            self._protocol.send_keyboard(final_mod, final_codes)

            # Step 3: Hold
            self._safe_delay(self.keypress_hold_time)

            # Step 4: restore
            self._protocol.send_keyboard(
                self._held_modifiers, list(self._pressed_keys)[:6]
            )
            self._safe_delay()

    def numpadPress(self, key: str):
        """
        Presses a numpad key. You can normally use press() for numpad keys with 'num' prefix.
        For example, numpadPress('7') is equivalent to press('num7').
        """
        numkey = "num" + key
        if numkey in NUMPAD_KEYS:
            self.keyDown(numkey)
            self._safe_delay(self.keypress_hold_time)
            self.keyUp(numkey)
        else:
            warnings.warn(f"Invalid numpad key: {key}")

    def numpadWrite(self, text: str):
        """Types a string of numpad characters."""
        for char in text:
            self.numpadPress(char)

    # -------------------------------------------------
    # Mouse Button
    # On macOS, mouse button states must be sent via Absolute Mouse Frame,
    # as Relative Mouse Frame does not recognize button state changes.
    # -------------------------------------------------
    def mouseDown(self, button="left"):
        """Presses and holds the mouse button. Essential for dragging."""
        btn_mask = MOUSE_BUTTON_MAP.get(button.lower())
        if btn_mask:
            self._mouse_btn_mask |= btn_mask
            self._commit_mouse_state()
            self._safe_delay()

    def mouseUp(self, button="left"):
        """Releases the specified mouse button."""
        btn_mask = MOUSE_BUTTON_MAP.get(button.lower())
        if btn_mask:
            self._mouse_btn_mask &= ~btn_mask
            self._commit_mouse_state()
            self._safe_delay()

    def click(self, x=None, y=None, button="left", clicks=1):
        """Simulates mouse clicks at optional coordinates."""
        if x is not None and y is not None:
            self.moveTo(x, y)

        for i in range(clicks):
            self.mouseDown(button)
            self._safe_delay(self.keypress_hold_time)
            self.mouseUp(button)
            if i < clicks - 1:
                self._safe_delay(self.double_click_interval)

    def releaseMouseButton(self):
        """Releases all pressed mouse buttons."""
        self._mouse_btn_mask = 0x00
        self._commit_mouse_state()
        self._safe_delay()

    # -------------------------------------------------
    # Mouse Movement
    # -------------------------------------------------
    def moveTo(self, x, y, duration=0):
        """
        Moves the cursor to absolute logical coordinates with smoothing.
        If duration is 0, it jumps instantly.
        """
        # 1. Setup targets and clamp to screen boundaries
        start_x, start_y = self._mouse_x, self._mouse_y
        target_x = self._clamp(x, 0, self._width - 1)
        target_y = self._clamp(y, 0, self._height - 1)

        # 2. Instant jump logic
        if duration <= 0:
            self._mouse_x = target_x
            self._mouse_y = target_y
            self._commit_mouse_state()
            self._safe_delay()
            return

        # 3. Calculate distance
        dist_x = target_x - start_x
        dist_y = target_y - start_y

        # 4 Avoid redundant movement if already at target
        if abs(dist_x) < 0.1 and abs(dist_y) < 0.1:
            return

        # 5. Dynamic step calculation
        steps = max(1, int(duration / self.move_interval))

        for i in range(1, steps):
            # Ease-Out calculation: (1 - (1-t)^2)
            t = i / steps
            ease_t = 1 - (1 - t) ** 2

            self._mouse_x = start_x + dist_x * ease_t
            self._mouse_y = start_y + dist_y * ease_t

            t = time.time()
            self._commit_mouse_state()
            self._safe_delay(self.move_interval - (time.time() - t))

        # 6. Final frame: Precision landing
        self._mouse_x = target_x
        self._mouse_y = target_y
        self._commit_mouse_state()
        self._safe_delay()

    # -------------------------------------------------
    # Mouse Movement
    # When CH9329 sends relative movement commands on macOS, the distance moved
    # in logical pixels is not 1:1 mapped to dx, dy parameters; there is a non-linear
    # scaling relationship. Use moveTo to simulate moveRel.
    # -------------------------------------------------
    def moveRel(self, dx, dy, duration=0):
        self.moveTo(self._mouse_x + dx, self._mouse_y + dy, duration=duration)

    # -------------------------------------------------
    # Mouse Operations - Scrolling
    # -------------------------------------------------

    def scroll(self, clicks: int):
        """
        Simulates vertical scrolling, consistent with pyautogui.scroll().
        Positive = Scroll Up, Negative = Scroll Down.
        """
        if clicks == 0:
            return

        # Compute total physical steps (clicks * sensitivity)
        total_steps = abs(clicks) * self.scroll_multiplier
        direction = 1 if clicks > 0 else -1

        # Limit the maximum physical steps per operation to avoid long serial blocking at low baud rates
        # (e.g., 150 steps would take ~150 * 0.015s = 2.25s)
        total_steps = self._clamp(total_steps, 0, 150)

        for _ in range(total_steps):
            self._protocol.send_mouse_rel(
                dx=0, dy=0, buttons=self._mouse_btn_mask, wheel=direction
            )

            self._safe_delay()

    def hscroll(self, clicks: int):
        """
        Simulates horizontal scrolling (macOS Compatible).
        Positive = Scroll Right, Negative = Scroll Left.

        Note: Since CH9329 0x05 protocol lacks a horizontal wheel byte,
        we use the macOS standard 'Shift + Vertical Scroll' combo.
        This automatically uses self.scroll_multiplier for sensitivity.
        """
        if clicks == 0:
            return

        # 1. Physically press and hold Shift
        self.keyDown("shift")

        # 2. Call vertical scroll logic (OS interprets as horizontal when Shift is held)
        # This uses `self.scroll_multiplier` automatically
        self.scroll(clicks)

        # 3. Release Shift and restore state
        self.keyUp("shift")

    # -------------------------------------------------
    # Drag Operations (High-Level Actions)
    # -------------------------------------------------

    def dragTo(self, x, y):
        dx, dy = x - self._mouse_x, y - self._mouse_y
        self.dragRel(dx, dy)

    def dragRel(self, dx, dy):
        """
        Relative drag movement in logical pixels.

        Args:
            dx (float): Horizontal displacement in logical pixels
            dy (float): Vertical displacement in logical pixels
        """
        # 1. Calculate total steps (using ~4.62 pixel step size)
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return

        step_size = 4.62
        steps = max(1, math.ceil(distance / step_size))

        # 2. Calculate precise physical increments per step using floating-point
        # Using floating-point accumulation prevents directional drift even though
        # we send integers to the hardware
        float_step_x = dx / steps
        float_step_y = dy / steps

        # 3. Press and hold the mouse button
        self.mouseDown()

        # 4. Accumulation loop with remainder tracking
        accum_x, accum_y = 0.0, 0.0

        for i in range(steps):
            accum_x += float_step_x
            accum_y += float_step_y

            # Extract integer displacement for current step
            send_x = int(accum_x)
            send_y = int(accum_y)

            # Deduct sent portion, preserve remainder for next frame
            accum_x -= send_x
            accum_y -= send_y

            if send_x != 0 or send_y != 0:
                # Core operation: send relative displacement while button is held
                self._protocol.send_mouse_rel(send_x, send_y)
                # self._safe_delay()

        # 5. Release mouse button
        self.mouseUp()

        # 6. Sync internal logical coordinates
        self._mouse_x += dx
        self._mouse_y += dy

    # -------------------------------------------------
    # Hardware reset for cursor position
    # -------------------------------------------------
    def reset(self):
        """
        Physically anchors the cursor to (0,0) using Relative commands.
        Sends multiple large negative movements to ensure the cursor
        is trapped in the top-left corner.
        """
        # Push significantly further than screen resolution to ensure
        # cursor is trapped in top-left corner.
        iters = int(max(self._width, self._height) / 100) + 10

        for _ in range(iters):
            # We use raw hid call to avoid updating our internal logical x,y yet
            self._protocol.send_mouse_rel(dx=-127, dy=-127, buttons=0)
            self._safe_delay()

        # Now sync the logic to the physical reality
        self._mouse_x = 0
        self._mouse_y = 0

        self.releaseAllKey()  # Ensure clean state on init
        self.releaseMouseButton()

    def getDeviceInfo(self) -> dict:
        """
        Get device information.

        Returns:
            dict: Device information dictionary
        """
        return self._protocol.get_info()
