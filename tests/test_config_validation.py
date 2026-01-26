#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pych9329_hid.config import CH9329Config


class TestConfigValidation:
    """Test validation in CH9329Config."""
    
    def test_validate_with_valid_data_length(self):
        """Test validate with correct data length."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[3:7] = (9600).to_bytes(4, byteorder='big')  # Set valid baudrate
        config = CH9329Config(data)
        
        # Should not raise any exception
        config.validate()
    
    def test_validate_with_invalid_work_mode(self):
        """Test validate with invalid work mode."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[0] = 0x04  # Invalid work mode
        data[3:7] = (9600).to_bytes(4, byteorder='big')  # Set valid baudrate
        config = CH9329Config(data)
        
        with pytest.raises(ValueError, match="Work mode must be"):
            config.validate()
    
    def test_validate_with_invalid_serial_mode(self):
        """Test validate with invalid serial mode."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[1] = 0x03  # Invalid serial mode
        data[3:7] = (9600).to_bytes(4, byteorder='big')  # Set valid baudrate
        config = CH9329Config(data)
        
        with pytest.raises(ValueError, match="Serial mode must be"):
            config.validate()
    
    def test_validate_with_invalid_baudrate(self):
        """Test validate with invalid baudrate."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[3:7] = (0).to_bytes(4, byteorder='big')  # Invalid baudrate (0)
        config = CH9329Config(data)
        
        with pytest.raises(ValueError, match="Baud rate must be"):
            config.validate()
    
    def test_validate_with_invalid_auto_enter_flag(self):
        """Test validate with invalid auto enter flag."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[19] = 0x02  # Invalid auto enter flag (> 1)
        data[3:7] = (9600).to_bytes(4, byteorder='big')  # Set valid baudrate
        config = CH9329Config(data)
        
        with pytest.raises(ValueError, match="Auto enter flag must be"):
            config.validate()
    
    def test_validate_with_invalid_keyboard_fast_upload(self):
        """Test validate with invalid keyboard fast upload."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[37] = 0x02  # Invalid fast upload (> 1)
        data[3:7] = (9600).to_bytes(4, byteorder='big')  # Set valid baudrate
        config = CH9329Config(data)
        
        with pytest.raises(ValueError, match="Keyboard fast upload must be"):
            config.validate()
    
    def test_validate_with_invalid_enter_characters(self):
        """Test validate with invalid enter characters (non-ASCII)."""
        from pych9329_hid.config import VALID_BAUDRATES
        data = bytearray(50)
        data[20] = 0x80  # Invalid enter character (> 0x7F)
        data[3:7] = (9600).to_bytes(4, byteorder='big')  # Set valid baudrate
        config = CH9329Config(data)
        
        with pytest.raises(ValueError, match="Enter character at position 0 must be"):
            config.validate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
