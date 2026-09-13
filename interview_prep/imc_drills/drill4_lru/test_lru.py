import pytest

from lru import LRUCache


def test_get_missing_is_none():
    assert LRUCache(2).get("a") is None


def test_put_then_get():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert len(c) == 1


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3
    assert len(c) == 2


def test_get_counts_as_a_use():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")          # a is now most recent, so b must be evicted next
    c.put("c", 3)
    assert c.get("b") is None
    assert c.get("a") == 1


def test_update_existing_key_does_not_grow():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("a", 9)
    assert c.get("a") == 9
    assert len(c) == 1


def test_update_existing_key_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 3)
    c.put("c", 4)
    assert c.get("b") is None
    assert c.get("a") == 3


def test_recency_order_visible():
    c = LRUCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    c.get("a")
    assert c.keys_mru_first() == ["a", "c", "b"]


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") is None
    assert c.get("b") == 2


def test_zero_capacity_raises():
    with pytest.raises(ValueError):
        LRUCache(0)
