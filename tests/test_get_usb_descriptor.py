#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.ch9329 import (
    CH9329,
    CMD_GET_USB_STRING,
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


class TestGetUsbDescriptor:
    """Test get_usb_descriptor method."""
    
    def test_get_vendor_descriptor_success(self):
        """Test getting vendor descriptor successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 12]) + b"TestVendor"
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result == "TestVendor"
    
    def test_get_product_descriptor_success(self):
        """Test getting product descriptor successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_PRODUCT, 11]) + b"TestProduct"
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_PRODUCT)
        
        assert result == "TestProduct"
    
    def test_get_serial_descriptor_success(self):
        """Test getting serial descriptor successfully."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_SERIAL, 10]) + b"SN1234567"
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_SERIAL)
        
        assert result == "SN1234567"
    
    def test_get_empty_descriptor(self):
        """Test getting empty descriptor (length 0)."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 0])
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result == ""
    
    def test_get_max_length_descriptor(self):
        """Test getting descriptor with maximum length (23 bytes)."""
        ch9329 = CH9329(MockTransport())
        test_string = "A" * 23
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 23]) + test_string.encode('ascii')
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result == test_string
    
    def test_get_ascii_descriptor(self):
        """Test getting descriptor with ASCII characters."""
        ch9329 = CH9329(MockTransport())
        test_string = "TestVendor123"
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 13]) + test_string.encode('ascii')
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result == test_string
    
    def test_invalid_string_type(self):
        """Test getting descriptor with invalid string type."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="string_type must be"):
            ch9329.get_usb_descriptor(0x03)
    
    def test_command_failure_returns_none(self):
        """Test that command failure returns None."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = None
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result is None
    
    def test_invalid_response_length(self):
        """Test handling of invalid response length."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR])
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result is None
    
    def test_string_type_mismatch(self):
        """Test handling of string type mismatch in response."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_PRODUCT, 10]) + b"TestVendor"
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result is None
    
    def test_invalid_string_length(self):
        """Test handling of invalid string length (> 23)."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 24]) + b"X" * 24
        )
        
        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        assert result is None
    
    def test_invalid_ascii_data(self):
        """Test handling of invalid ASCII data."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 3]) + b"\xFF\xFE\xFD"
        )

        result = ch9329.get_usb_descriptor(USB_STRING_VENDOR)

        assert result == str(b"\xFF\xFE\xFD")
    
    def test_command_frame_structure(self):
        """Test that command frame is built correctly."""
        ch9329 = CH9329(MockTransport())
        ch9329.t.response_data = build_response(
            CMD_GET_USB_STRING | 0x80,
            bytes([USB_STRING_VENDOR, 10]) + b"TestVendor"
        )
        
        ch9329.get_usb_descriptor(USB_STRING_VENDOR)
        
        frame = ch9329.t.write_data
        assert frame[0:2] == b"\x57\xab"
        assert frame[2] == 0x00
        assert frame[3] == CMD_GET_USB_STRING
        assert frame[4] == 1
        assert frame[5] == USB_STRING_VENDOR
        assert frame[6] == calculate_checksum(frame[0:6])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
