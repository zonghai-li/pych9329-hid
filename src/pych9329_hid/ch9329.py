# ch9329.py
# @author zonghai@gmail.com
# @description CH9329 protocol


import time
import warnings

from .transport import TransportTimeoutError


# Protocol Constants
FRAME_HEAD = b"\x57\xab"
ADDR_DEFAULT = 0x00

# Command Codes
CMD_GET_INFO = 0x01
CMD_SEND_KEY = 0x02
CMD_SEND_MS_REL = 0x05
CMD_SEND_MS_ABS = 0x04
CMD_GET_PARA_CFG = 0x08

# Mouse Buttons
MOUSE_BUTTON_LEFT = 0x01
MOUSE_BUTTON_RIGHT = 0x02
MOUSE_BUTTON_MIDDLE = 0x04

# Mouse Mode Flags
MOUSE_MODE_RELATIVE = 0x01
MOUSE_MODE_ABSOLUTE = 0x02

# Keyboard Constants
KEYBOARD_RESERVED_BYTE = 0x00
MAX_KEYCODES = 6

# Chip Version Constants
CHIP_VERSION_V1_0 = 0x30
CHIP_VERSION_V1_1 = 0x31

# USB Enumeration Status
USB_STATUS_DISCONNECTED = 0x00
USB_STATUS_CONNECTED = 0x01

# LED Status Bitmask
LED_MASK_NUM_LOCK = 0x01
LED_MASK_CAPS_LOCK = 0x02
LED_MASK_SCROLL_LOCK = 0x04

# ACK Frame Constants
ACK_FRAME_MIN_LENGTH = 6
ACK_STATUS_SUCCESS = 0x00

# Retry Constants
RETRY_COUNT = 3
RETRY_DELAY = 0.02  # seconds


class ACKError(Exception):
    """Raised when CH9329 returns an error response or verification fails."""

    pass


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
            self.t.read_all()
        except Exception:
            pass

    def _is_num_lock_on(self, led_status: int) -> bool:
        """Check if NUM LOCK LED is on."""
        return (led_status & LED_MASK_NUM_LOCK) != 0

    def _is_caps_lock_on(self, led_status: int) -> bool:
        """Check if CAPS LOCK LED is on."""
        return (led_status & LED_MASK_CAPS_LOCK) != 0

    def _is_scroll_lock_on(self, led_status: int) -> bool:
        """Check if SCROLL LOCK LED is on."""
        return (led_status & LED_MASK_SCROLL_LOCK) != 0

    def _is_usb_connected(self, usb_status: int) -> bool:
        """Check if USB is connected."""
        return usb_status == USB_STATUS_CONNECTED

    def _get_version_string(self, version: int) -> str:
        """Get version string from version byte."""
        if version == CHIP_VERSION_V1_0:
            return "V1.0"
        elif version == CHIP_VERSION_V1_1:
            return "V1.1"
        else:
            return f"Unknown (0x{version:02X})"

    def _decode_response(self, response: bytes, expected_cmd: int) -> bytes:
        """
        Decode and verify CH9329 response frame.

        Frame structure: HEAD(2) + ADDR(1) + CMD(1) + LEN(1) + DATA(N) + SUM(1)

        Args:
            response: Raw response bytes from transport.
            expected_cmd: Original command byte sent (without response bit).

        Returns:
            bytes: Response data payload if verification passes.

        Raises:
            ACKError: If frame verification fails or device returns error status.

        Response CMD format:
            - Normal response: Original CMD | 0x80
            - Error response: Original CMD | 0xC0
        """
        # Minimum frame length: HEAD(2) + ADDR(1) + CMD(1) + LEN(1) + SUM(1) = 6 bytes
        if len(response) < ACK_FRAME_MIN_LENGTH:
            raise ACKError(f"Frame too short: {len(response)} bytes (minimum 6)")

        # Check frame header
        if response[0:2] != FRAME_HEAD:
            raise ACKError(
                f"Invalid frame header: {response[0:2].hex()} (expected {FRAME_HEAD.hex()})"
            )

        # Parse frame fields
        addr = response[2]
        cmd = response[3]
        length = response[4]

        # Verify frame has enough bytes for data and checksum
        if 5 + length + 1 > len(response):
            raise ACKError(
                f"Length mismatch: LEN={length} but frame has {len(response)} bytes"
            )

        data = response[5 : 5 + length]
        checksum = response[5 + length]

        # Calculate and verify checksum using existing method
        # SUM = HEAD+ADDR+CMD+LEN+DATA (sum of all bytes except checksum itself)
        calculated_checksum = self._calculate_checksum(response[0 : 5 + length])
        if checksum != calculated_checksum:
            raise ACKError(
                f"Checksum mismatch: received 0x{checksum:02X}, calculated 0x{calculated_checksum:02X}"
            )

        # Determine response status
        expected_success_cmd = expected_cmd | 0x80
        expected_error_cmd = expected_cmd | 0xC0

        if cmd != expected_success_cmd:
            if cmd == expected_error_cmd:
                # Device returned error status
                error_status = data[0]
                raise ACKError(
                    f"Device returned error status 0x{error_status:02X} for CMD 0x{expected_cmd:02X}"
                )
            else:
                raise ACKError(
                    f"Unexpected command: 0x{cmd:02X} (expected 0x{expected_success_cmd:02X})"
                )

        # Return data payload
        return data

    def _send_frame(self, cmd: int, payload: bytes, expected_payload_length: int | None = None) -> bytes:
        """
        Constructs, sends a frame, and returns response data.
        
        Implements retry mechanism for transport timeouts and protocol errors.
        
        Args:
            cmd: Command byte.
            payload: Data payload.
            expected_response_length: Expected response length (None if unknown).

        Returns:
            bytes: Response data payload (None if fails after retries).

        Raises:
            TransportError: If transport error occurs (other than timeout).
            
        Note:
            - Transport timeouts (TransportTimeoutError) are retried up to RETRY_COUNT times
            - ACK errors (ACKError) are retried up to RETRY_COUNT times
            - Other transport errors are raised immediately
        """
        # Build Packet: HEAD(2) + ADDR(1) + CMD(1) + LEN(1) + DATA(N) + CS(1)
        frame = bytearray(FRAME_HEAD)
        frame.append(ADDR_DEFAULT)
        frame.append(cmd)
        frame.append(len(payload))
        frame.extend(payload)
        frame.append(self._calculate_checksum(frame))

        expected_length = expected_payload_length + 6 if expected_payload_length is not None else 70
        for attempt in range(RETRY_COUNT):
            # Clear stale data from buffer
            self._clear_buffer()

            # Send Packet
            try:
                self.t.write(frame)
            except TransportTimeoutError as e:
                warnings.warn(f"Transport timeout: {e}, re-send cmd...")
                if attempt < RETRY_COUNT - 1:
                    time.sleep(RETRY_DELAY)

                continue

            # read response
            response = self.t.read(expected_length)  

            if response and len(response) > 0:
                # Search for Frame Head in response
                head_idx = response.find(FRAME_HEAD)
                if head_idx >= 0:
                    ack = response[head_idx:]
                    try:
                        data = self._decode_response(ack, cmd)
                        return data
                    except ACKError as e:
                        warnings.warn(f"ack error: {e}, re-send cmd...")
                else:
                    warnings.warn("Frame head not found in response, re-send cmd...")
            else:
                warnings.warn("Empty response, re-send cmd...")

            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)

        warnings.warn(f"Failed to send CMD 0x{cmd:02X} after {RETRY_COUNT} retries.")
        return None

    # -------------------------------------------------
    # Device Info API
    # -------------------------------------------------

    def get_info(self):
        """
        Retrieves device information from CH9329 chip.

        Returns:
            dict with keys:
                - 'version': str, chip version string (e.g., "V1.0", "V1.1")
                - 'usb_connected': bool, True if USB is connected
                - 'num_lock_on': bool, True if NUM LOCK LED is on
                - 'caps_lock_on': bool, True if CAPS LOCK LED is on
                - 'scroll_lock_on': bool, True if SCROLL LOCK LED is on

        Returns None if command fails after retries.

        Raises:
            SerialTransportError: If transport error occurs.
        """
        data = self._send_frame(CMD_GET_INFO, b"", expected_payload_length=3)

        if data is None:
            return None

        if len(data) < 3:
            warnings.warn(f"get_info response data {data} length {len(data)} < 3")
            return None

        return {
            "version": self._get_version_string(data[0]),
            "usb_connected": self._is_usb_connected(data[1]),
            "num_lock_on": self._is_num_lock_on(data[2]),
            "caps_lock_on": self._is_caps_lock_on(data[2]),
            "scroll_lock_on": self._is_scroll_lock_on(data[2]),
        }

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

        resp = self._send_frame(CMD_SEND_KEY, payload, expected_payload_length=1)
        return resp is not None and len(resp) > 0 and resp[0] == ACK_STATUS_SUCCESS

    # -------------------------------------------------
    # Mouse API
    # -------------------------------------------------

    def send_mouse_rel(
        self, dx: int = 0, dy: int = 0, buttons: int = 0, wheel: int = 0
    ) -> bool:
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

        payload = bytes(
            [
                MOUSE_MODE_RELATIVE,
                buttons & 0x07,
                self._to_signed_char(dx),
                self._to_signed_char(dy),
                self._to_signed_char(wheel),
            ]
        )

        resp = self._send_frame(CMD_SEND_MS_REL, payload, expected_payload_length=1)
        return resp is not None and len(resp) > 0 and resp[0] == ACK_STATUS_SUCCESS

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

        payload = bytes(
            [
                MOUSE_MODE_ABSOLUTE,
                buttons & 0x07,
                x & 0xFF,
                (x >> 8) & 0xFF,
                y & 0xFF,
                (y >> 8) & 0xFF,
                self._to_signed_char(wheel),
            ]
        )

        resp = self._send_frame(CMD_SEND_MS_ABS, payload, expected_payload_length=1)
        return resp is not None and len(resp) > 0 and resp[0] == ACK_STATUS_SUCCESS
