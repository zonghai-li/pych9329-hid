import pytest
from tests.conftest import FakeTransportWithFakeCH
from pych9329_hid import HIDController


class TestHotkeyEdgeCases:
    """Edge case tests for hotkey() method."""

    def setup_method(self):
        """Set up test fixtures with FakeTransportWithFakeCH."""
        self.fake_transport = FakeTransportWithFakeCH()
        self.h = HIDController(self.fake_transport)
        self.h.keypress_hold_time = 0.01
        self.fake_transport._hid.keyboard_reports.clear()

    def _get_keyboard_reports(self):
        """Extract (modifier, keycodes) tuples from keyboard reports."""
        reports = []
        for report in self.fake_transport._hid.keyboard_reports:
            mod = report[0]
            codes = list(report[1])
            reports.append((mod, codes))
        return reports

    def test_hotkey_empty_args(self):
        """Edge case: no arguments."""
        self.h.hotkey()
        reports = self._get_keyboard_reports()
        assert len(reports) == 0, "No reports should be sent with no arguments"

    def test_hotkey_modifier_only(self):
        """Edge case: only modifier, no keycodes.

        When only modifiers are passed, the current implementation
        still sends release reports but no press reports with keycodes.
        """
        self.h.hotkey("ctrl")
        reports = self._get_keyboard_reports()

        assert len(reports) == 6, f"Expected 6 reports (3 press + 3 release), got {len(reports)}"

        for i in range(3):
            mod, codes = reports[i]
            assert mod == 0x01, f"Press phase, Report {i}: modifier should be Ctrl"
            assert all(k == 0 for k in codes), f"Press phase, Report {i}: all keycodes should be 0"

        for i in range(3, 6):
            mod, codes = reports[i]
            assert mod == 0x00, f"Release phase, Report {i}: modifier should be released"

    def test_hotkey_keycode_only(self):
        """Edge case: only keycode, no modifier."""
        self.h.hotkey("a")
        reports = self._get_keyboard_reports()
        mod, codes = reports[0]
        assert 0x04 in codes, "Should include 'a' keycode (0x04)"

    def test_hotkey_modifier_and_keycode(self):
        """Normal case: modifier + keycode."""
        self.h.hotkey("ctrl", "c")
        reports = self._get_keyboard_reports()

        assert len(reports) == 9, f"Should have exactly 9 calls, got {len(reports)}"

        for i in range(3):
            mod, codes = reports[i]
            assert mod == 0x01, f"Step 1, Report {i}: modifier should be Ctrl"
            assert 0x06 in codes, f"Step 1, Report {i}: should include 'c' keycode (0x06)"

        for i in range(3, 6):
            mod, codes = reports[i]
            assert mod == 0x01, f"Step 2, Report {i}: modifier should still be held"
            assert all(k == 0 for k in codes), f"Step 2, Report {i}: all keycodes should be 0"

        for i in range(6, 9):
            mod, codes = reports[i]
            assert mod == 0x00, f"Step 3, Report {i}: modifier should be released"

    def test_hotkey_multiple_keycodes(self):
        """Edge case: multiple keycodes (e.g., hotkey("a", "b", "c"))."""
        self.h.hotkey("a", "b", "c")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x00, "No modifiers"
        assert 0x04 in codes1, "Should include 'a' (0x04)"
        assert 0x05 in codes1, "Should include 'b' (0x05)"
        assert 0x06 in codes1, "Should include 'c' (0x06)"

    def test_hotkey_duplicate_keycodes(self):
        """Edge case: duplicate keycodes in arguments."""
        self.h.hotkey("a", "a")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert codes1.count(0x04) == 1, "Duplicate keycodes should be removed"

    def test_hotkey_duplicate_with_modifier(self):
        """Edge case: duplicate keycodes with modifier."""
        self.h.hotkey("ctrl", "a", "a")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert codes1.count(0x04) == 1, "Duplicate keycodes should be removed"

    def test_hotkey_state_persistence_modifiers(self):
        """Test that existing _held_modifiers is restored correctly after hotkey.

        Note: hotkey() does NOT combine with pre-existing modifiers.
        It only uses the modifiers from its arguments.
        """
        self.h._held_modifiers = 0x02

        self.h.hotkey("ctrl", "c")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, f"Step 1: should use Ctrl only, got {hex(mod1)}"

        assert self.h._held_modifiers == 0x02, f"Should restore existing modifier, got {hex(self.h._held_modifiers)}"

    def test_hotkey_state_persistence_pressed_keys(self):
        """Test that _pressed_keys is cleared after hotkey."""
        self.h._pressed_keys = [0x04, 0x05]

        self.h.hotkey("ctrl", "c")

        assert self.h._pressed_keys == [], f"_pressed_keys should be cleared, got {self.h._pressed_keys}"

    def test_hotkey_state_persistence_combined(self):
        """Test state persistence with both modifiers and pressed keys.

        Note: hotkey() does NOT combine with pre-existing modifiers.
        """
        self.h._held_modifiers = 0x02
        self.h._pressed_keys = [0x04]

        self.h.hotkey("ctrl", "c")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, f"Should use Ctrl only, got {hex(mod1)}"

        assert self.h._held_modifiers == 0x02, f"Should restore existing modifier, got {hex(self.h._held_modifiers)}"
        assert self.h._pressed_keys == [], "Should clear pressed keys"

    def test_hotkey_special_keys(self):
        """Test hotkey with special keys (F4, etc.)."""
        self.h.hotkey("alt", "f4")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert 0x3D in codes1, "Should include F4 keycode (0x3D)"

    def test_hotkey_numpad_keys(self):
        """Test hotkey with numpad keys."""
        self.h.hotkey("alt", "num2")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert 0x5A in codes1, "Should include num2 keycode (0x5A)"

    def test_hotkey_case_insensitive_modifier(self):
        """Test that modifiers are case-insensitive."""
        for var in ["CTRL", "Ctrl", "ctrl"]:
            self.fake_transport = FakeTransportWithFakeCH()
            self.h = HIDController(self.fake_transport)
            self.h.keypress_hold_time = 0.01
            self.fake_transport._hid.keyboard_reports.clear()

            self.h.hotkey(var, "c")

            reports = self._get_keyboard_reports()
            mod1, _ = reports[0]
            assert mod1 == 0x01, f"Modifier case {var} should work, got {hex(mod1)}"

    def test_hotkey_mixed_case_sensitive_keycode(self):
        """Test that keycodes handle case correctly (A and a both work)."""
        self.h.hotkey("ctrl", "A")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, "Step 1: Ctrl only"
        assert 0x04 in codes1, "Should include 'A'/'a' keycode (0x04)"

    def test_hotkey_special_characters(self):
        """Test hotkey with special characters like !, @, #."""
        self.h.hotkey("ctrl", "!")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x03, f"Step 1: Ctrl+Shift, got {hex(mod1)}"

        mod2, codes2 = reports[1]
        assert 0x1E in codes2, "Should include Shift+1 keycode (0x1E)"

    def test_hotkey_max_keycodes(self):
        """Test hotkey with more than 6 keycodes (should truncate)."""
        self.h.hotkey("a", "b", "c", "d", "e", "f", "g", "h")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert len([c for c in codes1 if c != 0]) == 6, f"Should truncate to 6 keycodes, got {len([c for c in codes1 if c != 0])}"

    def test_hotkey_with_space(self):
        """Test hotkey with space character."""
        self.h.hotkey("alt", " ")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert 0x2C in codes1, "Should include space keycode (0x2C)"

    def test_hotkey_arrows(self):
        """Test hotkey with arrow keys."""
        self.h.hotkey("ctrl", "up")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert 0x52 in codes1, "Should include up arrow keycode (0x52)"

    def test_hotkey_right_modifier(self):
        """Test hotkey with right-side modifiers."""
        self.h.hotkey("rctrl", "c")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x10, f"Should use Right Ctrl modifier (0x10), got {hex(mod1)}"

    def test_hotkey_win_key(self):
        """Test hotkey with Windows key."""
        self.h.hotkey("win", "r")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x08, f"Step 1: Win key, got {hex(mod1)}"

        mod2, codes2 = reports[1]
        assert 0x15 in codes2, "Should include 'r' keycode (0x15)"

    def test_hotkey_three_modifiers(self):
        """Test hotkey with three modifiers."""
        self.h.hotkey("ctrl", "shift", "alt")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x07, f"Should combine Ctrl+Shift+Alt, got {hex(mod1)}"

    def test_hotkey_modifier_with_numpad_digit(self):
        """Test hotkey with modifier and numpad digit (like alt+num2)."""
        self.h.hotkey("alt", "num2")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x04, f"Should use Alt modifier (0x04), got {hex(mod1)}"
        assert 0x5A in codes1, f"Should include num2 keycode (0x5A), got {codes1}"

    def test_hotkey_with_printable_chars(self):
        """Test hotkey with various printable characters."""
        test_cases = [
            ("ctrl", "a", 0x01, 0x04),
            ("ctrl", "z", 0x01, 0x1D),
            ("shift", "1", 0x02, 0x1E),
        ]

        for mod_name, char, expected_mod, expected_code in test_cases:
            self.fake_transport = FakeTransportWithFakeCH()
            self.h = HIDController(self.fake_transport)
            self.h.keypress_hold_time = 0.01
            self.fake_transport._hid.keyboard_reports.clear()

            self.h.hotkey(mod_name, char)

            reports = self._get_keyboard_reports()
            mod1, codes1 = reports[0]
            assert mod1 == expected_mod, f"{mod_name}+{char}: expected mod {hex(expected_mod)}, got {hex(mod1)}"
            assert expected_code in codes1, f"{mod_name}+{char}: expected code {hex(expected_code)}, got {codes1}"

    def test_hotkey_preserves_other_modifiers(self):
        """Test that hotkey restores pre-existing modifiers after completion.

        Note: hotkey() does NOT combine with pre-existing modifiers.
        It only uses the modifiers from its arguments during the hotkey press.
        """
        self.h._held_modifiers = 0x04

        self.h.hotkey("ctrl", "c")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, f"Should use Ctrl only during hotkey, got {hex(mod1)}"

        assert self.h._held_modifiers == 0x04, f"Should restore Alt, got {hex(self.h._held_modifiers)}"

    def test_hotkey_f4_closes_app(self):
        """Test Alt+F4 hotkey commonly used to close applications."""
        self.h.hotkey("alt", "f4")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x04, "Should use Alt modifier"
        assert 0x3D in codes1, "Should include F4 keycode (0x3D)"

    def test_hotkey_ctrl_c_copy(self):
        """Test Ctrl+C hotkey commonly used for copy."""
        self.h.hotkey("ctrl", "c")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, "Should use Ctrl modifier"
        assert 0x06 in codes1, "Should include 'c' keycode"

    def test_hotkey_ctrl_v_paste(self):
        """Test Ctrl+V hotkey commonly used for paste."""
        self.h.hotkey("ctrl", "v")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, "Should use Ctrl modifier"
        assert 0x19 in codes1, "Should include 'v' keycode (0x19)"

    def test_hotkey_ctrl_z_undo(self):
        """Test Ctrl+Z hotkey commonly used for undo."""
        self.h.hotkey("ctrl", "z")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, "Should use Ctrl modifier"
        assert 0x1D in codes1, "Should include 'z' keycode (0x1D)"

    def test_hotkey_ctrl_a_select_all(self):
        """Test Ctrl+A hotkey commonly used for select all."""
        self.h.hotkey("ctrl", "a")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, "Should use Ctrl modifier"
        assert 0x04 in codes1, "Should include 'a' keycode"

    def test_hotkey_ctrl_x_cut(self):
        """Test Ctrl+X hotkey commonly used for cut."""
        self.h.hotkey("ctrl", "x")
        reports = self._get_keyboard_reports()

        mod1, codes1 = reports[0]
        assert mod1 == 0x01, "Should use Ctrl modifier"
        assert 0x1B in codes1, "Should include 'x' keycode (0x1B)"
