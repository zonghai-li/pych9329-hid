#!/usr/bin/env python3

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pych9329_hid.ch9329 import CH9329, CMD_SET_DEFAULT_CFG
from pych9329_hid.transport import SerialTransport

# Mock transport for testing
class MockTransport:
    def __init__(self):
        self.written_data = []
        self.read_responses = []
        self.is_open_flag = True
    
    def write(self, data):
        self.written_data.append(data)
    
    def read(self, size):
        if self.read_responses:
            return self.read_responses.pop(0)
        return b''
    
    def read_all(self):
        return b''
    
    def is_open(self):
        return self.is_open_flag
    
    def close(self):
        self.is_open_flag = False

# Test the set_config_to_default function
def test_set_config_to_default():
    """Test set_config_to_default function with mock transport."""
    
    # Create mock transport
    transport = MockTransport()
    
    # Create CH9329 instance
    ch9329 = CH9329(transport)
    
    # Test 1: Successful command execution
    # Prepare successful response: HEAD + ADDR + CMD_RESPONSE + LEN(1) + STATUS(0x00) + CHECKSUM
    checksum = (0x57 + 0xAB + 0x00 + 0x8C + 0x01 + 0x00) % 256
    success_response = bytes([
        0x57, 0xAB,  # Frame header
        0x00,        # Address
        0x8C,        # Response command (CMD_SET_DEFAULT_CFG_RESPONSE)
        0x01,        # Length
        0x00,        # Status (success)
        checksum     # Checksum
    ])
    
    transport.read_responses = [success_response]
    
    result = ch9329.set_config_to_default()
    assert result is True, "set_config_to_default should return True for successful execution"
    
    # Verify the command was sent correctly
    assert len(transport.written_data) == 1, "Should have sent one command"
    
    sent_frame = transport.written_data[0]
    assert len(sent_frame) >= 6, "Frame should have at least 6 bytes"
    assert sent_frame[0:2] == b'\x57\xab', "Frame header should be correct"
    assert sent_frame[2] == 0x00, "Address should be 0x00"
    assert sent_frame[3] == CMD_SET_DEFAULT_CFG, "Command should be CMD_SET_DEFAULT_CFG"
    assert sent_frame[4] == 0x00, "Payload length should be 0"
    
    print("✓ Successful set_config_to_default execution")
    
    # Test 2: Command execution with error status
    transport.written_data = []
    checksum = (0x57 + 0xAB + 0x00 + 0x8C + 0x01 + 0xE1) % 256
    error_response = bytes([
        0x57, 0xAB,  # Frame header
        0x00,        # Address
        0x8C,        # Response command (CMD_SET_DEFAULT_CFG_RESPONSE)
        0x01,        # Length
        0xE1,        # Status (error)
        checksum     # Checksum
    ])
    
    transport.read_responses = [error_response]
    
    result = ch9329.set_config_to_default()
    assert result is False, "set_config_to_default should return False for error status"
    
    print("✓ set_config_to_default correctly handles error status")
    
    # Test 3: Command timeout/retry scenario
    transport.written_data = []
    transport.read_responses = []  # Empty responses will cause timeouts
    
    result = ch9329.set_config_to_default()
    assert result is False, "set_config_to_default should return False for timeout"
    
    # Should have retried 3 times (RETRY_COUNT)
    assert len(transport.written_data) == 3, "Should have retried 3 times"
    
    print("✓ set_config_to_default correctly handles timeout/retry")
    
    # Test 4: Short response
    transport.written_data = []
    short_response = b'\x57\xab\x00\x8c'  # Missing status byte
    transport.read_responses = [short_response]
    
    result = ch9329.set_config_to_default()
    assert result is False, "set_config_to_default should return False for short response"
    
    print("✓ set_config_to_default correctly handles short response")
    
    # Test 5: Verify default configuration values (documentation)
    print("\nDefault Configuration Values:")
    print("- Work mode: Hardware mode 0 (0x80) - Keyboard+Mouse")
    print("- Serial mode: Hardware mode 0 (0x80) - Protocol mode")
    print("- Baud rate: 9600 bps")
    print("- VID: 0x1A86, PID: 0xE129")
    print("- Packet interval: 3ms")
    print("- Configuration takes effect after next power cycle")

if __name__ == "__main__":
    test_set_config_to_default()
    print("\n✅ All set_config_to_default tests passed!")