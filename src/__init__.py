"""
PyCH9329-HID is a high-level Python package for CH9329 HID chip, designed to provide seamless, OS-independent peripheral control via serial communication.
"""

from .ch9329 import CH9329
from .hid import HIDController
from .transport import SerialTransport

__version__ = "0.1.0"
__author__ = "zonghai"
__email__ = "zonghai@gmail.com"

__all__ = ["CH9329", "HIDController", "SerialTransport", "__version__"]
