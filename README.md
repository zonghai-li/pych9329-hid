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
from pych9329_hid import HIDController, SerialTransport

# Option 2: Short alias (recommended)
from pych9329 import HIDController, SerialTransport
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
    
    # Get device information
    info = ch9329.get_info()
    print(f"Version: {info['version']}")
    print(f"USB Connected: {info['usb_connected']}")
    print(f"Num Lock: {info['num_lock_on']}")
    print(f"Caps Lock: {info['caps_lock_on']}")
    print(f"Scroll Lock: {info['scroll_lock_on']}")
```

**Keymap Support:**
- Characters: a-z, A-Z, 0-9, space, punctuation
- Special keys: f1-f12, enter, backspace, tab, esc, home, end, pageup, pagedown, insert, delete, arrows
- Modifiers: ctrl, shift, alt, cmd (also supports: control, option, win, command, meta, super)

### High-Level HID Controller

```python
from pych9329 import HIDController, SerialTransport

# Create HID controller
with SerialTransport(port='/dev/ttyUSB0', baudrate=115200) as transport:
    controller = HIDController(transport, screen_width=1920, screen_height=1080)
    
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

#### Device Information

| Method | Description | Returns |
|---------|-------------|---------|
| `get_info()` | Get device information | `dict` with keys: `version`, `usb_connected`, `num_lock_on`, `caps_lock_on`, `scroll_lock_on` |

#### Keyboard Operations

| Method | Description | Returns |
|---------|-------------|---------|
| `send_keyboard(modifier, keycodes)` | Send keyboard report | `bool` - True if successful |

#### Mouse Operations

| Method | Description | Returns |
|---------|-------------|---------|
| `send_mouse_rel(dx, dy, buttons, wheel)` | Send relative mouse movement | `bool` - True if successful |
| `send_mouse_abs(x, y, buttons, wheel)` | Send absolute mouse position | `bool` - True if successful |

## ⚠️ Error Handling

### CH9329 Layer

The CH9329 protocol layer uses a hybrid error handling strategy:

- **Soft Errors** (timeout, ACK error): Return `False` with a warning
  - Device doesn't respond within timeout
  - Device returns error status in ACK
  
- **Hard Errors** (transport failure): Raise `SerialTransportError`
  - Serial port disconnected
  - Serial port read/write failure
  - Invalid serial port configuration

### HIDController Layer

HIDController does not check return values from CH9329 - failures propagate naturally to the caller. This allows users to decide how to handle errors based on their use case.

### SerialTransport Layer

The transport layer provides custom exceptions:

- `SerialTransportError`: Base exception for transport errors
- `SerialTransportClosedError`: Raised when operation attempted on closed transport

---

### HIDController (High-Level API)

#### Keyboard Operations

| Method | Description | Example |
|---------|-------------|----------|
| `press(key)` | Press and release a key | `controller.press('a')` |
| `keyDown(key)` | Press and hold a key | `controller.keyDown('shift')` |
| `keyUp(key)` | Release a key | `controller.keyUp('shift')` |
| `write(text)` | Type a string | `controller.write('Hello\n')` |
| `hotkey(*keys)` | Press key combination | `controller.hotkey('cmd', 'a')` |
| `releaseAllKey()` | Release all keyboard keys | `controller.releaseAllKey()` |
| `numpadPress(key)` | Press numpad key | `controller.numpadPress('7')` |
| `numpadWrite(text)` | Type numpad characters | `controller.numpadWrite('123')` |

#### Mouse Button Operations

| Method | Description | Example |
|---------|-------------|----------|
| `click(button, clicks)` | Click mouse button | `controller.click('left', clicks=2)` |
| `mouseDown(button)` | Press and hold button | `controller.mouseDown('left')` |
| `mouseUp(button)` | Release button | `controller.mouseUp('left')` |
| `releaseMouseButton()` | Release all mouse buttons | `controller.releaseMouseButton()` |

#### Mouse Movement

| Method | Description | Example |
|---------|-------------|----------|
| `moveTo(x, y, duration)` | Move mouse to coordinates | `controller.moveTo(100, 200, duration=0.5)` |
| `moveRel(dx, dy, duration)` | Move mouse relatively | `controller.moveRel(10, 5)` |

#### Drag Operations

| Method | Description | Example |
|---------|-------------|----------|
| `dragRel(dx, dy)` | Drag relatively | `controller.dragRel(50, 30)` |
| `dragTo(x, y)` | Drag to coordinates | `controller.dragTo(100, 200)` |

#### Scrolling

| Method | Description | Example |
|---------|-------------|----------|
| `scroll(clicks)` | Vertical scroll | `controller.scroll(5)` |
| `hscroll(clicks)` | Horizontal scroll | `controller.hscroll(-2)` |

#### Hardware Operations

| Method | Description | Returns |
|---------|-------------|---------|
| `reset()` | Reset cursor to (0,0) | None |
| `getDeviceInfo()` | Get device information | `dict` with device info |

### SerialTransport (Transport Layer)

| Method | Description | Returns |
|---------|-------------|---------|
| `write(data)` | Write raw bytes to port | None |
| `read(size)` | Read up to `size` bytes | `bytes` read (may be empty on timeout) |
| `read_all()` | Read all available data | All available bytes |
| `is_open()` | Check if port is open | `bool` |
| `close()` | Close the serial port | None |

---

## 🔧 Configuration

### SerialTransport Parameters

| Parameter | Type | Default | Description |
|-----------|--------|----------|-------------|
| `port` | str | Required | Serial port path (e.g., '/dev/ttyUSB0' or 'COM3') |
| `baudrate` | int | 115200 | Baud rate (115200 recommended for CH9329) |
| `timeout` | float | 0.005 | Read/write timeout in seconds |

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
from pych9329 import HIDController, SerialTransport
import time

with SerialTransport(port='/dev/ttyUSB0', baudrate=115200) as transport:
    controller = HIDController(transport, screen_width=1920, screen_height=1080)
    
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
