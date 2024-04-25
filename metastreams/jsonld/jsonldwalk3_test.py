## begin license ##
#
# "Metastreams Json LD" provides utilities for handling json-ld data structures
#
# Copyright (C) 2024 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Metastreams Json LD"
#
# "Metastreams Json LD" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Metastreams Json LD" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Metastreams Json LD"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from .jsonldwalk3 import walk
import pytest


def test_simple_basics():
    r = []
    w = walk({"a": lambda *a: r.append(a)})
    w({"a": "whatever-is-here"})
    assert r.pop() == ({}, {"a": "whatever-is-here"}, "a", "whatever-is-here")
    w({"a": [42]})
    assert r.pop() == ({}, {"a": [42]}, "a", [42])


def test_nested_rule():
    r = []
    w = walk(
        {
            "a": {
                "b": {
                    "c": lambda *a: r.append(a),
                },
            },
        }
    )
    w({"a": [{"b": [{"c": 42}]}]})
    assert r.pop() == ({}, {"c": 42}, "c", 42)
    with pytest.raises(Exception) as e:
        w({"a": [{"b": 42}]})
    assert (
        str(e.value)
        == "TypeError: 'int' object is not iterable at:\n> a\n-> b while processing:\n{'b': 42}"
    )


def test_default_rule():
    r = []
    rules = {"*": lambda a, s, p, o: r.append((p, "default"))}
    j0 = {"a/a": 42, "a/b": 2}
    walk(rules)(j0)
    assert r.pop() == ("a/b", "default")
    assert r.pop() == ("a/a", "default")

    # should have same result
    w = walk({"a": rules})
    w({"a": [j0]})
    assert r.pop() == ("a/b", "default")
    assert r.pop() == ("a/a", "default")

    # should have same result
    w = walk({"*": rules})
    w({"a": [j0]})
    assert r.pop() == ("a/b", "default")
    assert r.pop() == ("a/a", "default")


def test_values():
    r = []
    rules = {
            '@value': lambda *a: r.append(a), # returns None
            '*'     : lambda *a: r.append(a),
            }
    w = walk(rules)
    s = {'@value': "hello",
         'b/b': [{'id': '16'}]}
    w(s)
    assert r.pop() == (None, s, 'b/b', [{'id': '16'}])
    assert r.pop() == ({}, s, '@value', "hello")

    # should have same result
    w = walk({'a': rules})
    w({'a': [s]})
    assert r.pop() == (None, s, 'b/b', [{'id': '16'}])
    assert r.pop() == ({}, s, '@value', "hello")
