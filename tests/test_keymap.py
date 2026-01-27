import pytest
from pych9329_hid.keymap import to_hid_code, MOD_LSHFT, MOD_NONE


def test_letters_and_shift():
    mod, code = to_hid_code('a')
    assert mod == MOD_NONE
    assert code is not None

    mod, code = to_hid_code('A')
    assert mod == MOD_LSHFT
    assert code is not None


def test_shifted_symbols():
    mod, code = to_hid_code('!')
    assert mod == MOD_LSHFT
    assert code is not None

    mod, code = to_hid_code('@')
    assert mod == MOD_LSHFT
    assert code is not None


def test_special_keys():
    mod, code = to_hid_code('enter')
    assert mod == MOD_NONE
    assert code == 0x28

    mod, code = to_hid_code('space')
    assert code == 0x2C


def test_unknown():
    mod, code = to_hid_code('非ASCII')
    assert code is None
