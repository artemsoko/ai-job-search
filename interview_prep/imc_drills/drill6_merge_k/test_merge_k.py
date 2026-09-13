import itertools

from merge_k import merge_sorted


def test_two_streams():
    assert list(merge_sorted([[1, 3, 5], [2, 4, 6]])) == [1, 2, 3, 4, 5, 6]


def test_three_streams_with_ties():
    assert list(merge_sorted([[1, 4], [1, 3], [2, 2]])) == [1, 1, 2, 2, 3, 4]


def test_empty_stream_list():
    assert list(merge_sorted([])) == []


def test_some_streams_empty():
    assert list(merge_sorted([[], [1, 2], []])) == [1, 2]


def test_single_stream_passthrough():
    assert list(merge_sorted([[5, 6, 7]])) == [5, 6, 7]


def test_uneven_lengths():
    assert list(merge_sorted([[1], [2, 3, 4, 5]])) == [1, 2, 3, 4, 5]


def test_negatives():
    assert list(merge_sorted([[-5, 0], [-3, 2]])) == [-5, -3, 0, 2]


def test_is_lazy_with_infinite_streams():
    """If your implementation materialises the input, this test hangs forever."""
    evens = itertools.count(0, 2)
    odds = itertools.count(1, 2)
    got = list(itertools.islice(merge_sorted([evens, odds]), 6))
    assert got == [0, 1, 2, 3, 4, 5]


def test_accepts_generators_not_just_lists():
    a = (x for x in [1, 4, 7])
    b = (x for x in [2, 5, 8])
    assert list(merge_sorted([a, b])) == [1, 2, 4, 5, 7, 8]
