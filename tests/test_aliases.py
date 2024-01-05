from __future__ import annotations

from basedtyping import (
    dict_itemiterator,
    dict_items,
    dict_keyiterator,
    dict_keys,
    dict_valueiterator,
    dict_values,
    list_iterator,
    list_reverseiterator,
    set_iterator,
    tuple_iterator,
)
import _collections_abc


def test_aliases():
    dk = dict_keys[int, str]
    dv = dict_values[int, str]
    di = dict_items[int, str]
    t1 = tuple_iterator[int, str]
    t2 = tuple_iterator[int, ...]
    si = set_iterator[int]
    lr = list_reverseiterator[int]
    li = list_iterator[int]
    dii = dict_itemiterator[int, str]
    dvi = dict_valueiterator[int, str]
    dki = dict_keyiterator[int, str]
    print(dk, dv, di, t1, t2, si, lr, li, dii, dvi, dki)  # noqa: T201
