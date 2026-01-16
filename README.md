# PyCH9329-HID

**PyCH9329-HID** is a high-level Python package for CH9329 HID chip, designed to provide seamless, OS-independent peripheral control via serial communication.

---

## 🎯 Target Use Cases

| Use Case | Description |
|-----------|-------------|
| **AI Vision Agents** | Perfect for models like UI-TARS or Claude Computer Use that require high-fidelity interaction with a screen based on visual coordinates |
| **Test Automation** | Reliable UI testing on macOS/Windows/Linux without requiring OS-level accessibility permissions |
| **Embedded Robotics** | Controlling computers via Raspberry Pi or ESP32 using a physical CH9329 USB dongle |

---

## 📦 Installation

```bash
pip install pych9329-hid
```

### Requirements

- Python >= 3
- pyserial

---

### Import Options

You can use either of the full package name or shorter alias:

```python
# Option 1: Full package name
from pych9329_hid import HIDController, CH9329, SerialTransport

# Option 2: Short alias (recommended)
from pych9329 import HIDController, CH9329, SerialTransport
```

Both options work identically - choose whichever you prefer!

---

## 🚀 Quick Start

### Basic Usage - Low Level Protocol

```python
from pych9329 import CH9329, SerialTransport

# Create transport and CH9329 instance
with SerialTransport(port='/dev/ttyUSB0', baudrate=115200) as transport:
    ch9329 = CH9329(transport)
    
    # Send keyboard report
    ch9329.send_keyboard(modifier=0, keycodes=[0x04])
    
    # Send relative mouse movement
    ch9329.send_mouse_rel(dx=10, dy=5, buttons=0x01)
    
    # Send absolute mouse position
    ch9329.send_mouse_abs(x=100, y=200, buttons=0x01)
```

### High-Level HID Controller

```python
from pych9329 import HIDController, CH9329, SerialTransport

# Create HID controller
with SerialTransport(port='/dev/ttyUSB0', baudrate=115200) as transport:
    ch9329 = CH9329(transport)
    controller = HIDController(ch9329, screen_width=1920, screen_height=1080)
    
    # Keyboard operations
    controller.press('a')
    controller.write('Hello World')
    controller.hotkey('cmd', 'space')
    
    # Mouse operations
    controller.moveTo(100, 200, duration=0.5)
    controller.click(button='left')
    controller.dragRel(50, 30)
    
    # Scrolling
    controller.scroll(5)  # Scroll up
    controller.hscroll(-2)  # Scroll left
```

---

## 📚 API Reference

### CH9329 (Low-Level Protocol)

| Method | Description |
|---------|-------------|
| `send_keyboard(modifier, keycodes)` | Send keyboard report with modifier and keycodes |
| `send_mouse_rel(dx, dy, buttons, wheel)` | Send relative mouse movement |
| `send_mouse_abs(x, y, buttons, wheel)` | Send absolute mouse position |

### HIDController (High-Level API)

#### Keyboard Operations

| Method | Description | Example |
|---------|-------------|----------|
| `press(key)` | Press and release a key | `controller.press('a')` |
| `keyDown(key)` | Press and hold a key | `controller.keyDown('shift')` |
| `keyUp(key)` | Release a key | `controller.keyUp('shift')` |
| `write(text)` | Type a string | `controller.write('Hello')` |
| `hotkey(*keys)` | Press key combination | `controller.hotkey('cmd', 'a')` |

#### Mouse Operations

| Method | Description | Example |
|---------|-------------|----------|
| `moveTo(x, y, duration)` | Move mouse to coordinates | `controller.moveTo(100, 200, duration=0.5)` |
| `moveRel(dx, dy, duration)` | Move mouse relatively | `controller.moveRel(10, 5)` |
| `click(button, clicks)` | Click mouse button | `controller.click('left', clicks=2)` |
| `mouseDown(button)` | Press and hold button | `controller.mouseDown('left')` |
| `mouseUp(button)` | Release button | `controller.mouseUp('left')` |
| `dragRel(dx, dy)` | Drag relatively | `controller.dragRel(50, 30)` |
| `dragTo(x, y)` | Drag to coordinates | `controller.dragTo(100, 200)` |

#### Scrolling

| Method | Description | Example |
|---------|-------------|----------|
| `scroll(clicks)` | Vertical scroll | `controller.scroll(5)` |
| `hscroll(clicks)` | Horizontal scroll | `controller.hscroll(-2)` |

---

## 🔧 Configuration

### HIDController Parameters

| Parameter | Type | Default | Description |
|-----------|--------|----------|-------------|
| `screen_width` | int | 1920 | Screen width in pixels |
| `screen_height` | int | 1080 | Screen height in pixels |
| `dwelling_time` | float | 0.01 | Delay between operations (seconds) |
| `move_interval` | float | 0.015 | Mouse movement interval (seconds) |
| `keypress_hold_time` | float | 0.05 | Key press duration (seconds) |
| `double_click_interval` | float | 0.1 | Double click interval (seconds) |
| `scroll_multiplier` | int | 5 | Scroll sensitivity multiplier |

---

## 📝 Examples

### List Available Serial Devices

```python
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"Port: {port.device}, Description: {port.description}")
```

### Complete Automation Example

```python
from pych9329_hid import HIDController, CH9329, SerialTransport
import time

with SerialTransport(port='/dev/ttyUSB0', baudrate=115200) as transport:
    ch9329 = CH9329(transport)
    controller = HIDController(ch9329, screen_width=1920, screen_height=1080)
    
    # Open Spotlight (macOS)
    controller.hotkey('cmd', 'space')
    time.sleep(0.5)
    
    # Type application name
    controller.write('Terminal')
    time.sleep(0.5)
    
    # Press Enter
    controller.press('enter')
    time.sleep(1)
    
    # Type command
    controller.write('echo "Hello from CH9329!"')
    controller.press('enter')
```



---

## ✨ Features

- ✅ **Low-level CH9329 protocol implementation** with ACK verification
- ✅ **High-level HID automation API** (keyboard, mouse, scrolling, dragging)
- ✅ **Smooth mouse movement** with interpolation
- ✅ **Drag and drop support** for UI automation
- ✅ **OS-independent** - works on macOS, Windows, Linux

---


## 📄 License

MIT License - see [LICENSE](LICENSE) file for details
