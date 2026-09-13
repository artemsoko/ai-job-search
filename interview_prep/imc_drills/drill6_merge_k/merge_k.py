"""Merge K sorted streams into one sorted stream, lazily.

Out loud before coding:
  * Naive: concatenate everything and sort -> O(N log N) and holds all N in memory.
  * Heap of K stream heads -> O(N log K) time and O(K) memory. Say why that matters when the
    streams are huge or infinite.
  * MUST BE A GENERATOR: the tests feed an infinite stream, so materialising is a hang, not a
    slow answer.
  * Ties: heap comparison must not blow up when values are equal - push (value, stream_index)
    so the tuple comparison never reaches a non-comparable element.
"""
from __future__ import annotations

from typing import Iterable, Iterator


def merge_sorted(streams: list[Iterable[int]]) -> Iterator[int]:
    """Yield every value from every stream, in ascending order. Must be lazy."""
    raise NotImplementedError
