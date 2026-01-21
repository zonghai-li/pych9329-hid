# ch9329.py
# @author zonghai@gmail.com
# @description Low-level driver for CH9329 UART-to-HID chip.

import time
import warnings

# Protocol Constants
FRAME_HEAD    = b'\x57\xAB'
ADDR_DEFAULT  = 0x00

# Command Codes
CMD_GET_INFO     = 0x01
CMD_SEND_KEY     = 0x02
CMD_SEND_MS_REL  = 0x05
CMD_SEND_MS_ABS  = 0x04
CMD_GET_PARA_CFG = 0x08

MOUSE_BUTTON_LEFT   = 0x01
MOUSE_BUTTON_RIGHT  = 0x02
MOUSE_BUTTON_MIDDLE = 0x04


ACK_TIMEOUT = 0.05  # seconds


class CH9329TimeoutError(Exception):
    """Raised when the hardware fails to respond within the expected window."""
    pass

class CH9329:
    """
    Core implementation of the CH9329 serial protocol.
    Provides reliable frame transmission with ACK verification.
    """

    def __init__(self, transport):
        """
        Args:
            transport: An instance of SerialTransport providing write() and read().
        """
        self.t = transport

    def _to_signed_char(self, v):
        # clamp to -127  to 127
        v = max(-127, min(127, v))
        return v & 0xFF 

    def _calculate_checksum(self, data: bytes) -> int:
        """
        CH9329 Checksum: Sum of all bytes from Head to Data, modulo 256.
        """
        return sum(data) & 0xFF

    def _send_frame(self, cmd: int, payload: bytes, retry: int = 3, timeout: float = ACK_TIMEOUT) -> bool:
        """
        Constructs, sends a frame, and validates the ACK from hardware.
        
        Logic Flow:
        1. Clear stale data from serial buffer.
        2. Build packet: HEAD(2) + ADDR(1) + CMD(1) + LEN(1) + DATA(N) + CS(1).
        3. Send and poll for valid ACK.
        """
        # 1. Build Packet
        frame = bytearray(FRAME_HEAD)
        frame.append(ADDR_DEFAULT)
        frame.append(cmd)
        frame.append(len(payload))
        frame.extend(payload)
        frame.append(self._calculate_checksum(frame))

        for attempt in range(retry):
            # Flush input to ensure we don't read an old ACK
            # Using read with a short timeout to clear buffer if transport doesn't have flush
            self.t.read(128)
            
            # 2. Send Packet
            self.t.write(frame)

            start_time = time.time()
            # print(start_time)
            while (time.time() - start_time) < timeout:
                response = self.t.read()
                # print(time.time() - start_time)
                # print(response)
                if not response:
                    continue
                
                # Search for Frame Head in response (handling potential garbage bytes)
                head_idx = response.find(FRAME_HEAD)
                if head_idx != -1 and len(response) >= head_idx + 6:
                    res_cmd = response[head_idx + 3]
                    res_status = response[head_idx + 5]
                    
                    # ACK CMD is always (Original CMD | 0x80)
                    if res_cmd == (cmd | 0x80):
                        if res_status == 0x00:
                            return True # Success
                        else:
                            # Hardware error (e.g., buffer full or invalid command)
                            break 
            
            time.sleep(0.02) # Short wait before retry( interval between attempts)

        warnings.warn(f"Failed to receive ACK for CMD 0x{cmd:02X} after {retry} retries.")
        return False

    # -------------------------------------------------
    # Keyboard API
    # -------------------------------------------------

    def send_keyboard(self, modifier: int, keycodes: list):
        """
        Sends a standard 8-byte USB HID keyboard report.
        
        Args:
            modifier: Bitmask (Shift, Ctrl, etc.)
            keycodes: List of up to 6 HID keycodes.
        """

        # Ensure exactly 6 keycodes in the payload
        keys = (keycodes[:6] + [0] * 6)[:6]
        payload = bytes([modifier, 0x00] + keys)

        self._send_frame(CMD_SEND_KEY, payload)


    # -------------------------------------------------
    # Mouse API
    # -------------------------------------------------

    def send_mouse_rel(self, dx: int = 0, dy: int = 0, buttons: int = 0, wheel: int = 0):
        """
        Relative mouse movement. Values: -127 to 127.
        """
        payload = bytes([
            0x01, # Relative mode flag
            buttons & 0x07,
            self._to_signed_char(dx),
            self._to_signed_char(dy),
            self._to_signed_char(wheel)
        ])

        self._send_frame(CMD_SEND_MS_REL, payload)

    def send_mouse_abs(self, x: int, y: int, buttons: int = 0, wheel: int = 0):
        """
        Absolute mouse movement (0-4095).
        Note: x and y are Little-Endian.
        """
        x = max(0, min(4095, x))
        y = max(0, min(4095, y))

        payload = bytes([
            0x02, # Absolute mode flag
            buttons & 0x07,
            x & 0xFF, (x >> 8) & 0xFF,
            y & 0xFF, (y >> 8) & 0xFF,
            self._to_signed_char(wheel)
        ])
        self._send_frame(CMD_SEND_MS_ABS, payload)