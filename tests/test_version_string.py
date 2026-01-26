#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.ch9329 import CH9329


class MockTransport:
    """Mock transport for testing."""
    
    def write(self, data):
        """Store written data."""
        pass
    
    def read(self, expected_length):
        """Return mock response."""
        return None
    
    def read_all(self):
        """Clear buffer."""
        pass


class TestVersionString:
    """Test version string functionality."""
    
    def test_version_v1_0(self):
        """Test V1.0 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x30)
        assert result == "V1.0"
    
    def test_version_v1_1(self):
        """Test V1.1 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x31)
        assert result == "V1.1"
    
    def test_version_v1_2(self):
        """Test V1.2 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x32)
        assert result == "V1.2"
    
    def test_version_v1_3(self):
        """Test V1.3 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x33)
        assert result == "V1.3"
    
    def test_version_v1_4(self):
        """Test V1.4 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x34)
        assert result == "V1.4"
    
    def test_version_v1_5(self):
        """Test V1.5 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x35)
        assert result == "V1.5"
    
    def test_version_v1_6(self):
        """Test V1.6 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x36)
        assert result == "V1.6"
    
    def test_version_v1_7(self):
        """Test V1.7 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x37)
        assert result == "V1.7"
    
    def test_version_v1_8(self):
        """Test V1.8 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x38)
        assert result == "V1.8"
    
    def test_version_v1_9(self):
        """Test V1.9 version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x39)
        assert result == "V1.9"
    
    def test_unknown_version(self):
        """Test unknown version string."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0xFF)
        assert result == "Unknown (0xFF)"
    
    def test_version_below_range(self):
        """Test version byte below valid range."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x2F)
        assert result == "Unknown (0x2F)"
    
    def test_version_above_range(self):
        """Test version byte above valid range."""
        ch9329 = CH9329(MockTransport())
        result = ch9329._get_version_string(0x3A)
        assert result == "Unknown (0x3A)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
