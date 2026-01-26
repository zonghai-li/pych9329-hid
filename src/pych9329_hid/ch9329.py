# ch9329.py
# @author zonghai@gmail.com
# @description CH9329 protocol


import time
import warnings

from .transport import TransportTimeoutError
from .config import CH9329Config


# Protocol Constants
FRAME_HEAD = b"\x57\xab"
ADDR_DEFAULT = 0x00

# Command Codes
CMD_GET_INFO = 0x01
CMD_SEND_KEY = 0x02
CMD_SEND_MS_REL = 0x05
CMD_SEND_MS_ABS = 0x04
CMD_GET_PARA_CFG = 0x08
CMD_SET_PARA_CFG = 0x09
CMD_GET_USB_STRING = 0x0A
CMD_SET_USB_STRING = 0x0B
CMD_SET_DEFAULT_CFG = 0x0C
CMD_RESET = 0x0F

# USB String Types
USB_STRING_VENDOR = 0x00
USB_STRING_PRODUCT = 0x01
USB_STRING_SERIAL = 0x02

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

# USB Enumeration Status
USB_STATUS_DISCONNECTED = 0x00
USB_STATUS_CONNECTED = 0x01

# LED Status Bitmask
LED_MASK_NUM_LOCK = 0x01
LED_MASK_CAPS_LOCK = 0x02
LED_MASK_SCROLL_LOCK = 0x04

ACK_FRAME_MIN_LENGTH = 7

ACK_STATUS_SUCCESS = 0x00
ACK_STATUS_BAD_PARAM = 0xE5

ACK_STATUS_MAP = {
    ACK_STATUS_SUCCESS: "Command success (命令执行成功)",
    0xE1: "(Chip Side)Serial receive timeout (串口接收字节超时)",
    0xE2: "(Request) Packet header error (包头错误)",
    0xE3: "(Request) Unknown command (命令码错误)",
    0xE4: "(Request) Checksum mismatch (校验和错误)",
    0xE5: "(Request) Invalid parameter (参数错误)",
    0xE6: "(Chip Side) Execution failed (帧正常但执行失败)",
}

# Retry Constants
RETRY_COUNT = 3
RETRY_DELAY = 0.02  # seconds


class ACKError(Exception):
    """Raised when CH9329 returns an error response or verification fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

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
        """Get version string from version byte.

        Version byte format: 0x30 = V1.0, 0x31 = V1.1, 0x32 = V1.2, ...
        """
        if 0x30 <= version <= 0x39:
            minor_version = version - 0x30
            return f"V1.{minor_version}"
        return f"Unknown (0x{version:02X})"

    def _decode_and_verify(
        self,
        response: bytes,
        expected_cmd: int,
        expected_payload_length: int | None = None,
    ) -> bytes:
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
        if 6 + length > len(response):
            raise ACKError(
                f"Partial response: expected={length + 6} but frame has {len(response)} bytes"
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

        expected_success_cmd = expected_cmd | 0x80
        expected_error_cmd = expected_cmd | 0xC0

        if cmd == expected_error_cmd:
            # Device returned error status
            error_status = data[0]
            raise ACKError(
                f"Device returned status 0x{error_status:02X}-{ACK_STATUS_MAP.get(error_status, 'Unknown')} for CMD 0x{expected_cmd:02X}",
                error_status,
            )

        if cmd != expected_success_cmd:
            raise ACKError(
                f"Unexpected command: 0x{cmd:02X} (expected 0x{expected_success_cmd:02X})"
            )

        # Verify payload length if specified
        if expected_payload_length is not None and length != expected_payload_length:
            raise ACKError(
                f"Payload size mismatch: LEN={length} but expected {expected_payload_length}"
            )

        # Return data payload
        return data

    def _send_frame(
        self, cmd: int, payload: bytes, expected_payload_length: int | None = None
    ) -> bytes:
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

        expected_length = (
            expected_payload_length + 6 if expected_payload_length is not None else 70
        )

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
                        data = self._decode_and_verify(ack, cmd)
                        return data
                    except ACKError as e:
                        warnings.warn(f"Ack error: {e}, {attempt + 1}/{RETRY_COUNT}")
                        if (
                            e.status_code == ACK_STATUS_BAD_PARAM
                        ):  # retry would make difference
                            return None
                else:
                    warnings.warn(
                        f"Bad response: no frame head, {attempt + 1}/{RETRY_COUNT}"
                    )
            else:
                warnings.warn(f"Empty response, {attempt + 1}/{RETRY_COUNT}")

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

        return {
            "version": self._get_version_string(data[0]),
            "usb_connected": self._is_usb_connected(data[1]),
            "num_lock_on": self._is_num_lock_on(data[2]),
            "caps_lock_on": self._is_caps_lock_on(data[2]),
            "scroll_lock_on": self._is_scroll_lock_on(data[2]),
        }

    # -------------------------------------------------
    # Parameter Config API
    # -------------------------------------------------

    def get_config(self) -> CH9329Config | None:
        """
        Retrieves current parameter configuration from CH9329 chip.

        Returns:
            CH9329Config object containing configuration parameters, or None if command fails.

        Raises:
            SerialTransportError: If transport error occurs.

        Protocol Specification:
            - Command: CMD_GET_PARA_CFG (0x08)
            - Response: 50 bytes of configuration data
            - Response command: CMD_GET_PARA_CFG_RESPONSE (0x88)
        """
        # Send CMD_GET_PARA_CFG with empty payload
        data = self._send_frame(CMD_GET_PARA_CFG, b"", expected_payload_length=50)

        if data is None:
            return None

        return CH9329Config(data)

    def set_config(self, config: CH9329Config) -> bool:
        """
        Sets parameter configuration on CH9329 chip.

        Args:
            config: CH9329Config object containing configuration parameters.

        Returns:
            True if successful, False if command fails.

        Raises:
            SerialTransportError: If transport error occurs.
            ValueError: If configuration parameters are invalid.

        Protocol Specification:
            - Command: CMD_SET_PARA_CFG (0x09)
            - Payload: 50 bytes of configuration data
            - Response command: CMD_SET_PARA_CFG_RESPONSE (0x89)

        Important Notes:
            - mode valid range: 0x00-0x03 (software modes only)
            - Serial mode valid range: 0x00-0x02 (software modes only)
            - Configuration takes effect after next power cycle
        """
        # Validate configuration parameters using the config object's validation method
        config.validate()

        # Convert configuration to 50-byte format
        config_data = config.to_bytes()

        # Send CMD_SET_PARA_CFG with configuration data
        resp = self._send_frame(
            CMD_SET_PARA_CFG, config_data, expected_payload_length=1
        )
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS

    def set_config_to_default(self) -> bool:
        """
        Restores chip configuration and string configuration to factory default settings.

        Returns:
            True if successful, False if command fails.

        Raises:
            SerialTransportError: If transport error occurs.

        Protocol Specification:
            - Command: CMD_SET_DEFAULT_CFG (0x0C)
            - Payload: Empty (no parameters)
            - Response command: CMD_SET_DEFAULT_CFG_RESPONSE (0x8C)
            - Response: 1 byte execution status

        Important Notes:
            - Restores both parameter configuration and string configuration
            - Configuration takes effect after next power cycle
            - Default settings include:
                - mode: Hardware mode 0 (0x80) - Keyboard+Mouse
                - Serial mode: Hardware mode 0 (0x80) - Protocol mode
                - Baud rate: 9600 bps
                - VID: 0x1A86, PID: 0xE129
                - Packet interval: 3ms
        """
        # Send CMD_SET_DEFAULT_CFG with empty payload
        resp = self._send_frame(CMD_SET_DEFAULT_CFG, b"", expected_payload_length=1)

        # Check if command was successful (ACK status 0x00)
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS

    # -------------------------------------------------
    # USB Descriptor
    # -------------------------------------------------

    def get_usb_descriptor(self, type: int) -> str | None:
        """
        Retrieves USB string descriptor from CH9329 chip.

        Args:
            type: USB string type:
                - USB_STRING_VENDOR (0x00): Vendor string descriptor
                - USB_STRING_PRODUCT (0x01): Product string descriptor
                - USB_STRING_SERIAL (0x02): Serial number string descriptor

        Returns:
            String descriptor content, or None if command fails.

        Raises:
            SerialTransportError: If transport error occurs.
            ValueError: If string_type is invalid.

        Protocol Specification:
            - Command: CMD_GET_USB_STRING (0x0A)
            - Payload: 1 byte string type
            - Response command: CMD_GET_USB_STRING_RESPONSE (0x8A)
            - Response: 2+N bytes (string type + string length + N bytes string data)
            - String length valid range: 0-23

        Important Notes:
            - String is decoded as ASCII
            - Only ASCII characters (0-127) are supported
            - Invalid ASCII data will return None
        """
        if type not in [USB_STRING_VENDOR, USB_STRING_PRODUCT, USB_STRING_SERIAL]:
            raise ValueError(
                f"string_type must be 0x00 (vendor), 0x01 (product), or 0x02 (serial), got 0x{type:02X}"
            )

        # Send CMD_GET_USB_STRING with string type parameter
        payload = bytes([type])
        data = self._send_frame(
            CMD_GET_USB_STRING, payload, expected_payload_length=None
        )

        if data is None:
            return None

        # Parse response: string_type(1) + string_length(1) + string_data(N)
        if len(data) < 2:
            warnings.warn(f"Invalid response length: {len(data)} bytes (minimum 2)")
            return None

        resp_type = data[0]
        length = data[1]

        # Verify string type matches request
        if resp_type != type:
            warnings.warn(
                f"String type mismatch: requested 0x{type:02X}, got 0x{resp_type:02X}"
            )
            return None

        # Verify string length is within valid range
        if length > 23:
            warnings.warn(f"Invalid string length: {length} (maximum 23)")
            return None

        # Extract string data
        string_data = data[2 : 2 + length]

        # Try decode as ASCII
        try:
            return string_data.decode("ascii")
        except UnicodeDecodeError:
            return str(string_data)

    def set_usb_descriptor(self, type: int, desc: str) -> bool:
        """
        Sets USB string descriptor on CH9329 chip.

        Args:
            type: USB string type:
                - USB_STRING_VENDOR (0x00): Vendor string descriptor
                - USB_STRING_PRODUCT (0x01): Product string descriptor
                - USB_STRING_SERIAL (0x02): Serial number string descriptor
            desc: String content to set (maximum 23 bytes when encoded as ASCII)

        Returns:
            True if successful, False if command fails.

        Raises:
            SerialTransportError: If transport error occurs.
            ValueError: If string_type is invalid or string is too long.

        Protocol Specification:
            - Command: CMD_SET_USB_STRING (0x0B)
            - Payload: 2+N bytes (string type + string length + N bytes string data)
            - Response command: CMD_SET_USB_STRING_RESPONSE (0x8B)
            - Response: 1 byte execution status
            - String length valid range: 0-23

        Important Notes:
            - String is encoded as ASCII before transmission
            - String length is measured in bytes, not characters
            - Maximum 23 bytes when encoded as ASCII
            - Only ASCII characters (0-127) are supported
            - Configuration takes effect after next power cycle
        """
        if type not in [USB_STRING_VENDOR, USB_STRING_PRODUCT, USB_STRING_SERIAL]:
            raise ValueError(
                f"string_type must be 0x00 (vendor), 0x01 (product), or 0x02 (serial), got 0x{type:02X}"
            )

        # Encode string as ASCII
        try:
            data = desc.encode("ascii")
        except UnicodeEncodeError as e:
            raise ValueError(f"String contains non-ASCII characters: {e}")

        length = len(data)

        # Verify string length is within valid range
        if length > 23:
            raise ValueError(
                f"String too long: {length} bytes (maximum 23 bytes when encoded as ASCII)"
            )

        # Build payload: string_type(1) + string_length(1) + string_data(N)
        payload = bytes([type, length]) + data

        # Send CMD_SET_USB_STRING with payload
        resp = self._send_frame(CMD_SET_USB_STRING, payload, expected_payload_length=1)
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS

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
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS

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
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS

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
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS

    # -------------------------------------------------
    # Reset
    # -------------------------------------------------

    def chip_reset(self) -> bool:
        """
        Performs software reset on CH9329 chip.

        Returns:
            True if successful, False if command fails.

        Raises:
            SerialTransportError: If transport error occurs.

        Protocol Specification:
            - Command: CMD_RESET (0x0F)
            - Payload: Empty (no parameters)
            - Response command: CMD_RESET_RESPONSE (0x8F)
            - Response: 1 byte execution status

        Important Notes:
            - Performs software reset on CH9329 chip
            - All registers and configurations are reset to default values
            - Communication may be temporarily interrupted during reset
            - Reset takes approximately 100-200ms to complete
        """
        # Send CMD_RESET with empty payload
        resp = self._send_frame(CMD_RESET, b"", expected_payload_length=1)

        # Check if command was successful (ACK status 0x00)
        return resp is not None and resp[0] == ACK_STATUS_SUCCESS
