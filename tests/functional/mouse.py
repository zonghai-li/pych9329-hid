import sys
import os
import time
import random, math 

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src import HIDController, SerialTransport, CH9329


def run_mouse_test(hid):
    print("--- Starting Mouse Functional Test ---")
    
    # 假设按钮在页面上的大致逻辑坐标 (需要根据你的实际浏览器位置调整)
    # 建议先用 reset() 确保坐标对齐
    hid.reset()
    time.sleep(0.5)

    # 定义按钮中心坐标 (示例坐标)
    buttons = {
        "single": (200, 280),
        "double": (600, 280),
        "right":  (200, 360),
        "middle": (600, 360),
        "cmd":    (200, 440),
        "shift":  (600, 440)
    }

    # 1. Single Click
    print("Test 1: Single Click")
    x, y = buttons["single"]
    hid.click(x, y, button='left')
    time.sleep(1)

    # 2. Double Click
    print("Test 2: Double Click")
    x, y = buttons["double"]
    hid.click(x, y, button='left', clicks=2)
    time.sleep(1)

    # 3. Right Click
    print("Test 3: Right Click")
    x, y = buttons["right"]
    hid.click(x, y, button='right')
    time.sleep(1)

    # 4. Middle Click (CH9329 0x01 mask)
    print("Test 4: Middle Click")
    x, y = buttons["middle"]
    hid.click(x, y, button='middle')
    time.sleep(1)

    # 5. Cmd + Click (验证跨层同步)
    print("Test 5: Cmd + Click")
    x, y = buttons["cmd"]
    hid.moveTo(x, y)
    hid.keyDown('command')
    time.sleep(0.1)
    hid.click(button='left')
    hid.keyUp('command')
    time.sleep(1)

    # 6. Shift + Click (多选模拟)
    print("Test 6: Shift + Click")
    x, y = buttons["shift"]
    hid.moveTo(x, y)
    hid.keyDown('shift')
    time.sleep(0.1)
    hid.click(button='left')
    hid.keyUp('shift')
    

# --- 暂停等待 ---
    print("\n" + "="*30)
    print("SECTION 1 完成！")
    input("请切换到 [Canvas Drawing] 标签，然后按回车开始 SECTION 2 (绘图测试)...")
    print("="*30 + "\n")
    
    # --- SECTION 2: CANVAS DRAWING ---
    print(">>> SECTION 2: 正在绘图 (Triangle & Rectangle)...")
    
    # 1. 寻找画布起始点
    # 建议先手动看一眼 Canvas 左上角的 System Pointer 坐标
    # 假设 Canvas 内部起始点为 (400, 300)
    start_x, start_y = 400, 300 
    
    # A. 画一个三角形 (Triangle)
    print("正在绘制三角形...")
    hid.moveTo(start_x, start_y)
    
    
    # 使用 moveRel 测试相对平滑移动
    hid.dragRel(100, 150) # 下斜边
    hid.dragRel(-200, 0)  # 底边
    hid.dragRel(100, -150) # 返回顶点
    

    time.sleep(1)

    # B. 画一个正方形 (Rectangle)
    # 移动到新的起点
    rect_start_x, rect_start_y = start_x + 150, start_y
    print("正在绘制正方形...")
    
    # 直接使用 dragTo 测试绝对坐标拖拽
    hid.dragRel(300, 0)       # 右
    hid.dragRel(0, 300 ) # 下
    hid.dragRel(-300, 0)       # 左
    hid.dragRel(0, -300)
    hid.dragRel(300,300)             # 上

    # C. 模拟人类“圆滑”移动 (Circular-ish)
    print("正在绘制圆形近似...")
    hid.moveTo(rect_start_x + 200, rect_start_y + 50)
    hid.mouseDown()
    steps = 20
    radius = 50
    for i in range(steps + 1):
        angle = (2 * math.pi / steps) * i
        dx = int(radius * math.cos(angle))
        dy = int(radius * math.sin(angle))
        # 这里的持续时间要短，考验 9600 速率下的密集包处理
        hid.moveRel(dx if i==0 else (int(radius*math.cos(angle)) - int(radius*math.cos((2*math.pi/steps)*(i-1)))), 
                    dy if i==0 else (int(radius*math.sin(angle)) - int(radius*math.sin((2*math.pi/steps)*(i-1)))), 
                    duration=0.1)
    hid.mouseUp()
    time.sleep(1)

    print("--- Mouse Test Completed ---")
    hid.reset()
    

my_hid = HIDController(CH9329(SerialTransport('/dev/ttyUSB6', 9600)), 1440, 900)
run_mouse_test(my_hid)