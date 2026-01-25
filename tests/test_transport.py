import pytest

from pych9329_hid import transport
from pych9329_hid.transport import TransportError, TransportClosedError


class FakeSerial:
    def __init__(self, should_fail_open=False, should_fail_write=False, should_fail_read=False):
        self.written = b''
        self._buffer = b''
        self.is_open = True
        self.should_fail_open = should_fail_open
        self.should_fail_write = should_fail_write
        self.should_fail_read = should_fail_read
        self.SerialException = Exception
        self.PortNotOpenError = Exception  # Add this attribute for exception handling

    def write(self, data):
        if not self.is_open:
            raise self.PortNotOpenError("Port is closed")
        if self.should_fail_write:
            raise OSError("Write failed")
        self.written += data

    def flush(self):
        pass

    def read(self, size=1):
        if not self.is_open:
            raise self.PortNotOpenError("Port is closed")
        if self.should_fail_read:
            raise OSError("Read failed")
        if not self._buffer:
            return b''
        out = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return out

    def read_all(self):
        if not self.is_open:
            raise self.PortNotOpenError("Port is closed")
        if self.should_fail_read:
            raise OSError("Read failed")
        out = self._buffer
        self._buffer = b''
        return out

    def close(self):
        self.is_open = False


def test_serial_transport_write_and_read(monkeypatch):
    fake = FakeSerial()

    monkeypatch.setattr(transport, 'serial', type('m', (), {'Serial': lambda *a, **k: fake}))

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)
    t.write(b'hello')
    assert fake.written == b'hello'

    fake._buffer = b'abcde'
    data = t.read(3)
    assert data == b'abc'

    t.close()
    assert not fake.is_open


def test_serial_transport_read_all(monkeypatch):
    fake = FakeSerial()

    monkeypatch.setattr(transport, 'serial', type('m', (), {'Serial': lambda *a, **k: fake}))

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)

    fake._buffer = b'abcde'
    data = t.read_all()
    assert data == b'abcde'
    assert fake._buffer == b''


def test_serial_transport_is_open(monkeypatch):
    fake = FakeSerial()

    monkeypatch.setattr(transport, 'serial', type('m', (), {'Serial': lambda *a, **k: fake}))

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)
    assert t.is_open() is True

    t.close()
    assert t.is_open() is False


def test_serial_transport_write_on_closed(monkeypatch):
    fake = FakeSerial()

    # Create a proper mock that includes all necessary attributes
    mock_serial = type('m', (), {
        'Serial': lambda *a, **k: fake,
        'PortNotOpenError': Exception,
        'SerialException': Exception,
        'SerialTimeoutException': Exception
    })
    
    monkeypatch.setattr(transport, 'serial', mock_serial)

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)
    t.close()

    with pytest.raises(TransportClosedError):
        t.write(b'hello')


def test_serial_transport_read_on_closed(monkeypatch):
    fake = FakeSerial()

    # Create a proper mock that includes all necessary attributes
    mock_serial = type('m', (), {
        'Serial': lambda *a, **k: fake,
        'PortNotOpenError': Exception,
        'SerialException': Exception,
        'SerialTimeoutException': Exception
    })
    
    monkeypatch.setattr(transport, 'serial', mock_serial)

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)
    t.close()

    with pytest.raises(TransportClosedError):
        t.read()


def test_serial_transport_write_failure(monkeypatch):
    fake = FakeSerial(should_fail_write=True)

    # Create a proper mock that includes all necessary attributes
    mock_serial = type('m', (), {
        'Serial': lambda *a, **k: fake,
        'PortNotOpenError': Exception,
        'SerialException': Exception,
        'SerialTimeoutException': Exception
    })
    
    monkeypatch.setattr(transport, 'serial', mock_serial)

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)

    with pytest.raises(TransportError):
        t.write(b'hello')


def test_serial_transport_read_failure(monkeypatch):
    fake = FakeSerial(should_fail_read=True)

    # Create a proper mock that includes all necessary attributes
    mock_serial = type('m', (), {
        'Serial': lambda *a, **k: fake,
        'PortNotOpenError': Exception,
        'SerialException': Exception,
        'SerialTimeoutException': Exception
    })
    
    monkeypatch.setattr(transport, 'serial', mock_serial)

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)

    with pytest.raises(TransportError):
        t.read()


def test_serial_transport_invalid_port():
    with pytest.raises(ValueError, match="port must be a non-empty string"):
        transport.SerialTransport(port='', baudrate=9600)

    with pytest.raises(ValueError, match="port must be a non-empty string"):
        transport.SerialTransport(port=None, baudrate=9600)


def test_serial_transport_invalid_baudrate():
    with pytest.raises(ValueError, match="baudrate must be 9600 or 115200"):
        transport.SerialTransport(port='/dev/fake', baudrate=0)

    with pytest.raises(ValueError, match="baudrate must be 9600 or 115200"):
        transport.SerialTransport(port='/dev/fake', baudrate=-1)


def test_serial_transport_context_manager(monkeypatch):
    fake = FakeSerial()

    monkeypatch.setattr(transport, 'serial', type('m', (), {'Serial': lambda *a, **k: fake}))

    with transport.SerialTransport(port='/dev/fake', baudrate=9600) as t:
        t.write(b'hello')
        assert fake.written == b'hello'

    assert not fake.is_open



def test_serial_transport_read_zero_size(monkeypatch):
    fake = FakeSerial()

    monkeypatch.setattr(transport, 'serial', type('m', (), {'Serial': lambda *a, **k: fake}))

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)
    data = t.read(0)
    assert data == b''
