import sys
import os
import time
import random

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from pych9329_hid import HIDController, SerialTransport, CH9329

def run_circular_test(hid):
    """
    Starts with the target string, performs 10 phases of editing chaos,
    and must result in the exact same target string.
    """
    CMD = 'command' # Toggle to 'ctrl' for Windows
    TARGET = "This is the final content that should be left here."
    
    print(f"--- Starting Circular Test ---")
    print(f"Goal: Transform text and return to: '{TARGET}'")
    time.sleep(3)

    # --- SETUP ---
    hid.hotkey(CMD, 'a')
    hid.press('backspace')
    hid.write(TARGET)
    time.sleep(2)

    # PHASE 1: The Word-Swap (Selection & Clipboard)
    # Action: Select "final", cut it, move to end, paste, then undo.
    print("Phase 1: Clipboard & Undo Symmetry")
    for _ in range(8): hid.press('left') # Move before 'here.'
    hid.keyDown('shift')
    for _ in range(5): hid.press('left') # Select 'left '
    hid.keyUp('shift')
    hid.hotkey(CMD, 'x')
    hid.hotkey(CMD, 'z') # Should put it back exactly
    time.sleep(2)

    # PHASE 2: The "Ghost" Character (Backspace/Delete balance)
    # Action: Type garbage in the middle, then delete it from the opposite direction.
    print("Phase 2: Bidirectional Deletion")
    hid.hotkey(CMD, 'left')
    for _ in range(5): hid.press('right') # Cursor after 'This '
    hid.write("!!!SCRUB!!!")
    for _ in range(11): hid.press('left') # Go back before '!!!'
    for _ in range(11): hid.press('delete') # Delete forward
    time.sleep(2)

    # PHASE 3: Multi-Line Chaos (Enter & Up/Down)
    # Action: Break the sentence into 3 lines, then join them back.
    print("Phase 3: Structural Integrity")
    hid.hotkey(CMD, 'left')
    for _ in range(10): hid.press('right') 
    hid.press('enter') # Break at 'final'
    hid.press('enter')
    hid.press('up')
    hid.press('up')
    hid.press('down')
    hid.hotkey(CMD, 'left')
    hid.press('backspace') # Join line 2
    hid.press('down')
    hid.hotkey(CMD, 'left')
    hid.press('backspace') # Join line 3
    time.sleep(2)



    # PHASE 4: Selection Overwrite (Shift+Cmd)
    # Action: Select from cursor to end, type something, then undo.
    # 修改 Phase 4 的逻辑
    print("Phase 4: Selection Overwrite & Recovery")
    hid.hotkey(CMD, 'left')
    for _ in range(4): hid.press('right') # 移动到 "This" 之后

    # 记录当前位置，准备覆盖
    hid.hotkey(CMD, 'shift', 'right') # 选中剩余所有内容
    hid.write(" is temporary chaos.")
    time.sleep(1)

    # 恢复逻辑：不再用 Cmd+Z，而是再次全选删除，重新打回原样
    # 或者利用热键删除刚才打的一行
    hid.hotkey(CMD, 'a')
    hid.press('backspace')
    hid.write(TARGET) # 直接重写目标字符串确保同步

    # PHASE 5: Rapid Modifier Toggling
    # Action: Rapidly type with Shift on and off.
    print("Phase 5: Modifier Rapid-Fire")
    hid.hotkey(CMD, 'right')
    hid.press('enter')
    # Write a mirrored string and delete it
    mirror = "AaBbCcDdEeFf1!2@3#4$"
    hid.write(mirror)
    for _ in range(len(mirror)): hid.press('backspace')
    hid.press('backspace') # Remove the enter
    time.sleep(2)

    # PHASE 6: Word-by-Word Navigation (Alt/Opt)
    # Action: Jump words to the start, then jump back.
    print("Phase 6: Word-Jump Navigation")
    for _ in range(10): hid.hotkey('alt', 'left')
    for _ in range(10): hid.hotkey('alt', 'right')
    time.sleep(2)

    # PHASE 7: The "Select-All" Duplicate
    # Action: Select all, copy, go to end, enter, paste, then select that line and delete.
    print("Phase 7: Block Copy/Delete")
    hid.hotkey(CMD, 'a')
    hid.hotkey(CMD, 'c')
    hid.hotkey(CMD, 'right')
    hid.press('enter')
    hid.hotkey(CMD, 'v')
    hid.hotkey('shift', 'up')
    hid.press('backspace')
    time.sleep(2)


# PHASE 6: UI Resilience (Spotlight Search)
    # 目的：验证快捷键能否在不破坏编辑器内容的情况下，完成系统级焦点的切出与切回。
    print("Phase 8: Spotlight UI Resilience")
    hid.hotkey(CMD, 'space') # 唤起 Spotlight
    time.sleep(0.8)          # 关键：给 macOS 动画留出 800ms 缓冲
    
    hid.write("Gemini Test") # 在搜索框输入
    time.sleep(1)
    
    hid.press('escape')      # 关闭 Spotlight 搜索结果
    time.sleep(0.3)
    hid.press('escape')      # 再次退出（确保彻底回到浏览器焦点）
    time.sleep(0.5)
    
    # PHASE 7: State Persistence (App Switcher)
    # 目的：验证修饰键（Modifier）的“长按”持久性。
    # 逻辑：按住 CMD 不放，连续点按两次 Tab，最后释放 CMD。
    print("Phase 9: Modifier State Persistence (Cmd+Tab)")
    hid.keyDown(CMD)         # 激活持久化按住
    time.sleep(0.2)
    
    hid.press('tab')         # 唤起切换界面
    time.sleep(0.8)          # 停留观察
    
    hid.press('tab')         # 移动到下一个应用
    time.sleep(0.8)
    
    hid.keyUp(CMD)           # 物理释放，确认系统完成切换
    time.sleep(1)            # 等待应用激活动画

    # FINAL SYNC
    print("Test finished. Result should be identical to start.")

    # 在脚本最后
    print(f"Final Internal Modifiers: {hex(hid._held_modifiers)}")
    print(f"Final Pressed Keys: {hid._pressed_keys}")

my_hid = HIDController(CH9329(SerialTransport('/dev/ttyUSB6', 9600)))
run_circular_test(my_hid)