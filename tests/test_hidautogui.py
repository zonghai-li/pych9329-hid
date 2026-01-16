"""
Tests for HIDController high-level operations.
"""
import pytest
from src import HIDController
from conftest import FakeCH


@pytest.fixture
def fake_ch():
    """Fixture providing a FakeCH mock device."""
    return FakeCH()


def test_key_down_up_and_press(fake_ch):
    """
    Test key down, up, and press operations.
    
    Verifies that:
    1. keyDown generates a keyboard report
    2. keyUp clears the modifier byte
    3. press generates both down and up reports
    """
    gui = HIDController(fake_ch, screen_width=800, screen_height=600)

    gui.keyDown('a')
    assert fake_ch.keyboard_reports
    mod, codes = fake_ch.keyboard_reports[-1]
    assert isinstance(codes, list)

    gui.keyUp('a')
    assert fake_ch.keyboard_reports[-1][0] == 0

    gui.press('b')
    assert len(fake_ch.keyboard_reports) >= 3


def test_hotkey_combination(fake_ch):
    """
    Test hotkey (key combination) functionality.
    
    Verifies that hotkey generates multiple keyboard reports
    including modifier and key code combinations.
    """
    gui = HIDController(fake_ch)
    fake_ch.keyboard_reports.clear()

    gui.hotkey('command', 'a')
    assert len(fake_ch.keyboard_reports) >= 2


def test_move_and_commit_mouse(fake_ch):
    """
    Test mouse movement and state commitment.
    
    Verifies that:
    1. moveTo generates absolute mouse calls
    2. Mouse position is committed to hardware
    """
    gui = HIDController(fake_ch, screen_width=1920, screen_height=1080)
    gui.moveTo(100, 50)
    assert fake_ch.mouse_calls
    typ, *args = fake_ch.mouse_calls[-1]
    assert typ == 'abs'

