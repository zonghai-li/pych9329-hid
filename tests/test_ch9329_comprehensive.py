"""
Comprehensive tests for CH9329 protocol implementation.
"""
import pytest
from pych9329_hid.ch9329 import CH9329, FRAME_HEAD, ADDR_DEFAULT, CMD_SEND_KEY, CMD_SEND_MS_REL, CMD_SEND_MS_ABS
from conftest import FakeTransport, build_ack


class TestCH9329Checksum:
    """Test checksum calculation for data integrity."""
    
    def test_checksum_simple_data(self, fake_transport):
        """Test checksum calculation with simple data."""
        ch = CH9329(fake_transport)
        data = b'\x57\xAB\x00\x02\x01\x00'
        expected_checksum = sum(data) & 0xFF
        assert ch._calculate_checksum(data) == expected_checksum
    
    def test_checksum_all_zeros(self, fake_transport):
        """Test checksum with all zeros."""
        ch = CH9329(fake_transport)
        data = b'\x00\x00\x00\x00\x00\x00'
        assert ch._calculate_checksum(data) == 0
    
    def test_checksum_max_values(self, fake_transport):
        """Test checksum with maximum byte values."""
        ch = CH9329(fake_transport)
        data = b'\xFF\xFF\xFF\xFF\xFF\xFF'
        expected_checksum = sum(data) & 0xFF
        assert ch._calculate_checksum(data) == expected_checksum


class TestCH9329Keyboard:
    """Test keyboard report sending functionality."""
    
    def test_send_keyboard_basic(self, fake_transport):
        """Test sending a basic keyboard report."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_KEY))
        
        ch.send_keyboard(modifier=0x02, keycodes=[0x04, 0x05])
        
        assert len(fake_transport.writes) >= 1
        assert fake_transport._has_written
    
    def test_send_keyboard_no_keycodes(self, fake_transport):
        """Test sending keyboard report with no keycodes."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_KEY))
        
        ch.send_keyboard(modifier=0x00, keycodes=[])
        
        assert len(fake_transport.writes) >= 1
    
    def test_send_keyboard_multiple_reports(self, fake_transport):
        """Test sending multiple keyboard reports in sequence."""
        ch = CH9329(fake_transport)
        fake_transport._responses.extend([
            build_ack(CMD_SEND_KEY),
            build_ack(CMD_SEND_KEY),
            build_ack(CMD_SEND_KEY)
        ])
        
        ch.send_keyboard(0x01, [0x04])
        ch.send_keyboard(0x02, [0x05])
        ch.send_keyboard(0x00, [])
        
        assert len(fake_transport.writes) == 3


class TestCH9329MouseRelative:
    """Test relative mouse movement functionality."""
    
    def test_send_mouse_rel_basic(self, fake_transport):
        """Test sending basic relative mouse movement."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=10, dy=5, buttons=0x01, wheel=0)
        
        assert len(fake_transport.writes) >= 1
    
    def test_send_mouse_rel_clamping_positive(self, fake_transport):
        """Test that positive values are clamped to maximum (127)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=300, dy=200, buttons=0x03, wheel=5)
        
        last_frame = fake_transport.writes[-1]
        assert last_frame[7] == 127  # dx clamped
        assert last_frame[8] == 127  # dy clamped
    
    def test_send_mouse_rel_clamping_negative(self, fake_transport):
        """Test that negative values are clamped to minimum (-127)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=-300, dy=-200, buttons=0x03, wheel=5)
        
        last_frame = fake_transport.writes[-1]
        assert last_frame[7] == 129  # dx clamped (-127 & 0xFF)
        assert last_frame[8] == 129  # dy clamped (-127 & 0xFF)
    
    def test_send_mouse_rel_zero_movement(self, fake_transport):
        """Test sending zero movement with button state."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=0, dy=0, buttons=0x01, wheel=0)
        
        assert len(fake_transport.writes) >= 1
        last_frame = fake_transport.writes[-1]
        assert last_frame[6] == 0x01  # button state


class TestCH9329MouseAbsolute:
    """Test absolute mouse positioning functionality."""
    
    def test_send_mouse_abs_basic(self, fake_transport):
        """Test sending basic absolute mouse position."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))
        
        ch.send_mouse_abs(x=100, y=200, buttons=0x01, wheel=0)
        
        assert len(fake_transport.writes) >= 1
    
    def test_send_mouse_abs_clamping_positive(self, fake_transport):
        """Test that coordinates are clamped to maximum (4095)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))
        
        ch.send_mouse_abs(x=5000, y=6000, buttons=0x02, wheel=-10)
        
        last_frame = fake_transport.writes[-1]
        x_low = last_frame[7]
        x_high = last_frame[8]
        x_val = x_low | (x_high << 8)
        assert x_val == 4095  # x clamped to max
    
    def test_send_mouse_abs_clamping_negative(self, fake_transport):
        """Test that negative coordinates are clamped to minimum (0)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))
        
        ch.send_mouse_abs(x=-100, y=-50, buttons=0x02, wheel=-10)
        
        last_frame = fake_transport.writes[-1]
        x_low = last_frame[7]
        x_high = last_frame[8]
        x_val = x_low | (x_high << 8)
        assert x_val == 0  # x clamped to min
    
    def test_send_mouse_abs_boundary_values(self, fake_transport):
        """Test mouse absolute positioning at boundary values."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))

        ch.send_mouse_abs(x=0, y=0, buttons=0x00, wheel=0)
        ch.send_mouse_abs(x=4095, y=4095, buttons=0x00, wheel=0)

        assert len(fake_transport.writes) == 2


class TestCH9329FrameSending:
    """Test frame sending and error handling."""
    
    def test_send_frame_timeout(self, fake_transport):
        """Test that timeout returns None and issues warning when no response received."""
        import warnings
        ch = CH9329(fake_transport)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = ch._send_frame(0x99, b'')
            assert result is None
            assert len(w) == 4  # 3 retry warnings + 1 final failure warning
            assert "Failed to send CMD 0x99 after 3 retries" in str(w[3].message)  # Check the final warning
    
    def test_send_frame_success(self, fake_transport):
        """Test successful frame sending with ACK response."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(0x99))
        
        result = ch._send_frame(0x99, b'\x01\x02')
        
        assert result is not None
    
    def test_send_frame_multiple_writes(self, fake_transport):
        """Test that multiple writes are tracked correctly."""
        ch = CH9329(fake_transport)
        fake_transport._responses.extend([
            build_ack(CMD_SEND_KEY),
            build_ack(CMD_SEND_KEY)
        ])
        
        ch.send_keyboard(0x01, [0x04])
        ch.send_keyboard(0x02, [0x05])
        
        assert len(fake_transport.writes) == 2


class TestCH9329SignedCharConversion:
    """Test signed char conversion for relative movement."""
    
    def test_to_signed_char_positive(self, fake_transport):
        """Test conversion of positive values."""
        ch = CH9329(fake_transport)
        
        assert ch._to_signed_char(0) == 0
        assert ch._to_signed_char(100) == 100
        assert ch._to_signed_char(127) == 127
    
    def test_to_signed_char_negative(self, fake_transport):
        """Test conversion of negative values."""
        ch = CH9329(fake_transport)
        
        assert ch._to_signed_char(-1) == 0xFF
        assert ch._to_signed_char(-100) == 156
        assert ch._to_signed_char(-127) == 129
    
    def test_to_signed_char_clamping(self, fake_transport):
        """Test that values are clamped to signed char range."""
        ch = CH9329(fake_transport)
        
        assert ch._to_signed_char(200) == 127
        assert ch._to_signed_char(-200) == 129
        assert ch._to_signed_char(1000) == 127
        assert ch._to_signed_char(-1000) == 129
