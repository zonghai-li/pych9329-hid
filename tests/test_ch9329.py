"""
Basic tests for CH9329 protocol implementation.
"""
import pytest
from pych9329_hid.ch9329 import CH9329, FRAME_HEAD, ADDR_DEFAULT, CMD_SEND_KEY, CMD_GET_INFO, ACKError
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
    Test that timeout returns None and issues warning when no ACK response is received.
    
    Verifies that the CH9329 class properly handles timeout conditions
    when the device does not respond to a command.
    """
    import warnings
    ch = CH9329(fake_transport)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = ch._send_frame(0x99, b'')
        assert result is None
        assert len(w) == 4  # 3 retry warnings + 1 final failure warning
        assert "Failed to send CMD" in str(w[3].message)  # Check the final warning


def test_decode_response_valid_success(fake_transport):
    """
    Test decoding a valid success response.
    
    Verifies that:
    1. Valid success response is decoded correctly
    2. Data payload is returned
    3. Checksum verification passes
    """
    ch = CH9329(fake_transport)
    
    # Build a valid success response for CMD_GET_INFO (0x01)
    # Response CMD = 0x01 | 0x80 = 0x81
    # Data: version(0x30), usb_status(0x01), led_status(0x00), 5 bytes padding
    data = bytes([0x30, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    frame = bytearray(FRAME_HEAD)
    frame.append(ADDR_DEFAULT)
    frame.append(0x81)  # CMD_GET_INFO | 0x80
    frame.append(len(data))
    frame.extend(data)
    frame.append(sum(frame) & 0xFF)
    
    result = ch._decode_and_verify(bytes(frame), CMD_GET_INFO)
    
    assert result == data


def test_decode_response_valid_error(fake_transport):
    """
    Test decoding a valid error response.
    
    Verifies that:
    1. Error response raises ACKError
    2. Error message includes error status
    """
    ch = CH9329(fake_transport)
    
    # Build a valid error response for CMD_SEND_KEY (0x02)
    # Response CMD = 0x02 | 0xC0 = 0xC2
    # Data: error status (0x01 = buffer full)
    data = bytes([0x01])
    frame = bytearray(FRAME_HEAD)
    frame.append(ADDR_DEFAULT)
    frame.append(0xC2)  # CMD_SEND_KEY | 0xC0
    frame.append(len(data))
    frame.extend(data)
    frame.append(sum(frame) & 0xFF)
    
    with pytest.raises(ACKError) as exc_info:
        ch._decode_and_verify(bytes(frame), CMD_SEND_KEY)
    
    assert 'error status 0x01' in str(exc_info.value)
    assert 'CMD 0x02' in str(exc_info.value)


def test_decode_response_invalid_header(fake_transport):
    """
    Test decoding response with invalid frame header.
    
    Verifies that:
    1. Invalid header raises ACKError
    2. Error message includes header details
    """
    ch = CH9329(fake_transport)
    
    # Frame with invalid header
    frame = b'\x57\xAA\x00\x81\x08\x30\x01\x00\x00\x00\x00\x00\x00\x00\x00'
    
    with pytest.raises(ACKError) as exc_info:
        ch._decode_and_verify(frame, CMD_GET_INFO)
    
    assert 'Invalid frame header' in str(exc_info.value)
    assert '57aa' in str(exc_info.value)
    assert '57ab' in str(exc_info.value)


def test_decode_response_too_short(fake_transport):
    """
    Test decoding response that is too short.
    
    Verifies that:
    1. Short frame raises ACKError
    2. Error message includes actual and expected length
    """
    ch = CH9329(fake_transport)
    
    # Frame with only 5 bytes (minimum is 6)
    frame = b'\x57\xAB\x00\x81\x00'
    
    with pytest.raises(ACKError) as exc_info:
        ch._decode_and_verify(frame, CMD_GET_INFO)
    
    assert 'Frame too short' in str(exc_info.value)
    assert '5 bytes' in str(exc_info.value)
    assert 'minimum 6' in str(exc_info.value)


def test_decode_response_length_mismatch(fake_transport):
    """
    Test decoding response with length field mismatch.
    
    Verifies that:
    1. Length field inconsistency raises ACKError
    2. Error message includes length and actual frame size
    """
    ch = CH9329(fake_transport)
    
    # LEN field says 8 bytes, but frame only has 7 bytes of data
    frame = bytearray(FRAME_HEAD)
    frame.append(ADDR_DEFAULT)
    frame.append(0x81)
    frame.append(8)  # LEN = 8
    frame.extend(bytes([0x30, 0x01, 0x00]))  # Only 3 bytes of data
    frame.append(0x00)  # checksum
    
    with pytest.raises(ACKError) as exc_info:
        ch._decode_and_verify(bytes(frame), CMD_GET_INFO)
    
    assert 'Length mismatch' in str(exc_info.value)
    assert 'LEN=8' in str(exc_info.value)


def test_decode_response_checksum_mismatch(fake_transport):
    """
    Test decoding response with incorrect checksum.
    
    Verifies that:
    1. Checksum mismatch raises ACKError
    2. Error message includes received and calculated checksums
    """
    ch = CH9329(fake_transport)
    
    # Valid frame but with wrong checksum
    data = bytes([0x30, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    frame = bytearray(FRAME_HEAD)
    frame.append(ADDR_DEFAULT)
    frame.append(0x81)
    frame.append(len(data))
    frame.extend(data)
    frame.append(0xFF)  # Wrong checksum
    
    with pytest.raises(ACKError) as exc_info:
        ch._decode_and_verify(bytes(frame), CMD_GET_INFO)
    
    assert 'Checksum mismatch' in str(exc_info.value)
    assert 'received 0xFF' in str(exc_info.value)


def test_decode_response_unexpected_command(fake_transport):
    """
    Test decoding response with unexpected command byte.
    
    Verifies that:
    1. Unexpected command raises ACKError
    2. Error message includes expected and actual command bytes
    """
    ch = CH9329(fake_transport)
    
    # Frame with wrong command byte (0x90 instead of 0x81 or 0xC1)
    data = bytes([0x30, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    frame = bytearray(FRAME_HEAD)
    frame.append(ADDR_DEFAULT)
    frame.append(0x90)  # Wrong command
    frame.append(len(data))
    frame.extend(data)
    frame.append(sum(frame) & 0xFF)
    
    with pytest.raises(ACKError) as exc_info:
        ch._decode_and_verify(bytes(frame), CMD_GET_INFO)
    
    assert 'Unexpected command' in str(exc_info.value)
    assert '0x90' in str(exc_info.value)
    assert '0x81' in str(exc_info.value)


def test_decode_response_empty_data(fake_transport):
    """
    Test decoding response with empty data payload.
    
    Verifies that:
    1. ACK-only response (no data) is decoded correctly
    2. Empty bytes are returned
    """
    ch = CH9329(fake_transport)
    
    # ACK-only success response
    frame = bytearray(FRAME_HEAD)
    frame.append(ADDR_DEFAULT)
    frame.append(0x82)  # CMD_SEND_KEY | 0x80
    frame.append(0)  # LEN = 0
    frame.append(sum(frame) & 0xFF)  # checksum
    
    result = ch._decode_and_verify(bytes(frame), CMD_SEND_KEY)
    
    assert result == b''


def test_get_info_success(fake_transport):
    """
    Test get_info command returns correct chip information.
    
    Verifies that:
    1. get_info sends CMD_GET_INFO command
    2. Response is parsed correctly
    3. Version, USB status, and LED status are extracted
    """
    ch = CH9329(fake_transport)
    
    # Build response: CMD 0x81 with 8 bytes of data
    # Version 0x30 (V1.0), USB connected (0x01), LEDs (0x00)
    response_data = bytes([0x30, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    response = FRAME_HEAD + bytes([ADDR_DEFAULT, CMD_GET_INFO | 0x80, 0x08]) + response_data
    checksum = sum(response) & 0xFF
    response = response + bytes([checksum])
    fake_transport._responses.append(response)
    
    info = ch.get_info()
    
    assert info['version'] == 'V1.0'
    assert info['usb_connected'] is True
    assert info['num_lock_on'] is False
    assert info['caps_lock_on'] is False
    assert info['scroll_lock_on'] is False


def test_get_info_with_led_status(fake_transport):
    """
    Test get_info command with LED status bits set.
    
    Verifies that LED status bitmask is correctly parsed:
    - Bit 0: NUM LOCK
    - Bit 1: CAPS LOCK
    - Bit 2: SCROLL LOCK
    """
    ch = CH9329(fake_transport)
    
    # Build response with LEDs: NUM (0x01) + CAPS (0x02) + SCROLL (0x04) = 0x07
    response_data = bytes([0x31, 0x01, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00])
    response = FRAME_HEAD + bytes([ADDR_DEFAULT, CMD_GET_INFO | 0x80, 0x08]) + response_data
    checksum = sum(response) & 0xFF
    response = response + bytes([checksum])
    fake_transport._responses.append(response)
    
    info = ch.get_info()
    
    assert info['version'] == 'V1.1'
    assert info['usb_connected'] is True
    assert info['num_lock_on'] is True
    assert info['caps_lock_on'] is True
    assert info['scroll_lock_on'] is True


def test_get_info_timeout(fake_transport):
    """
    Test get_info command when device does not respond.
    
    Verifies that:
    1. Timeout returns None
    2. Warning is issued
    """
    import warnings
    ch = CH9329(fake_transport)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        info = ch.get_info()
        assert info is None
        assert len(w) == 4  # 3 retry warnings + 1 final failure warning
        assert "Failed to send CMD 0x01" in str(w[3].message)  # Check the final warning


def test_send_frame_transport_timeout(fake_transport):
    """Test that TransportTimeoutError triggers retry mechanism."""
    import warnings
    from pych9329_hid.transport import TransportTimeoutError
    
    ch = CH9329(fake_transport)
    
    # Mock the transport to raise TransportTimeoutError on write
    original_write = ch.t.write
    def mock_write_timeout(data):
        raise TransportTimeoutError("Write timeout occurred")
    
    ch.t.write = mock_write_timeout
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = ch._send_frame(0x99, b'')
        
        # Should return None after all retries
        assert result is None
        
        # Should have warnings for each retry attempt
        # 3 retry attempts + 1 final failure = 4 warnings
        assert len(w) == 4
        
        # Check that transport timeout warnings are present
        transport_timeout_warnings = [msg for msg in w if "Transport timeout" in str(msg.message)]
        assert len(transport_timeout_warnings) == 3  # One for each retry
        
        # Check final failure warning
        assert "Failed to send CMD 0x99" in str(w[3].message)


def test_is_num_lock_on(fake_transport):
    """
    Test NUM LOCK LED status helper.
    """
    ch = CH9329(fake_transport)
    
    assert ch._is_num_lock_on(0x00) is False
    assert ch._is_num_lock_on(0x01) is True
    assert ch._is_num_lock_on(0x02) is False
    assert ch._is_num_lock_on(0x03) is True
    assert ch._is_num_lock_on(0xFF) is True


def test_is_caps_lock_on(fake_transport):
    """
    Test CAPS LOCK LED status helper.
    """
    ch = CH9329(fake_transport)
    
    assert ch._is_caps_lock_on(0x00) is False
    assert ch._is_caps_lock_on(0x02) is True
    assert ch._is_caps_lock_on(0x01) is False
    assert ch._is_caps_lock_on(0x03) is True
    assert ch._is_caps_lock_on(0xFF) is True


def test_is_scroll_lock_on(fake_transport):
    """
    Test SCROLL LOCK LED status helper.
    """
    ch = CH9329(fake_transport)
    
    assert ch._is_scroll_lock_on(0x00) is False
    assert ch._is_scroll_lock_on(0x04) is True
    assert ch._is_scroll_lock_on(0x01) is False
    assert ch._is_scroll_lock_on(0x05) is True
    assert ch._is_scroll_lock_on(0xFF) is True


def test_is_usb_connected(fake_transport):
    """
    Test USB connection status helper.
    """
    ch = CH9329(fake_transport)
    
    assert ch._is_usb_connected(0x00) is False
    assert ch._is_usb_connected(0x01) is True
    assert ch._is_usb_connected(0x02) is False


def test_get_version_string(fake_transport):
    """
    Test version string helper.
    """
    ch = CH9329(fake_transport)
    
    assert ch._get_version_string(0x30) == "V1.0"
    assert ch._get_version_string(0x31) == "V1.1"
    assert ch._get_version_string(0x32) == "Unknown (0x32)"
    assert ch._get_version_string(0xFF) == "Unknown (0xFF)"
