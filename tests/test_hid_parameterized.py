"""
Parameterized tests for HIDController keyboard and mouse operations.
"""
import pytest
from src import HIDController
from conftest import FakeCH


class TestKeyboardParameterized:
    """Parameterized tests for keyboard operations."""
    
    @pytest.mark.parametrize("key,expected_modifier", [
        ('shift', 0x02),
        ('ctrl', 0x01),
        ('alt', 0x04),
        ('command', 0x08),
        ('cmd', 0x08),
    ])
    def test_modifier_key_down(self, fake_ch, key, expected_modifier):
        """Test that modifier keys set the correct modifier byte."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.keyDown(key)
        
        assert len(fake_ch.keyboard_reports) >= 1
        mod, _ = fake_ch.keyboard_reports[-1]
        assert mod == expected_modifier
    
    @pytest.mark.parametrize("key,expected_modifier", [
        ('shift', 0x02),
        ('ctrl', 0x01),
        ('alt', 0x04),
        ('command', 0x08),
    ])
    def test_modifier_key_up(self, fake_ch, key, expected_modifier):
        """Test that releasing modifier keys clears the modifier byte."""
        gui = HIDController(fake_ch)
        gui.keyDown(key)
        fake_ch.keyboard_reports.clear()
        
        gui.keyUp(key)
        
        assert len(fake_ch.keyboard_reports) >= 1
        mod, _ = fake_ch.keyboard_reports[-1]
        assert mod == 0x00
    
    @pytest.mark.parametrize("text", [
        'a',
        'abc',
        'Hello World',
        '123',
        '!@#',
    ])
    def test_write_text(self, fake_ch, text):
        """Test writing various text strings."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.write(text)
        
        # Each character should generate at least 2 reports (down and up)
        assert len(fake_ch.keyboard_reports) >= len(text) * 2
    
    @pytest.mark.parametrize("keys", [
        ('command', 'a'),
        ('ctrl', 'c'),
        ('shift', 'command', '4'),
        ('command', 'shift', '3'),
    ])
    def test_hotkey_combinations(self, fake_ch, keys):
        """Test various hotkey combinations."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.hotkey(*keys)
        
        # Hotkey should generate multiple reports
        assert len(fake_ch.keyboard_reports) >= 2


class TestMouseParameterized:
    """Parameterized tests for mouse operations."""
    
    @pytest.mark.parametrize("button,expected_mask", [
        ('left', 0x01),
        ('right', 0x02),
        ('middle', 0x04),
    ])
    def test_mouse_button_down(self, fake_ch, button, expected_mask):
        """Test that mouse button down sets the correct button mask."""
        gui = HIDController(fake_ch)
        fake_ch.mouse_calls.clear()
        
        gui.mouseDown(button)
        
        assert len(fake_ch.mouse_calls) >= 1
        call_type, _, _, buttons = fake_ch.mouse_calls[-1]
        assert call_type == 'abs'
        assert buttons == expected_mask
    
    @pytest.mark.parametrize("button,expected_mask", [
        ('left', 0x01),
        ('right', 0x02),
        ('middle', 0x04),
    ])
    def test_mouse_button_up(self, fake_ch, button, expected_mask):
        """Test that mouse button up clears the button mask."""
        gui = HIDController(fake_ch)
        gui.mouseDown(button)
        fake_ch.mouse_calls.clear()
        
        gui.mouseUp(button)
        
        assert len(fake_ch.mouse_calls) >= 1
        call_type, _, _, buttons = fake_ch.mouse_calls[-1]
        assert call_type == 'abs'
        assert buttons == 0x00
    
    @pytest.mark.parametrize("x,y", [
        (0, 0),
        (100, 100),
        (500, 300),
        (1920, 1080),
        (50, 50),
    ])
    def test_move_to_coordinates(self, fake_ch, x, y):
        """Test moving mouse to various coordinates."""
        gui = HIDController(fake_ch, screen_width=1920, screen_height=1080)
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(x, y)
        
        assert len(fake_ch.mouse_calls) >= 1
        call_type, actual_x, actual_y, _ = fake_ch.mouse_calls[-1]
        assert call_type == 'abs'
        # Coordinates are mapped to device range (0-4095)
        assert 0 <= actual_x <= 4095
        assert 0 <= actual_y <= 4095
    
    @pytest.mark.parametrize("dx,dy", [
        (10, 10),
        (-10, -10),
        (100, 50),
        (-50, 100),
        (0, 0),
    ])
    def test_move_relative(self, fake_ch, dx, dy):
        """Test relative mouse movement in various directions."""
        gui = HIDController(fake_ch, screen_width=200, screen_height=200)
        fake_ch.mouse_calls.clear()
        
        gui.moveRel(dx, dy, duration=0)
        
        assert len(fake_ch.mouse_calls) >= 1
        # Internal coordinates should be updated
        assert gui._mouse_x == max(0, min(200, dx))
        assert gui._mouse_y == max(0, min(200, dy))
    
    @pytest.mark.parametrize("clicks", [
        1,
        2,
        3,
    ])
    def test_multiple_clicks(self, fake_ch, clicks):
        """Test clicking multiple times."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        fake_ch.mouse_calls.clear()
        
        gui.click(100, 100, button='left', clicks=clicks)
        
        # Each click should generate abs calls (move, down, up)
        abs_calls = [c for c in fake_ch.mouse_calls if c[0] == 'abs']
        assert len(abs_calls) >= clicks  # At least one abs call per click
    
    @pytest.mark.parametrize("scroll_direction,clicks", [
        ('up', 1),
        ('down', 1),
        ('up', 5),
        ('down', 5),
    ])
    def test_scroll_directions(self, fake_ch, scroll_direction, clicks):
        """Test scrolling in different directions."""
        gui = HIDController(fake_ch)
        fake_ch.mouse_calls.clear()
        
        if scroll_direction == 'up':
            gui.scroll(clicks)
        else:
            gui.scroll(-clicks)
        
        # Scroll should generate rel calls with wheel parameter
        rel_calls = [c for c in fake_ch.mouse_calls if c[0] == 'rel']
        assert len(rel_calls) >= 1
        # At least one call should have non-zero wheel
        assert any(c[4] != 0 for c in rel_calls)


class TestDragParameterized:
    """Parameterized tests for drag operations."""
    
    @pytest.mark.parametrize("dx,dy", [
        (10, 10),
        (50, 30),
        (20, 40),
        (-10, -10),
    ])
    def test_drag_relative(self, fake_ch, dx, dy):
        """Test relative drag with various parameters."""
        gui = HIDController(fake_ch, screen_width=300, screen_height=200)
        fake_ch.mouse_calls.clear()
        
        gui.dragRel(dx, dy)
        
        # Drag should generate abs calls (button state changes)
        abs_calls = [c for c in fake_ch.mouse_calls if c[0] == 'abs']
        assert len(abs_calls) >= 2  # At least down and up
    
    @pytest.mark.parametrize("x,y", [
        (100, 100),
        (200, 150),
        (50, 75),
    ])
    def test_drag_to(self, fake_ch, x, y):
        """Test drag to specific coordinates."""
        gui = HIDController(fake_ch, screen_width=300, screen_height=200)
        fake_ch.mouse_calls.clear()
        
        gui.dragTo(x, y)
        
        # Drag should generate abs calls
        abs_calls = [c for c in fake_ch.mouse_calls if c[0] == 'abs']
        assert len(abs_calls) >= 2


class TestEdgeCases:
    """Parameterized tests for edge cases."""
    
    @pytest.mark.parametrize("invalid_key", [
        'nonexistent',
        '',
        '🎵',
        '中文',
    ])
    def test_invalid_keys(self, fake_ch, invalid_key):
        """Test handling of invalid or unsupported keys."""
        gui = HIDController(fake_ch)
        fake_ch.keyboard_reports.clear()
        
        gui.keyDown(invalid_key)
        
        # Should handle gracefully without crashing
        # May or may not generate reports depending on implementation
    
    @pytest.mark.parametrize("x,y", [
        (-100, -100),
        (10000, 10000),
        (-50, 100),
        (100, -50),
    ])
    def test_out_of_bounds_coordinates(self, fake_ch, x, y):
        """Test handling of out-of-bounds coordinates."""
        gui = HIDController(fake_ch, screen_width=1920, screen_height=1080)
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(x, y)
        
        # Should handle gracefully, clamping to valid range
        assert len(fake_ch.mouse_calls) >= 1
    
    @pytest.mark.parametrize("duration", [
        0,
        0.1,
        1.0,
        2.5,
    ])
    def test_movement_durations(self, fake_ch, duration):
        """Test mouse movement with various durations."""
        gui = HIDController(fake_ch, screen_width=800, screen_height=600)
        gui.dwelling_time = 0  # Speed up tests
        fake_ch.mouse_calls.clear()
        
        gui.moveTo(100, 100, duration=duration)
        
        assert len(fake_ch.mouse_calls) >= 1
