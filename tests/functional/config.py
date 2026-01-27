import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from pych9329_hid import HIDController, SerialTransport, CH9329
from pych9329_hid.keymap import MOD_LALT, MOD_RALT, char_to_hid

with SerialTransport('/dev/tty.usbserial-110', 115200) as t:
    h = HIDController(t)

    # code = char_to_hid("2")[1]

    # print('[TEST 1] 左 Alt (0x04) + 2')
    # h._protocol.send_keyboard(MOD_LALT, [code, 0x00, 0x00, 0x00, 0x00, 0x00])
    # time.sleep(0.5)
    # h._protocol.send_keyboard(0x00, [0x00] * 6)
    # time.sleep(1.0)

    # print('\n[TEST 2] 右 Alt (0x40) + 2')
    # h._protocol.send_keyboard(MOD_RALT, [code, 0x00, 0x00, 0x00, 0x00, 0x00])
    # time.sleep(0.5)
    # h._protocol.send_keyboard(0x00, [0x00] * 6)
    # time.sleep(1.0)

    # print('\n[TEST 3] 左右 Alt 都按 (0x44) + 2')
    # h._protocol.send_keyboard(MOD_LALT | MOD_RALT, [code, 0x00, 0x00, 0x00, 0x00, 0x00])
    # time.sleep(0.5)
    # h._protocol.send_keyboard(0x00, [0x00] * 6)
    # time.sleep(1.0)

    # print('\n[TEST 4] 只发 2 (验证设备)')
    # h._protocol.send_keyboard(0x00, [code, 0x00, 0x00, 0x00, 0x00, 0x00])
    # time.sleep(0.05)
    # h._protocol.send_keyboard(0x00, [0x00] * 6)
    # time.sleep(1.0)

    # print('\n[TEST 5] 组合键 Alt+F4 (验证 Alt 工作)')
    # h._protocol.send_keyboard(MOD_LALT, [0x3E, 0x00, 0x00, 0x00, 0x00, 0x00])  # F4 = 0x3E
    # time.sleep(0.5)
    # h._protocol.send_keyboard(0x00, [0x00] * 6)
    # time.sleep(1.0)

    h.press("4")
    h.hotkey("alt", "2")
    # h.press("alt")
    # h.hotkey("cmd", "a")
    # # time.sleep(0.5)
    # h.hotkey("cmd", "C")
    # # time.sleep(0.5)
    # h.press("right")
    # # time.sleep(0.5)
    # h.hotkey("cmd", "v")



    print('[DONE]')

    
