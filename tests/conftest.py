"""
Shared test fixtures and utilities for all test modules.
"""
import pytest


class FakeCH:
    """
    Mock CH9329 device for testing HIDController without hardware.
    Tracks all keyboard and mouse calls made by HIDController.
    """
    def __init__(self):
        self.keyboard_reports = []
        self.mouse_calls = []
        self.key_released = False

    def send_keyboard(self, modifier, keycodes):
        self.keyboard_reports.append((modifier, list(keycodes)))

    def key_release(self):
        self.key_released = True

    def send_mouse_abs(self, x, y, buttons=0):
        self.mouse_calls.append(('abs', x, y, buttons))

    def send_mouse_rel(self, dx=0, dy=0, buttons=0, wheel=0):
        self.mouse_calls.append(('rel', dx, dy, buttons, wheel))


class FakeTransport:
    """
    Mock transport layer for testing CH9329 without actual serial connection.
    """
    def __init__(self):
        self.writes = []
        self._responses = []
        self._has_written = False

    def write(self, data):
        self.writes.append(data)
        self._has_written = True

    def read(self, size=64):
        if size >= 128:
            return b''
        if not self._responses or not self._has_written:
            return b''
        return self._responses.pop(0)


def build_ack(cmd, frame_head=b'\x57\xAB', addr_default=0x00):
    """
    Build an ACK response frame for testing.
    
    Args:
        cmd: Command byte to acknowledge
        frame_head: Frame header bytes (default: 0x57 0xAB)
        addr_default: Device address (default: 0x00)
    
    Returns:
        bytes: Complete ACK frame
    """
    return frame_head + bytes([addr_default, (cmd | 0x80), 0x00, 0x00])


@pytest.fixture
def fake_ch():
    """Fixture providing a FakeCH mock device."""
    return FakeCH()


@pytest.fixture
def fake_transport():
    """Fixture providing a FakeTransport mock transport."""
    return FakeTransport()
