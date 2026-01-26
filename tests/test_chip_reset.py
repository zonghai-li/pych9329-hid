#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.ch9329 import (
    CH9329,
    CMD_RESET,
    ACK_STATUS_SUCCESS
)


class MockTransport:
    """Mock transport for testing."""
    
    def __init__(self):
        self.write_data = None
        self.response_data = None
    
    def write(self, data):
        """Store written data."""
        self.write_data = data
    
    def read(self, expected_length):
        """Return mock response."""
        return self.response_data
    
    def read_all(self):
        """Clear buffer."""
        pass


def calculate_checksum(data: bytes) -> int:
    """Calculate CH9329 checksum."""
    return sum(data) & 0xFF


def build_response(cmd: int, payload: bytes) -> bytes:
    """Build CH9329 response frame."""
    frame = bytearray(b"\x57\xab\x00")
    frame.append(cmd)
    frame.append(len(payload))
    frame.extend(payload)
    frame.append(calculate_checksum(frame))
    return bytes(frame)


class TestChipReset:
    """Test chip_reset method."""
    
    def test_chip_reset_success(self):
        """Test chip reset successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_RESET | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.chip_reset()
        
        assert result is True
    
    def test_chip_reset_failure(self):
        """Test chip reset failure."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_RESET | 0x80,
            bytes([0x01])  # Error status
        )
        
        result = ch9329.chip_reset()
        
        assert result is False
    
    def test_command_failure_returns_false(self):
        """Test that command failure returns False."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = None
        
        result = ch9329.chip_reset()
        
        assert result is False
    
    def test_command_frame_structure(self):
        """Test that command frame is built correctly."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_RESET | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        ch9329.chip_reset()
        
        frame = ch9329.t.write_data
        assert frame[0:2] == b"\x57\xab"
        assert frame[2] == 0x00
        assert frame[3] == CMD_RESET
        assert frame[4] == 0  # Empty payload
        assert frame[5] == calculate_checksum(frame[0:5])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
