# transport.py
# @author zonghai@gmail.com
# @description Lightweight serial transport

import serial


class TransportError(Exception):
    """Base exception for transport errors."""

    pass


class TransportClosedError(TransportError):
    """Raised when operation attempted on closed transport."""

    pass


class TransportTimeoutError(TransportError):
    """Raised when operation times out."""

    pass


class SerialTransport:
    """
    Lightweight serial transport wrapper with context management.
    """

    def __init__(self, port: str, baudrate: int = 9600):
        """
        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3').
            baudrate: Baud rate (default 115200).
            timeout: Read timeout in seconds (default 0.005).

        Raises:
            TransportError: If port cannot be opened.
            ValueError: If parameters are invalid.
        """
        if not port or not isinstance(port, str):
            raise ValueError("port must be a non-empty string")
        if baudrate not in [9600, 115200]:
            raise ValueError("baudrate must be 9600 or 115200")

        # Timeout Calculation:
        # send ~ 16bytes read ~ 16 bytes
        # Baudrate | Request time | resp<=56bytes | Processing | Total
        # ---------|--------------|---------------|------------|-------------------
        # 9600     | 14.6 ms      | 58 ms         | 5-15 ms    | ~90 ms
        # 115200   | 1.22 ms      | 5  ms         | 5-15 ms    | ~21 ms

        read_timeout = 0.1 if baudrate == 9600 else 0.03
        write_timeout = 0.05 if baudrate == 9600 else 0.015

        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=read_timeout,
                write_timeout=write_timeout,
            )
        except (serial.SerialException, OSError) as e:
            raise TransportError(f"Failed to open serial port {port}: {e}") from e

    def write(self, data: bytes) -> None:
        """
        Write raw bytes and ensure they are physically sent.
        This function is blocking because it explicit flushes the data to ensure the transmission.

        Raises:
            TransportClosedError: If transport is closed.
            TransportError: If write fails.
        """

        try:
            self.ser.write(data)
            self.ser.flush()
        except serial.PortNotOpenError as e:
            raise TransportClosedError("Cannot write: transport is closed") from e
        except serial.SerialTimeoutException as e:
            raise TransportTimeoutError(f"Write timeout: {e}") from e
        except (serial.SerialException, OSError) as e:
            raise TransportError(f"Write failed: {e}") from e

    def read(self, size: int = 16) -> bytes:
        """
        Read up to 'size' bytes from the port.
        This function is blocking read w/ read_timeout.
        If timeout occurs, return whatever bytes are available.

        Args:
            size: Maximum number of bytes to read.

        Returns:
            Bytes read (may be less than size if timeout occurs).

        Raises:
            TransportClosedError: If transport is closed.
            TransportError: If read fails.
        """

        if size <= 0:
            return b""

        try:
            return self.ser.read(size)
        except serial.PortNotOpenError as e:
            raise TransportClosedError("Cannot read: transport is closed") from e
        except (serial.SerialException, OSError) as e:
            raise TransportError(f"Read failed: {e}") from e

    def read_all(self) -> bytes:
        """
        Read all currently available data from the port. This function is non-blocking.

        Returns:
            All available bytes.

        Raises:
            TransportClosedError: If transport is closed.
            TransportError: If read fails.
        """

        try:
            return self.ser.read_all()
        except serial.PortNotOpenError as e:
            raise TransportClosedError("Cannot read: transport is closed") from e
        except (serial.SerialException, OSError) as e:
            raise TransportError(f"Read failed: {e}") from e

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
