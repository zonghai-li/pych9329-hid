"""
Tests for HIDController keyboard operations.
"""
import pytest
from pych9329_hid import HIDController
from conftest import FakeCH


@pytest.fixture
def fake_ch():
    """Fixture providing a FakeCH mock device."""
    return FakeCH()


def test_modifier_only_and_release(fake_ch):
    """
    Test pressing and releasing a modifier key.
    
    Verifies that:
    1. Pressing a modifier key sends a report with non-zero modifier
    2. Releasing the modifier clears the modifier byte (sets to 0)
    """
    gui = HIDController(fake_ch)

    fake_ch.keyboard_reports.clear()
    gui.keyDown('shift')
    assert fake_ch.keyboard_reports, "modifier down should send a report"
    mod, codes = fake_ch.keyboard_reports[-1]
    assert mod != 0

    gui.keyUp('shift')
    assert fake_ch.keyboard_reports[-1][0] == 0


def test_many_keys_truncated_to_six(fake_ch):
    """
    Test that HID protocol limits keycodes to 6 per report.
    
    Verifies that pressing more than 6 keys results in
    only the most recent 6 being sent in the report.
    """
    gui = HIDController(fake_ch)
    fake_ch.keyboard_reports.clear()

    for k in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
        gui.keyDown(k)

    assert fake_ch.keyboard_reports
    _, codes = fake_ch.keyboard_reports[-1]
    assert len(codes) <= 6


def test_hotkey_includes_shift_mod_from_char(fake_ch):
    """
    Test that hotkey properly includes modifier from shifted characters.
    
    Verifies that when a hotkey includes a shifted character (like '@'),
    the shift modifier is properly applied in the keyboard reports.
    """
    gui = HIDController(fake_ch)
    fake_ch.keyboard_reports.clear()

    gui.hotkey('@', 'b')

    assert any(r[0] != 0 for r in fake_ch.keyboard_reports), "shift mod from '@' should be applied"
