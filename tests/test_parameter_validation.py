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


class TestParameterValidation:
    """Test parameter validation in CH9329 methods."""
    
    def test_send_keyboard_invalid_modifier_too_high(self):
        """Test send_keyboard with modifier > 0xFF."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="modifier must be 0-0xFF"):
            ch9329.send_keyboard(0x100, [0x04])
    
    def test_send_keyboard_invalid_modifier_negative(self):
        """Test send_keyboard with negative modifier."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="modifier must be 0-0xFF"):
            ch9329.send_keyboard(-1, [0x04])
    
    def test_send_keyboard_too_many_keycodes(self):
        """Test send_keyboard with more than 6 keycodes."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="keycodes can have at most 6"):
            ch9329.send_keyboard(0x00, [0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A])
    
    def test_send_keyboard_invalid_keycode_type(self):
        """Test send_keyboard with non-integer keycode."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="keycode\\[0\\] must be 0-0xFF"):
            ch9329.send_keyboard(0x00, ["invalid"])
    
    def test_send_keyboard_invalid_keycode_too_high(self):
        """Test send_keyboard with keycode > 0xFF."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="keycode\\[0\\] must be 0-0xFF"):
            ch9329.send_keyboard(0x00, [0x100])
    
    def test_send_keyboard_invalid_keycode_negative(self):
        """Test send_keyboard with negative keycode."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="keycode\\[0\\] must be 0-0xFF"):
            ch9329.send_keyboard(0x00, [-1])
    
    def test_send_keyboard_multiple_invalid_keycodes(self):
        """Test send_keyboard with multiple invalid keycodes."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="keycode\\[2\\] must be 0-0xFF"):
            ch9329.send_keyboard(0x00, [0x04, 0x05, 0x100])
    
    def test_send_mouse_rel_invalid_buttons_too_high(self):
        """Test send_mouse_rel with buttons > 0x07."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="buttons must be 0-0x07"):
            ch9329.send_mouse_rel(0, 0, 0x08)
    
    def test_send_mouse_rel_invalid_buttons_negative(self):
        """Test send_mouse_rel with negative buttons."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="buttons must be 0-0x07"):
            ch9329.send_mouse_rel(0, 0, -1)
    
    def test_send_mouse_abs_invalid_buttons_too_high(self):
        """Test send_mouse_abs with buttons > 0x07."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="buttons must be 0-0x07"):
            ch9329.send_mouse_abs(0, 0, 0x08)
    
    def test_send_mouse_abs_invalid_buttons_negative(self):
        """Test send_mouse_abs with negative buttons."""
        ch9329 = CH9329(MockTransport())
        
        with pytest.raises(ValueError, match="buttons must be 0-0x07"):
            ch9329.send_mouse_abs(0, 0, -1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
