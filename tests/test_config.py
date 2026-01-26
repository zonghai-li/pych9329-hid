#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.config import (
    CH9329Config,
    CHIP_MODE_SW_COMPOSITE,
    CHIP_MODE_SW_KEYBOARD,
    CHIP_MODE_SW_MOUSE,
    CHIP_MODE_SW_CUSTOM_HID,
    CHIP_MODE_HW_COMPOSITE,
    CHIP_MODE_HW_KEYBOARD,
    CHIP_MODE_HW_MOUSE,
    CHIP_MODE_HW_CUSTOM_HID,
    SERIAL_MODE_SW_PROTOCOL,
    SERIAL_MODE_SW_ASCII,
    SERIAL_MODE_SW_TRANSPARENT,
    SERIAL_MODE_HW_PROTOCOL,
    SERIAL_MODE_HW_ASCII,
    SERIAL_MODE_HW_TRANSPARENT,
    ENABLE_CUSTOM_DESCRIPTOR,
    ENABLE_VENDOR_DESCRIPTOR,
    ENABLE_PRODUCT_DESCRIPTOR,
    ENABLE_SERIAL_NO,
    VALID_BAUDRATES,
    CHIP_MODE_NAMES,
    SERIAL_MODE_NAMES
)


class TestCH9329ConfigInitialization:
    """Test CH9329Config initialization."""
    
    def test_valid_50_byte_data(self):
        """Test initialization with valid 50-byte data."""
        data = bytes(50)
        config = CH9329Config(data)
        assert config.to_bytes() == data
    
    def test_invalid_short_data(self):
        """Test initialization with short data raises ValueError."""
        with pytest.raises(ValueError, match="50 bytes"):
            CH9329Config(b"short")
    
    def test_invalid_long_data(self):
        """Test initialization with long data raises ValueError."""
        with pytest.raises(ValueError, match="50 bytes"):
            CH9329Config(b"0" * 51)


class TestChipMode:
    """Test chip_mode property."""
    
    def test_get_chip_mode(self):
        """Test getting chip mode."""
        data = bytes(50)
        data = bytearray(data)
        data[0] = CHIP_MODE_HW_COMPOSITE
        config = CH9329Config(bytes(data))
        assert config.chip_mode == CHIP_MODE_HW_COMPOSITE
    
    def test_set_software_modes(self):
        """Test setting software chip modes."""
        config = CH9329Config(bytes(50))
        for mode in [CHIP_MODE_SW_COMPOSITE, CHIP_MODE_SW_KEYBOARD, 
                     CHIP_MODE_SW_MOUSE, CHIP_MODE_SW_CUSTOM_HID]:
            config.chip_mode = mode
            assert config.chip_mode == mode
            assert config._data[0] == mode
    
    def test_set_hardware_modes(self):
        """Test setting hardware chip modes."""
        config = CH9329Config(bytes(50))
        for mode in [CHIP_MODE_HW_COMPOSITE, CHIP_MODE_HW_KEYBOARD,
                     CHIP_MODE_HW_MOUSE, CHIP_MODE_HW_CUSTOM_HID]:
            config.chip_mode = mode
            assert config.chip_mode == mode
            assert config._data[0] == mode
    
    def test_set_invalid_mode(self):
        """Test setting invalid chip mode raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Work mode"):
            config.chip_mode = 0x04


class TestSerialMode:
    """Test serial_mode property."""
    
    def test_get_serial_mode(self):
        """Test getting serial mode."""
        data = bytes(50)
        data = bytearray(data)
        data[1] = SERIAL_MODE_HW_PROTOCOL
        config = CH9329Config(bytes(data))
        assert config.serial_mode == SERIAL_MODE_HW_PROTOCOL
    
    def test_set_software_modes(self):
        """Test setting software serial modes."""
        config = CH9329Config(bytes(50))
        for mode in [SERIAL_MODE_SW_PROTOCOL, SERIAL_MODE_SW_ASCII,
                     SERIAL_MODE_SW_TRANSPARENT]:
            config.serial_mode = mode
            assert config.serial_mode == mode
            assert config._data[1] == mode
    
    def test_set_hardware_modes(self):
        """Test setting hardware serial modes."""
        config = CH9329Config(bytes(50))
        for mode in [SERIAL_MODE_HW_PROTOCOL, SERIAL_MODE_HW_ASCII,
                     SERIAL_MODE_HW_TRANSPARENT]:
            config.serial_mode = mode
            assert config.serial_mode == mode
            assert config._data[1] == mode
    
    def test_set_invalid_mode(self):
        """Test setting invalid serial mode raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Serial mode"):
            config.serial_mode = 0x03


class TestAddress:
    """Test address property."""
    
    def test_get_address(self):
        """Test getting address."""
        data = bytes(50)
        data = bytearray(data)
        data[2] = 0x42
        config = CH9329Config(bytes(data))
        assert config.address == 0x42
    
    def test_set_address(self):
        """Test setting address."""
        config = CH9329Config(bytes(50))
        for addr in [0x00, 0x01, 0x7F, 0xFF]:
            config.address = addr
            assert config.address == addr
            assert config._data[2] == addr
    
    def test_set_invalid_address(self):
        """Test setting invalid address raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Address"):
            config.address = 0x100


class TestBaudrate:
    """Test baudrate property."""
    
    def test_get_baudrate(self):
        """Test getting baudrate."""
        data = bytes(50)
        data = bytearray(data)
        data[3:7] = (115200).to_bytes(4, byteorder='big')
        config = CH9329Config(bytes(data))
        assert config.baudrate == 115200
    
    def test_set_baudrate(self):
        """Test setting baudrate."""
        config = CH9329Config(bytes(50))
        for baud in VALID_BAUDRATES:
            config.baudrate = baud
            assert config.baudrate == baud
            assert int.from_bytes(config._data[3:7], byteorder='big') == baud
    
    def test_set_invalid_baudrate(self):
        """Test setting invalid baudrate raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Baud rate"):
            config.baudrate = 4800


class TestPacketInterval:
    """Test packet_interval property."""
    
    def test_get_packet_interval(self):
        """Test getting packet interval."""
        data = bytes(50)
        data = bytearray(data)
        data[9:11] = (100).to_bytes(2, byteorder='big')
        config = CH9329Config(bytes(data))
        assert config.packet_interval == 100
    
    def test_set_packet_interval(self):
        """Test setting packet interval."""
        config = CH9329Config(bytes(50))
        for interval in [0x0000, 0x0001, 0x0123, 0xFFFF]:
            config.packet_interval = interval
            assert config.packet_interval == interval
            assert int.from_bytes(config._data[9:11], byteorder='big') == interval
    
    def test_set_invalid_packet_interval(self):
        """Test setting invalid packet interval raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Packet interval"):
            config.packet_interval = 0x10000


class TestVID:
    """Test vid property."""
    
    def test_get_vid(self):
        """Test getting VID."""
        data = bytes(50)
        data = bytearray(data)
        data[11:13] = (0x1234).to_bytes(2, byteorder='big')
        config = CH9329Config(bytes(data))
        assert config.vid == 0x1234
    
    def test_set_vid(self):
        """Test setting VID."""
        config = CH9329Config(bytes(50))
        for vid in [0x0000, 0x1234, 0xFFFF]:
            config.vid = vid
            assert config.vid == vid
            assert int.from_bytes(config._data[11:13], byteorder='big') == vid


class TestPID:
    """Test pid property."""
    
    def test_get_pid(self):
        """Test getting PID."""
        data = bytes(50)
        data = bytearray(data)
        data[13:15] = (0x5678).to_bytes(2, byteorder='big')
        config = CH9329Config(bytes(data))
        assert config.pid == 0x5678
    
    def test_set_pid(self):
        """Test setting PID."""
        config = CH9329Config(bytes(50))
        for pid in [0x0000, 0x1234, 0xFFFF]:
            config.pid = pid
            assert config.pid == pid
            assert int.from_bytes(config._data[13:15], byteorder='big') == pid


class TestKeyboardSubmissionInterval:
    """Test keyboard_submission_interval property."""
    
    def test_get_keyboard_submission_interval(self):
        """Test getting keyboard submission interval."""
        data = bytes(50)
        data = bytearray(data)
        data[15:17] = (50).to_bytes(2, byteorder='big')
        config = CH9329Config(bytes(data))
        assert config.keyboard_submission_interval == 50
    
    def test_set_keyboard_submission_interval(self):
        """Test setting keyboard submission interval."""
        config = CH9329Config(bytes(50))
        for interval in [0x0000, 0x0001, 0x0123, 0xFFFF]:
            config.keyboard_submission_interval = interval
            assert config.keyboard_submission_interval == interval
            assert int.from_bytes(config._data[15:17], byteorder='big') == interval
    
    def test_set_invalid_keyboard_submission_interval(self):
        """Test setting invalid keyboard submission interval raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Keyboard interval"):
            config.keyboard_submission_interval = 0x10000


class TestKeyboardReleaseDelay:
    """Test keyboard_release_delay property."""
    
    def test_get_keyboard_release_delay(self):
        """Test getting keyboard release delay."""
        data = bytes(50)
        data = bytearray(data)
        data[17:19] = (10).to_bytes(2, byteorder='big')
        config = CH9329Config(bytes(data))
        assert config.keyboard_release_delay == 10
    
    def test_set_keyboard_release_delay(self):
        """Test setting keyboard release delay."""
        config = CH9329Config(bytes(50))
        for delay in [0x0000, 0x0001, 0x0123, 0xFFFF]:
            config.keyboard_release_delay = delay
            assert config.keyboard_release_delay == delay
            assert int.from_bytes(config._data[17:19], byteorder='big') == delay
    
    def test_set_invalid_keyboard_release_delay(self):
        """Test setting invalid keyboard release delay raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Keyboard release delay"):
            config.keyboard_release_delay = 0x10000


class TestAutoEnterFlag:
    """Test auto_enter_flag property."""
    
    def test_get_auto_enter_flag(self):
        """Test getting auto enter flag."""
        data = bytes(50)
        data = bytearray(data)
        data[19] = 0x01
        config = CH9329Config(bytes(data))
        assert config.auto_enter_flag == 0x01
    
    def test_set_auto_enter_flag(self):
        """Test setting auto enter flag."""
        config = CH9329Config(bytes(50))
        for flag in [0x00, 0x01]:
            config.auto_enter_flag = flag
            assert config.auto_enter_flag == flag
            assert config._data[19] == flag
    
    def test_set_invalid_auto_enter_flag(self):
        """Test setting invalid auto enter flag raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Auto enter flag"):
            config.auto_enter_flag = 0x02


class TestEnterCharacters:
    """Test enter_characters property."""
    
    def test_get_enter_characters(self):
        """Test getting enter characters."""
        data = bytes(50)
        data = bytearray(data)
        data[20:28] = b'\x0D\x00\x00\x00\x0D\x00\x00\x00'
        config = CH9329Config(bytes(data))
        assert config.enter_characters == b'\x0D\x00\x00\x00\x0D\x00\x00\x00'
    
    def test_set_enter_characters(self):
        """Test setting enter characters."""
        config = CH9329Config(bytes(50))
        test_chars = [
            b'\x0D\x00\x00\x00\x0D\x00\x00\x00',
            b'\x00\x00\x00\x00\x00\x00\x00\x00',
            b'\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F',
        ]
        for chars in test_chars:
            config.enter_characters = chars
            assert config.enter_characters == chars
            assert config._data[20:28] == chars
    
    def test_set_short_enter_characters(self):
        """Test setting short enter characters raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Enter characters must be 8 bytes"):
            config.enter_characters = b'short'
    
    def test_set_long_enter_characters(self):
        """Test setting long enter characters raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Enter characters must be 8 bytes"):
            config.enter_characters = b'longlonglong'


class TestFilterStrings:
    """Test filter_strings property."""
    
    def test_get_filter_strings(self):
        """Test getting filter strings."""
        data = bytes(50)
        data = bytearray(data)
        data[28:36] = b'abcdefgh'
        config = CH9329Config(bytes(data))
        assert config.filter_strings == b'abcdefgh'
    
    def test_set_filter_strings(self):
        """Test setting filter strings."""
        config = CH9329Config(bytes(50))
        test_strings = [
            b'\x00\x00\x00\x00\x00\x00\x00\x00',
            b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF',
            b'abcdefgh',
        ]
        for strings in test_strings:
            config.filter_strings = strings
            assert config.filter_strings == strings
            assert config._data[28:36] == strings
    
    def test_set_short_filter_strings(self):
        """Test setting short filter strings raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Filter strings must be 8 bytes"):
            config.filter_strings = b'short'


class TestCustomDescriptorEnable:
    """Test custom_descriptor_enable property."""
    
    def test_get_custom_descriptor_enable(self):
        """Test getting custom descriptor enable."""
        data = bytes(50)
        data = bytearray(data)
        data[36] = 0x87
        config = CH9329Config(bytes(data))
        assert config.custom_descriptor_enable == {
            'vendor': True,
            'product': True,
            'sn': True
        }
    
    def test_set_custom_descriptor_enable_all_disabled(self):
        """Test setting all descriptors disabled."""
        config = CH9329Config(bytes(50))
        config.custom_descriptor_enable = False, False, False
        assert config.custom_descriptor_enable == {
            'vendor': False,
            'product': False,
            'sn': False
        }
        assert config._data[36] == 0x00
    
    def test_set_custom_descriptor_enable_vendor_only(self):
        """Test setting only vendor descriptor enabled."""
        config = CH9329Config(bytes(50))
        config.custom_descriptor_enable = True, False, False
        assert config.custom_descriptor_enable == {
            'vendor': True,
            'product': False,
            'sn': False
        }
        assert config._data[36] == 0x84
    
    def test_set_custom_descriptor_enable_product_only(self):
        """Test setting only product descriptor enabled."""
        config = CH9329Config(bytes(50))
        config.custom_descriptor_enable = False, True, False
        assert config.custom_descriptor_enable == {
            'vendor': False,
            'product': True,
            'sn': False
        }
        assert config._data[36] == 0x82
    
    def test_set_custom_descriptor_enable_sn_only(self):
        """Test setting only serial number descriptor enabled."""
        config = CH9329Config(bytes(50))
        config.custom_descriptor_enable = False, False, True
        assert config.custom_descriptor_enable == {
            'vendor': False,
            'product': False,
            'sn': True
        }
        assert config._data[36] == 0x81
    
    def test_set_custom_descriptor_enable_all_enabled(self):
        """Test setting all descriptors enabled."""
        config = CH9329Config(bytes(50))
        config.custom_descriptor_enable = True, True, True
        assert config.custom_descriptor_enable == {
            'vendor': True,
            'product': True,
            'sn': True
        }
        assert config._data[36] == 0x87


class TestKeyboardFastSubmission:
    """Test keyboard_fast_submission property."""
    
    def test_get_keyboard_fast_submission(self):
        """Test getting keyboard fast submission."""
        data = bytes(50)
        data = bytearray(data)
        data[37] = 0x01
        config = CH9329Config(bytes(data))
        assert config.keyboard_fast_submission == 0x01
    
    def test_set_keyboard_fast_submission(self):
        """Test setting keyboard fast submission."""
        config = CH9329Config(bytes(50))
        for flag in [0x00, 0x01]:
            config.keyboard_fast_submission = flag
            assert config.keyboard_fast_submission == flag
            assert config._data[37] == flag
    
    def test_set_invalid_keyboard_fast_submission(self):
        """Test setting invalid keyboard fast submission raises ValueError."""
        config = CH9329Config(bytes(50))
        with pytest.raises(ValueError, match="Keyboard fast upload"):
            config.keyboard_fast_submission = 0x02


class TestValidate:
    """Test validate method."""
    
    def test_validate_valid_config(self):
        """Test validating valid configuration."""
        data = bytes(50)
        data = bytearray(data)
        data[3:7] = (9600).to_bytes(4, byteorder='big')
        config = CH9329Config(bytes(data))
        config.validate()
    
    def test_validate_invalid_chip_mode(self):
        """Test validating invalid chip mode raises ValueError."""
        data = bytes(50)
        data = bytearray(data)
        data[0] = 0x04
        data[3:7] = (9600).to_bytes(4, byteorder='big')
        config = CH9329Config(bytes(data))
        with pytest.raises(ValueError, match="Work mode"):
            config.validate()
    
    def test_validate_invalid_serial_mode(self):
        """Test validating invalid serial mode raises ValueError."""
        data = bytes(50)
        data = bytearray(data)
        data[1] = 0x03
        data[3:7] = (9600).to_bytes(4, byteorder='big')
        config = CH9329Config(bytes(data))
        with pytest.raises(ValueError, match="Serial mode"):
            config.validate()
    
    def test_validate_invalid_baudrate(self):
        """Test validating invalid baudrate raises ValueError."""
        data = bytes(50)
        data = bytearray(data)
        data[3:7] = (4800).to_bytes(4, byteorder='big')
        config = CH9329Config(bytes(data))
        with pytest.raises(ValueError, match="Baud rate"):
            config.validate()
    
    def test_validate_invalid_auto_enter_flag(self):
        """Test validating invalid auto enter flag raises ValueError."""
        data = bytes(50)
        data = bytearray(data)
        data[3:7] = (9600).to_bytes(4, byteorder='big')
        data[19] = 0x02
        config = CH9329Config(bytes(data))
        with pytest.raises(ValueError, match="Auto enter flag"):
            config.validate()
    
    def test_validate_invalid_keyboard_fast_submission(self):
        """Test validating invalid keyboard fast submission raises ValueError."""
        data = bytes(50)
        data = bytearray(data)
        data[3:7] = (9600).to_bytes(4, byteorder='big')
        data[37] = 0x02
        config = CH9329Config(bytes(data))
        with pytest.raises(ValueError, match="Keyboard fast upload"):
            config.validate()
    
    def test_validate_invalid_enter_character(self):
        """Test validating invalid enter character raises ValueError."""
        data = bytes(50)
        data = bytearray(data)
        data[3:7] = (9600).to_bytes(4, byteorder='big')
        data[20] = 0x80
        config = CH9329Config(bytes(data))
        with pytest.raises(ValueError, match="Enter character"):
            config.validate()


class TestToBytes:
    """Test to_bytes method."""
    
    def test_to_bytes_returns_original_data(self):
        """Test to_bytes returns original data."""
        original_data = bytes(50)
        config = CH9329Config(original_data)
        assert config.to_bytes() == original_data
    
    def test_to_bytes_returns_50_bytes(self):
        """Test to_bytes returns 50 bytes."""
        config = CH9329Config(bytes(50))
        assert len(config.to_bytes()) == 50


class TestStringRepresentation:
    """Test __str__ and __repr__ methods."""
    
    def test_str_contains_config_info(self):
        """Test __str__ contains configuration information."""
        config = CH9329Config(bytes(50))
        str_repr = str(config)
        assert "CH9329Config" in str_repr
        assert "Work Mode:" in str_repr
        assert "Serial Mode:" in str_repr
        assert "Baud Rate:" in str_repr
        assert "VID:" in str_repr
        assert "PID:" in str_repr
    
    def test_repr_contains_data(self):
        """Test __repr__ contains data."""
        config = CH9329Config(bytes(50))
        repr_repr = repr(config)
        assert "CH9329Config" in repr_repr
        assert "data=" in repr_repr
    
    def test_str_shows_readable_mode_names(self):
        """Test __str__ shows readable mode names."""
        data = bytes(50)
        data = bytearray(data)
        data[0] = CHIP_MODE_HW_COMPOSITE
        data[1] = SERIAL_MODE_HW_PROTOCOL
        config = CH9329Config(bytes(data))
        str_repr = str(config)
        assert "Keyboard+Mouse (Hardware)" in str_repr
        assert "Protocol mode (Hardware)" in str_repr


class TestConstants:
    """Test configuration constants."""
    
    def test_chip_mode_constants(self):
        """Test chip mode constants."""
        assert CHIP_MODE_SW_COMPOSITE == 0x00
        assert CHIP_MODE_SW_KEYBOARD == 0x01
        assert CHIP_MODE_SW_MOUSE == 0x02
        assert CHIP_MODE_SW_CUSTOM_HID == 0x03
        assert CHIP_MODE_HW_COMPOSITE == 0x80
        assert CHIP_MODE_HW_KEYBOARD == 0x81
        assert CHIP_MODE_HW_MOUSE == 0x82
        assert CHIP_MODE_HW_CUSTOM_HID == 0x83
    
    def test_serial_mode_constants(self):
        """Test serial mode constants."""
        assert SERIAL_MODE_SW_PROTOCOL == 0x00
        assert SERIAL_MODE_SW_ASCII == 0x01
        assert SERIAL_MODE_SW_TRANSPARENT == 0x02
        assert SERIAL_MODE_HW_PROTOCOL == 0x80
        assert SERIAL_MODE_HW_ASCII == 0x81
        assert SERIAL_MODE_HW_TRANSPARENT == 0x82
    
    def test_usb_descriptor_constants(self):
        """Test USB descriptor enable constants."""
        assert ENABLE_CUSTOM_DESCRIPTOR == 0x80
        assert ENABLE_VENDOR_DESCRIPTOR == 0x04
        assert ENABLE_PRODUCT_DESCRIPTOR == 0x02
        assert ENABLE_SERIAL_NO == 0x01
    
    def test_valid_baudrates(self):
        """Test valid baudrates."""
        assert 9600 in VALID_BAUDRATES
        assert 19200 in VALID_BAUDRATES
        assert 38400 in VALID_BAUDRATES
        assert 57600 in VALID_BAUDRATES
        assert 115200 in VALID_BAUDRATES
    
    def test_chip_mode_names(self):
        """Test chip mode name mappings."""
        assert CHIP_MODE_NAMES[CHIP_MODE_SW_COMPOSITE] == "Keyboard+Mouse (Software)"
        assert CHIP_MODE_NAMES[CHIP_MODE_HW_COMPOSITE] == "Keyboard+Mouse (Hardware)"
        assert CHIP_MODE_NAMES[CHIP_MODE_SW_KEYBOARD] == "Keyboard only (Software)"
        assert CHIP_MODE_NAMES[CHIP_MODE_HW_KEYBOARD] == "Keyboard only (Hardware)"
    
    def test_serial_mode_names(self):
        """Test serial mode name mappings."""
        assert SERIAL_MODE_NAMES[SERIAL_MODE_SW_PROTOCOL] == "Protocol mode (Software)"
        assert SERIAL_MODE_NAMES[SERIAL_MODE_HW_PROTOCOL] == "Protocol mode (Hardware)"
        assert SERIAL_MODE_NAMES[SERIAL_MODE_SW_ASCII] == "ASCII mode (Software)"
        assert SERIAL_MODE_NAMES[SERIAL_MODE_HW_ASCII] == "ASCII mode (Hardware)"


class TestDataModification:
    """Test that data modifications are reflected in properties."""
    
    def test_chip_mode_modification(self):
        """Test chip_mode modification reflected in data."""
        config = CH9329Config(bytes(50))
        config.chip_mode = CHIP_MODE_SW_KEYBOARD
        assert config._data[0] == CHIP_MODE_SW_KEYBOARD
    
    def test_baudrate_modification(self):
        """Test baudrate modification reflected in data."""
        config = CH9329Config(bytes(50))
        config.baudrate = 115200
        assert int.from_bytes(config._data[3:7], byteorder='big') == 115200
    
    def test_vid_modification(self):
        """Test vid modification reflected in data."""
        config = CH9329Config(bytes(50))
        config.vid = 0x1234
        assert int.from_bytes(config._data[11:13], byteorder='big') == 0x1234
    
    def test_custom_descriptor_enable_modification(self):
        """Test custom_descriptor_enable modification reflected in data."""
        config = CH9329Config(bytes(50))
        config.custom_descriptor_enable = True, True, True
        assert config._data[36] == 0x87


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
