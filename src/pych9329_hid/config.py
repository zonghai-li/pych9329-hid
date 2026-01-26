# config.py
# @author zonghai@gmail.com
# @description CH9329 configuration data structure and constants


# Configuration Constants
CHIP_MODE_SW_COMPOSITE = 0x00  # Keyboard+Mouse
CHIP_MODE_SW_KEYBOARD = 0x01  # Keyboard only
CHIP_MODE_SW_MOUSE = 0x02  # Mouse only
CHIP_MODE_SW_CUSTOM_HID = 0x03  # Custom HID

CHIP_MODE_HW_COMPOSITE = 0x80  # Keyboard+Mouse (MODE1=H, MODE0=H)
CHIP_MODE_HW_KEYBOARD = 0x81  # Keyboard only (MODE1=H, MODE0=L)
CHIP_MODE_HW_MOUSE = 0x82  # Mouse only (MODE1=L, MODE0=H)
CHIP_MODE_HW_CUSTOM_HID = 0x83  # Custom HID (MODE1=L, MODE0=L)

SERIAL_MODE_SW_PROTOCOL = 0x00  # Protocol mode
SERIAL_MODE_SW_ASCII = 0x01  # ASCII mode
SERIAL_MODE_SW_TRANSPARENT = 0x02  # Transparent mode

SERIAL_MODE_HW_PROTOCOL = 0x80  # Protocol mode (CFG1=H, CFG0=H)
SERIAL_MODE_HW_ASCII = 0x81  # ASCII mode (CFG1=H, CFG0=L)
SERIAL_MODE_HW_TRANSPARENT = 0x82  # Transparent mode (CFG1=L, CFG0=H)

ENABLE_CUSTOM_DESCRIPTOR = 0x80  # Bit 7: Enable custom string descriptor
ENABLE_VENDOR_DESCRIPTOR = 0x04  # Bit 2: Enable custom vendor string descriptor
ENABLE_PRODUCT_DESCRIPTOR = 0x02  # Bit 1: Enable custom product string descriptor
ENABLE_SERIAL_NO = 0x01  # Bit 0: Enable custom serial number string descriptor

# Valid Baud Rates
VALID_BAUDRATES = (9600, 19200, 38400, 57600, 115200)

# Mode name mappings
CHIP_MODE_NAMES = {
    CHIP_MODE_SW_COMPOSITE: "Keyboard+Mouse (Software)",
    CHIP_MODE_SW_KEYBOARD: "Keyboard only (Software)",
    CHIP_MODE_SW_MOUSE: "Mouse only (Software)",
    CHIP_MODE_SW_CUSTOM_HID: "Custom HID (Software)",
    CHIP_MODE_HW_COMPOSITE: "Keyboard+Mouse (Hardware)",
    CHIP_MODE_HW_KEYBOARD: "Keyboard only (Hardware)",
    CHIP_MODE_HW_MOUSE: "Mouse only (Hardware)",
    CHIP_MODE_HW_CUSTOM_HID: "Custom HID (Hardware)",
}

SERIAL_MODE_NAMES = {
    SERIAL_MODE_SW_PROTOCOL: "Protocol mode (Software)",
    SERIAL_MODE_SW_ASCII: "ASCII mode (Software)",
    SERIAL_MODE_SW_TRANSPARENT: "Transparent mode (Software)",
    SERIAL_MODE_HW_PROTOCOL: "Protocol mode (Hardware)",
    SERIAL_MODE_HW_ASCII: "ASCII mode (Hardware)",
    SERIAL_MODE_HW_TRANSPARENT: "Transparent mode (Hardware)",
}


class CH9329Config:
    """Configuration data structure for CH9329 chip."""

    def __init__(self, data: bytes):
        """
        Initialize configuration from 50-byte response data.

        Args:
            data: 50-byte configuration data from CMD_GET_PARA_CFG response.
        """
        if len(data) != 50:
            raise ValueError(
                f"Configuration data must be 50 bytes, got {len(data)} bytes"
            )

        self._data = bytearray(data)  # Store as bytearray for in-place modification

        # No parsing - only maintain raw data

    def __str__(self):
        """Return string representation."""
        chip_mode = self.chip_mode
        serial_mode = self.serial_mode

        work_mode_str = CHIP_MODE_NAMES.get(chip_mode, f"Unknown (0x{chip_mode:02X})")
        serial_mode_str = SERIAL_MODE_NAMES.get(
            serial_mode, f"Unknown (0x{serial_mode:02X})"
        )

        lines = [
            "CH9329Config:",
            f"  Work Mode: {work_mode_str}",
            f"  Serial Mode: {serial_mode_str}",
            f"  Address: 0x{self.address:02X}",
            f"  Baud Rate: {self.baudrate}",
            f"  Packet Interval: {self.packet_interval}ms",
            f"  VID: 0x{self.vid:04X}",
            f"  PID: 0x{self.pid:04X}",
            f"  Keyboard Submit Interval: {self.keyboard_submission_interval}ms",
            f"  Keyboard Release Delay: {self.keyboard_release_delay}ms",
            f"  Auto Enter Flag: {self.auto_enter_flag}",
            f"  Enter Characters: {self.enter_characters.hex()}",
            f"  Filter Strings: {self.filter_strings.hex()}",
            f"  Custom Descriptor Enable: {self.custom_descriptor_enable}",
            f"  Keyboard Fast Submission: {self.keyboard_fast_submission}",
        ]

        return "\n".join(lines)

    def __repr__(self):
        """Return detailed string representation."""
        return f"CH9329Config(data={self._data.hex()})"

    def to_bytes(self) -> bytes:
        """Convert configuration to 50-byte format for sending to chip."""
        return bytes(self._data)

    @property
    def chip_mode(self) -> int:
        """Get work mode (0x00-0x03 or 0x80-0x83)."""
        return self._data[0]

    @chip_mode.setter
    def chip_mode(self, value: int) -> None:
        """Set work mode."""
        if not (0x00 <= value <= 0x03 or 0x80 <= value <= 0x83):
            raise ValueError(
                f"Work mode must be 0x00-0x03 (software) or 0x80-0x83 (hardware), got 0x{value:02X}"
            )
        self._data[0] = value

    @property
    def serial_mode(self) -> int:
        """Get serial mode (0x00-0x02 or 0x80-0x82)."""
        return self._data[1]

    @serial_mode.setter
    def serial_mode(self, value: int) -> None:
        """Set serial mode."""
        if not (0x00 <= value <= 0x02 or 0x80 <= value <= 0x82):
            raise ValueError(
                f"Serial mode must be 0x00-0x02 (software) or 0x80-0x82 (hardware), got 0x{value:02X}"
            )
        self._data[1] = value

    @property
    def address(self) -> int:
        """Get serial address (0x00-0xFF)."""
        return self._data[2]

    @address.setter
    def address(self, value: int) -> None:
        """Set serial address."""
        if not 0x00 <= value <= 0xFF:
            raise ValueError(f"Address must be 0x00-0xFF, got 0x{value:02X}")
        self._data[2] = value

    @property
    def baudrate(self) -> int:
        """Get baud rate (9600, 19200, 38400, 57600, 115200)."""
        return int.from_bytes(self._data[3:7], byteorder="big")

    @baudrate.setter
    def baudrate(self, value: int) -> None:
        """Set baud rate."""
        if value not in VALID_BAUDRATES:
            raise ValueError(f"Baud rate must be one of {VALID_BAUDRATES}, got {value}")
        self._data[3:7] = value.to_bytes(4, byteorder="big")

    @property
    def packet_interval(self) -> int:
        """Get packet interval (0x0000-0xFFFF)."""
        return int.from_bytes(self._data[9:11], byteorder="big")

    @packet_interval.setter
    def packet_interval(self, value: int) -> None:
        """Set packet interval."""
        if not 0x0000 <= value <= 0xFFFF:
            raise ValueError(
                f"Packet interval must be 0x0000-0xFFFF, got 0x{value:04X}"
            )
        self._data[9:11] = value.to_bytes(2, byteorder="big")

    @property
    def vid(self) -> int:
        """Get USB VID (0x0000-0xFFFF)."""
        return int.from_bytes(self._data[11:13], byteorder="big")

    @vid.setter
    def vid(self, value: int) -> None:
        """Set USB VID."""
        self._data[11:13] = value.to_bytes(2, byteorder="big")

    @property
    def pid(self) -> int:
        """Get USB PID (0x0000-0xFFFF)."""
        return int.from_bytes(self._data[13:15], byteorder="big")

    @pid.setter
    def pid(self, value: int) -> None:
        """Set USB PID."""
        self._data[13:15] = value.to_bytes(2, byteorder="big")

    @property
    def keyboard_submission_interval(self) -> int:
        """Get keyboard upload interval (0x0000-0xFFFF)."""
        return int.from_bytes(self._data[15:17], byteorder="big")

    @keyboard_submission_interval.setter
    def keyboard_submission_interval(self, value: int) -> None:
        """Set keyboard upload interval."""
        if not 0x0000 <= value <= 0xFFFF:
            raise ValueError(
                f"Keyboard interval must be 0x0000-0xFFFF, got 0x{value:04X}"
            )
        self._data[15:17] = value.to_bytes(2, byteorder="big")

    @property
    def keyboard_release_delay(self) -> int:
        """Get keyboard release delay (0x0000-0xFFFF)."""
        return int.from_bytes(self._data[17:19], byteorder="big")

    @keyboard_release_delay.setter
    def keyboard_release_delay(self, value: int) -> None:
        """Set keyboard release delay."""
        if not 0x0000 <= value <= 0xFFFF:
            raise ValueError(
                f"Keyboard release delay must be 0x0000-0xFFFF, got 0x{value:04X}"
            )
        self._data[17:19] = value.to_bytes(2, byteorder="big")

    @property
    def auto_enter_flag(self) -> int:
        """Get auto enter flag (0x00-0x01)."""
        return self._data[19]

    @auto_enter_flag.setter
    def auto_enter_flag(self, value: int) -> None:
        """Set auto enter flag."""
        if not 0x00 <= value <= 0x01:
            raise ValueError(f"Auto enter flag must be 0x00-0x01, got 0x{value:02X}")
        self._data[19] = value

    @property
    def enter_characters(self) -> bytes:
        """Get enter characters (8 bytes)."""
        return bytes(self._data[20:28])

    @enter_characters.setter
    def enter_characters(self, value: bytes) -> None:
        """Set enter characters."""
        if len(value) != 8:
            raise ValueError(
                f"Enter characters must be 8 bytes, got {len(value)} bytes"
            )
        self._data[20:28] = value

    @property
    def filter_strings(self) -> bytes:
        """Get filter strings (8 bytes)."""
        return bytes(self._data[28:36])

    @filter_strings.setter
    def filter_strings(self, value: bytes) -> None:
        """Set filter strings."""
        if len(value) != 8:
            raise ValueError(f"Filter strings must be 8 bytes, got {len(value)} bytes")
        self._data[28:36] = value

    @property
    def custom_descriptor_enable(self) -> dict:
        """
        Get USB string enable flag status.

        Returns:
            dict: Dictionary with keys 'vendor', 'product', 'sn' indicating
                  whether each descriptor is enabled (True/False).
        """
        value = self._data[36]
        return {
            "vendor": bool(value & ENABLE_VENDOR_DESCRIPTOR),
            "product": bool(value & ENABLE_PRODUCT_DESCRIPTOR),
            "sn": bool(value & ENABLE_SERIAL_NO),
        }

    @custom_descriptor_enable.setter
    def custom_descriptor_enable(
        self,
        vendor: bool | tuple | list | None = None,
        product: bool | None = None,
        sn: bool | None = None,
    ) -> None:
        """
        Set custom descriptor enable flag status.

        Args:
            vendor: Either a tuple/list of three booleans (vendor, product, sn),
                   or the vendor boolean value.
            product: Whether product descriptor should be enabled (True/False).
            sn: Whether serial number descriptor should be enabled (True/False).

        Example:
            config.custom_descriptor_enable = True, True, False
        """
        current_value = self._data[36]

        if isinstance(vendor, (tuple, list)):
            vendor, product, sn = vendor

        if vendor or product or sn:
            current_value |= 0x80
        else:
            current_value &= ~0x80

        if vendor is not None:
            if vendor:
                current_value |= ENABLE_VENDOR_DESCRIPTOR
            else:
                current_value &= ~ENABLE_VENDOR_DESCRIPTOR

        if product is not None:
            if product:
                current_value |= ENABLE_PRODUCT_DESCRIPTOR
            else:
                current_value &= ~ENABLE_PRODUCT_DESCRIPTOR

        if sn is not None:
            if sn:
                current_value |= ENABLE_SERIAL_NO
            else:
                current_value &= ~ENABLE_SERIAL_NO

        self._data[36] = current_value

    @property
    def keyboard_fast_submission(self) -> int:
        """Get keyboard fast upload flag (0x00-0x01)."""
        return self._data[37]

    @keyboard_fast_submission.setter
    def keyboard_fast_submission(self, value: int) -> None:
        """Set keyboard fast upload flag."""
        if not 0x00 <= value <= 0x01:
            raise ValueError(
                f"Keyboard fast upload must be 0x00-0x01, got 0x{value:02X}"
            )
        self._data[37] = value

    def validate(self) -> None:
        """
        Validate configuration parameters according to protocol specifications.

        Raises:
            ValueError: If any configuration parameter violates protocol requirements

        Protocol Requirements:
            - Work mode: 0x00-0x03 (software modes) or 0x80-0x83 (hardware modes)
            - Serial mode: 0x00-0x02 (software modes) or 0x80-0x82 (hardware modes)
            - Address: 0x00-0xFF
            - Baud rate: in (9600, 19200, 38400, 57600, 115200)
            - Packet interval: 0x0000-0xFFFF
            - VID/PID: 0x0000-0xFFFF
            - Keyboard upload interval: 0x0000-0xFFFF
            - Keyboard release delay: 0x0000-0xFFFF
            - Auto enter flag: 0x00-0x01
            - USB string enable flag: 0x00-0xFF (bitmask)
            - Keyboard fast upload: 0x00-0x01
            - Enter characters: 8 bytes, each must be ASCII (0x00-0x7F)
            - USB filter string: 8 bytes
        """

        if not len(self._data) == 50:
            raise ValueError(
                f"Configuration data must be 50 bytes, got {len(self._data)} bytes"
            )

        # Work mode validation
        mode = self.chip_mode
        if not (0x00 <= mode <= 0x03 or 0x80 <= mode <= 0x83):
            raise ValueError(
                f"Work mode must be 0x00-0x03 (software) or 0x80-0x83 (hardware), got 0x{mode:02X}"
            )

        # Serial mode validation
        serial_mode = self.serial_mode
        if not (0x00 <= serial_mode <= 0x02 or 0x80 <= serial_mode <= 0x82):
            raise ValueError(
                f"Serial mode must be 0x00-0x02 (software) or 0x80-0x82 (hardware), got 0x{serial_mode:02X}"
            )

        # Baud rate validation
        baudrate = self.baudrate
        if baudrate not in VALID_BAUDRATES:
            raise ValueError(
                f"Baud rate must be one of {VALID_BAUDRATES}, got {baudrate}"
            )

        # Auto enter flag validation
        auto_enter_flag = self.auto_enter_flag
        if auto_enter_flag not in (0x00, 0x01):
            raise ValueError(
                f"Auto enter flag must be 0x00-0x01, got 0x{auto_enter_flag:02X}"
            )

        # Keyboard fast upload validation
        keyboard_fast_upload = self.keyboard_fast_submission
        if not 0x00 <= keyboard_fast_upload <= 0x01:
            raise ValueError(
                f"Keyboard fast upload must be 0x00-0x01, got 0x{keyboard_fast_upload:02X}"
            )

        # Enter characters validation (must be ASCII: 0x00-0x7F)
        enter_characters = self.enter_characters
        for i, char in enumerate(enter_characters):
            if char > 0x7F:
                raise ValueError(
                    f"Enter character at position {i} must be 0x00-0x7F, got 0x{char:02X}"
                )
