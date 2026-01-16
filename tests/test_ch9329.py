"""
Basic tests for CH9329 protocol implementation.
"""
import pytest
from src.ch9329 import CH9329, FRAME_HEAD, ADDR_DEFAULT, CMD_SEND_KEY
from conftest import FakeTransport, build_ack


def test_calculate_checksum_and_send_keyboard(fake_transport):
    """
    Test checksum calculation and keyboard report sending.
    
    Verifies that:
    1. Checksum is calculated correctly for a data frame
    2. Keyboard report is sent successfully with ACK response
    3. Transport layer receives the written data
    """
    ch = CH9329(fake_transport)

    data = b'\x57\xAB\x00\x02\x01\x00'
    assert ch._calculate_checksum(data) == (sum(data) & 0xFF)

    fake_transport._responses.append(build_ack(CMD_SEND_KEY))

    ch.send_keyboard(0x02, [0x04, 0x05])
    assert len(fake_transport.writes) >= 1


def test_send_frame_timeout_raises(fake_transport):
    """
    Test that timeout exception is raised when no ACK response is received.
    
    Verifies that the CH9329 class properly handles timeout conditions
    when the device does not respond to a command.
    """
    ch = CH9329(fake_transport)

    with pytest.raises(Exception):
        ch._send_frame(0x99, b'')
