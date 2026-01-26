#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.ch9329 import (
    CH9329,
    CMD_SET_USB_STRING,
    USB_STRING_VENDOR,
    USB_STRING_PRODUCT,
    USB_STRING_SERIAL,
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


class TestSetUsbDescriptor:
    """Test set_usb_descriptor method."""
    
    def test_set_vendor_descriptor_success(self):
        """Test setting vendor descriptor successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_VENDOR, "TestVendor")
        
        assert result is True
    
    def test_set_product_descriptor_success(self):
        """Test setting product descriptor successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_PRODUCT, "TestProduct")
        
        assert result is True
    
    def test_set_serial_descriptor_success(self):
        """Test setting serial descriptor successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_SERIAL, "SN1234567")
        
        assert result is True
    
    def test_set_empty_descriptor(self):
        """Test setting empty descriptor (length 0)."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_VENDOR, "")
        
        assert result is True
    
    def test_set_max_length_descriptor(self):
        """Test setting descriptor with maximum length (23 bytes)."""
        ch9329 = CH9329(MockTransport())
        test_string = "A" * 23
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_VENDOR, test_string)
        
        assert result is True
    
    def test_set_ascii_descriptor(self):
        """Test setting descriptor with ASCII characters."""
        ch9329 = CH9329(MockTransport())
        test_string = "TestVendor123"
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_VENDOR, test_string)
        
        assert result is True
    
    def test_non_ascii_characters_raise_error(self):
        """Test that non-ASCII characters raise ValueError."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="String contains non-ASCII characters"):
            ch9329.set_usb_descriptor(USB_STRING_VENDOR, "测试中文")
    
    def test_invalid_string_type(self):
        """Test setting descriptor with invalid string type."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="string_type must be"):
            ch9329.set_usb_descriptor(0x03, "Test")
    
    def test_string_too_long(self):
        """Test setting descriptor with string too long (> 23 bytes)."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="String too long"):
            ch9329.set_usb_descriptor(USB_STRING_VENDOR, "A" * 24)
    
    def test_command_failure_returns_false(self):
        """Test that command failure returns False."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = None
        
        result = ch9329.set_usb_descriptor(USB_STRING_VENDOR, "TestVendor")
        
        assert result is False
    
    def test_command_frame_structure(self):
        """Test that command frame is built correctly."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        test_string = "TestVendor"
        ch9329.set_usb_descriptor(USB_STRING_VENDOR, test_string)
        
        frame = ch9329.t.write_data
        assert frame[0:2] == b"\x57\xab"
        assert frame[2] == 0x00
        assert frame[3] == CMD_SET_USB_STRING
        
        # Payload: string_type(1) + string_length(1) + string_data(N)
        assert frame[4] == 2 + len(test_string)
        assert frame[5] == USB_STRING_VENDOR
        assert frame[6] == len(test_string)
        assert frame[7:7 + len(test_string)] == test_string.encode('ascii')
        assert frame[7 + len(test_string)] == calculate_checksum(frame[0:7 + len(test_string)])
    
    def test_ascii_encoding(self):
        """Test that ASCII string is correctly encoded."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([ACK_STATUS_SUCCESS])
        )
        
        test_string = "Test123"
        ch9329.set_usb_descriptor(USB_STRING_VENDOR, test_string)
        
        frame = ch9329.t.write_data
        # "Test123" in ASCII is 7 bytes
        assert frame[6] == 7
        assert frame[7:14] == test_string.encode('ascii')
    
    def test_device_error_status(self):
        """Test handling of device error status."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_SET_USB_STRING | 0x80,
            bytes([0x01])  # Error status
        )
        
        result = ch9329.set_usb_descriptor(USB_STRING_VENDOR, "TestVendor")
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
