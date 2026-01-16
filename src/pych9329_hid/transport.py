# transport.py
# @author zonghai@gmail.com
# @description Lightweight serial transport wrapper without logging.

import time
import serial


IO_DELAY = 0.005  # seconds


class SerialTransport:
    """
    Lightweight serial transport wrapper with context management.
    """

    def __init__(self, port, baudrate=115200):
        """
        Args:
            port (str): Serial port path (e.g., '/dev/ttyUSB0' or 'COM3').
            baudrate (int): 115200 is recommended for CH9329 for low latency.
        """
        # Open serial port with both read and write timeouts
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=IO_DELAY # Read timeout for ACK handling 
        )

    def write(self, data: bytes):
        """
        Write raw bytes and ensure they are physically sent.
        """
        if self.ser.is_open:
            self.ser.write(data)
            self.ser.flush()  # Ensure data is sent to the wire immediately

    def write_delay(self, data: bytes, delay: float = IO_DELAY):
        """
        Write data and sleep for hardware processing.
        """
        self.write(data)
        if delay > 0:
            time.sleep(delay)

    def read(self, size=64) -> bytes:
        """
        Read up to 'size' bytes from the port.
        """
        if self.ser.is_open:
            return self.ser.read(size)
        return b""

    def close(self):
        """Safely close the serial port."""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()

    # --- Support for 'with' statement ---
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()