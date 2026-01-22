# ch9329.py
# @author zonghai@gmail.com
# @description CH9329 protocol


import time
import warnings

# Protocol Constants
FRAME_HEAD    = b'\x57\xAB'
ADDR_DEFAULT  = 0x00

# Command Codes
CMD_GET_INFO     = 0x01
CMD_SEND_KEY     = 0x02
CMD_SEND_MS_REL  = 0x05
CMD_SEND_MS_ABS  = 0x04
CMD_GET_PARA_CFG = 0x08

# Mouse Buttons
MOUSE_BUTTON_LEFT   = 0x01
MOUSE_BUTTON_RIGHT  = 0x02
MOUSE_BUTTON_MIDDLE = 0x04

# Mouse Mode Flags
MOUSE_MODE_RELATIVE = 0x01
MOUSE_MODE_ABSOLUTE = 0x02

# Keyboard Constants
KEYBOARD_RESERVED_BYTE = 0x00
MAX_KEYCODES = 6

# ACK Frame Constants
ACK_FRAME_MIN_LENGTH = 6
ACK_STATUS_SUCCESS = 0x00

# Retry Constants
ACK_TIMEOUT = 0.05  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 0.02  # seconds


class CH9329:
    """
    Core implementation of CH9329 serial protocol.
    Provides reliable frame transmission with ACK verification.
    Keymap
    refer to keymap.py

    Error Handling Strategy:
    - Soft errors (ACK errors, timeouts): Return False with warning
    - Hard errors (transport failure): Raise SerialTransportError
    """

    def __init__(self, transport):
        """
        Args:
            transport: An instance of SerialTransport providing write() and read().
        """
        self.t = transport

    def _clamp(self, v: int, min_val: int, max_val: int) -> int:
        """Clamp value to range [min_val, max_val]."""
        return max(min_val, min(max_val, v))

    def _to_signed_char(self, v: int) -> int:
        """Convert integer to signed 8-bit value (-127 to 127)."""
        v = self._clamp(v, -127, 127)
        return v & 0xFF 

    def _calculate_checksum(self, data: bytes) -> int:
        """
        CH9329 Checksum: Sum of all bytes from Head to Data, modulo 256.
        """
        return sum(data) & 0xFF

    def _clear_buffer(self) -> None:
        """Clear any stale data from the serial buffer."""
        try:
            while self.t.read(128):
                pass
        except Exception:
            pass

    def _send_frame(self, cmd: int, payload: bytes) -> bool:
        """
        Constructs, sends a frame, and validates the ACK from hardware.
        
        Args:
            cmd: Command byte.
            payload: Data payload.
        
        Returns:
            True if successful.
        
        Raises:
            SerialTransportError: If transport error occurs.
        """
        # Build Packet: HEAD(2) + ADDR(1) + CMD(1) + LEN(1) + DATA(N) + CS(1)
        frame = bytearray(FRAME_HEAD)
        frame.append(ADDR_DEFAULT)
        frame.append(cmd)
        frame.append(len(payload))
        frame.extend(payload)
        frame.append(self._calculate_checksum(frame))

        for attempt in range(RETRY_COUNT):
            # Clear stale data from buffer
            self._clear_buffer()
            
            # Send Packet
            self.t.write(frame)

            # Poll for ACK
            start_time = time.time()
            while (time.time() - start_time) < ACK_TIMEOUT:
                response = self.t.read()
                
                if not response:
                    continue
                
                # Search for Frame Head in response
                head_idx = response.find(FRAME_HEAD)
                if head_idx != -1 and len(response) >= head_idx + ACK_FRAME_MIN_LENGTH:
                    res_cmd = response[head_idx + 3]
                    res_status = response[head_idx + 5]
                    
                    # ACK CMD is always (Original CMD | 0x80)
                    if res_cmd == (cmd | 0x80):
                        if res_status == ACK_STATUS_SUCCESS:
                            return True
                        else:
                            # Hardware error (e.g., buffer full or invalid command)
                            warnings.warn(f"Received ACK error status 0x{res_status:02X} for CMD 0x{cmd:02X}, retrying...")
                            break
            
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)

        warnings.warn(f"Failed to receive ACK for CMD 0x{cmd:02X} after {RETRY_COUNT} retries.")
        return False

    # -------------------------------------------------
    # Keyboard API
    # -------------------------------------------------

    def send_keyboard(self, modifier: int, keycodes: list) -> bool:
        """
        Sends a standard 8-byte USB HID keyboard report.
        
        Args:
            modifier: Bitmask (Shift, Ctrl, etc.) - must be 0-0xFF.
            keycodes: List of up to 6 HID keycodes (0-0xFF each).
        
        Returns:
            True if successful.
        
        Raises:
            SerialTransportError: If transport error occurs.
            ValueError: If parameters are invalid.
        """
        if not 0 <= modifier <= 0xFF:
            raise ValueError(f"modifier must be 0-0xFF, got {modifier}")
        
        if len(keycodes) > MAX_KEYCODES:
            raise ValueError(f"keycodes can have at most {MAX_KEYCODES} elements")
        
        for i, keycode in enumerate(keycodes):
            if not isinstance(keycode, int) or not 0 <= keycode <= 0xFF:
                raise ValueError(f"keycode[{i}] must be 0-0xFF, got {keycode}")

        # Ensure exactly 6 keycodes in the payload
        keys = (keycodes[:6] + [0] * 6)[:6]
        payload = bytes([modifier, KEYBOARD_RESERVED_BYTE] + keys)

        return self._send_frame(CMD_SEND_KEY, payload)

    # -------------------------------------------------
    # Mouse API
    # -------------------------------------------------

    def send_mouse_rel(self, dx: int = 0, dy: int = 0, buttons: int = 0, wheel: int = 0) -> bool:
        """
        Relative mouse movement. Values: -127 to 127.
        
        Args:
            dx: X movement (-127 to 127).
            dy: Y movement (-127 to 127).
            buttons: Button bitmask (0-0x07).
            wheel: Wheel movement (-127 to 127).
        
        Returns:
            True if successful.
        
        Raises:
            SerialTransportError: If transport error occurs.
            ValueError: If parameters are invalid.
        """
        if not 0 <= buttons <= 0x07:
            raise ValueError(f"buttons must be 0-0x07, got {buttons}")

        payload = bytes([
            MOUSE_MODE_RELATIVE,
            buttons & 0x07,
            self._to_signed_char(dx),
            self._to_signed_char(dy),
            self._to_signed_char(wheel)
        ])

        return self._send_frame(CMD_SEND_MS_REL, payload)

    def send_mouse_abs(self, x: int, y: int, buttons: int = 0, wheel: int = 0) -> bool:
        """
        Absolute mouse movement (0-4095).
        Note: x and y are Little-Endian.
        
        Args:
            x: X coordinate (0-4095).
            y: Y coordinate (0-4095).
            buttons: Button bitmask (0-0x07).
            wheel: Wheel movement (-127 to 127).
        
        Returns:
            True if successful, False if timeout or ACK error.
        
        Raises:
            SerialTransportError: If transport error occurs.
            ValueError: If parameters are invalid.
        """
        if not 0 <= buttons <= 0x07:
            raise ValueError(f"buttons must be 0-0x07, got {buttons}")

        x = self._clamp(x, 0, 4095)
        y = self._clamp(y, 0, 4095)

        payload = bytes([
            MOUSE_MODE_ABSOLUTE,
            buttons & 0x07,
            x & 0xFF, (x >> 8) & 0xFF,
            y & 0xFF, (y >> 8) & 0xFF,
            self._to_signed_char(wheel)
        ])
        return self._send_frame(CMD_SEND_MS_ABS, payload)
