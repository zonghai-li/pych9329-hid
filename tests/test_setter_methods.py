#!/usr/bin/env python3

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pych9329_hid.ch9329 import CH9329Config

# Test the new setter methods in CH9329Config class
def test_ch9329_config_setters():
    """Test CH9329Config setter methods and data synchronization."""
    
    # Create sample 50-byte configuration data
    sample_data = bytes([
        # Work mode: Software mode 0 (Keyboard+Mouse)
        0x00,
        # Serial mode: Software mode 0 (Protocol mode)
        0x00,
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
    
    # Test initial values
    assert config.chip_mode == 0x00, f"Expected work_mode=0x00, got {config.chip_mode:02X}"
    assert config.serial_mode == 0x00, f"Expected serial_mode=0x00, got {config.serial_mode:02X}"
    assert config.baudrate == 9600, f"Expected baudrate=9600, got {config.baudrate}"
    
    print("✓ Initial configuration values correct")
    
    # Test work_mode setter
    config.chip_mode = 0x02  # Change to Mouse only mode
    assert config.chip_mode == 0x02, f"Expected work_mode=0x02 after setter, got {config.chip_mode:02X}"
    
    # Verify that underlying data was updated
    data_after_work_mode = config.to_bytes()
    assert data_after_work_mode[0] == 0x02, f"Expected data[0]=0x02, got {data_after_work_mode[0]:02X}"
    
    print("✓ work_mode setter updates both field and data")
    
    # Test serial_mode setter
    config.serial_mode = 0x01  # Change to ASCII mode
    assert config.serial_mode == 0x01, f"Expected serial_mode=0x01 after setter, got {config.serial_mode:02X}"
    
    # Verify that underlying data was updated
    data_after_serial_mode = config.to_bytes()
    assert data_after_serial_mode[1] == 0x01, f"Expected data[1]=0x01, got {data_after_serial_mode[1]:02X}"
    
    print("✓ serial_mode setter updates both field and data")
    
    # Test baudrate setter
    config.baudrate = 115200  # Change to 115200 baud
    assert config.baudrate == 115200, f"Expected baudrate=115200 after setter, got {config.baudrate}"
    
    # Verify that underlying data was updated (big-endian)
    data_after_baudrate = config.to_bytes()
    expected_baudrate_bytes = (115200).to_bytes(4, byteorder='big')
    assert data_after_baudrate[3:7] == expected_baudrate_bytes, (
        f"Expected baudrate bytes {expected_baudrate_bytes.hex()}, got {data_after_baudrate[3:7].hex()}"
    )
    
    print("✓ baudrate setter updates both field and data")
    
    # Test multiple changes
    config.chip_mode = 0x03  # Custom HID mode
    config.serial_mode = 0x02  # Transparent mode
    config.baudrate = 57600  # 57600 baud
    
    final_data = config.to_bytes()
    assert final_data[0] == 0x03, f"Expected final work_mode=0x03, got {final_data[0]:02X}"
    assert final_data[1] == 0x02, f"Expected final serial_mode=0x02, got {final_data[1]:02X}"
    assert int.from_bytes(final_data[3:7], byteorder='big') == 57600, f"Expected final baudrate=57600"
    
    print("✓ Multiple setter calls work correctly")
    
    # Test validation in setter
    try:
        config.chip_mode = 0xFF  # Invalid value
        assert False, "Should have raised ValueError for invalid work mode"
    except ValueError as e:
        assert "Work mode must be 0x00-0x03 (software) or 0x80-0x83 (hardware)" in str(e)
        print("✓ Work mode validation in setter works")
    
    try:
        config.serial_mode = 0xFF  # Invalid value
        assert False, "Should have raised ValueError for invalid serial mode"
    except ValueError as e:
        assert "Serial mode must be 0x00-0x02 (software) or 0x80-0x82 (hardware)" in str(e)
        print("✓ Serial mode validation in setter works")
    
    try:
        config.baudrate = 999999  # Invalid value
        assert False, "Should have raised ValueError for invalid baudrate"
    except ValueError as e:
        assert "Baud rate must be one of" in str(e)
        print("✓ Baudrate validation in setter works")
    
    # Test other properties
    config.address = 0x01
    assert config.address == 0x01
    print("✓ address property works")
    
    config.packet_interval = 10
    assert config.packet_interval == 10
    print("✓ packet_interval property works")
    
    config.vid = 0x1234
    assert config.vid == 0x1234
    print("✓ vid property works")
    
    config.pid = 0x5678
    assert config.pid == 0x5678
    print("✓ pid property works")
    
    config.keyboard_submission_interval = 100
    assert config.keyboard_submission_interval == 100
    print("✓ keyboard_upload_interval property works")
    
    config.keyboard_release_delay = 50
    assert config.keyboard_release_delay == 50
    print("✓ keyboard_release_delay property works")
    
    config.auto_enter_flag = 1
    assert config.auto_enter_flag == 1
    print("✓ auto_enter_flag property works")
    
    config.enter_characters = b'\x0D\x00\x00\x00\x0D\x00\x00\x00'
    assert config.enter_characters == b'\x0D\x00\x00\x00\x0D\x00\x00\x00'
    print("✓ enter_characters property works")
    
    config.filter_strings = b'\x00\x00\x00\x00\x00\x00\x00\x00'
    assert config.filter_strings == b'\x00\x00\x00\x00\x00\x00\x00\x00'
    print("✓ filter_strings property works")
    
    config.custom_descriptor_enable = True, True, True
    assert config.custom_descriptor_enable == {'vendor': True, 'product': True, 'sn': True}
    print("✓ custom_descriptor_enable property works")
    
    config.keyboard_fast_submission = 1
    assert config.keyboard_fast_submission == 1
    print("✓ keyboard_fast_upload property works")
    
    print("\n✅ All setter method tests passed!")

if __name__ == "__main__":
    test_ch9329_config_setters()