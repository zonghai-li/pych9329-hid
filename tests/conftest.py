"""
Shared test fixtures and utilities for all test modules.
"""
import pytest
from pych9329_hid import CH9329
from pych9329_hid.ch9329 import ACK_STATUS_SUCCESS


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

    def send_mouse_abs(self, x, y, buttons=0, wheel=0):
        self.mouse_calls.append(('abs', x, y, buttons, wheel))

    def send_mouse_rel(self, dx=0, dy=0, buttons=0, wheel=0):
        self.mouse_calls.append(('rel', dx, dy, buttons, wheel))


class FakeTransportWithFakeCH:
    """
    Mock transport that wraps FakeCH for testing.
    Processes CH9329 frames and calls appropriate FakeCH methods.
    """
    def __init__(self):
        self._hid = FakeCH()
        self.writes = []
        self._responses = []
        self._has_written = False

    def write(self, data):
        self.writes.append(data)
        self._has_written = True
        self._process_frame(data)

    def _process_frame(self, data):
        """Process CH9329 frame and call appropriate FakeCH method."""
        if len(data) < 6:
            return
        
        # Parse frame: HEAD(2) + ADDR(1) + CMD(1) + LEN(1) + DATA(N) + CS(1)
        if data[0:2] != b'\x57\xAB':
            return
        
        cmd = data[3]
        length = data[4]
        payload = data[5:5+length]
        
        # Command Codes
        CMD_SEND_KEY = 0x02
        CMD_SEND_MS_REL = 0x05
        CMD_SEND_MS_ABS = 0x04
        
        if cmd == CMD_SEND_KEY:
            # Keyboard report: modifier, reserved, 6 keycodes
            if len(payload) >= 8:
                modifier = payload[0]
                keycodes = list(payload[2:8])
                self._hid.send_keyboard(modifier, keycodes)
        
        elif cmd == CMD_SEND_MS_REL:
            # Relative mouse: mode, buttons, dx, dy, wheel
            if len(payload) >= 5:
                buttons = payload[1]
                dx = self._to_signed(payload[2])
                dy = self._to_signed(payload[3])
                wheel = self._to_signed(payload[4])
                self._hid.send_mouse_rel(dx, dy, buttons, wheel)
        
        elif cmd == CMD_SEND_MS_ABS:
            # Absolute mouse: mode, buttons, x_low, x_high, y_low, y_high, wheel
            if len(payload) >= 7:
                buttons = payload[1]
                x = payload[2] | (payload[3] << 8)
                y = payload[4] | (payload[5] << 8)
                wheel = self._to_signed(payload[6])
                self._hid.send_mouse_abs(x, y, buttons, wheel)

    def _to_signed(self, v: int) -> int:
        """Convert unsigned byte to signed value."""
        if v >= 128:
            return v - 256
        return v

    def read(self, size=64):
        if size >= 128:
            return b''
        if not self._responses or not self._has_written:
            return b''
        return self._responses.pop(0)


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


def build_ack(cmd, frame_head=b'\x57\xAB', addr_default=0x00, status=ACK_STATUS_SUCCESS):
    """
    Build an ACK response frame for testing.
    
    Args:
        cmd: Command byte to acknowledge
        frame_head: Frame header bytes (default: 0x57 0xAB)
        addr_default: Device address (default: 0x00)
        status: Status byte (default: ACK_STATUS_SUCCESS = 0x00)
    
    Returns:
        bytes: Complete ACK frame
    """
    data = bytes([status])
    length = len(data)
    cmd_response = cmd | 0x80
    frame_without_checksum = frame_head + bytes([addr_default, cmd_response, length]) + data
    checksum = sum(frame_without_checksum) & 0xFF
    return frame_without_checksum + bytes([checksum])


@pytest.fixture
def fake_ch():
    """Fixture providing a FakeCH mock device."""
    return FakeCH()


@pytest.fixture
def fake_transport():
    """Fixture providing a FakeTransport mock transport."""
    return FakeTransport()
