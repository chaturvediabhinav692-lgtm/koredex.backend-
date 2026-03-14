from calc import add


def test_add_basic():
    assert add(2, 2) == 4
    assert add(3, 2) == 5
    assert add(10, 1) == 11


def test_add_negative():
    assert add(-1, 1) == 0
    assert add(-3, -2) == -5


def test_add_zero():
    assert add(0, 5) == 5
    assert add(7, 0) == 7
