"""
Extended tests for HIDController operations.
"""
import pytest
from pych9329_hid import HIDController
from conftest import FakeCH


def test_moveRel_duration_zero_and_small_steps():
    """
    Test relative movement with zero duration and small steps.
    
    Verifies that:
    1. Movement is performed even with duration=0
    2. Internal coordinates are updated correctly
    3. Absolute mouse calls are generated (moveTo uses abs)
    """
    fake = FakeCH()
    gui = HIDController(fake, screen_width=200, screen_height=200)
    gui.dwelling_time = 0
    gui.move_interval = 0.001

    fake.mouse_calls.clear()

    gui.moveRel(10, 5, duration=0)
    assert any(c[0] == 'abs' for c in fake.mouse_calls)
    assert gui._mouse_x == 10
    assert gui._mouse_y == 5


def test_click_and_double_click_and_hscroll():
    """
    Test click, double-click, and horizontal scroll operations.
    
    Verifies that:
    1. Click generates absolute mouse calls
    2. Double-click generates multiple click sequences
    3. Scroll generates relative calls with wheel parameter
    4. Horizontal scroll generates keyboard modifier reports
    """
    fake = FakeCH()
    gui = HIDController(fake, screen_width=800, screen_height=600)
    gui.dwelling_time = 0
    gui.keypress_hold_time = 0
    gui.double_click_interval = 0
    gui.scroll_multiplier = 1

    fake.mouse_calls.clear()

    gui.click(50, 40, button='left', clicks=2)

    abs_calls = [c for c in fake.mouse_calls if c[0] == 'abs']
    assert len(abs_calls) >= 3

    fake.mouse_calls.clear()
    gui.scroll(2)
    rel_wheels = [c for c in fake.mouse_calls if c[0] == 'rel' and c[4] != 0]
    assert len(rel_wheels) >= 1

    fake.keyboard_reports.clear()
    fake.mouse_calls.clear()
    gui.hscroll(1)
    assert any(c[0] == 'rel' for c in fake.mouse_calls)
    assert fake.keyboard_reports
