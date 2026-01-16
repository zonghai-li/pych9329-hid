import pytest

from src import transport


class FakeSerial:
    def __init__(self):
        self.written = b''
        self._buffer = b''
        self.is_open = True

    def write(self, data):
        self.written += data

    def flush(self):
        pass

    def read(self, size=1):
        # return up to `size` bytes from internal buffer
        if not self._buffer:
            return b''
        out = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return out

    def close(self):
        self.is_open = False


def test_serial_transport_write_and_read(monkeypatch):
    fake = FakeSerial()

    # Monkeypatch serial.Serial to return our fake serial
    monkeypatch.setattr(transport, 'serial', type('m', (), {'Serial': lambda *a, **k: fake}))

    t = transport.SerialTransport(port='/dev/fake', baudrate=9600)
    t.write(b'hello')
    assert fake.written == b'hello'

    # prime buffer and read
    fake._buffer = b'abcde'
    data = t.read(3)
    assert data == b'abc'

    t.close()
    assert not fake.is_open
