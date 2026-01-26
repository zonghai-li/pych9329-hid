#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pych9329_hid.ch9329 import CH9329Config

def test_custom_descriptor_enable():
    """Test custom_descriptor_enable property getter and setter."""
    
    # Create sample configuration data
    sample_data = bytes([
        0x80, 0x80, 0x00, 0x00, 0x00, 0x25, 0x80, 0x00, 0x00,
        0x00, 0x03, 0x1A, 0x86, 0xE1, 0x29, 0x00, 0x00, 0x00,
        0x01, 0x00, 0x0D, 0x00, 0x00, 0x00, 0x0D, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00
    ])
    
    config = CH9329Config(sample_data)
    
    # Test 1: Initial state (all disabled)
    result = config.custom_descriptor_enable
    assert result == {'vendor': False, 'product': False, 'sn': False}, f"Expected all disabled, got {result}"
    print("✓ Initial state: all descriptors disabled")
    
    # Test 2: Enable all descriptors
    config.custom_descriptor_enable = True, True, True
    result = config.custom_descriptor_enable
    assert result == {'vendor': True, 'product': True, 'sn': True}, f"Expected all enabled, got {result}"
    assert config._data[36] == 0x87, f"Expected data[36]=0x87, got 0x{config._data[36]:02X}"
    print("✓ Enable all descriptors")
    
    # Test 3: Enable only vendor
    config.custom_descriptor_enable = True, False, False
    result = config.custom_descriptor_enable
    assert result == {'vendor': True, 'product': False, 'sn': False}, f"Expected only vendor enabled, got {result}"
    assert config._data[36] == 0x84, f"Expected data[36]=0x84, got 0x{config._data[36]:02X}"
    print("✓ Enable only vendor descriptor")
    
    # Test 4: Enable only product
    config.custom_descriptor_enable = False, True, False
    result = config.custom_descriptor_enable
    assert result == {'vendor': False, 'product': True, 'sn': False}, f"Expected only product enabled, got {result}"
    assert config._data[36] == 0x82, f"Expected data[36]=0x82, got 0x{config._data[36]:02X}"
    print("✓ Enable only product descriptor")
    
    # Test 5: Enable only serial number
    config.custom_descriptor_enable = False, False, True
    result = config.custom_descriptor_enable
    assert result == {'vendor': False, 'product': False, 'sn': True}, f"Expected only sn enabled, got {result}"
    assert config._data[36] == 0x81, f"Expected data[36]=0x81, got 0x{config._data[36]:02X}"
    print("✓ Enable only serial number descriptor")
    
    # Test 6: Enable vendor and product
    config.custom_descriptor_enable = True, True, False
    result = config.custom_descriptor_enable
    assert result == {'vendor': True, 'product': True, 'sn': False}, f"Expected vendor and product enabled, got {result}"
    assert config._data[36] == 0x86, f"Expected data[36]=0x86, got 0x{config._data[36]:02X}"
    print("✓ Enable vendor and product descriptors")
    
    # Test 7: Disable all
    config.custom_descriptor_enable = False, False, False
    result = config.custom_descriptor_enable
    assert result == {'vendor': False, 'product': False, 'sn': False}, f"Expected all disabled, got {result}"
    assert config._data[36] == 0x00, f"Expected data[36]=0x00, got 0x{config._data[36]:02X}"
    print("✓ Disable all descriptors")
    
    # Test 8: Test with raw data that has flags set
    data_with_flags = bytearray(sample_data)
    data_with_flags[36] = 0x87  # All enabled
    config2 = CH9329Config(bytes(data_with_flags))
    result = config2.custom_descriptor_enable
    assert result == {'vendor': True, 'product': True, 'sn': True}, f"Expected all enabled from raw data, got {result}"
    print("✓ Read from raw data with all flags set")
    
    # Test 9: Test with partial flags in raw data
    data_partial = bytearray(sample_data)
    data_partial[36] = 0x84  # Only vendor enabled
    config3 = CH9329Config(bytes(data_partial))
    result = config3.custom_descriptor_enable
    assert result == {'vendor': True, 'product': False, 'sn': False}, f"Expected only vendor enabled from raw data, got {result}"
    print("✓ Read from raw data with partial flags set")

if __name__ == "__main__":
    test_custom_descriptor_enable()
    print("\n✅ All custom_descriptor_enable tests passed!")
