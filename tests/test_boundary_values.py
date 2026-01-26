#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.ch9329 import (
    CH9329,
    CMD_SEND_KEY,
    CMD_SEND_MS_REL,
    CMD_SEND_MS_ABS,
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


class TestBoundaryValues:
    """Test boundary values in CH9329 methods."""
    
    def test_send_keyboard_max_keycodes(self):
        """Test send_keyboard with exactly 6 keycodes."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_KEY | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_keyboard(0x00, [0x04, 0x05, 0x06, 0x07, 0x08, 0x09])
        
        assert result is True
    
    def test_send_keyboard_zero_keycodes(self):
        """Test send_keyboard with empty keycodes."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_KEY | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_keyboard(0x00, [])
        
        assert result is True
    
    def test_send_keyboard_modifier_boundary_max(self):
        """Test send_keyboard with modifier = 0xFF."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_KEY | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_keyboard(0xFF, [0x04])
        
        assert result is True
    
    def test_send_keyboard_modifier_boundary_min(self):
        """Test send_keyboard with modifier = 0x00."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_KEY | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_keyboard(0x00, [0x04])
        
        assert result is True
    
    def test_send_keyboard_keycode_boundary_max(self):
        """Test send_keyboard with keycode = 0xFF."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_KEY | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_keyboard(0x00, [0xFF])
        
        assert result is True
    
    def test_send_keyboard_keycode_boundary_min(self):
        """Test send_keyboard with keycode = 0x00."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_KEY | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_keyboard(0x00, [0x00])
        
        assert result is True
    
    def test_send_mouse_rel_buttons_boundary_max(self):
        """Test send_mouse_rel with buttons = 0x07."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_REL | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_rel(0x07, 0, 0)
        
        assert result is True
    
    def test_send_mouse_rel_buttons_boundary_min(self):
        """Test send_mouse_rel with buttons = 0x00."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_REL | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_rel(0x00, 0, 0)
        
        assert result is True
    
    def test_send_mouse_rel_x_boundary_max(self):
        """Test send_mouse_rel with x = 127."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_REL | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_rel(0x00, 127, 0)
        
        assert result is True
    
    def test_send_mouse_rel_x_boundary_min(self):
        """Test send_mouse_rel with x = -127."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_REL | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_rel(0x00, -127, 0)
        
        assert result is True
    
    def test_send_mouse_rel_y_boundary_max(self):
        """Test send_mouse_rel with y = 127."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_REL | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_rel(0, 127, 0)
        
        assert result is True
    
    def test_send_mouse_rel_y_boundary_min(self):
        """Test send_mouse_rel with y = -127."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_REL | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_rel(0, -127, 0)
        
        assert result is True
    
    def test_send_mouse_abs_buttons_boundary_max(self):
        """Test send_mouse_abs with buttons = 0x07."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_ABS | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_abs(0, 0, 0x07)
        
        assert result is True
    
    def test_send_mouse_abs_buttons_boundary_min(self):
        """Test send_mouse_abs with buttons = 0x00."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_ABS | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_abs(0, 0, 0x00)
        
        assert result is True
    
    def test_send_mouse_abs_x_boundary_max(self):
        """Test send_mouse_abs with x = 4095."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_ABS | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_abs(4095, 0)
        
        assert result is True
    
    def test_send_mouse_abs_x_boundary_min(self):
        """Test send_mouse_abs with x = 0."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_ABS | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_abs(0, 0)
        
        assert result is True
    
    def test_send_mouse_abs_y_boundary_max(self):
        """Test send_mouse_abs with y = 4095."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_ABS | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_abs(0, 4095)
        
        assert result is True
    
    def test_send_mouse_abs_y_boundary_min(self):
        """Test send_mouse_abs with y = 0."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SEND_MS_ABS | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.send_mouse_abs(0, 0)
        
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
