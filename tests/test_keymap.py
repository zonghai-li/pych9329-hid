import pytest
from src.keymap import char_to_hid, MOD_LSHFT, MOD_NONE


def test_letters_and_shift():
    mod, code = char_to_hid('a')
    assert mod == MOD_NONE
    assert code is not None

    mod, code = char_to_hid('A')
    assert mod == MOD_LSHFT
    assert code is not None


def test_shifted_symbols():
    mod, code = char_to_hid('!')
    assert mod == MOD_LSHFT
    assert code is not None

    mod, code = char_to_hid('@')
    assert mod == MOD_LSHFT
    assert code is not None


def test_special_keys():
    mod, code = char_to_hid('enter')
    assert mod == MOD_NONE
    assert code == 0x28

    mod, code = char_to_hid('space')
    assert code == 0x2C


def test_unknown():
    mod, code = char_to_hid('非ASCII')
    assert code is None
