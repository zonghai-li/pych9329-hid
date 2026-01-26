import sys
import os



sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from pych9329_hid import HIDController, SerialTransport, CH9329


with SerialTransport('/dev/tty.usbserial-110', 115200) as t:
    p = CH9329(t)
    # config = p.get_config()

    # print(config)

    # vendor = p.get_usb_descriptor(0)
    # print (vendor)

    # product = p.get_usb_descriptor(1)
    # print (product)

    # serial_number = p.get_usb_descriptor(2)
    # print (serial_number)



    # p.set_usb_descriptor(0, "VendorZonghai")
    # p.set_usb_descriptor(1, "ProductZonghai")
    # p.set_usb_descriptor(2, "SerialZonghai")

    
    # config.baudrate = 115200
    # config.custom_descriptor_enable = (None, None, True)
    # print(p.set_config(config))

    # p.set_config_to_default()
