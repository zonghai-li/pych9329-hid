#!/usr/bin/env python3

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pych9329_hid.ch9329 import CH9329Config

# Test the CH9329Config class with sample data
def test_ch9329_config():
    """Test CH9329Config class with sample configuration data."""
    
    # Create sample 50-byte configuration data
    # This simulates what the CH9329 chip would return
    sample_data = bytes([
        # Work mode: Hardware mode 0 (Keyboard+Mouse)
        0x80,
        # Serial mode: Hardware mode 0 (Protocol mode)
        0x80,
        # Address: 0x00
        0x00,
        # Baud rate: 9600 (0x00002580)
        0x00, 0x00, 0x25, 0x80,
        # Reserved (2 bytes)
        0x00, 0x00,
        # Packet interval: 3ms
        0x00, 0x03,
        # VID: 0x1A86, PID: 0xE129
        0x1A, 0x86, 0xE1, 0x29,
        # Keyboard upload interval: 0ms
        0x00, 0x00,
        # Keyboard release delay: 1ms
        0x00, 0x01,
        # Auto enter flag: 0 (disabled)
        0x00,
        # Enter characters: 0x0D (carriage return) repeated
        0x0D, 0x00, 0x00, 0x00, 0x0D, 0x00, 0x00, 0x00,
        # Filter strings: empty
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # USB string enable flag: 0 (disabled)
        0x00,
        # Keyboard fast upload: 0 (disabled)
        0x00,
        # Reserved (12 bytes)
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ])
    
    # Test creating configuration object
    config = CH9329Config(sample_data)
    
    # Test basic properties
    assert config.chip_mode == 0x80, f"Expected work_mode=0x80, got {config.chip_mode:02X}"
    assert config.serial_mode == 0x80, f"Expected serial_mode=0x80, got {config.serial_mode:02X}"
    assert config.address == 0x00, f"Expected address=0x00, got {config.address:02X}"
    assert config.baudrate == 9600, f"Expected baudrate=9600, got {config.baudrate}"
    assert config.packet_interval == 3, f"Expected packet_interval=3, got {config.packet_interval}"
    assert config.vid == 0x1A86, f"Expected vid=0x1A86, got {config.vid:04X}"
    assert config.pid == 0xE129, f"Expected pid=0xE129, got {config.pid:04X}"
    assert config.keyboard_submission_interval == 0, f"Expected keyboard_upload_interval=0, got {config.keyboard_submission_interval}"
    assert config.keyboard_release_delay == 1, f"Expected keyboard_release_delay=1, got {config.keyboard_release_delay}"
    assert config.auto_enter_flag == 0, f"Expected auto_enter_flag=0, got {config.auto_enter_flag}"
    assert config.custom_descriptor_enable == {'vendor': False, 'product': False, 'sn': False}, f"Expected usb_string_enable disabled, got {config.custom_descriptor_enable}"
    assert config.keyboard_fast_submission == 0, f"Expected keyboard_fast_upload=0, got {config.keyboard_fast_submission}"
    
    # Test string representations
    str_repr = str(config)
    repr_repr = repr(config)
    
    print("✓ CH9329Config class test passed")
    print(f"String representation: {str_repr}")
    print(f"Detailed representation: {repr_repr}")
    
    # Test error handling for invalid data length
    try:
        CH9329Config(b"short")
        assert False, "Should have raised ValueError for short data"
    except ValueError as e:
        assert "50 bytes" in str(e), f"Unexpected error message: {e}"
        print("✓ Error handling for invalid data length passed")

if __name__ == "__main__":
    test_ch9329_config()
    print("\n✅ All CH9329Config tests passed!")