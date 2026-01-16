"""
Tests for HIDController mouse operations.
"""
import pytest
from pych9329_hid import HIDController
from conftest import FakeCH


@pytest.fixture
def fake_ch():
    """Fixture providing a FakeCH mock device."""
    return FakeCH()


def test_move_rel_duration_zero_updates_state(fake_ch):
    """
    Test relative mouse movement with zero duration.
    
    Verifies that:
    1. Movement is performed even with duration=0
    2. Internal mouse coordinates are updated
    """
    gui = HIDController(fake_ch, screen_width=200, screen_height=100)
    fake_ch.mouse_calls.clear()

    gui.moveRel(10, 5, duration=0)
    assert fake_ch.mouse_calls
    assert gui._mouse_x != 0 or gui._mouse_y != 0


def test_scroll_and_hscroll_generate_wheel_calls(fake_ch):
    """
    Test vertical and horizontal scrolling.
    
    Verifies that:
    1. Vertical scroll generates rel calls with wheel parameter
    2. Horizontal scroll generates keyboard modifier reports (shift)
    """
    gui = HIDController(fake_ch)
    fake_ch.mouse_calls.clear()
    fake_ch.keyboard_reports.clear()

    gui.scroll(2)
    assert any(call[0] == 'rel' and call[4] != 0 for call in fake_ch.mouse_calls)

    fake_ch.mouse_calls.clear()
    gui.hscroll(1)
    assert any(r[0] != 0 for r in fake_ch.keyboard_reports)
    assert any(call[0] == 'rel' for call in fake_ch.mouse_calls)


def test_drag_to_and_rel(fake_ch):
    """
    Test drag operations (relative and absolute).
    
    Verifies that:
    1. Relative drag generates mouse movement calls
    2. Absolute drag generates mouse movement calls
    """
    gui = HIDController(fake_ch, screen_width=300, screen_height=200)
    fake_ch.mouse_calls.clear()

    gui.dragRel(20, 10)
    assert any(c[0] == 'rel' for c in fake_ch.mouse_calls)

    fake_ch.mouse_calls.clear()
    gui.dragTo(50, 40)
    assert any(c[0] == 'rel' or c[0] == 'abs' for c in fake_ch.mouse_calls)
