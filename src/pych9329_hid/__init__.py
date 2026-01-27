"""
PyCH9329-HID is a high-level Python package for CH9329 HID chip, designed to provide seamless, OS-independent peripheral control via serial communication.
"""

from .ch9329 import CH9329
from .config import CH9329Config
from .hid import HIDController
from .transport import SerialTransport

__version__ = "0.2.1"
__author__ = "zonghai-li"
__email__ = "zonghai@gmail.com"

__all__ = ["CH9329", "CH9329Config", "HIDController", "SerialTransport", "__version__"]
