import time
import random, math, os, sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from pych9329_hid import HIDController, SerialTransport, CH9329


def run_mouse_test(hid):
    print("--- Starting Mouse Functional Test ---")
    
    # 假设按钮在页面上的大致逻辑坐标 (需要根据你的实际浏览器位置调整)
    # 建议先用 reset() 确保坐标对齐
    hid.reset()
    time.sleep(0.5)

   
    # print("极简拖拽测试开始")
    hid.moveTo(720, 450) # button mask 0
    
                                       # X: 0， 0， 1， 3， 5, 7, 9, 11, 13, 15
    hid._hid.send_mouse_rel(4, 3, buttons=0)# Y: 0， 1， 2， 4， 6, 8, 10, 12, 14, 16

    print("--- Mouse Test Completed ---")
    # hid.reset()
    

my_hid = HIDController(CH9329(SerialTransport('/dev/ttyUSB6', 9600)), 1440, 900)
run_mouse_test(my_hid)