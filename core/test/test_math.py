from core.math import clamp, previous_multiple, next_multiple


def test_clamp_minimum():
    assert clamp(-1, 0, 1) == 0
    assert clamp(-5, -2, -1) == -2
    assert clamp(2, 4, 8) == 4


def test_clamp_maximum():
    assert clamp(2, 0, 1) == 1
    assert clamp(5, -2, -1) == -1
    assert clamp(10, 6, 8) == 8


def test_clamp_untouched():
    assert clamp(0.5, 0, 1) == 0.5
    assert clamp(-2, -4, 1) == -2


def test_previous_multiple_identity():
    assert previous_multiple(1, 1) == 1
    assert previous_multiple(4, 4) == 4


def test_previous_multiple_zero():
    assert previous_multiple(2, 4) == 0


def test_previous_multiple_variety():
    assert previous_multiple(129, 128) == 128


def test_previous_multiple_floats():
    assert previous_multiple(1.1, 2) == 0
    assert previous_multiple(2.001, 2) == 2
    assert previous_multiple(2.0, 2.001) == 0


def test_previous_multiple_k():
    assert previous_multiple(9, 2, k=2) == 6
    assert previous_multiple(9, 2, k=3) == 4
    assert previous_multiple(9, 2, k=4) == 2

    assert previous_multiple(-100, 2, k=40) == -178


def test_next_multiple_identity():
    assert next_multiple(1, 1) == 1
    assert next_multiple(4, 4) == 4


def test_next_multiple_variety():
    assert next_multiple(63, 64) == 64
    assert next_multiple(129, 128) == 256


def test_next_multiple_floats():
    assert next_multiple(1.1, 2) == 2
    assert next_multiple(2.001, 2) == 4
