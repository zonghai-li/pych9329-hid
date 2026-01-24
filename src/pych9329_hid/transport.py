# transport.py
# @author zonghai@gmail.com
# @description Lightweight serial transport

import serial


IO_DELAY = 0.005  # seconds


class SerialTransportError(Exception):
    """Base exception for transport errors."""
    pass


class SerialTransportClosedError(SerialTransportError):
    """Raised when operation attempted on closed transport."""
    pass


class SerialTransport:
    """
    Lightweight serial transport wrapper with context management.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = IO_DELAY):
        """
        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3').
            baudrate: Baud rate (default 115200).
            timeout: Read timeout in seconds (default 0.005).

        Raises:
            SerialTransportError: If port cannot be opened.
            ValueError: If parameters are invalid.
        """
        if not port or not isinstance(port, str):
            raise ValueError("port must be a non-empty string")
        if baudrate <= 0:
            raise ValueError("baudrate must be positive")
        if timeout < 0:
            raise ValueError("timeout must be non-negative")

        try:
            self.ser = serial.Serial(
                port=port, baudrate=baudrate, timeout=timeout, write_timeout=timeout
            )
        except (serial.SerialException, OSError) as e:
            raise SerialTransportError(f"Failed to open serial port {port}: {e}") from e

    def write(self, data: bytes) -> None:
        """
        Write raw bytes and ensure they are physically sent.

        Raises:
            SerialTransportClosedError: If transport is closed.
            SerialTransportError: If write fails.
        """
        if not self.ser.is_open:
            raise SerialTransportClosedError("Cannot write: transport is closed")

        try:
            self.ser.write(data)
            self.ser.flush()
        except (serial.SerialException, OSError) as e:
            raise SerialTransportError(f"Write failed: {e}") from e

    def read(self, size: int = 64) -> bytes:
        """
        Read up to 'size' bytes from the port.

        Args:
            size: Maximum number of bytes to read.

        Returns:
            Bytes read (may be less than size if timeout occurs).

        Raises:
            SerialTransportClosedError: If transport is closed.
            SerialTransportError: If read fails.
        """
        if not self.ser.is_open:
            raise SerialTransportClosedError("Cannot read: transport is closed")

        if size <= 0:
            return b""

        try:
            return self.ser.read(size)
        except (serial.SerialException, OSError) as e:
            raise SerialTransportError(f"Read failed: {e}") from e

    def read_all(self) -> bytes:
        """
        Read all currently available data from the port.

        Returns:
            All available bytes.

        Raises:
            SerialTransportClosedError: If transport is closed.
            SerialTransportError: If read fails.
        """
        if not self.ser.is_open:
            raise SerialTransportClosedError("Cannot read: transport is closed")

        try:
            return self.ser.read_all()
        except (serial.SerialException, OSError) as e:
            raise SerialTransportError(f"Read failed: {e}") from e

    def close(self) -> None:
        """Safely close the serial port."""
        if hasattr(self, "ser") and self.ser.is_open:
            try:
                self.ser.close()
            except (serial.SerialException, OSError):
                pass

    def is_open(self) -> bool:
        """Check if the serial port is open."""
        return self.ser.is_open

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        self.close()
