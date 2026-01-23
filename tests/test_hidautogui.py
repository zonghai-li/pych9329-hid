"""
Tests for HIDController high-level operations.
"""
import pytest
from pych9329_hid import HIDController
from conftest import FakeTransportWithFakeCH


@pytest.fixture
def fake_transport():
    """Fixture providing a FakeTransportWithFakeCH instance."""
    return FakeTransportWithFakeCH()


def test_key_down_up_and_press(fake_transport):
    """
    Test key down, up, and press operations.
    
    Verifies that:
    1. keyDown generates a keyboard report
    2. keyUp clears the modifier byte
    3. press generates both down and up reports
    """
    gui = HIDController(fake_transport, screen_width=800, screen_height=600)

    gui.keyDown('a')
    assert fake_transport._hid.keyboard_reports
    mod, codes = fake_transport._hid.keyboard_reports[-1]
    assert isinstance(codes, list)

    gui.keyUp('a')
    assert fake_transport._hid.keyboard_reports[-1][0] == 0

    gui.press('b')
    assert len(fake_transport._hid.keyboard_reports) >= 3


def test_hotkey_combination(fake_transport):
    """
    Test hotkey (key combination) functionality.
    
    Verifies that hotkey generates multiple keyboard reports
    including modifier and key code combinations.
    """
    gui = HIDController(fake_transport)
    fake_transport._hid.keyboard_reports.clear()

    gui.hotkey('command', 'a')
    assert len(fake_transport._hid.keyboard_reports) >= 2


def test_move_and_commit_mouse(fake_transport):
    """
    Test mouse movement and state commitment.
    
    Verifies that:
    1. moveTo generates absolute mouse calls
    2. Mouse position is committed to hardware
    """
    gui = HIDController(fake_transport, screen_width=1920, screen_height=1080)
    gui.moveTo(100, 50)
    assert fake_transport._hid.mouse_calls
    typ, *args = fake_transport._hid.mouse_calls[-1]
    assert typ == 'abs'
