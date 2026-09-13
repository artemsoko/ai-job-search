import pytest

from top_k import StreamingTopK, top_k_frequent


def test_simple_counts():
    assert top_k_frequent(["a", "b", "a", "c", "a", "b"], 2) == ["a", "b"]


def test_k_larger_than_distinct_returns_all():
    assert top_k_frequent(["a", "b"], 5) == ["a", "b"]


def test_k_zero_is_empty():
    assert top_k_frequent(["a"], 0) == []


def test_empty_stream():
    assert top_k_frequent([], 3) == []


def test_ties_broken_by_item_ascending():
    assert top_k_frequent(["b", "a", "c"], 2) == ["a", "b"]


def test_single_item_repeated():
    assert top_k_frequent(["x"] * 100, 1) == ["x"]


def test_streaming_matches_batch():
    data = ["a", "b", "a", "c", "a", "b", "d", "d", "d", "d"]
    s = StreamingTopK(2)
    for item in data:
        s.add(item)
    assert s.top() == top_k_frequent(data, 2)


def test_streaming_updates_as_counts_change():
    s = StreamingTopK(1)
    s.add("a")
    assert s.top() == ["a"]
    s.add("b")
    s.add("b")
    assert s.top() == ["b"]


def test_rejects_negative_k():
    with pytest.raises(ValueError):
        top_k_frequent(["a"], -1)
