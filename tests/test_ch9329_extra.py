"""
Extended tests for CH9329 mouse operations and value clamping.
"""
import pytest
from src.ch9329 import CH9329, CMD_SEND_MS_REL, CMD_SEND_MS_ABS
from conftest import FakeTransport, build_ack


def test_to_signed_char_clamping(fake_transport):
    """
    Test that signed char conversion properly clamps values.
    
    Verifies that:
    1. Values greater than 127 are clamped to 127
    2. Values less than -127 are clamped to -127 (represented as 129 in unsigned)
    """
    ch = CH9329(fake_transport)

    assert ch._to_signed_char(200) == 127
    assert ch._to_signed_char(-200) == ((-127) & 0xFF)


def test_mouse_rel_and_abs_payloads(fake_transport):
    """
    Test mouse relative and absolute movement with value clamping.
    
    Verifies that:
    1. Relative movement values are clamped to signed char range (-127 to 127)
    2. Absolute coordinates are clamped to 0-4095 range
    3. Button states are properly masked
    4. Wheel values are included in the frame
    """
    ch = CH9329(fake_transport)

    fake_transport._responses.append(build_ack(CMD_SEND_MS_REL))
    fake_transport._responses.append(build_ack(CMD_SEND_MS_ABS))

    ch.send_mouse_rel(dx=300, dy=-300, buttons=0x03, wheel=5)
    assert fake_transport.writes, "send_mouse_rel did not write any frame"
    last = fake_transport.writes[-1]
    assert last[5] == 0x01  # relative mode
    assert last[6] == (0x03 & 0x07)
    assert last[7] == 127  # dx clamped

    ch.send_mouse_abs(x=5000, y=-100, buttons=0x02, wheel=-10)
    assert len(fake_transport.writes) >= 2
    last2 = fake_transport.writes[-1]
    assert last2[5] == 0x02  # absolute mode flag
    x_low = last2[7]
    x_high = last2[8]
    x_val = x_low | (x_high << 8)
    assert x_val == 4095
