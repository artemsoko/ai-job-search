import pytest

from window_max import sliding_window_max


def test_classic_case():
    assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]


def test_window_of_one_is_identity():
    assert sliding_window_max([4, 2, 9], 1) == [4, 2, 9]


def test_window_equals_length():
    assert sliding_window_max([4, 2, 9], 3) == [9]


def test_monotonic_increasing():
    assert sliding_window_max([1, 2, 3, 4], 2) == [2, 3, 4]


def test_monotonic_decreasing():
    assert sliding_window_max([4, 3, 2, 1], 2) == [4, 3, 2]


def test_all_equal():
    assert sliding_window_max([7, 7, 7], 2) == [7, 7]


def test_negatives():
    assert sliding_window_max([-5, -2, -8, -1], 2) == [-2, -2, -1]


def test_empty_input():
    assert sliding_window_max([], 3) == []


def test_window_larger_than_input_raises():
    with pytest.raises(ValueError):
        sliding_window_max([1, 2], 5)


def test_zero_window_raises():
    with pytest.raises(ValueError):
        sliding_window_max([1, 2], 0)
