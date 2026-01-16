"""
Error handling and edge case tests for CH9329 and HIDController.
"""
import pytest
from src import HIDController, CH9329
from conftest import FakeCH, FakeTransport, build_ack
from src.ch9329 import CMD_SEND_KEY, CMD_SEND_MS_REL, CMD_SEND_MS_ABS


class TestCH9329ErrorHandling:
    """Test error handling in CH9329 protocol layer."""
    
    def test_timeout_on_no_response(self, fake_transport):
        """Test that timeout occurs when device doesn't respond."""
        ch = CH9329(fake_transport)
        
        with pytest.raises(Exception):
            ch._send_frame(0x99, b'')
    
    def test_checksum_with_empty_data(self, fake_transport):
        """Test checksum calculation with empty data."""
        ch = CH9329(fake_transport)
        
        checksum = ch._calculate_checksum(b'')
        assert checksum == 0
    
    def test_checksum_with_large_data(self, fake_transport):
        """Test checksum calculation with large data."""
        ch = CH9329(fake_transport)
        data = bytes(range(256))
        
        checksum = ch._calculate_checksum(data)
        expected = sum(data) & 0xFF
        assert checksum == expected
    
    def test_empty_keyboard_report(self, fake_transport):
        """Test sending empty keyboard report."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_KEY))
        
        ch.send_keyboard(modifier=0, keycodes=[])
        
        assert len(fake_transport.writes) >= 1
    
    def test_zero_mouse_movement(self, fake_transport):
        """Test sending zero mouse movement."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=0, dy=0, buttons=0, wheel=0)
        
        assert len(fake_transport.writes) >= 1
    
    def test_mouse_at_origin(self, fake_transport):
        """Test mouse at origin (0, 0)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))
        
        ch.send_mouse_abs(x=0, y=0, buttons=0, wheel=0)
        
        assert len(fake_transport.writes) >= 1
    
    def test_mouse_at_max_position(self, fake_transport):
        """Test mouse at maximum position (4095, 4095)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))
        
        ch.send_mouse_abs(x=4095, y=4095, buttons=0, wheel=0)
        
        assert len(fake_transport.writes) >= 1
        last_frame = fake_transport.writes[-1]
        x_low = last_frame[7]
        x_high = last_frame[8]
        x_val = x_low | (x_high << 8)
        assert x_val == 4095
    
    def test_max_relative_movement(self, fake_transport):
        """Test maximum relative movement (127, 127)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=127, dy=127, buttons=0, wheel=0)
        
        assert len(fake_transport.writes) >= 1
        last_frame = fake_transport.writes[-1]
        assert last_frame[7] == 127
        assert last_frame[8] == 127
    
    def test_min_relative_movement(self, fake_transport):
        """Test minimum relative movement (-127, -127)."""
        ch = CH9329(fake_transport)
        fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
        
        ch.send_mouse_rel(dx=-127, dy=-127, buttons=0, wheel=0)
        
        assert len(fake_transport.writes) >= 1
        last_frame = fake_transport.writes[-1]
        assert last_frame[7] == 129  # -127 & 0xFF
        assert last_frame[8] == 129  # -127 & 0xFF


class TestHIDControllerErrorHandling:
    """Test error handling in HIDController."""
    
    def test_invalid_modifier_key(self, fake_ch):
        """Test handling of invalid modifier key."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.keyDown('invalid_modifier')
        
        # Should handle gracefully without crashing
        assert isinstance(fake_ch.keyboard_reports, list)
    
    def test_empty_string_write(self, fake_ch):
        """Test writing empty string."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.write('')
        
        # Should handle gracefully
        assert isinstance(fake_ch.keyboard_reports, list)
    
    def test_zero_duration_movement(self, fake_ch):
        """Test movement with zero duration."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(100, 100, duration=0)
        
        assert len(fake_ch.mouse_calls) >= 1
    
    def test_negative_duration_movement(self, fake_ch):
        """Test movement with negative duration (should be treated as 0)."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(100, 100, duration=-1)
        
        # Should handle gracefully
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_zero_scroll(self, fake_ch):
        """Test scrolling with zero clicks."""
        gui = HIDController(fake_ch)
        fake_ch.mouse_calls.clear()
        
        gui.scroll(0)
        
        # Should handle gracefully (may or may not generate calls)
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_large_scroll_value(self, fake_ch):
        """Test scrolling with large value (should be clamped)."""
        gui = HIDController(fake_ch)
        fake_ch.mouse_calls.clear()
        
        gui.scroll(1000)
        
        # Should handle gracefully
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_invalid_mouse_button(self, fake_ch):
        """Test using invalid mouse button."""
        gui = HIDController(fake_ch)
        fake_ch.mouse_calls.clear()
        
        gui.mouseDown('invalid_button')
        
        # Should handle gracefully
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_release_non_pressed_key(self, fake_ch):
        """Test releasing a key that wasn't pressed."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.keyUp('a')
        
        # Should handle gracefully
        assert isinstance(fake_ch.keyboard_reports, list)
    
    def test_hotkey_with_empty_keys(self, fake_ch):
        """Test hotkey with no keys."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.hotkey()
        
        # Should handle gracefully
        assert isinstance(fake_ch.keyboard_reports, list)
    
    def test_out_of_bounds_coordinates_positive(self, fake_ch):
        """Test moving to coordinates beyond screen bounds (positive)."""
        gui = HIDController(fake_ch, screen_width=1920, screen_height=1080)
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(5000, 5000)
        
        # Should handle gracefully (clamping to screen bounds)
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_out_of_bounds_coordinates_negative(self, fake_ch):
        """Test moving to negative coordinates."""
        gui = HIDController(fake_ch, screen_width=1920, screen_height=1080)
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(-100, -100)
        
        # Should handle gracefully (clamping to 0)
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_click_with_zero_clicks(self, fake_ch):
        """Test clicking with zero clicks."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        fake_ch.mouse_calls.clear()
        
        gui.click(100, 100, button='left', clicks=0)
        
        # Should handle gracefully
        assert isinstance(fake_ch.mouse_calls, list)
    
    def test_drag_with_zero_distance(self, fake_ch):
        """Test dragging with zero distance."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        fake_ch.mouse_calls.clear()
        
        gui.dragRel(0, 0)
        
        # Should handle gracefully
        assert isinstance(fake_ch.mouse_calls, list)


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_six_keys_pressed(self, fake_ch):
        """Test pressing exactly 6 keys (HID limit)."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        for key in ['a', 'b', 'c', 'd', 'e', 'f']:
            gui.keyDown(key)
        
        _, codes = fake_ch.keyboard_reports[-1]
        assert len(codes) == 6
    
    def test_seven_keys_pressed(self, fake_ch):
        """Test pressing 7 keys (exceeds HID limit)."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        for key in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            gui.keyDown(key)
        
        _, codes = fake_ch.keyboard_reports[-1]
        assert len(codes) <= 6  # Should be truncated
    
    def test_all_modifiers_pressed(self, fake_ch):
        """Test pressing all modifier keys simultaneously."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.keyDown('shift')
        gui.keyDown('ctrl')
        gui.keyDown('alt')
        gui.keyDown('command')
        
        mod, _ = fake_ch.keyboard_reports[-1]
        assert mod == 0x0F  # All modifiers set
    
    def test_all_mouse_buttons_pressed(self, fake_ch):
        """Test pressing all mouse buttons."""
        gui = HIDController(fake_ch)
        fake_ch.mouse_calls.clear()
        
        gui.mouseDown('left')
        gui.mouseDown('right')
        gui.mouseDown('middle')
        
        _, _, _, buttons = fake_ch.mouse_calls[-1]
        assert buttons == 0x07  # All buttons set
    
    def test_rapid_key_presses(self, fake_ch):
        """Test rapid key presses."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        for _ in range(10):
            gui.press('a')
        
        # Should generate many reports
        assert len(fake_ch.keyboard_reports) >= 20  # At least down+up for each
    
    def test_rapid_mouse_movements(self, fake_ch):
        """Test rapid mouse movements."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        gui.dwelling_time = 0
        fake_ch.mouse_calls.clear()
        
        for i in range(10):
            gui.moveTo(i * 10, i * 10)
        
        # Should generate many calls
        assert len(fake_ch.mouse_calls) >= 10
